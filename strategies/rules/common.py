"""Shared helpers for the rules-based strategy backtests.

Data:      yfinance (auto_adjust=True), cached per ticker as parquet in ./data
Simulator: vectorised-with-drift daily simulator. Signals are formed at the close of
           day t, executed at the close of day t+1 (lag=2 in return-accrual terms:
           the first return earned is r_{t+2}). Costs = cost_bps per unit of one-way
           turnover. Uninvested cash earns the 3m T-bill (^IRX); net borrowing pays it.
           Short positions pay an extra borrow fee (default 25 bp/yr).
Metrics:   CAGR, vol, Sharpe (excess of T-bill), Sortino, MaxDD, Calmar, turnover,
           IS (< 2018) / OOS (>= 2018) split, deflated Sharpe via ml4t-diagnostic.
"""
from __future__ import annotations

import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RES_DIR = ROOT / "results"
DATA_DIR.mkdir(exist_ok=True)
RES_DIR.mkdir(exist_ok=True)

START = "1990-01-01"
OOS_START = pd.Timestamp("2018-01-01")
ANN = 252

# Region labels used in reports
REGION = {
    "SPY": "US", "QQQ": "US", "IWM": "US", "^GSPC": "US",
    "EZU": "Europe", "VGK": "Europe", "EWG": "Europe", "EWU": "Europe", "EWQ": "Europe",
    "^GDAXI": "Europe", "^STOXX50E": "Europe", "FEZ": "Europe",
    "EWJ": "Japan", "DXJ": "Japan", "^N225": "Japan",
    "FXI": "China", "MCHI": "China", "ASHR": "China", "KWEB": "China", "EWH": "China/HK",
    "000300.SS": "China",
    "TLT": "Bonds", "IEF": "Bonds", "LQD": "Bonds", "TIP": "Bonds",
    "GLD": "Commodity", "USO": "Commodity", "DBC": "Commodity", "FXE": "FX",
    "EFA": "Intl DM", "EEM": "EM", "IYR": "US REIT",
}


# ----------------------------------------------------------------------------- data
AKSHARE_MAP = {"000300.SS": "sh000300"}

def _cache_path(ticker: str) -> Path:
    safe = ticker.replace("^", "IDX_").replace(".", "_").replace("=", "_")
    return DATA_DIR / f"{safe}.parquet"


def fetch(ticker: str, refresh: bool = False, max_age_days: float = 7.0) -> pd.DataFrame:
    """Daily OHLCV for one ticker (auto_adjust=True), cached to parquet."""
    p = _cache_path(ticker)
    if p.exists() and not refresh:
        age = (time.time() - p.stat().st_mtime) / 86400
        if age < max_age_days or os.environ.get("RULES_OFFLINE"):
            return pd.read_parquet(p)
    import yfinance as yf

    if ticker in AKSHARE_MAP:  # Yahoo's 000300.SS history is broken (1 row) -> akshare/Sina
        import akshare as ak
        x = ak.stock_zh_index_daily(symbol=AKSHARE_MAP[ticker])
        df = x.rename(columns=str.capitalize).set_index("Date")
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
        df.to_parquet(p)
        return df

    start = "1970-01-01" if ticker.startswith("^") else START
    last_err = None
    for attempt in range(3):
        try:
            df = yf.download(ticker, start=start, auto_adjust=True, progress=False,
                             threads=False, multi_level_index=False)
            if df is not None and len(df) > 1:
                break
        except Exception as e:  # network hiccups
            last_err = e
        time.sleep(2 + 2 * attempt)
    else:
        if p.exists():
            print(f"[warn] download failed for {ticker} ({last_err}); using stale cache")
            return pd.read_parquet(p)
        raise RuntimeError(f"no data for {ticker}: {last_err}")
    df = df[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    df = df[df["Close"].notna() & (df["Close"] > 0)]
    df.to_parquet(p)
    return df


def closes(tickers: list[str], refresh: bool = False, calendar: str | None = "SPY") -> pd.DataFrame:
    """Wide close-price frame. If calendar is given, align to that ticker's trading days
    (no forward-fill across *missing* days of the other series beyond 3 days)."""
    out = {}
    for t in tickers:
        try:
            out[t] = fetch(t, refresh=refresh)["Close"]
        except Exception as e:
            print(f"[warn] skipping {t}: {e}")
    px = pd.DataFrame(out).sort_index()
    if calendar is not None:
        cal = fetch(calendar)["Close"].index
        px = px.reindex(cal).ffill(limit=3)
        # do not invent prices before inception
        for t in px.columns:
            first = out[t].first_valid_index()
            px.loc[px.index < first, t] = np.nan
    return px


def tbill_daily(index: pd.DatetimeIndex) -> pd.Series:
    """Daily T-bill return from ^IRX (13-week yield, %), aligned to index."""
    irx = fetch("^IRX")["Close"]
    irx = irx.reindex(index.union(irx.index)).ffill().reindex(index).fillna(0.0)
    return (irx / 100.0) / ANN


def returns(px: pd.DataFrame) -> pd.DataFrame:
    r = px.pct_change(fill_method=None)
    # clip absurd data errors (yfinance sometimes has bad ticks)
    return r.where(r.abs() < 0.5)


# ----------------------------------------------------------------------------- simulator
def simulate(target: pd.DataFrame, rets: pd.DataFrame, rf: pd.Series | None = None,
             cost_bps: float = 5.0, rebal: pd.Series | None = None, lag: int = 2,
             short_fee_bps_yr: float = 25.0, return_weights: bool = False):
    """Simulate a portfolio of target weights with drift between rebalances.

    target : weights decided at close of day t (index = signal dates, cols = assets).
    rebal  : bool Series on signal dates; True = rebalance to target (default: every day).
    lag    : 2 -> decided at close t, executed at close t+1, first return r_{t+2}.
             For calendar rules known in advance (TOM) pass the holding mask with lag=0.
    Returns DataFrame [ret, gross_ret, cost, turnover, gross_exposure, net_exposure].
    """
    rets = rets.copy()
    cols = list(target.columns)
    rets = rets.reindex(columns=cols)
    idx = rets.index
    tgt = target.reindex(idx).shift(lag)
    if rebal is None:
        rb = tgt.notna().any(axis=1)
    else:
        rb = rebal.reindex(idx).fillna(False).astype(bool).shift(lag).fillna(False).astype(bool)
    T = tgt.fillna(0.0).to_numpy()
    R = rets.fillna(0.0).to_numpy()
    avail = rets.notna().to_numpy()
    RB = rb.to_numpy()
    rfv = (rf.reindex(idx).fillna(0.0).to_numpy() if rf is not None else np.zeros(len(idx)))
    c = cost_bps / 1e4
    sf = short_fee_bps_yr / 1e4 / ANN
    n, k = R.shape
    w = np.zeros(k)
    out = np.zeros((n, 6))
    W = np.zeros((n, k)) if return_weights else None
    for i in range(n):
        to = 0.0
        if RB[i]:
            new = np.where(avail[i] | (w != 0), T[i], 0.0)  # cannot open a position without data
            to = np.abs(new - w).sum()
            w = new
        cash = 1.0 - w.sum()
        gross = float(w @ R[i]) + cash * rfv[i] - sf * np.abs(np.minimum(w, 0)).sum()
        cost = to * c
        port = gross - cost
        out[i] = (port, gross, cost, to, np.abs(w).sum(), w.sum())
        if W is not None:
            W[i] = w
        denom = 1.0 + gross
        if denom > 0:
            w = w * (1.0 + R[i]) / denom
    res = pd.DataFrame(out, index=idx, columns=["ret", "gross_ret", "cost", "turnover",
                                                 "gross_exposure", "net_exposure"])
    if return_weights:
        return res, pd.DataFrame(W, index=idx, columns=cols)
    return res


def trim_start(res: pd.DataFrame, start=None) -> pd.DataFrame:
    """Drop the warm-up period before the strategy is first invested."""
    if start is None:
        nz = res.index[res["gross_exposure"] > 0]
        start = nz[0] if len(nz) else res.index[0]
    return res.loc[res.index >= pd.Timestamp(start)]


# ----------------------------------------------------------------------------- metrics
def _stats(r: pd.Series, rf: pd.Series | None, turnover: pd.Series | None = None) -> dict:
    r = r.dropna()
    if len(r) < 20:
        return {k: np.nan for k in ["CAGR", "Vol", "Sharpe", "Sortino", "MaxDD", "Calmar", "Turnover"]}
    ex = r - (rf.reindex(r.index).fillna(0.0) if rf is not None else 0.0)
    eq = (1 + r).cumprod()
    yrs = len(r) / ANN
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1.0
    vol = r.std() * np.sqrt(ANN)
    sharpe = ex.mean() / ex.std() * np.sqrt(ANN) if ex.std() > 0 else np.nan
    dd_dev = np.sqrt((np.minimum(ex, 0) ** 2).mean()) * np.sqrt(ANN)
    sortino = ex.mean() * ANN / dd_dev if dd_dev > 0 else np.nan
    mdd = (eq / eq.cummax() - 1).min()
    calmar = cagr / abs(mdd) if mdd < 0 else np.nan
    to = turnover.reindex(r.index).sum() / yrs if turnover is not None else np.nan
    return dict(CAGR=cagr, Vol=vol, Sharpe=sharpe, Sortino=sortino, MaxDD=mdd, Calmar=calmar,
                Turnover=to)


def metrics(res: pd.DataFrame | pd.Series, rf: pd.Series | None, name: str,
            family: str, region: str = "", params: str = "") -> dict:
    if isinstance(res, pd.Series):
        r, to = res, None
    else:
        r, to = res["ret"], res["turnover"]
    full = _stats(r, rf, to)
    is_ = _stats(r[r.index < OOS_START], rf, to)
    oos = _stats(r[r.index >= OOS_START], rf, to)
    d = dict(family=family, strategy=name, region=region, start=r.index[0].date(),
             end=r.index[-1].date(), years=round(len(r) / ANN, 1), **full)
    for k in ["CAGR", "Sharpe", "MaxDD"]:
        d[f"IS_{k}"] = is_[k]
        d[f"OOS_{k}"] = oos[k]
    d["params"] = params
    return d


def _dsr_core(df: pd.DataFrame, n_trials: int | None) -> dict:
    """DSR of the best column of df (K variants), K raised to n_trials if larger."""
    K = df.shape[1]
    try:
        from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio
        if K == 1 and (n_trials or 1) == 1:
            res = deflated_sharpe_ratio(df.iloc[:, 0].to_numpy(), frequency="daily")
        elif K == 1:  # one series but several trials: use the from-statistics form
            from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio_from_statistics
            from scipy.stats import kurtosis, skew
            x = df.iloc[:, 0].to_numpy()
            res = deflated_sharpe_ratio_from_statistics(
                observed_sharpe=float(x.mean() / x.std(ddof=1)), n_samples=len(x), n_trials=n_trials,
                variance_trials=0.0, skewness=float(skew(x)), excess_kurtosis=float(kurtosis(x)),
                autocorrelation=float(pd.Series(x).autocorr()), frequency="daily")
        else:
            res = deflated_sharpe_ratio([df[c].to_numpy() for c in df.columns], frequency="daily",
                                        effective_trials=(float(n_trials) if n_trials and n_trials > K else None))
        return dict(prob=float(res.probability), sr=float(res.sharpe_ratio_annualized), impl="ml4t.diagnostic")
    except Exception as e:  # local Bailey & Lopez de Prado (2014) fallback
        from scipy.stats import kurtosis, norm, skew
        Kt = max(K, n_trials or 1)
        srs = df.mean() / df.std()
        x = df[srs.idxmax()]
        sr = srs.max()
        v = srs.var(ddof=1) if K > 1 else 0.0
        g = 0.5772156649
        sr0 = np.sqrt(v) * ((1 - g) * norm.ppf(1 - 1 / Kt) + g * norm.ppf(1 - 1 / (Kt * np.e))) if Kt > 1 else 0.0
        den = np.sqrt(1 - skew(x) * sr + (kurtosis(x) / 4) * sr ** 2)
        z = (sr - sr0) * np.sqrt(len(x) - 1) / den
        return dict(prob=float(norm.cdf(z)), sr=float(sr * np.sqrt(ANN)), impl=f"local ({e.__class__.__name__})")


def deflated_sharpe(ret_list: list[pd.Series], label: str = "", rf: pd.Series | None = None,
                    n_trials: int | None = None, bench: pd.Series | None = None) -> dict:
    """Deflated Sharpe ratio (Bailey & Lopez de Prado) of the best of K variants, via
    ml4t.diagnostic.evaluation.stats.deflated_sharpe_ratio (local fallback if it fails).
      dsr_prob        : P(true SR of best variant > 0) on excess-of-T-bill returns
      dsr_active_prob : same on active returns (variant - benchmark), if bench is given
    """
    df = pd.concat(ret_list, axis=1, join="inner").dropna()
    K = df.shape[1]
    ex = df.sub(rf.reindex(df.index).fillna(0.0), axis=0) if rf is not None else df
    a = _dsr_core(ex, n_trials)
    out = dict(family=label, n_trials=int(max(K, n_trials or 0)), n_obs=len(df),
               best_variant=ex.columns[int(np.argmax((ex.mean() / ex.std()).to_numpy()))],
               best_sharpe_ann=a["sr"], dsr_prob=a["prob"], dsr_impl=a["impl"])
    if bench is not None:
        act = df.sub(bench.reindex(df.index).fillna(0.0), axis=0)
        b = _dsr_core(act, n_trials)
        out.update(best_active_variant=act.columns[int(np.argmax((act.mean() / act.std()).to_numpy()))],
                   best_active_IR_ann=b["sr"], dsr_active_prob=b["prob"], benchmark=bench.name)
    return out


# ----------------------------------------------------------------------------- plotting
def plot_equity(curves: dict[str, pd.Series], title: str, fname: str, logy: bool = True):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1]})
    for name, r in curves.items():
        r = r.dropna()
        eq = (1 + r).cumprod()
        ax.plot(eq.index, eq.values, label=name, lw=1.2)
        ax2.plot(eq.index, (eq / eq.cummax() - 1).values, lw=0.9)
    if logy:
        ax.set_yscale("log")
    ax.axvline(OOS_START, color="grey", ls="--", lw=0.8)
    ax.text(OOS_START, ax.get_ylim()[1], " OOS", va="top", fontsize=8, color="grey")
    ax.set_title(title)
    ax.set_ylabel("Growth of $1")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    ax2.set_ylabel("Drawdown")
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RES_DIR / fname, dpi=110)
    plt.close(fig)


def month_end_flags(index: pd.DatetimeIndex) -> pd.Series:
    """True on the last trading day of each month in `index`."""
    s = pd.Series(index, index=index)
    last = s.groupby([index.year, index.month]).transform("max")
    return pd.Series(index == last.values, index=index)
