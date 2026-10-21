"""SEC EDGAR access (free, no key). SEC requires a User-Agent with a contact email: set the
SEC_USER_AGENT environment variable, e.g.  "Your Name your.email@example.com". It is read from the
environment (never stored in the repo). Requests are throttled below SEC's 10/second limit.
"""
from __future__ import annotations

import gzip
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import core

EDGAR = core.DATA / "edgar"
EDGAR.mkdir(exist_ok=True)
_last = [0.0]
_lock = threading.Lock()


def _ua():
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua or "@" not in ua:
        raise RuntimeError("Set SEC_USER_AGENT='Name email@domain' (SEC requires a contact email).")
    return ua


def get(url: str, attempts: int = 5, rate: float = 0.13) -> bytes:
    for i in range(attempts):
        with _lock:                                     # global throttle shared by all threads
            wait = rate - (time.time() - _last[0])
            if wait > 0:
                time.sleep(wait)
            _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _ua(), "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=120) as r:
                b = r.read()
                return gzip.decompress(b) if r.headers.get("Content-Encoding") == "gzip" else b
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            time.sleep(2 ** i)
        except Exception:  # noqa: BLE001
            time.sleep(2 ** i)
    raise RuntimeError(f"EDGAR download failed: {url}")


def cik_map() -> dict:
    p = EDGAR / "company_tickers.json"
    if not p.exists():
        p.write_bytes(get("https://www.sec.gov/files/company_tickers.json"))
    d = json.loads(p.read_text())
    return {v["ticker"].replace(".", "-"): int(v["cik_str"]) for v in d.values()}


def companyfacts(cik: int) -> dict:
    p = EDGAR / "facts" / f"CIK{cik:010d}.json.gz"
    p.parent.mkdir(exist_ok=True)
    if p.exists():
        return json.loads(gzip.decompress(p.read_bytes()))
    b = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    p.write_bytes(gzip.compress(b))
    return json.loads(b)


def submissions(cik: int) -> dict:
    """All filings metadata (recent block + older pages merged)."""
    p = EDGAR / "subs" / f"CIK{cik:010d}.json.gz"
    p.parent.mkdir(exist_ok=True)
    if p.exists():
        return json.loads(gzip.decompress(p.read_bytes()))
    d = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    frames = [pd.DataFrame(d["filings"]["recent"])]
    for f in d["filings"].get("files", []):
        frames.append(pd.DataFrame(json.loads(get(f"https://data.sec.gov/submissions/{f['name']}"))))
    allf = pd.concat(frames, ignore_index=True)
    out = {"cik": cik, "filings": allf.to_dict(orient="list")}
    p.write_bytes(gzip.compress(json.dumps(out).encode()))
    return out


# ----------------------------------------------------------------------------- point-in-time fundamentals
CONCEPTS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "cogs": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "gross_profit": ["GrossProfit"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "assets": ["Assets"],
    "equity": ["StockholdersEquity",
               "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "shares": ["CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding"],
    "eps": ["EarningsPerShareDiluted", "EarningsPerShareBasic"],
}
FLOW = {"revenue", "cogs", "gross_profit", "net_income", "cfo"}


def facts_table(d: dict) -> pd.DataFrame:
    """Long table: item, end, start, val, filed, form, fp — first-reported values only (PIT)."""
    rows = []
    for item, names in CONCEPTS.items():
        for name in names:
            for ns in ("us-gaap", "dei"):
                c = d.get("facts", {}).get(ns, {}).get(name)
                if not c:
                    continue
                for unit, vals in c["units"].items():
                    if unit not in ("USD", "shares", "USD/shares"):
                        continue
                    for v in vals:
                        if v.get("form") not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
                            continue
                        rows.append((item, name, v.get("start"), v["end"], v["val"], v["filed"], v.get("form"), v.get("fp")))
    # alternative concept names are merged: each period keeps whichever value was filed first
    t = pd.DataFrame(rows, columns=["item", "concept", "start", "end", "val", "filed", "form", "fp"])
    if t.empty:
        return t
    for c in ("start", "end", "filed"):
        t[c] = pd.to_datetime(t[c], errors="coerce")
    t["days"] = (t["end"] - t["start"]).dt.days
    # first time each (item, period) was reported = what was knowable then (no restatements)
    t = t.sort_values("filed").drop_duplicates(["item", "start", "end"], keep="first")
    return t


def pit_panel(tickers, dates: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    """Daily point-in-time panels (dates x tickers), each value usable from filed + 1 day:
       annual flows (latest FY, 330-380 day duration), quarterly EPS (80-100 days) and stock items."""
    cm = cik_map()
    items = ["revenue_ttm", "gp_ttm", "cogs_ttm", "ni_ttm", "cfo_ttm", "assets", "equity", "shares",
             "assets_lag1y", "shares_lag1y", "eps_q", "eps_q_lag4", "sue"]
    out = {k: pd.DataFrame(np.nan, index=dates, columns=tickers) for k in items}
    for i, tk in enumerate(tickers):
        cik = cm.get(tk)
        if cik is None:
            continue
        try:
            t = facts_table(companyfacts(cik))
        except Exception as e:  # noqa: BLE001
            print(f"  [edgar] {tk}: {e}", flush=True)
            continue
        if t.empty:
            continue
        t["avail"] = t["filed"] + pd.Timedelta(1, "D")

        def series(item, dur=None, value_shift=None):
            x = t[t.item == item]
            if dur is not None:
                x = x[(x.days >= dur[0]) & (x.days <= dur[1])]
            if x.empty:
                return None
            x = x.sort_values(["avail", "end"]).drop_duplicates("avail", keep="last")
            s = pd.Series(x["val"].to_numpy(float), index=x["avail"])
            return s.groupby(level=0).last().reindex(dates.union(s.index)).ffill().reindex(dates)

        for k, it in [("revenue_ttm", "revenue"), ("gp_ttm", "gross_profit"), ("cogs_ttm", "cogs"),
                      ("ni_ttm", "net_income"), ("cfo_ttm", "cfo")]:
            s = series(it, (330, 380))
            if s is not None:
                out[k][tk] = s
        for k in ("assets", "equity", "shares"):
            s = series(k)
            if s is not None:
                out[k][tk] = s
        # year-ago stock values: the value whose period end is ~1y before the latest one, known by then
        for k, it in (("assets_lag1y", "assets"), ("shares_lag1y", "shares")):
            x = t[t.item == it].sort_values("end")
            if len(x) > 4:
                lag = x.set_index("end")["val"]
                cur = x.sort_values(["avail", "end"]).drop_duplicates("avail", keep="last")
                vals = [lag[lag.index <= e - pd.Timedelta(330, "D")].iloc[-1] if (lag.index <= e - pd.Timedelta(330, "D")).any()
                        else np.nan for e in cur["end"]]
                s = pd.Series(vals, index=cur["avail"]).groupby(level=0).last()
                out[k][tk] = s.reindex(dates.union(s.index)).ffill().reindex(dates)
        # SUE from quarterly EPS: (EPS_q - EPS_{q-4}) / std of that change over the last 8 quarters
        q = t[(t.item == "eps") & (t.days >= 80) & (t.days <= 100)].sort_values("end").drop_duplicates("end")
        if len(q) > 6:
            q = q.set_index("end")
            yoy = []
            for e, row in q.iterrows():
                prev = q[(q.index >= e - pd.Timedelta(380, "D")) & (q.index <= e - pd.Timedelta(350, "D"))]
                yoy.append(row["val"] - prev["val"].iloc[-1] if len(prev) else np.nan)
            q["d"] = yoy
            q["sue"] = q["d"] / q["d"].rolling(8, min_periods=4).std()
            s = pd.Series(q["sue"].to_numpy(), index=q["avail"]).groupby(level=0).last()
            out["sue"][tk] = s.reindex(dates.union(s.index)).ffill(limit=70).reindex(dates)
        if (i + 1) % 50 == 0:
            print(f"  [edgar] fundamentals {i + 1}/{len(tickers)}", flush=True)
    return out
