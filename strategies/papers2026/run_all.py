"""Run every 2026-paper replication in sequence, then the ML4T cross-check and the
deflated-Sharpe summary.

    .venv\\Scripts\\python strategies\\papers2026\\run_all.py            # everything (several hours)
    .venv\\Scripts\\python strategies\\papers2026\\run_all.py --only 1 4 # selected papers

Runtimes on a 12-core laptop (CPU only): p1 ~2 min, p2 ~1 h, p3 ~3 h (Optuna + TabNet; cached
best params in results/p3_best_*.json make reruns ~30 min), p4 ~1 h, p8 ~1.5 h.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd  # noqa: E402

from common import RES_DIR, deflated_sharpe, save_rows, tbill_daily  # noqa: E402


def dsr_summary():
    """Deflated Sharpe (ml4t-diagnostic) of the best variant in each paper's family."""
    rows = []
    p8 = sorted(RES_DIR.glob("p8_daily_*.csv"))
    if p8:
        s = [pd.read_csv(f, index_col=0, parse_dates=True)["net"].rename(f.stem[9:]) for f in p8]
        base = [x for x in s if x.name.endswith("baseline")]
        rows.append(deflated_sharpe(s, "p8 residual stat-arb (net 5bp, all rules)", n_trials=len(s) * 8,
                                    bench=base[0] if base else None))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int, default=[1, 2, 3, 4, 8])
    a = ap.parse_args()
    t0 = time.time()
    if 1 in a.only:
        import p1_stock_bond_gold; p1_stock_bond_gold.main([])
        import ml4t_check; ml4t_check.main()
    if 2 in a.only:
        import p2_wasserstein_hmm; p2_wasserstein_hmm.main([])
    if 3 in a.only:
        import p3_tabular_hybrid; p3_tabular_hybrid.main([])
    if 4 in a.only:
        import p4_kellyboost; p4_kellyboost.main([])
    if 8 in a.only:
        import p8_attribution_statarb; p8_attribution_statarb.main([])
    rows = dsr_summary()
    if rows:
        save_rows(rows, "dsr_papers2026.csv")
    print(f"done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
