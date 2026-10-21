"""Deflated Sharpe over the logged trials on the full common window (2013-03 -> 2026-08).

core.deflated_all() uses the intersection of every trial's dates, which the short FINRA (2018 ->) and
MOSEK min-trade (2022 ->) series shrink to ~7 years. Here only trials with full 2013-2026 history are used,
(a) against all of them and (b) excluding the deliberately naive daily-full-rebalance variants, whose very
negative Sharpes inflate the cross-trial variance. Also tests the two leading strategies individually.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio_from_statistics

import core

LEADERS = ["s4_blend__optimiser_slow=LightGBM_fast_w=0.0_g=0.5",
           "s3_dlsa__Attention_Factors_lite_K=10_cost-in-loss"]
NAIVE = ("daily_full", "rev5_daily", "clusters_daily", "fast_w=1.0_g=0.05")


def dsr(x: pd.Series, sr_obs: float, trials_sr: pd.Series) -> float:
    r = deflated_sharpe_ratio_from_statistics(
        observed_sharpe=float(sr_obs), n_samples=len(x), n_trials=len(trials_sr),
        variance_trials=float(trials_sr.var()), skewness=float(skew(x)), excess_kurtosis=float(kurtosis(x)),
        autocorrelation=float(x.autocorr()), frequency="daily")
    return float(r.probability)


def main():
    S = {f.stem: pd.read_parquet(f).iloc[:, 0] for f in sorted(core.TRIALS.glob("*.parquet"))}
    W = pd.DataFrame(S).loc["2013-03-01":"2026-08-27"]
    full = W.loc[:, W.notna().mean() > 0.99].fillna(0.0)
    sr = full.mean() / full.std()
    cand = [c for c in full if not any(k in c for k in NAIVE)]
    rows = []
    for label, cols in [("all full-history trials", list(full.columns)), ("excluding naive daily-rebalance variants", cand)]:
        s = sr[cols]
        best = s.idxmax()
        rows.append(dict(set=label, n_trials=len(cols), window="2013-03..2026-08", strategy=best,
                         SR_ann=float(s.max() * np.sqrt(core.ANN)), dsr_prob=dsr(full[best], s.max(), s)))
    for nm in LEADERS:
        if nm in full:
            rows.append(dict(set="single strategy vs candidate trials", n_trials=len(cand), window="2013-03..2026-08",
                             strategy=nm, SR_ann=float(sr[nm] * np.sqrt(core.ANN)), dsr_prob=dsr(full[nm], sr[nm], sr[cand])))
    # (c) noise-only null: trial Sharpes differ only by sampling error (Var = 1/T), K = all candidate trials
    for nm in LEADERS:
        if nm in full:
            x = full[nm]
            r = deflated_sharpe_ratio_from_statistics(
                observed_sharpe=float(sr[nm]), n_samples=len(x), n_trials=len(cand), variance_trials=1.0 / len(x),
                skewness=float(skew(x)), excess_kurtosis=float(kurtosis(x)), autocorrelation=float(x.autocorr()),
                frequency="daily")
            rows.append(dict(set="noise-only null (Var=1/T), K = candidate trials", n_trials=len(cand),
                             window="2013-03..2026-08", strategy=nm, SR_ann=float(sr[nm] * np.sqrt(core.ANN)),
                             dsr_prob=float(r.probability)))
    # (d) family-level: each leader against the variants it was selected from, correlation-adjusted K_eff
    from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio
    fams = {LEADERS[0]: [c for c in full if c.startswith("s4_")],
            LEADERS[1]: [c for c in full if c.startswith("s3_")]}
    for nm, cols in fams.items():
        if nm in full and len(cols) > 1:
            r = deflated_sharpe_ratio([full[c].to_numpy() for c in cols], frequency="daily",
                                      correlation_method="effective_rank")
            rows.append(dict(set=f"family selection ({len(cols)} variants, effective-rank K_eff)", n_trials=len(cols),
                             window="2013-03..2026-08", strategy=nm, SR_ann=float(sr[cols].max() * np.sqrt(core.ANN)),
                             dsr_prob=float(r.probability)))
    df = pd.DataFrame(rows)
    if all(n in full for n in LEADERS):
        print("correlation of the two leaders' daily returns:", round(full[LEADERS[0]].corr(full[LEADERS[1]]), 3))
        combo = full[LEADERS[0]] / full[LEADERS[0]].std() + full[LEADERS[1]] / full[LEADERS[1]].std()
        print("equal-risk combination SR:", round(combo.mean() / combo.std() * np.sqrt(core.ANN), 3))
    df.to_csv(core.RES / "deflated_sharpe_full_window.csv", index=False, float_format="%.4f")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
