"""Run all rules-based / regime strategy backtests end to end.

Usage (from the project root):
    .venv\\Scripts\\python strategies\\rules\\run_all.py              # use cached data (<7 days old)
    .venv\\Scripts\\python strategies\\rules\\run_all.py --refresh    # re-download prices + refit JM
    .venv\\Scripts\\python strategies\\rules\\run_all.py --only tom,sector

Outputs (strategies\\rules\\results\\):
    metrics_rules.csv      one row per strategy / variant / benchmark
    dsr_rules.csv          deflated Sharpe ratio per strategy family (ml4t-diagnostic)
    tom_stats.csv          turn-of-month in-window vs out-of-window daily returns
    trend_region_contrib.csv  trend P&L by region
    notes_rules.json       engine parity checks, lambda usage, gate shares
    *.png                  equity curves + drawdowns
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pandas as pd  # noqa: E402

MODULES = ["jump_model", "trend", "momentum", "tom", "sector", "ml4t_engine"]
TICKERS = ["SPY", "QQQ", "IWM", "EZU", "VGK", "EWG", "EWU", "EWQ", "EWJ", "DXJ", "FXI", "MCHI", "ASHR",
           "KWEB", "EWH", "TLT", "IEF", "GLD", "EFA", "EEM", "IYR", "LQD", "TIP", "USO", "DBC", "FXE",
           "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLRE", "XLC",
           "^GSPC", "^GDAXI", "^N225", "000300.SS", "^STOXX50E", "^IRX"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download data and refit jump models")
    ap.add_argument("--only", default="", help="comma list of modules to run")
    a = ap.parse_args()
    from common import RES_DIR, fetch

    t0 = time.time()
    print("== data ==")
    for t in TICKERS:
        try:
            fetch(t, refresh=a.refresh)
        except Exception as e:
            print(f"  [warn] {t}: {e}")
    os.environ["RULES_OFFLINE"] = "1"  # everything below reads the cache

    mods = [m for m in MODULES if not a.only or m in a.only.split(",")]
    all_rows, all_dsr, notes, failures = [], [], {}, {}
    for name in mods:
        print(f"== {name} ==", flush=True)
        t = time.time()
        try:
            mod = __import__(name)
            if name == "jump_model":
                df, dsr, extra = mod.run(refresh_signals=a.refresh)
            else:
                df, dsr, extra = mod.run()
            all_rows.append(df)
            if dsr is not None:
                all_dsr.extend(dsr if isinstance(dsr, list) else [dsr])
            for k, v in (extra or {}).items():
                if isinstance(v, pd.DataFrame):
                    fn = {"tom_stats": "tom_stats.csv", "region_contrib": "trend_region_contrib.csv"}.get(k, f"{k}.csv")
                    v.to_csv(RES_DIR / fn, index=False)
                else:
                    notes[f"{name}.{k}"] = v
            print(f"   ok ({time.time() - t:.0f}s, {len(df)} rows)")
        except Exception as e:
            failures[name] = f"{e.__class__.__name__}: {e}"
            traceback.print_exc()
    if all_rows:
        met = pd.concat(all_rows, ignore_index=True)
        met.to_csv(RES_DIR / "metrics_rules.csv", index=False, float_format="%.5f")
        pd.set_option("display.width", 250)
        pd.set_option("display.max_rows", 500)
        cols = ["strategy", "start", "CAGR", "Vol", "Sharpe", "Sortino", "MaxDD", "Calmar", "Turnover",
                "IS_Sharpe", "OOS_Sharpe"]
        print(met[cols].round(3).to_string())
    if all_dsr:
        dsr = pd.DataFrame(all_dsr)
        dsr.to_csv(RES_DIR / "dsr_rules.csv", index=False, float_format="%.5f")
        print(dsr.round(4).to_string())
    notes["failures"] = failures
    with open(RES_DIR / "notes_rules.json", "w") as f:
        json.dump(notes, f, indent=2, default=str)
    print(f"done in {time.time() - t0:.0f}s; failures: {failures or 'none'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
