"""Phase 5 — one scorecard for every price-action strategy run in rounds 5 and 5b.

Candidates (net daily returns):
  swing      round-5 swing rules, 15 ETFs, MOC fill        (2 bp base; 6 and 10 bp stress; next-open fill stress)
  hybrid     round-5b daily rules and hybrids              (same cost grid)
  positional round-5 Faber offset 0, ATH + ATR books etc.  (5 bp; no stress grid -> stress = base cost)
  intraday   round-5 / 5b minute strategies                ($0.001/share slippage base; $0.01 stress)
Windows: daily strategies - development to 2015, sealed holdout 2016 -> Oct 2026 (later-inception rules start when
their data does); intraday - development 2016-2022, holdout 2023 -> Oct 2026.

Per candidate: Sharpe (dev / holdout / holdout at stress cost / holdout next-open fill), CAGR, max DD, exposure,
Lo-adjusted Sharpe, stationary-bootstrap 95% CI, PSR, MinTRL, Harvey-Liu BHY haircut Sharpe (N = distinct strategy
configurations: every ranked candidate plus the Faber rebalance offsets left out of the ranking; cost and fill
re-runs of the same rule are not counted as new trials), alpha/beta vs SPY (Newey-West),
Ledoit-Wolf-style Sharpe difference vs SPY, share of positive holdout years.
Family-level: PBO by CSCV (16 blocks) per family; Hansen SPA / White RC and Romano-Wolf StepM vs cash and vs SPY on
holdout; deflated Sharpe over all candidates.
Gates: holdout Sharpe > 0 at stress cost, development Sharpe > 0, haircut Sharpe > 0.
Score: percentile ranks - holdout Sharpe 30%, stress-cost holdout Sharpe 20%, haircut Sharpe 15%, NW alpha t 10%,
Lo full Sharpe 10%, holdout max DD 10%, positive-year share 5%.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import data
import engine as E
import evaluate as V

PPY = 252
D_HOLD, I_HOLD = "2016-01-01", "2023-01-01"
D = data.DATA


def trim(r: pd.Series) -> pd.Series:
    r = r.astype(float).fillna(0.0)
    nz = r.ne(0)
    return r.loc[nz.idxmax():] if nz.any() else r


def load() -> tuple[dict, int]:
    """{key: dict(family, base, stress, next_open, hold)}, total trial count."""
    C = {}
    n_trials = 0
    sw = pd.read_parquet(D / "swing_series.parquet")
    n_trials += sw.shape[1]
    for col in sw.columns:
        if col.endswith("|close|2bp"):
            k = col.rsplit("|", 2)[0]
            C[f"swing:{k}"] = dict(family="swing", base=sw[col], stress=sw[f"{k}|close|10bp"],
                                   next_open=sw[f"{k}|next_open|2bp"], hold=D_HOLD)
    hb = {c: pd.read_parquet(D / f"hybrid_series_{c}bp.parquet") for c in (2, 6, 10)}
    hn = pd.read_parquet(D / "hybrid_series_2bp_next_open.parquet")
    n_trials += sum(x.shape[1] for x in hb.values()) + hn.shape[1]
    for k in hb[2].columns:
        C[f"hybrid:{k}"] = dict(family="hybrid", base=hb[2][k], stress=hb[10][k],
                                next_open=hn[k] if k in hn else None, hold=D_HOLD)
    ps = pd.read_parquet(D / "positional_series.parquet")
    n_trials += ps.shape[1]
    for k in ps.columns:
        if k.startswith("faber|") and not k.endswith("|off0"):
            continue
        C[f"positional:{k}"] = dict(family="positional", base=ps[k], stress=ps[k], next_open=None, hold=D_HOLD)
    i1 = pd.read_parquet(D / "intraday_series_base.parquet")
    i2 = pd.read_parquet(D / "intraday2_series.parquet")
    n_trials += i1.shape[1] + i2.shape[1]
    for col in i2.columns:
        if col.endswith("|0.001"):
            k = col.rsplit("|", 1)[0]
            C[f"intraday:{k}"] = dict(family="intraday", base=i2[col], stress=i2[f"{k}|0.01"], next_open=None,
                                      hold=I_HOLD)
    for col in i1.columns:
        k = col.rsplit("|", 1)[0]
        if not k.startswith("noise") and f"intraday:{k}" not in C:
            C[f"intraday:{k}"] = dict(family="intraday", base=i1[col], stress=i1[col], next_open=None, hold=I_HOLD)
    for v in C.values():
        v["base"].index = pd.DatetimeIndex(v["base"].index).normalize()
        v["stress"].index = pd.DatetimeIndex(v["stress"].index).normalize()
    return C, n_trials


def sr(r):
    return float(r.mean() / r.std() * np.sqrt(PPY)) if r.std() > 0 else 0.0


def score_one(key, c, spy, n_trials):
    b = trim(c["base"])
    st = c["stress"].reindex(b.index).fillna(0.0)
    hold = c["hold"]
    dev, ho = b.loc[:pd.Timestamp(hold) - pd.Timedelta(days=1)], b.loc[hold:]
    if len(ho) < 250:
        return None
    sp = spy.reindex(ho.index).fillna(0.0)
    m = E.metrics(ho, pd.DataFrame(), (ho != 0).astype(int), PPY, 0)
    lo, hi = V.sharpe_ci(ho, PPY, reps=500)
    ab = V.alpha_beta(ho, sp)
    d_sr, p_diff = V.sharpe_diff(ho, sp, PPY, reps=500)
    yrs = (1 + ho).groupby(ho.index.year).prod() - 1
    no = trim(c["next_open"]).loc[hold:] if c.get("next_open") is not None else None
    return dict(
        key=key, family=c["family"], start=str(b.index[0].date()), holdout_start=hold,
        SR_dev=sr(dev) if len(dev) > 250 else np.nan, SR_holdout=sr(ho), SR_holdout_stress=sr(st.loc[hold:]),
        SR_holdout_next_open=sr(no) if no is not None and len(no) else np.nan,
        CAGR_holdout=m["CAGR"], maxDD_holdout=m["maxDD"], exposure=m.get("exposure", np.nan),
        SR_full=sr(b), SR_full_lo=V.lo_sharpe(b, PPY), CI_lo=lo, CI_hi=hi, PSR_holdout=E.psr(ho),
        MinTRL_yrs=V.min_trl(b, PPY), SR_haircut=V.haircut_sharpe(sr(b), len(b), n_trials, PPY),
        alpha_ann=ab["alpha_ann"], alpha_t=ab["alpha_t"], beta=ab["beta"],
        SR_minus_SPY=d_sr, p_SR_vs_SPY=p_diff, pos_years=float((yrs > 0).mean()),
        SPY_SR_holdout=sr(sp),
    )


def main():
    C, n_trials = load()
    n_distinct = len(C) + 20 * 8          # ranked candidates + the 20 extra Faber rebalance offsets of 8 series
    spy = data.daily("SPY")["Close"].pct_change()
    spy.index = spy.index.normalize()
    rows = [x for x in (score_one(k, c, spy, n_distinct) for k, c in C.items()) if x]
    L = pd.DataFrame(rows)
    L["gate_stress"] = L.SR_holdout_stress > 0
    L["gate_dev"] = L.SR_dev.fillna(0) > 0
    L["gate_haircut"] = L.SR_haircut > 0
    L["passes"] = L[["gate_stress", "gate_dev", "gate_haircut"]].all(1)
    pr = lambda s, asc=True: s.rank(pct=True, ascending=asc)  # noqa: E731
    L["score"] = (0.30 * pr(L.SR_holdout) + 0.20 * pr(L.SR_holdout_stress) + 0.15 * pr(L.SR_haircut)
                  + 0.10 * pr(L.alpha_t) + 0.10 * pr(L.SR_full_lo) + 0.10 * pr(L.maxDD_holdout)
                  + 0.05 * pr(L.pos_years))
    # ---- family / multiple-testing diagnostics on holdout
    fam = {}
    for f in ("swing", "hybrid", "positional", "intraday"):
        keys = L.key[L.family == f].tolist()
        R = pd.DataFrame({k: trim(C[k]["base"]) for k in keys})
        hold = I_HOLD if f == "intraday" else D_HOLD
        start = R.notna().all(1).idxmax() if f != "intraday" else R.index[0]
        Rf = R.loc[start:].fillna(0.0)
        Rh = R.loc[hold:].fillna(0.0)
        zero = pd.Series(0.0, index=Rh.index)
        sp = spy.reindex(Rh.index).fillna(0.0)
        fam[f] = dict(n=len(keys), pbo=V.pbo(Rf, 16), spa_vs_cash=V.spa(Rh, zero, reps=500),
                      spa_vs_spy=V.spa(Rh, sp, reps=500), stepm_vs_cash=V.stepm(Rh, zero, reps=500),
                      stepm_vs_spy=V.stepm(Rh, sp, reps=500), pbo_window=str(start.date()))
        print(f, json.dumps({k: v for k, v in fam[f].items() if k != "pbo"}, default=str)[:600], flush=True)
    L["stepm_vs_cash"] = L.key.isin(sum((fam[f]["stepm_vs_cash"] for f in fam), []))
    L["stepm_vs_spy"] = L.key.isin(sum((fam[f]["stepm_vs_spy"] for f in fam), []))
    dsr = E.deflated_sharpe([trim(C[k]["base"]).rename(k) for k in L.key], PPY)
    L = L.sort_values(["passes", "score"], ascending=False)
    L.to_csv(data.RES / "leaderboard.csv", index=False, float_format="%.4f")
    (data.RES / "leaderboard_family.json").write_text(json.dumps(dict(n_trials=n_trials, n_distinct=n_distinct, dsr_all=dsr, families=fam),
                                                                indent=1, default=str))
    cols = ["key", "SR_dev", "SR_holdout", "SR_holdout_stress", "CAGR_holdout", "maxDD_holdout", "SR_haircut",
            "alpha_t", "passes", "stepm_vs_cash", "score"]
    print(L[cols].head(30).to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print("trials", n_trials, "DSR", dsr)


if __name__ == "__main__":
    main()
