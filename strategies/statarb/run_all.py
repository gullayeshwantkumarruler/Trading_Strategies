"""Run the whole equity stat-arb build (report "Equity stat arb alpha and alt data") and the final
deflated-Sharpe check across every variant tried.

    set SEC_USER_AGENT=Your Name your.email@example.com      (needed for steps 4-5; SEC policy)
    .venv\\Scripts\\python strategies\\statarb\\run_all.py              # everything (many hours)
    .venv\\Scripts\\python strategies\\statarb\\run_all.py --only 1 2   # selected steps

Steps: 1 construction/optimiser, 2 residual ladder + Robeco + SPONGE, 3 DLSA, 3b Attention Factors lite,
4 alpha library + EDGAR fundamentals + blends, 5 FINRA / insiders / Lazy Prices, 6 collector (one run),
mosek (needs a licence). Runtimes on a 12-core laptop: 1 ~1 h, 2 ~30 min, 3 ~3 h, 3b ~2.5 h, 4 ~20 min,
5 ~3-4 h first time (EDGAR text download), cached afterwards.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd  # noqa: E402

import core  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=["1", "2", "3", "3b", "4", "5", "6", "mosek"])
    a = ap.parse_args()
    log = core.Timer()
    if "1" in a.only:
        import step1_construction; step1_construction.main([])
    if "2" in a.only:
        import step2_residuals; step2_residuals.main()
    if "3" in a.only:
        import step3_dlsa; step3_dlsa.main([])
    if "3b" in a.only:
        import step3b_attention_factors; step3b_attention_factors.main()
    if "4" in a.only:
        import step4_alpha_library; step4_alpha_library.main([])
    if "5" in a.only:
        import step5_altdata; step5_altdata.main([])
    if "6" in a.only:
        import collect_daily; collect_daily.main()
    if "mosek" in a.only:
        import mosek_bench; mosek_bench.main([])
    d = core.deflated_all()
    pd.DataFrame([d]).to_csv(core.RES / "deflated_sharpe_all_trials.csv", index=False)
    print(pd.Series(d).to_string(), flush=True)
    log("all done")


if __name__ == "__main__":
    main()
