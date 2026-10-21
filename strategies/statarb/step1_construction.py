"""Step 1 — cost-aware construction around the residual-reversal signal (report priority 1).

Signals (FF5 residuals from paper 8): resid_rev_k = -(sum of last k daily residuals), k = 1, 5, 10.
Aim book = dollar-neutral, unit-gross, FF5-neutral weights from the signal.

(a) Garleanu-Pedersen partial trading   w_t = (1 - tau) w_{t-1} + tau * aim_t
(b) No-trade bands                      trade name i only if |aim_i - w_i| > band / N
(c) Holding periods / smoothed aims     rebalance every H days; or aim = mean of last H aims
(d) Convex optimiser (CVXPY + Clarabel, "Markowitz++"-style, Boyd et al. 2024):
      max  alpha'w - lam * (||L f||^2 + sum d_i w_i^2) - g_trade * (c ||w - w_prev||_1 + sum k_i (w_i - w_prev,i)^2)
      s.t. f = B'w (FF5 exposures), |f_mkt| <= 0.02, |f_other| <= 0.10, 1'w = 0, sector-neutral,
           ||w||_1 <= 1, |w_i| <= 0.02
    alpha_i = IC * sigma_i * z_i (Grinold), IC = 0.01; L = chol(252-day FF5 covariance);
    d_i = 60-day residual variance; k_i = impact ~ sigma_i / sqrt(dollar volume) (scaled).
    g_trade swept over {0.05, 0.1, 0.2, 0.5, 1, 2}: with a daily alpha of ~1-2 bp a full 5 bp trade cost
    (g = 1) is rarely worth paying in one day, so g < 1 amortises the cost over an expected holding period
    of ~1/g days (g = 5 left the book empty in a test). Problem compiled once with cvxpy Parameters.

Backtests: 5 bp per unit turnover + 1 bp/day on shorts, 2010-01 -> 2026-08, 2022-2026 reported separately.
"""
from __future__ import annotations

import argparse

import cvxpy as cp
import numpy as np
import pandas as pd

import core

SIGNAL_K = [1, 5, 10]


def resid_rev(eps, k):
    cs = np.cumsum(np.nan_to_num(eps), 0)
    prev = np.vstack([np.zeros((k, eps.shape[1])), cs[:-k]])
    return -(cs - prev)


def aims(P):
    out = {}
    for k in SIGNAL_K:
        out[k] = core.factor_neutral(core.to_book(resid_rev(P["eps"], k)), P["B"])
    return out


# ----------------------------------------------------------------------------- (a)-(c)
def partial(aim, tau):
    W = np.zeros_like(aim)
    for t in range(1, len(aim)):
        W[t] = (1 - tau) * W[t - 1] + tau * aim[t]
    return W


def band(aim, b):
    N = aim.shape[1]
    W = np.zeros_like(aim)
    thr = b / N
    for t in range(1, len(aim)):
        w = W[t - 1].copy()
        move = np.abs(aim[t] - w) > thr
        w[move] = aim[t][move]
        w -= w.mean()                                     # keep dollar neutral
        g = np.abs(w).sum()
        W[t] = w / g if g > 1 else w
    return W


def hold(aim, H):
    W = np.zeros_like(aim)
    for t in range(len(aim)):
        W[t] = aim[t] if t % H == 0 else W[t - 1]
    return W


def smooth(aim, H):
    W = pd.DataFrame(aim).rolling(H, min_periods=1).mean().to_numpy()
    g = np.abs(W).sum(axis=1, keepdims=True)
    return np.divide(W, g, out=np.zeros_like(W), where=g > 0)


def run_simple(P, A):
    rows = []
    for k, aim in A.items():
        rows.append(core.summarize(core.backtest(aim), f"k{k} daily full rebalance", "s1_simple", {"k": k}))
        for tau in (0.5, 0.25, 0.1, 0.05):
            rows.append(core.summarize(core.backtest(partial(aim, tau)), f"k{k} partial tau={tau}", "s1_simple",
                                       {"k": k, "tau": tau}))
        for b in (0.5, 1.0, 2.0):
            rows.append(core.summarize(core.backtest(band(aim, b)), f"k{k} band {b}/N", "s1_simple", {"k": k, "band": b}))
        for H in (5, 20):
            rows.append(core.summarize(core.backtest(hold(aim, H)), f"k{k} hold {H}d", "s1_simple", {"k": k, "hold": H}))
            rows.append(core.summarize(core.backtest(smooth(aim, H)), f"k{k} smoothed aim {H}d", "s1_simple",
                                       {"k": k, "smooth": H}))
    return rows


# ----------------------------------------------------------------------------- (d) optimiser
class Optimiser:
    def __init__(self, N, sector_dummies, g_trade, lam=5.0, c=core.COST):
        self.w = cp.Variable(N)
        self.f = cp.Variable(5)
        self.alpha = cp.Parameter(N)
        self.wprev = cp.Parameter(N)
        self.Bt = cp.Parameter((5, N))
        self.L = cp.Parameter((5, 5))
        self.dsq = cp.Parameter(N, nonneg=True)
        self.ksq = cp.Parameter(N, nonneg=True)
        dw = self.w - self.wprev
        risk = cp.sum_squares(self.L @ self.f) + cp.sum_squares(cp.multiply(self.dsq, self.w))
        tcost = c * cp.norm1(dw) + cp.sum_squares(cp.multiply(self.ksq, dw))
        cons = [self.f == self.Bt @ self.w, cp.abs(self.f[0]) <= 0.02, cp.abs(self.f[1:]) <= 0.10,
                cp.sum(self.w) == 0, cp.norm1(self.w) <= 1, cp.abs(self.w) <= 0.02,
                sector_dummies.T @ self.w == 0]
        self.prob = cp.Problem(cp.Maximize(self.alpha @ self.w - lam * risk - g_trade * tcost), cons)

    def solve(self, **kw):
        for k, v in kw.items():
            getattr(self, k).value = v
        try:
            self.prob.solve(solver=cp.CLARABEL, warm_start=True)
        except cp.error.SolverError:
            self.prob.solve(solver=cp.SCS, warm_start=True)
        return self.w.value


def run_optimiser(P, k, g_trade, solver_name="CLARABEL", log=core.Timer()):
    R, eps, B = P["R"], np.nan_to_num(P["eps"]), P["B"]
    T, N = R.shape
    sig = resid_rev(P["eps"], k)
    vol = R.rolling(60).std().to_numpy()
    rvar = pd.DataFrame(eps).rolling(60).var().to_numpy()
    dv = (P["px"] * P["vol"]).rolling(21).mean().to_numpy()
    ffc = P["ff"][["mkt_rf", "smb", "hml", "rmw", "cma"]]
    sec = core.sectors(R.columns)
    S = pd.get_dummies(sec).astype(float).to_numpy()
    S = S[:, S.sum(0) >= 3]                               # skip tiny sectors
    opt = Optimiser(N, S, g_trade)
    W = np.zeros((T, N))
    t0 = R.index.get_indexer([pd.Timestamp(core.START)], method="bfill")[0] - 1
    wprev = np.zeros(N)
    fails = 0
    for t in range(t0, T - 1):
        z = sig[t]
        z = (z - np.nanmean(z)) / (np.nanstd(z) + 1e-12)
        alpha = np.nan_to_num(0.01 * vol[t] * np.clip(z, -3, 3))
        cov = np.cov(ffc.iloc[max(0, t - 251):t + 1].to_numpy().T) + 1e-10 * np.eye(5)
        imp = np.nan_to_num(vol[t] / np.sqrt(np.maximum(dv[t], 1e6)) * 1e3, nan=1.0)
        w = opt.solve(alpha=alpha, wprev=wprev, Bt=np.nan_to_num(B[t]).T, L=np.linalg.cholesky(cov).T,
                      dsq=np.sqrt(np.nan_to_num(rvar[t], nan=1e-4)), ksq=np.sqrt(imp))
        if w is None:
            fails += 1
            w = wprev
        W[t] = w
        wprev = w
        if (t - t0) % 500 == 0:
            log(f"  optimiser k={k} g_trade={g_trade}: day {t - t0}/{T - 1 - t0} {R.index[t].date()}")
    return W, fails


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-opt", action="store_true")
    ap.add_argument("--opt-k", type=int, nargs="*", default=[1, 5])
    ap.add_argument("--gammas", type=float, nargs="*", default=[0.05, 0.1, 0.2, 0.5, 1, 2])
    a = ap.parse_args(argv)
    log = core.Timer()
    P = core.panel()
    A = aims(P)
    log("aims ready; running (a)-(c)")
    rows = run_simple(P, A)
    df = core.save(rows, "step1_simple.csv")
    core.show(df)
    if a.skip_opt:
        return
    orows, curves = [], {}
    for k in a.opt_k:
        for g in a.gammas:
            W, fails = run_optimiser(P, k, g, log=log)
            np.save(core.DATA / f"step1_opt_W_k{k}_g{g}.npy", W.astype(np.float32))
            bt = core.backtest(W)
            d = core.summarize(bt, f"k{k} optimiser g_trade={g}", "s1_opt", {"k": k, "g_trade": g, "fails": fails})
            orows.append(d)
            curves[f"k{k} g={g}"] = bt["net"]
            log(f"k={k} g_trade={g}: SR net {d['SR_net']:.2f} gross {d['SR_gross']:.2f} TO {d['turnover_daily']:.3f} "
                f"2022-26 {d['SR_net_2022_26']:.2f} (fails {fails})")
            core.save(orows, "step1_optimiser.csv")
    core.show(pd.DataFrame(orows))
    core.plot(curves, "Step 1: optimiser on residual reversal, net of 5bp + 1bp/day shorts", "step1_optimiser.png")


if __name__ == "__main__":
    main()
