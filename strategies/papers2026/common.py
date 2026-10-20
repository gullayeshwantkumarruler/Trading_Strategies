"""Shared helpers for the 2026-paper replications.

Re-uses the simulator / metrics / deflated-Sharpe / plotting helpers from
strategies/rules/common.py (same cost and lag conventions), and adds keyless loaders for
FRED series (fredgraph.csv), Kenneth French daily factors, and an S&P 500 large-cap
stock universe (current constituents -> survivorship bias, stated in every write-up).
"""
from __future__ import annotations

import io
import re
import sys
import time
import warnings
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parent
RULES = ROOT.parent / "rules"


def _load_rules_common():
    """Import strategies/rules/common.py as 'rules_common' (both folders have a common.py)."""
    import importlib.util
    if "rules_common" in sys.modules:
        return sys.modules["rules_common"]
    spec = importlib.util.spec_from_file_location("rules_common", RULES / "common.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rules_common"] = mod
    spec.loader.exec_module(mod)
    return mod


rules_common = _load_rules_common()
ANN = rules_common.ANN
closes, deflated_sharpe, fetch = rules_common.closes, rules_common.deflated_sharpe, rules_common.fetch
metrics, returns = rules_common.metrics, rules_common.returns
simulate, tbill_daily, trim_start = rules_common.simulate, rules_common.tbill_daily, rules_common.trim_start
_stats = rules_common._stats

DATA_DIR = ROOT / "data"
RES_DIR = ROOT / "results"
DATA_DIR.mkdir(exist_ok=True)
RES_DIR.mkdir(exist_ok=True)


def plot_equity(curves, title, fname, logy=True):
    """rules' plot_equity writes into strategies/rules/results; move the PNG here."""
    import shutil
    rules_common.plot_equity(curves, title, fname, logy=logy)
    shutil.move(str(rules_common.RES_DIR / fname), str(RES_DIR / fname))

UA = {"User-Agent": "Mozilla/5.0 (research replication script)"}


def _get(url: str, attempts: int = 4) -> bytes:
    err = None
    for i in range(attempts):
        try:
            with urlopen(Request(url, headers=UA), timeout=60) as r:  # noqa: S310
                return r.read()
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 ** i)
    raise RuntimeError(f"download failed: {url}") from err


def _fresh(p: Path, days: float = 7.0) -> bool:
    return p.exists() and (time.time() - p.stat().st_mtime) / 86400 < days


# ----------------------------------------------------------------------------- FRED
def fred(series: str, refresh: bool = False) -> pd.Series:
    """FRED series via the public fredgraph.csv endpoint (no API key)."""
    p = DATA_DIR / f"fred_{series}.parquet"
    if _fresh(p) and not refresh:
        return pd.read_parquet(p).iloc[:, 0]
    raw = _get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}")
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = ["date", series]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df.set_index("date")[series], errors="coerce").dropna()
    s.to_frame().to_parquet(p)
    return s


# ----------------------------------------------------------------------------- Ken French
def _french_zip(name: str) -> pd.DataFrame:
    raw = _get(f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        txt = zf.read(zf.namelist()[0]).decode("latin1")
    lines = txt.splitlines()
    first = next(i for i, l in enumerate(lines) if re.match(r"^\s*\d{8}\s*,", l))
    ff = pd.read_csv(io.StringIO(txt), skiprows=first - 1)
    c0 = ff.columns[0]
    ff = ff[ff[c0].astype(str).str.strip().str.match(r"^\d{8}$")].copy()
    ff[c0] = pd.to_datetime(ff[c0].astype(str).str.strip(), format="%Y%m%d")
    ff = ff.set_index(c0)
    ff.columns = [c.strip().replace("-", "_").replace(" ", "_").lower() for c in ff.columns]
    return ff.astype(float) / 100.0


def french_factors(refresh: bool = False) -> pd.DataFrame:
    """Daily FF5 + MOM + ST_REV + LT_REV + RF (decimal)."""
    p = DATA_DIR / "french_daily.parquet"
    if _fresh(p, 30) and not refresh:
        return pd.read_parquet(p)
    ff5 = _french_zip("F-F_Research_Data_5_Factors_2x3_daily_CSV.zip")
    mom = _french_zip("F-F_Momentum_Factor_daily_CSV.zip")
    st = _french_zip("F-F_ST_Reversal_Factor_daily_CSV.zip")
    lt = _french_zip("F-F_LT_Reversal_Factor_daily_CSV.zip")
    mom.columns, st.columns, lt.columns = ["mom"], ["st_rev"], ["lt_rev"]
    out = pd.concat([ff5, mom, st, lt], axis=1, join="inner").sort_index()
    out.to_parquet(p)
    return out


# ----------------------------------------------------------------------------- S&P 500 universe
def sp500_universe(n: int = 300, refresh: bool = False) -> list[str]:
    """Current S&P 500 constituents (Wikipedia), keeping the n with the longest
    clean history and highest median dollar volume. CURRENT constituents only ->
    survivorship bias (the same caveat as both source papers' 300/346-stock universes)."""
    p = DATA_DIR / f"sp500_top{n}.txt"
    if p.exists() and not refresh:
        return p.read_text().split()
    html = _get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies").decode("utf-8")
    tab = pd.read_html(io.StringIO(html))[0]
    syms = [s.replace(".", "-") for s in tab["Symbol"].astype(str)]
    px, vol = stock_panel(syms)
    dv = (px * vol).loc["2015":].median()
    ok = px.loc["2005":].notna().mean() > 0.97          # listed for (almost) the whole window
    keep = dv[ok[ok].index].sort_values(ascending=False).index[:n].tolist()
    p.write_text("\n".join(sorted(keep)))
    return sorted(keep)


def stock_panel(tickers: list[str], start: str = "2004-01-01", refresh: bool = False):
    """Adjusted close and volume panels for many stocks (one batched yfinance call, cached)."""
    p_px, p_vol = DATA_DIR / "stocks_close.parquet", DATA_DIR / "stocks_volume.parquet"
    have_px = pd.read_parquet(p_px) if p_px.exists() else pd.DataFrame()
    have_vol = pd.read_parquet(p_vol) if p_vol.exists() else pd.DataFrame()
    stale = not _fresh(p_px, 7)
    need = [t for t in tickers if t not in have_px.columns] if not (refresh or stale) else list(tickers)
    if need:
        import yfinance as yf
        chunks = [need[i:i + 100] for i in range(0, len(need), 100)]
        pxs, vols = [], []
        for ch in chunks:
            d = yf.download(ch, start=start, auto_adjust=True, progress=False, threads=True,
                            group_by="column")
            pxs.append(d["Close"])
            vols.append(d["Volume"])
        newpx, newvol = pd.concat(pxs, axis=1), pd.concat(vols, axis=1)
        have_px = newpx.combine_first(have_px) if len(have_px) else newpx
        have_vol = newvol.combine_first(have_vol) if len(have_vol) else newvol
        have_px.to_parquet(p_px)
        have_vol.to_parquet(p_vol)
    cols = [t for t in tickers if t in have_px.columns]
    return have_px[cols].sort_index(), have_vol[cols].sort_index()


# ----------------------------------------------------------------------------- misc
def save_rows(rows: list[dict], fname: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df.to_csv(RES_DIR / fname, index=False, float_format="%.4f")
    return df


def ann_stats(r: pd.Series, rf: pd.Series | None = None) -> dict:
    return _stats(r, rf)
