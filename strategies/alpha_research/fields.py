"""Data fields for formulaic alpha research — one aligned daily grid (dates x 337 stocks).

All fields are known at the close of each date (alt data from the day after its filing/publication).
Groups:
  price/volume : close, ret, volume, dvol (dollar volume), resid (FF5 residual return), beta (FF5 market beta)
  fundamentals : gpa, asset_growth, accruals, issuance, ey, bm, roe, cfoa, sue   (SEC XBRL, first-reported, PIT)
  alt (round 3): insider_opp (opportunistic insider buyers active in last 21d), svr (FINRA short-volume ratio, 2018->),
                 lp_jac / lp_cos (Lazy Prices similarity of latest 10-K/10-Q vs year-ago filing)
  alt (new)    : wiki (log daily Wikipedia page views, 2015-07->), k8 (8-K filings that day), k8_502 (executive
                 change items), k8_202 (results-of-operations items), k8_101 (material agreements),
                 filing_delay (days from period end to 10-K/10-Q filing minus the firm's trailing median delay)
Cached to data/fields.npz.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
STATARB = ROOT.parent / "statarb"
sys.path.insert(0, str(STATARB))
import core  # noqa: E402  (also puts papers2026 on the path)

DATA = ROOT / "data"
RES = ROOT / "results"
for d in (DATA, RES):
    d.mkdir(exist_ok=True)
UA = {"User-Agent": "Trading_Strategies research (github.com/gullayeshwantkumarruler/Trading_Strategies)"}


def _to_grid(events: pd.DataFrame, dates, tickers, value="n", how="sum"):
    """events: columns ticker, date (usable date), value -> dates x tickers grid (0 where no event)."""
    g = pd.DataFrame(0.0, index=dates, columns=tickers)
    if events.empty:
        return g
    ev = events.copy()
    ev["loc"] = dates.searchsorted(ev["date"])
    ev = ev[ev["loc"] < len(dates)]
    agg = ev.groupby(["loc", "ticker"])[value].agg(how)
    for (loc, tk), v in agg.items():
        if tk in g.columns:
            g.iat[loc, g.columns.get_loc(tk)] += v
    return g


def wiki_titles() -> dict:
    p = DATA / "wiki_titles.json"
    if p.exists():
        return json.loads(p.read_text())
    from common import _get
    from lxml import html as LH
    doc = LH.fromstring(_get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies").decode())
    m = {}
    for r in doc.xpath('//table[@id="constituents"]//tr')[1:]:
        tds = r.xpath("./td")
        if len(tds) >= 2:
            a = tds[1].xpath(".//a/@href")
            if a:
                m[tds[0].text_content().strip().replace(".", "-")] = a[0].split("/wiki/")[-1]
    p.write_text(json.dumps(m))
    return m


def wiki_views(tickers, dates) -> pd.DataFrame:
    p = DATA / "wiki_views.parquet"
    have = pd.read_parquet(p) if p.exists() else pd.DataFrame()
    titles = wiki_titles()
    missing = [t for t in tickers if t not in have.columns and t in titles]
    if not missing:
        return have.reindex(index=dates, columns=tickers)

    def one(tk):
        t = titles.get(tk)
        if not t:
            return tk, None
        u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
             f"{t}/daily/2015070100/{pd.Timestamp.today():%Y%m%d}00")
        for i in range(4):
            try:
                b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
                it = json.loads(b)["items"]
                return tk, pd.Series({pd.Timestamp(x["timestamp"][:8]): x["views"] for x in it})
            except Exception:  # noqa: BLE001
                time.sleep(2 ** i)
        return tk, None

    res = {}
    for tk in missing:                                  # sequential + pause: the API rate-limits bursts
        res[tk] = one(tk)[1]
        time.sleep(0.4)
    new = pd.DataFrame({k: v for k, v in res.items() if v is not None})
    df = pd.concat([have, new], axis=1) if len(have) else new
    df.to_parquet(p)
    return df.reindex(index=dates, columns=tickers)


def refresh_wiki():
    """Fetch missing tickers and update only the 'wiki' field in the cached fields.npz."""
    P = core.panel()
    dates, tickers = P["R"].index, list(P["R"].columns)
    wv = wiki_views(tickers, dates)
    z = dict(np.load(DATA / "fields.npz"))
    z["wiki"] = np.log1p(wv).to_numpy(np.float32)
    np.savez_compressed(DATA / "fields.npz", **z)
    return wv


def sec_events(tickers, dates):
    """8-K counts by item and 10-K/10-Q filing delay from the cached EDGAR submissions index."""
    import edgar
    cm = edgar.cik_map()
    rows, delays = [], []
    for tk in tickers:
        cik = cm.get(tk)
        p = edgar.EDGAR / "subs" / f"CIK{cik:010d}.json.gz" if cik else None
        if not p or not p.exists():
            continue
        f = pd.DataFrame(json.loads(gzip.decompress(p.read_bytes()))["filings"])
        f["date"] = pd.to_datetime(f["filingDate"]) + pd.Timedelta(1, "D")       # usable the day after filing
        k = f[f.form == "8-K"]
        for _, r in k.iterrows():
            items = str(r.get("items") or "")
            rows.append((tk, r.date, 1.0, float("5.02" in items), float("2.02" in items), float("1.01" in items)))
        q = f[f.form.isin(["10-K", "10-Q"])].copy()
        q["rep"] = pd.to_datetime(q["reportDate"], errors="coerce")
        q = q.dropna(subset=["rep"]).sort_values("date")
        q["delay"] = (pd.to_datetime(q["filingDate"]) - q["rep"]).dt.days
        q["rel"] = q["delay"] - q.groupby("form")["delay"].transform(lambda s: s.shift(1).rolling(8, min_periods=3).median())
        for _, r in q.dropna(subset=["rel"]).iterrows():
            delays.append((tk, r.date, float(r.rel)))
    ev = pd.DataFrame(rows, columns=["ticker", "date", "n", "i502", "i202", "i101"])
    out = {"k8": _to_grid(ev, dates, tickers, "n"), "k8_502": _to_grid(ev, dates, tickers, "i502"),
           "k8_202": _to_grid(ev, dates, tickers, "i202"), "k8_101": _to_grid(ev, dates, tickers, "i101")}
    dl = pd.DataFrame(delays, columns=["ticker", "date", "rel"])
    fd = pd.DataFrame(np.nan, index=dates, columns=tickers)
    for tk, g in dl.groupby("ticker"):
        s = pd.Series(g["rel"].to_numpy(), index=g["date"]).groupby(level=0).last()
        fd[tk] = s.reindex(dates.union(s.index)).ffill(limit=100).reindex(dates)
    out["filing_delay"] = fd
    return out


def build(refresh=False) -> dict[str, pd.DataFrame]:
    p = DATA / "fields.npz"
    P = core.panel()
    R = P["R"]
    dates, tickers = R.index, list(R.columns)
    if p.exists() and not refresh:
        z = np.load(p)
        return {k: pd.DataFrame(z[k], dates, tickers) for k in z.files}
    F = {}
    px, vol = P["px"], P["vol"]
    F["close"], F["ret"], F["volume"] = px, px.pct_change(fill_method=None), vol
    F["dvol"] = px * vol
    F["resid"] = pd.DataFrame(P["eps"], dates, tickers)
    F["beta"] = pd.DataFrame(P["B"][:, :, 0], dates, tickers)
    import step4_alpha_library as s4
    fs = s4.fund_signals(P)
    F.update({"gpa": fs["gross_prof"], "asset_growth": -fs["asset_growth"], "accruals": -fs["accruals"],
              "issuance": -fs["net_issuance"], "ey": fs["earnings_yield"], "bm": fs["book_to_market"],
              "roe": fs["roe"], "cfoa": fs["cfo_assets"], "sue": fs["sue"]})       # raw (unsigned) definitions
    import step5_altdata as s5
    ins = s5.insiders(lambda m: None)
    F["insider_opp"], _ = s5.insider_signal(ins, dates, tickers)
    svr = s5.finra(dates, tickers, lambda m: None)
    F["svr"] = svr
    lp = pd.read_parquet(core.DATA / "lazy_prices_all.parquet")
    F["lp_jac"] = s5.lp_signal(lp, dates, tickers, "jaccard")
    F["lp_cos"] = s5.lp_signal(lp, dates, tickers, "cosine")
    wv = wiki_views(tickers, dates)
    F["wiki"] = np.log1p(wv)
    F.update(sec_events(tickers, dates))
    np.savez_compressed(p, **{k: v.to_numpy(np.float32) for k, v in F.items()})
    return F


def coverage(F) -> pd.DataFrame:
    rows = []
    for k, v in F.items():
        nn = v.notna().mean(axis=1)
        first = nn[nn > 0.5].index.min()
        rows.append(dict(field=k, first_date_50pct=None if pd.isna(first) else first.date(),
                         avg_coverage_2020=float(nn.loc["2020"].mean())))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import os
    assert os.environ.get("SEC_USER_AGENT"), "set SEC_USER_AGENT (only needed if EDGAR caches are missing)"
    F = build(refresh=True)
    cov = coverage(F)
    cov.to_csv(RES / "field_coverage.csv", index=False)
    print(cov.to_string(index=False))
