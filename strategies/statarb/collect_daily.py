"""Step 6 — daily forward collection of data that has no free history (report priority 6).

Saves into data/archive/YYYY-MM-DD/ (gitignored):
  news.parquet     Yahoo Finance RSS headlines per ticker (title, link, pubDate, fetched_at) for the
                   337-stock universe, plus Google News RSS for the 50 largest names
  options.parquet  yfinance option-chain snapshots (2 nearest expiries + the ~30-day expiry) for the 100
                   most-traded names: strike, bid/ask, IV, OI, volume
  finra.parquet    FINRA consolidated daily short-volume file for the last trading day (and any gaps)
Idempotent: re-running the same day overwrites that day's files. Designed for a daily scheduled run after
the US close. A news-conditioned residual-reversal test needs 12-24 months of this archive.
"""
from __future__ import annotations

import datetime as dt
import io
import sys
import time
import traceback
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
ARCH = ROOT / "data" / "archive"
UNIVERSE = ROOT.parent / "papers2026" / "data" / "sp500_top350.txt"
UA = {"User-Agent": "Mozilla/5.0 (research archive)"}


def fetch(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def rss(url, ticker, source):
    rows = []
    root = ET.fromstring(fetch(url))
    for it in root.iter("item"):
        rows.append(dict(ticker=ticker, source=source, title=(it.findtext("title") or "").strip(),
                         link=it.findtext("link"), pubDate=it.findtext("pubDate"),
                         fetched_at=dt.datetime.now(dt.timezone.utc).isoformat()))
    return rows


def news(tickers, top50):
    rows, fails = [], 0
    for t in tickers:
        try:
            rows += rss(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={t}&region=US&lang=en-US", t, "yahoo")
        except Exception:  # noqa: BLE001
            fails += 1
        time.sleep(0.3)
    for t in top50:
        try:
            rows += rss(f"https://news.google.com/rss/search?q={t}+stock&hl=en-US&gl=US&ceid=US:en", t, "google")
        except Exception:  # noqa: BLE001
            fails += 1
        time.sleep(0.5)
    return pd.DataFrame(rows), fails


def options(tickers):
    import yfinance as yf
    parts, fails = [], 0
    today = pd.Timestamp.today().normalize()
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            ex = list(tk.options)
            if not ex:
                continue
            exd = pd.to_datetime(ex)
            pick = set(ex[:2]) | {ex[int(abs((exd - (today + pd.Timedelta(30, "D"))).days).argmin())]}
            for e in sorted(pick):
                ch = tk.option_chain(e)
                for kind, df in (("call", ch.calls), ("put", ch.puts)):
                    df = df.assign(ticker=t, expiry=e, type=kind, snapshot=dt.datetime.now(dt.timezone.utc).isoformat())
                    parts.append(df)
        except Exception:  # noqa: BLE001
            fails += 1
        time.sleep(0.2)
    return (pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()), fails


def finra(days_back=7):
    out = []
    for k in range(days_back):
        d = pd.Timestamp.today().normalize() - pd.Timedelta(k, "D")
        if d.weekday() >= 5:
            continue
        try:
            b = fetch(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt", 60)
            df = pd.read_csv(io.BytesIO(b), sep="|")
            out.append(df[df.Date.astype(str).str.isdigit()])
        except Exception:  # noqa: BLE001
            continue
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main():
    day = dt.date.today().isoformat()
    out = ARCH / day
    out.mkdir(parents=True, exist_ok=True)
    log = open(ARCH / "collect_log.txt", "a", encoding="utf-8")
    def say(m):
        line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {m}"
        print(line, flush=True)
        log.write(line + "\n"); log.flush()
    try:
        tickers = UNIVERSE.read_text().split()
        top = tickers  # alphabetical file; rank by dollar volume if the price cache exists
        try:
            px = pd.read_parquet(ROOT.parent / "papers2026" / "data" / "stocks_close.parquet")
            vol = pd.read_parquet(ROOT.parent / "papers2026" / "data" / "stocks_volume.parquet")
            dv = (px * vol).iloc[-63:].median().reindex(tickers).sort_values(ascending=False)
            top = dv.index.tolist()
        except Exception:  # noqa: BLE001
            pass
        n, f = news(tickers, top[:50]); n.to_parquet(out / "news.parquet"); say(f"news: {len(n)} items, {f} failures")
        o, f = options(top[:100]); o.to_parquet(out / "options.parquet"); say(f"options: {len(o)} rows, {f} failures")
        s = finra(); s.to_parquet(out / "finra.parquet"); say(f"finra: {len(s)} rows")
        say(f"done -> {out}")
    except Exception:  # noqa: BLE001
        say("FAILED\n" + traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
