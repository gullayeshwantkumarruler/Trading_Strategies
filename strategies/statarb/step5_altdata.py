"""Step 5 — free alternative data from SEC EDGAR and FINRA (report priority 5).

(1) Lazy Prices (Cohen, Malloy & Nguyen 2020): for every 10-K and 10-Q (2008 ->), cosine similarity of
    term-frequency vectors (and Jaccard of word sets) with the same form filed ~1 year earlier (10-K vs prior
    10-K; 10-Q vs the 10-Q filed 330-400 days before). Documents are streamed, tokenised and discarded; only
    the similarities are kept. Signal = similarity of the latest filing in the last 92 days; long high-similarity
    ("non-changers"), short low-similarity, monthly rebalance.
(2) Insider purchases (Cohen, Malloy & Pomorski 2012): SEC Form 3/4/5 quarterly datasets (2006 ->), open-market
    purchases (code P). An insider is "routine" if they traded in the same calendar month in each of the prior
    3 years, otherwise "opportunistic". Signal = number of opportunistic buyers in the last 21 days (filing
    date + 1); long flagged names vs the rest; 21-day and 5-day holds.
(3) FINRA short volume (2018-08 ->): short-volume ratio SVR = ShortVolume / TotalVolume (consolidated CNMS
    files), 20-day mean, cross-sectional rank; high SVR expected to underperform -> signal = -SVR; monthly.
Every signal: monthly long-short book net of 5 bp + 1 bp/day shorts, FF5 alpha with Newey-West t-stat, IC.
"""
from __future__ import annotations

import argparse
import io
import re
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer

import core
import edgar

LP = edgar.EDGAR / "lazy_prices"
LP.mkdir(exist_ok=True)
HV = HashingVectorizer(n_features=2 ** 18, alternate_sign=False, norm="l2", token_pattern=r"(?u)\b[a-z]{3,}\b",
                       lowercase=True)
TAG = re.compile(r"<[^>]+>")
HIDDEN = re.compile(r"<ix:header>.*?</ix:header>|<script.*?</script>|<style.*?</style>", re.S | re.I)


# ----------------------------------------------------------------------------- (1) Lazy Prices
def doc_text(cik, acc, doc):
    b = edgar.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}")
    t = b.decode("utf-8", errors="ignore")
    t = HIDDEN.sub(" ", t)
    t = TAG.sub(" ", t)
    return re.sub(r"&[a-z#0-9]+;", " ", t).lower()


def lazy_prices_company(tk, cik):
    out_p = LP / f"{tk}.parquet"
    if out_p.exists():
        return pd.read_parquet(out_p)
    f = pd.DataFrame(edgar.submissions(cik)["filings"])
    f = f[f.form.isin(["10-K", "10-Q"]) & (f.filingDate >= "2008-01-01")].sort_values("filingDate")
    rows, vecs = [], []
    for _, r in f.iterrows():
        try:
            txt = doc_text(cik, r.accessionNumber, r.primaryDocument)
        except Exception:  # noqa: BLE001
            continue
        v = HV.transform([txt])
        words = set(re.findall(r"\b[a-z]{3,}\b", txt))
        filed = pd.Timestamp(r.filingDate)
        prev = None
        for (pf, pform, pv, pw) in reversed(vecs):
            gap = (filed - pf).days
            if pform == r.form and 330 <= gap <= 400:
                prev = (pv, pw)
                break
            if gap > 400:
                break
        cos = float(v.multiply(prev[0]).sum()) if prev else np.nan
        jac = len(words & prev[1]) / max(1, len(words | prev[1])) if prev else np.nan
        rows.append(dict(ticker=tk, form=r.form, filed=filed, accession=r.accessionNumber, cosine=cos, jaccard=jac,
                         n_words=len(words)))
        vecs.append((filed, r.form, v, words))
        vecs = vecs[-12:]
    df = pd.DataFrame(rows)
    df.to_parquet(out_p)
    return df


def lazy_prices(tickers, log, workers=4):
    cm = edgar.cik_map()
    todo = [(t, cm[t]) for t in tickers if t in cm]
    done = []
    with ThreadPoolExecutor(workers) as ex:
        for i, df in enumerate(ex.map(lambda x: lazy_prices_company(*x), todo)):
            done.append(df)
            if (i + 1) % 10 == 0:
                log(f"  lazy prices: {i + 1}/{len(todo)} companies")
    return pd.concat(done, ignore_index=True)


def lp_signal(lp: pd.DataFrame, dates, tickers, col="cosine"):
    S = pd.DataFrame(np.nan, index=dates, columns=tickers)
    lp = lp.dropna(subset=[col])
    for tk, g in lp.groupby("ticker"):
        if tk not in S.columns:
            continue
        s = pd.Series(g[col].to_numpy(), index=g["filed"] + pd.Timedelta(1, "D")).groupby(level=0).last()
        S[tk] = s.reindex(dates.union(s.index)).ffill(limit=92).reindex(dates)
    return S


# ----------------------------------------------------------------------------- (2) insiders
def insider_quarter(y, q):
    p = edgar.EDGAR / "form345" / f"{y}q{q}.parquet"
    p.parent.mkdir(exist_ok=True)
    if p.exists():
        return pd.read_parquet(p)
    z = zipfile.ZipFile(io.BytesIO(edgar.get(
        f"https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{y}q{q}_form345.zip")))
    rd = lambda n: pd.read_csv(z.open(n), sep="\t", dtype=str, on_bad_lines="skip")
    sub = rd("SUBMISSION.tsv")[["ACCESSION_NUMBER", "FILING_DATE", "ISSUERCIK", "DOCUMENT_TYPE"]]
    own = rd("REPORTINGOWNER.tsv")[["ACCESSION_NUMBER", "RPTOWNERCIK"]].drop_duplicates("ACCESSION_NUMBER")
    tr = rd("NONDERIV_TRANS.tsv")[["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES",
                                    "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD"]]
    df = tr.merge(sub, on="ACCESSION_NUMBER").merge(own, on="ACCESSION_NUMBER")
    df = df[df.DOCUMENT_TYPE.isin(["4", "4/A"])]
    df.to_parquet(p)
    return df


def insiders(log):
    frames = []
    for y in range(2006, 2027):
        for q in range(1, 5):
            try:
                frames.append(insider_quarter(y, q))
            except Exception as e:  # noqa: BLE001
                if y < 2026 or q < 3:
                    log(f"  form345 {y}q{q}: {e}")
        log(f"  form345 year {y} loaded")
    return pd.concat(frames, ignore_index=True)


def insider_signal(ins: pd.DataFrame, dates, tickers):
    cm = edgar.cik_map()
    cik2tk = {v: k for k, v in cm.items() if k in set(tickers)}
    d = ins.copy()
    d["cik"] = pd.to_numeric(d.ISSUERCIK, errors="coerce")
    d = d[d.cik.isin(cik2tk.keys())]
    d["ticker"] = d.cik.map(cik2tk)
    d["tdate"] = pd.to_datetime(d.TRANS_DATE, errors="coerce", format="mixed", dayfirst=True)
    d["fdate"] = pd.to_datetime(d.FILING_DATE, errors="coerce", format="mixed", dayfirst=True)
    d = d.dropna(subset=["tdate", "fdate"])
    # routine = traded (any code P/S) in the same calendar month in each of the prior 3 years
    trades = d[d.TRANS_CODE.isin(["P", "S"])]
    ym = set(zip(trades.RPTOWNERCIK, trades.tdate.dt.year, trades.tdate.dt.month))
    buys = d[d.TRANS_CODE == "P"].copy()
    buys["routine"] = [all((o, y - k, m) in ym for k in (1, 2, 3))
                       for o, y, m in zip(buys.RPTOWNERCIK, buys.tdate.dt.year, buys.tdate.dt.month)]
    opp = buys[~buys.routine].drop_duplicates(["ticker", "RPTOWNERCIK", "fdate"])
    S = pd.DataFrame(0.0, index=dates, columns=tickers)
    ev = opp.groupby(["fdate", "ticker"]).size()
    for (fd, tk), n in ev.items():
        loc = dates.searchsorted(fd + pd.Timedelta(1, "D"))
        if loc < len(dates):
            S.iloc[loc:loc + 21, S.columns.get_loc(tk)] += n           # active for 21 trading days
    return S, len(opp)


# ----------------------------------------------------------------------------- (3) FINRA short volume
def finra_day(d: pd.Timestamp):
    p = core.DATA / "finra" / f"{d:%Y%m%d}.parquet"
    p.parent.mkdir(exist_ok=True)
    if p.exists():
        return pd.read_parquet(p)
    try:
        b = urllib.request.urlopen(urllib.request.Request(
            f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt",
            headers={"User-Agent": "Mozilla/5.0 research"}), timeout=60).read()
    except Exception:  # noqa: BLE001
        return None
    df = pd.read_csv(io.BytesIO(b), sep="|")
    df = df[df.Symbol.notna() & df.Date.astype(str).str.isdigit()]
    df = df[["Symbol", "ShortVolume", "TotalVolume"]]
    df.to_parquet(p)
    return df


def finra(dates, tickers, log):
    ds = [d for d in dates if d >= pd.Timestamp("2018-08-01")]
    with ThreadPoolExecutor(8) as ex:
        parts = list(ex.map(finra_day, ds))
    svr = pd.DataFrame(np.nan, index=dates, columns=tickers)
    for d, df in zip(ds, parts):
        if df is None:
            continue
        df = df.assign(Symbol=df.Symbol.str.replace(".", "-", regex=False)).set_index("Symbol")
        x = (df.ShortVolume / df.TotalVolume).reindex(tickers)
        svr.loc[d] = x.to_numpy()
    log(f"  FINRA: {sum(p is not None for p in parts)} daily files")
    return svr


# ----------------------------------------------------------------------------- evaluation
def ff5_alpha(r: pd.Series):
    import statsmodels.api as sm
    ff = core.panel()["ff"][["mkt_rf", "smb", "hml", "rmw", "cma"]].reindex(r.index)
    m = sm.OLS(r.values, sm.add_constant(ff.values), missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": 21})
    return m.params[0] * core.ANN, m.tvalues[0]


def monthly_ls(S: pd.DataFrame, P, quantile=0.2, hold=None):
    R = P["R"]
    me = pd.Series(R.index, R.index).groupby([R.index.year, R.index.month]).max().to_list()
    reb = me if hold is None else list(R.index[::hold])
    aim = pd.DataFrame(np.nan, R.index, R.columns)
    Sr = S.reindex(R.index)
    for d in reb:
        x = Sr.loc[d]
        if x.notna().sum() < 30:
            aim.loc[d] = 0.0
            continue
        hi, lo = x.quantile(1 - quantile), x.quantile(quantile)
        w = (x >= hi).astype(float) / max(1, (x >= hi).sum()) - (x <= lo).astype(float) / max(1, (x <= lo).sum())
        aim.loc[d] = (w / w.abs().sum()).fillna(0).to_numpy()
    return aim.ffill().fillna(0.0).to_numpy()


def flag_book(F: pd.DataFrame, P, hold=21):
    """Long names with a flag, short the equal-weighted rest (dollar neutral), rebalanced daily."""
    f = (F > 0).astype(float)
    n = f.sum(axis=1)
    long = f.div(n.replace(0, np.nan), axis=0).fillna(0)
    short = (1 - f).div((1 - f).sum(axis=1), axis=0)
    W = (long - short).where(n > 0, 0.0) * 0.5
    return W.to_numpy()


def report(name, W, P, family, params, start):
    bt = core.backtest(W, start=start)
    d = core.summarize(bt, name, family, params)
    a, t = ff5_alpha(bt["net"])
    d.update(FF5_alpha_ann=a, FF5_alpha_t=t)
    return d, bt


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", nargs="*", default=["finra", "insider", "lazy"])
    a = ap.parse_args(argv)
    log = core.Timer()
    P = core.panel()
    R = P["R"]
    dates, tickers = R.index, list(R.columns)
    curves = {}
    # keep rows from parts not rerun this time
    prev = core.RES / "step5_altdata.csv"
    tag = {"finra": "FINRA", "insider": "Insider", "lazy": "Lazy Prices"}
    rows = []
    if prev.exists():
        rows = [r for r in pd.read_csv(prev).to_dict("records")
                if not any(str(r["strategy"]).startswith(tag[p]) for p in a.parts)]

    if "finra" in a.parts:
        log("FINRA short volume")
        svr = finra(dates, tickers, log).rolling(20, min_periods=10).mean()
        d, bt = report("FINRA -SVR20 monthly quintile L/S", monthly_ls(-svr, P), P, "s5_altdata",
                       {"src": "FINRA"}, "2018-10-01")
        rows.append(d); curves["FINRA -SVR"] = bt["net"]
        core.save(rows, "step5_altdata.csv")

    if "insider" in a.parts:
        log("SEC Form 345 insider purchases")
        ins = insiders(log)
        F, n_opp = insider_signal(ins, dates, tickers)
        log(f"  opportunistic purchase events in universe: {n_opp}")
        new_events = (F.diff().fillna(F) > 0).astype(float)          # first day a purchase becomes public
        for hold in (21, 5):
            Fh = F if hold == 21 else new_events.rolling(5, min_periods=1).sum()
            d, bt = report(f"Insider opportunistic buys hold {hold}d", flag_book(Fh, P), P, "s5_altdata",
                           {"src": "Form4", "hold": hold, "events": n_opp}, core.START)
            rows.append(d); curves[f"Insider {hold}d"] = bt["net"]
        core.save(rows, "step5_altdata.csv")

    if "lazy" in a.parts:
        log("Lazy Prices: downloading and comparing 10-K / 10-Q text (long)")
        lp = lazy_prices(tickers, log)
        lp.to_parquet(core.DATA / "lazy_prices_all.parquet")
        for col in ("cosine", "jaccard"):
            S = lp_signal(lp, dates, tickers, col)
            d, bt = report(f"Lazy Prices {col} monthly quintile L/S", monthly_ls(S, P), P, "s5_altdata",
                           {"src": "EDGAR text", "measure": col}, core.START)
            rows.append(d); curves[f"Lazy Prices {col}"] = bt["net"]
        core.save(rows, "step5_altdata.csv")

    df = core.save(rows, "step5_altdata.csv")
    core.show(df)
    print(df[["strategy", "FF5_alpha_ann", "FF5_alpha_t"]].to_string(index=False), flush=True)
    core.plot(curves, "Step 5: free alt-data signals (net of 5bp + 1bp/day shorts)", "step5_altdata.png")
    log("done")


if __name__ == "__main__":
    main()
