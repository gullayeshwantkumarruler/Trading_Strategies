"""Optional — MOSEK vs Clarabel on the step 1 optimiser, plus mixed-integer extensions only MOSEK solves here.

Needs a licence file at %USERPROFILE%\\mosek\\mosek.lic (free 30-day trial or free academic licence from
https://www.mosek.com/products/academic-licenses/ / https://www.mosek.com/try/). Without one the script
exits with instructions.

(1) Same continuous problem (step 1, 5-day residual reversal, g_trade 0.5) solved by Clarabel and by MOSEK
    over 2024-01 -> 2026-08: wall time per solve, solver status, max |w_clarabel - w_mosek|.
(2) MIP variants with MOSEK: cardinality (at most 100 names held) over 2010 -> 2026 (~0.5 s/solve, optimal);
    minimum trade size (each trade either 0 or >= 0.1% of gross) over 2022 -> 2026 only, with a 5 s limit per
    solve (it hits any time limit, 20 s tested, so full history would take ~23 h). The continuous problem is
    reported over the same windows for comparison.
"""
from __future__ import annotations

import time
from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd

import core
from step1_construction import Optimiser, resid_rev

LIC = Path.home() / "mosek" / "mosek.lic"


def licence_ok():
    if not LIC.exists():
        return False
    try:
        x = cp.Variable(1)
        cp.Problem(cp.Minimize(cp.sum_squares(x - 1))).solve(solver=cp.MOSEK)
        return True
    except Exception as e:  # noqa: BLE001
        print("MOSEK licence check failed:", e)
        return False


def inputs(P, k=5):
    R = P["R"]
    sig = resid_rev(P["eps"], k)
    vol = R.rolling(60).std().to_numpy()
    rvar = pd.DataFrame(np.nan_to_num(P["eps"])).rolling(60).var().to_numpy()
    dv = (P["px"] * P["vol"]).rolling(21).mean().to_numpy()
    ffc = P["ff"][["mkt_rf", "smb", "hml", "rmw", "cma"]]
    S = pd.get_dummies(core.sectors(R.columns)).astype(float).to_numpy()
    S = S[:, S.sum(0) >= 3]

    def at(t):
        z = sig[t]
        z = (z - np.nanmean(z)) / (np.nanstd(z) + 1e-12)
        cov = np.cov(ffc.iloc[max(0, t - 251):t + 1].to_numpy().T) + 1e-10 * np.eye(5)
        return dict(alpha=np.nan_to_num(0.01 * vol[t] * np.clip(z, -3, 3)), Bt=np.nan_to_num(P["B"][t]).T,
                    L=np.linalg.cholesky(cov).T, dsq=np.sqrt(np.nan_to_num(rvar[t], nan=1e-4)),
                    ksq=np.sqrt(np.nan_to_num(vol[t] / np.sqrt(np.maximum(dv[t], 1e6)) * 1e3, nan=1.0)))
    return at, S


class MIPOptimiser(Optimiser):
    def __init__(self, N, S, g_trade, max_names=None, min_trade=None, max_time=20.0):
        super().__init__(N, S, g_trade)
        self.max_time = max_time
        cons = list(self.prob.constraints)
        if max_names:
            z = cp.Variable(N, boolean=True)
            cons += [cp.abs(self.w) <= 0.02 * z, cp.sum(z) <= max_names]
        if min_trade:
            # each name either does not trade or trades at least min_trade: buy/sell legs with binaries
            dw = self.w - self.wprev
            b, s = cp.Variable(N, nonneg=True), cp.Variable(N, nonneg=True)
            ub, us = cp.Variable(N, boolean=True), cp.Variable(N, boolean=True)
            cons += [dw == b - s, b <= 0.04 * ub, s <= 0.04 * us, b >= min_trade * ub, s >= min_trade * us,
                     ub + us <= 1]
        self.prob = cp.Problem(self.prob.objective, cons)

    def solve(self, **kw):
        for k, v in kw.items():
            getattr(self, k).value = v
        try:
            self.prob.solve(solver=cp.MOSEK, mosek_params={"MSK_DPAR_MIO_TOL_REL_GAP": 1e-3,
                                                          "MSK_DPAR_MIO_MAX_TIME": self.max_time})
        except cp.error.SolverError:            # time limit hit before any feasible integer solution
            return None
        return self.w.value


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-mintrade", action="store_true", help="rerun only the min-trade MIP (keeps earlier rows)")
    a = ap.parse_args(argv)
    if not licence_ok():
        print(f"No usable MOSEK licence at {LIC}.\n"
              "Get a free 30-day trial (https://www.mosek.com/try/) or academic licence "
              "(https://www.mosek.com/products/academic-licenses/), save it as that file, then rerun:\n"
              "  .venv\\Scripts\\python strategies\\statarb\\mosek_bench.py")
        return
    log = core.Timer()
    P = core.panel()
    R = P["R"]
    N = R.shape[1]
    at, S = inputs(P)
    rows = []
    if a.only_mintrade:
        rows = [r for r in pd.read_csv(core.RES / "mosek_bench.csv").to_dict("records")
                if "min trade" not in str(r.get("strategy"))]
    # (1) continuous: Clarabel vs MOSEK
    days = np.where((R.index >= "2024-01-01") & (R.index < R.index[-1]))[0]
    for name in (() if a.only_mintrade else ("CLARABEL", "MOSEK")):
        opt = Optimiser(N, S, 0.5)
        wprev, W, ts = np.zeros(N), {}, []
        for t in days:
            for k, v in dict(at(t), wprev=wprev).items():
                getattr(opt, k).value = v
            t0 = time.time()
            opt.prob.solve(solver=getattr(cp, name))
            ts.append(time.time() - t0)
            W[t] = wprev = opt.w.value
        rows.append(dict(test="continuous step-1 problem", solver=name, solves=len(days),
                         sec_per_solve=np.mean(ts), status=opt.prob.status))
        if name == "CLARABEL":
            Wc = W
        else:
            rows[-1]["max_abs_weight_diff_vs_clarabel"] = max(np.abs(W[t] - Wc[t]).max() for t in days)
        log(f"{name}: {np.mean(ts):.3f} s/solve")
    # (2) MIP variants with MOSEK
    variants = [("max 100 names", dict(max_names=100), core.START, 20.0),
                ("min trade 0.1%", dict(min_trade=0.001), core.SPLIT, 5.0)]
    for label, kw, start, tmax in (variants[1:] if a.only_mintrade else variants):
        opt = MIPOptimiser(N, S, 0.5, max_time=tmax, **kw)
        Wm = np.zeros(R.shape)
        t0i = R.index.get_indexer([pd.Timestamp(start)], method="bfill")[0]
        wprev, ts, fails = np.zeros(N), [], 0
        for t in range(t0i, len(R) - 1):
            t0 = time.time()
            w = opt.solve(**at(t), wprev=wprev)
            ts.append(time.time() - t0)
            fails += w is None
            Wm[t] = wprev = (w if w is not None else wprev)
            if (t - t0i) % 500 == 0:
                log(f"  MIP {label}: day {t - t0i}")
        bt = core.backtest(Wm, start=start)
        d = core.summarize(bt, f"MOSEK MIP {label}", "s_mosek", kw)
        d.update(sec_per_solve=np.mean(ts), window_start=start, failed_solves=fails)
        rows.append(d)
        core.save(rows, "mosek_bench.csv")
    # continuous baseline (step 1, k=5, g=0.5) over the same windows
    Wc = np.load(core.DATA / "step1_opt_W_k5_g0.5.npy")
    for start in (core.START, core.SPLIT):
        d = core.summarize(core.backtest(Wc, start=start), f"Clarabel continuous (step 1) from {start[:4]}", "s_mosek_ref",
                           {"window": start}, log=False)
        rows.append(d)
    df = core.save(rows, "mosek_bench.csv")
    print(df.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
