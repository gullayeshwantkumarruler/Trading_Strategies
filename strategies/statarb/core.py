"""Shared core for the equity stat-arb build (report: "Equity stat arb alpha and alt data").

Universe : 337 current S&P 500 large caps with full history 2004 -> Aug 2026 (same as paper 8;
           survivorship bias -> results are upper bounds).
Data     : cached by strategies/papers2026 (yfinance prices/volume, Ken French daily factors) and
           paper 8's FF5 residual / OU signal arrays (data/p8_signals.npz).
Timing   : weights decided at the close of day d (using data <= d) earn the excess return of d+1.
Costs    : the literature's common model — 5 bp per unit of one-way turnover (|w_d - w_{d-1}|_1)
           plus 1 bp per day on short notional; books normalised to unit gross leverage.
Trials   : every variant's daily net returns are logged to results/trials/ so a deflated Sharpe
           (ml4t.diagnostic) can be computed over everything tried.
"""
from __future__ import annotations

import io
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
P26 = ROOT.parent / "papers2026"
sys.path.insert(0, str(P26))

from common import (ANN, DATA_DIR as P26_DATA, _get, fetch, french_factors, plot_equity as _plot,  # noqa: E402
                    sp500_universe, stock_panel)

DATA = ROOT / "data"
RES = ROOT / "results"
TRIALS = RES / "trials"
for d in (DATA, RES, TRIALS):
    d.mkdir(exist_ok=True)

COST = 0.0005          # per unit one-way turnover
SHORT_FEE = 0.0001     # per day on short notional
START = "2010-01-01"
SPLIT = "2022-01-01"   # report 2022-2026 separately


# ----------------------------------------------------------------------------- data
_PANEL = None


def panel():
    """Dict with R (excess returns), px, vol, ff, B (betas, T x N x 5), eps (FF5 residuals) and
    the cached OU feature arrays, all aligned on the same dates/tickers."""
    global _PANEL
    if _PANEL is not None:
        return _PANEL
    u = sp500_universe(350)
    px, vol = stock_panel(u)
    ff = french_factors()
    px, vol = px.loc["2004-01-01":ff.index[-1]], vol.loc["2004-01-01":ff.index[-1]]
    full = px.notna().all() & (vol > 0).mean().gt(0.99)
    px, vol = px.loc[:, full], vol.loc[:, full]
    r = px.pct_change(fill_method=None).iloc[1:]
    ffa = ff.reindex(r.index).ffill()
    R = r.sub(ffa["rf"], axis=0)
    z = np.load(P26_DATA / "p8_signals.npz")
    assert z["eps"].shape == R.shape, "p8 cache does not match the panel; rerun p8 with --rebuild"
    _PANEL = dict(R=R, px=px.iloc[1:], vol=vol.iloc[1:], ff=ffa, B=z["B"], eps=z["eps"],
                  feats={k: z[k] for k in z.files if k not in ("B", "P", "eps")})
    return _PANEL


def sectors(tickers) -> pd.Series:
    """GICS sector per ticker (current classification, Wikipedia S&P 500 table)."""
    p = DATA / "gics_sectors.csv"
    if not p.exists():
        html = _get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies").decode("utf-8")
        t = pd.read_html(io.StringIO(html))[0]
        t["Symbol"] = t["Symbol"].astype(str).str.replace(".", "-", regex=False)
        t.set_index("Symbol")["GICS Sector"].to_csv(p)
    s = pd.read_csv(p, index_col=0).iloc[:, 0]
    return s.reindex(tickers).fillna("Unknown")


# ----------------------------------------------------------------------------- book helpers
def to_book(sig: np.ndarray) -> np.ndarray:
    """Cross-sectional signal (T x N) -> dollar-neutral weights with unit gross leverage."""
    s = np.where(np.isfinite(sig), sig, np.nan)
    s = s - np.nanmean(s, axis=1, keepdims=True)
    s = np.nan_to_num(s)
    g = np.abs(s).sum(axis=1, keepdims=True)
    return np.divide(s, g, out=np.zeros_like(s), where=g > 0)


def factor_neutral(W: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Project each day's weights off the FF5 loadings (w - B (B'B)^-1 B'w), renormalise."""
    out = np.zeros_like(W)
    for t in range(len(W)):
        b = B[t]
        if not np.isfinite(b).all() or not W[t].any():
            continue
        x = np.column_stack([np.ones(len(b)), b])           # also keeps dollar neutrality
        w = W[t] - x @ np.linalg.lstsq(x, W[t], rcond=None)[0]
        g = np.abs(w).sum()
        out[t] = w / g if g > 0 else 0.0
    return out


# ----------------------------------------------------------------------------- backtest
def backtest(W, R=None, cost=COST, short_fee=SHORT_FEE, start=START, end=None) -> pd.DataFrame:
    """W (T x N array or DataFrame aligned to panel R): weights at close d -> excess return d+1."""
    P = panel()
    R = P["R"] if R is None else R
    Wd = pd.DataFrame(np.asarray(W), index=R.index, columns=R.columns)
    nxt = R.shift(-1).fillna(0.0)
    gross = (Wd * nxt).sum(axis=1)
    to = Wd.diff().abs().sum(axis=1)
    to.iloc[0] = Wd.iloc[0].abs().sum()
    short = (-Wd.clip(upper=0)).sum(axis=1)
    net = gross - cost * to - short_fee * short
    out = pd.DataFrame({"net": net, "gross": gross, "turnover": to, "gross_lev": Wd.abs().sum(axis=1)})
    out = out.iloc[:-1]                                     # last day has no next return
    out = out.loc[start:end]
    return out[out.gross_lev > 0] if (out.gross_lev > 0).any() else out


def sr(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(ANN)) if len(x) > 20 and x.std() > 0 else np.nan


def summarize(bt: pd.DataFrame, name: str, family: str, params: dict | None = None, log: bool = True) -> dict:
    """Metrics incl. 2010-2021 vs 2022-2026 split; logs the daily net series as a trial."""
    a, b = bt.loc[:"2021-12-31"], bt.loc[SPLIT:]
    eq = (1 + bt["net"]).cumprod()
    d = dict(family=family, strategy=name, start=str(bt.index[0].date()), end=str(bt.index[-1].date()),
             SR_gross=sr(bt.gross), SR_net=sr(bt.net), ann_net=bt.net.mean() * ANN,
             vol=bt.net.std() * np.sqrt(ANN), maxDD=float((eq / eq.cummax() - 1).min()),
             turnover_daily=bt.turnover.mean(), avg_gross_lev=bt.gross_lev.mean(),
             SR_net_2010_21=sr(a.net), SR_net_2022_26=sr(b.net),
             SR_gross_2022_26=sr(b.gross), params=json.dumps(params or {}, default=str))
    if log:
        key = f"{family}__{name}".replace(" ", "_").replace("/", "-")
        bt[["net"]].rename(columns={"net": key}).to_parquet(TRIALS / f"{key}.parquet")
    return d


def save(rows: list[dict], fname: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df.to_csv(RES / fname, index=False, float_format="%.4f")
    return df


def show(df: pd.DataFrame):
    cols = ["strategy", "SR_gross", "SR_net", "turnover_daily", "avg_gross_lev", "SR_net_2010_21", "SR_net_2022_26", "maxDD"]
    print(df[[c for c in cols if c in df]].to_string(index=False, float_format=lambda x: f"{x:.3f}"), flush=True)


def plot(curves: dict, title: str, fname: str):
    import shutil
    import common as c26
    _plot(curves, title, fname, logy=False)
    src = c26.RES_DIR / fname
    if src.exists():
        shutil.move(str(src), str(RES / fname))


def deflated_all(bench_key: str | None = None) -> dict:
    """Deflated Sharpe (ml4t.diagnostic) of the best logged trial across ALL trials."""
    from common import deflated_sharpe
    series = [pd.read_parquet(f).iloc[:, 0] for f in sorted(TRIALS.glob("*.parquet"))]
    bench = None
    if bench_key:
        bench = next((s for s in series if s.name == bench_key), None)
    return deflated_sharpe(series, "all stat-arb trials", n_trials=len(series), bench=bench)


class Timer:
    def __init__(self):
        self.t0 = time.time()

    def __call__(self, msg):
        print(f"[{(time.time() - self.t0) / 60:6.1f} min] {msg}", flush=True)
