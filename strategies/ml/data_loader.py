"""Data loading for the ML cross-sectional strategies.

Universes are CURRENT large-cap index constituents (hand-picked list as of 2026).
This creates SURVIVORSHIP BIAS: firms that were delisted, merged or dropped out
of the index since 2012 are missing, and today's winners are over-represented.
Long-only results in particular are biased upward; long-short results are less
affected but still not clean.

Sources:
  US / Europe / Japan : yfinance, auto_adjust=True (split+dividend adjusted OHLC)
  China A-shares      : akshare `stock_zh_a_daily` (Sina) with adjust='hfq'
                        (back-adjusted), which also returns RMB amount and
                        true turnover (volume / free float shares).  Eastmoney
                        (`stock_zh_a_hist`) was unreachable from this machine.
                        Fallback: yfinance .SS/.SZ.
Cached as parquet in strategies/ml/data/.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
START = "2012-01-01"
# last complete session common to all regions at build time (avoid partial intraday bars)
END = "2026-10-17"

UNIVERSES: dict[str, list[str]] = {
    # ~S&P 100 large caps (50 names)
    "US": """AAPL MSFT AMZN GOOGL META NVDA BRK-B JPM JNJ V PG UNH HD MA XOM CVX MRK ABBV
    PEP KO COST WMT BAC PFE TMO CSCO ABT MCD DIS ADBE CRM NFLX INTC CMCSA VZ T NKE ORCL
    AMGN TXN QCOM HON UNP LOW IBM CAT GS MS BA LLY""".split(),
    # Euro Stoxx 50 / STOXX large caps (40 names, all EUR-listed)
    "EU": """SAP.DE SIE.DE ALV.DE DTE.DE BAS.DE BAYN.DE BMW.DE MBG.DE MUV2.DE DBK.DE ADS.DE
    IFX.DE DHL.DE VOW3.DE MC.PA OR.PA TTE.PA SAN.PA AIR.PA BNP.PA SU.PA AI.PA EL.PA KER.PA
    DG.PA CS.PA RI.PA SAF.PA ASML.AS INGA.AS PHIA.AS AD.AS ENEL.MI ISP.MI ENI.MI UCG.MI
    IBE.MC SAN.MC ITX.MC BBVA.MC""".split(),
    # Nikkei 225 large caps (40 names)
    "JP": """7203.T 6758.T 9984.T 6861.T 8306.T 9432.T 6098.T 8035.T 9983.T 4063.T 6501.T
    7974.T 8316.T 4502.T 6367.T 7267.T 8058.T 8001.T 6902.T 4519.T 6954.T 7741.T 9433.T
    8411.T 4568.T 6981.T 6273.T 6594.T 8031.T 6702.T 7751.T 4661.T 2914.T 3382.T 8766.T
    6752.T 4503.T 5108.T 6503.T 7011.T""".split(),
    # CSI 300 large caps (40 names); codes are yfinance style, converted for akshare
    "CN": """600519.SS 601318.SS 600036.SS 000858.SZ 000333.SZ 601166.SS 600276.SS 600900.SS
    000651.SZ 601398.SS 601288.SS 601988.SS 600030.SS 000002.SZ 600887.SS 601012.SS
    300750.SZ 002594.SZ 600309.SS 601888.SS 000568.SZ 600000.SS 601328.SS 600048.SS
    601601.SS 601628.SS 600104.SS 000001.SZ 002415.SZ 600585.SS 601857.SS 600028.SS
    601668.SS 600050.SS 000725.SZ 002475.SZ 300059.SZ 600809.SS 601899.SS 600031.SS""".split(),
}

COLS = ["date", "asset", "open", "high", "low", "close", "volume", "amount", "turnover"]


def _yf_download(tickers: list[str]) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(tickers, start=START, auto_adjust=True, group_by="column",
                      progress=False, threads=True)
    long = raw.stack(level=1, future_stack=True).rename_axis(["date", "asset"]).reset_index()
    long.columns = [str(c).lower() for c in long.columns]
    long = long.dropna(subset=["open", "close"])
    long = long[(long["close"] > 0) & (long["open"] > 0)]
    long["amount"] = long["close"] * long["volume"]  # dollar volume proxy (adjusted px)
    long["turnover"] = np.nan  # shares outstanding not available for free
    return long[COLS]


def _ak_one(ticker: str) -> pd.DataFrame | None:
    import akshare as ak

    code, exch = ticker.split(".")
    sym = ("sh" if exch == "SS" else "sz") + code
    for attempt in range(3):
        try:
            df = ak.stock_zh_a_daily(symbol=sym, start_date=START.replace("-", ""),
                                     end_date="20500101", adjust="hfq")
            if df is None or df.empty:
                return None
            df = df.rename(columns={"date": "date"})
            df["date"] = pd.to_datetime(df["date"])
            df["asset"] = ticker
            # Sina hfq turnover column is a fraction (volume / float shares)
            return df[COLS]
        except Exception as exc:  # network flakiness
            print(f"  akshare {ticker} attempt {attempt + 1} failed: {exc!r}"[:160])
            time.sleep(2 + 2 * attempt)
    return None


def load_region(region: str, refresh: bool = False) -> pd.DataFrame:
    path = DATA_DIR / f"prices_{region}.parquet"
    if path.exists() and not refresh:
        df = pd.read_parquet(path)
        return df[df["date"] < pd.Timestamp(END)].reset_index(drop=True)
    tickers = UNIVERSES[region]
    if region == "CN":
        frames, failed = [], []
        for t in tickers:
            df = _ak_one(t)
            if df is None:
                failed.append(t)
            else:
                frames.append(df)
            time.sleep(0.5)
        if failed:
            print(f"  akshare failed for {failed}; trying yfinance fallback")
            yfdf = _yf_download(failed)
            if not yfdf.empty:
                frames.append(yfdf)
        df = pd.concat(frames, ignore_index=True)
    else:
        df = _yf_download(tickers)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df = df.sort_values(["asset", "date"]).drop_duplicates(["asset", "date"]).reset_index(drop=True)
    df.to_parquet(path, index=False)
    return df[df["date"] < pd.Timestamp(END)].reset_index(drop=True)


def load_all(refresh: bool = False) -> dict[str, pd.DataFrame]:
    out = {}
    for r in UNIVERSES:
        t0 = time.time()
        out[r] = load_region(r, refresh=refresh)
        d = out[r]
        print(f"[data] {r}: {d['asset'].nunique()} assets, {len(d):,} rows, "
              f"{d['date'].min().date()} -> {d['date'].max().date()} ({time.time() - t0:.0f}s)")
    return out


if __name__ == "__main__":
    load_all(refresh=True)
