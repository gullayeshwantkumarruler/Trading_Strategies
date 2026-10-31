"""Data for the price-action backtests.

Daily/weekly: yfinance adjusted OHLC (auto_adjust=True), cached to data/daily/<TICKER>.parquet.
Intraday: Alpaca Market Data API (free Basic plan, SIP feed, 2016 ->), 1-minute bars cached per symbol/month to
data/minute/<SYMBOL>/<YYYY-MM>.parquet. Keys are read from the environment or from the repo-root `.env` file
(git-ignored): ALPACA_API_KEY, ALPACA_SECRET_KEY. They are never written anywhere else.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DATA = ROOT / "data"
RES = ROOT / "results"
for d in (DATA / "daily", DATA / "minute", RES):
    d.mkdir(parents=True, exist_ok=True)

ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "SMH", "MTUM",
        "EFA", "EEM", "TLT", "GLD"]


def daily(ticker: str, refresh: bool = False) -> pd.DataFrame:
    p = DATA / "daily" / f"{ticker.replace('^', 'IDX_')}.parquet"
    if p.exists() and not refresh and (time.time() - p.stat().st_mtime) < 7 * 86400:
        return pd.read_parquet(p)
    import yfinance as yf
    df = yf.download(ticker, start="1990-01-01", auto_adjust=True, progress=False, multi_level_index=False)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.to_parquet(p)
    return df


def weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Weekly bars ending Friday (or the last trading day of the week)."""
    w = df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
    return w.dropna()


# ----------------------------------------------------------------------------- Alpaca minute bars
def _load_env():
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if v.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()


def alpaca_client():
    _load_env()
    key, sec = os.environ.get("ALPACA_API_KEY"), os.environ.get("ALPACA_SECRET_KEY")
    if not key or not sec:
        raise RuntimeError("Alpaca keys missing: fill ALPACA_API_KEY / ALPACA_SECRET_KEY in the repo-root .env file")
    from alpaca.data.historical import StockHistoricalDataClient
    return StockHistoricalDataClient(key, sec)


def minute(symbol: str, start: str = "2016-01-01", end: str | None = None) -> pd.DataFrame:
    """1-minute SIP bars (regular + extended hours as returned), cached per month; tz = America/New_York."""
    from alpaca.data.enums import DataFeed
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    client = None
    end_ts = pd.Timestamp(end) if end else pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(1, "D")
    months = pd.period_range(pd.Timestamp(start), end_ts, freq="M")
    out = []
    d = DATA / "minute" / symbol
    d.mkdir(parents=True, exist_ok=True)
    for m in months:
        p = d / f"{m}.parquet"
        last_full = m < pd.Period(end_ts, "M")
        if p.exists() and last_full:
            out.append(pd.read_parquet(p))
            continue
        client = client or alpaca_client()
        s = m.start_time.tz_localize("America/New_York")
        e = min(m.end_time.tz_localize("America/New_York"), pd.Timestamp(end_ts).tz_localize("UTC") - pd.Timedelta(20, "min"))
        for attempt in range(5):
            try:
                req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, start=s, end=e,
                                       feed=DataFeed.SIP)
                bars = client.get_stock_bars(req).df
                break
            except Exception as ex:  # noqa: BLE001
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt + 1)
        if len(bars):
            bars = bars.reset_index(level=0, drop=True)
            bars.index = bars.index.tz_convert("America/New_York")
            bars = bars.rename(columns=str.capitalize)[["Open", "High", "Low", "Close", "Volume", "Vwap"]]
            bars.to_parquet(p)
            out.append(bars)
        time.sleep(0.35)                                   # stay well under 200 requests/minute
    return pd.concat(out).sort_index() if out else pd.DataFrame()


def rth(df: pd.DataFrame) -> pd.DataFrame:
    """Regular trading hours 09:30-15:59 New York."""
    t = df.index.time
    return df[(t >= pd.Timestamp("09:30").time()) & (t <= pd.Timestamp("15:59").time())]
