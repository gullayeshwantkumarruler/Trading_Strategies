"""Paper 4 — Li (2026), "KellyBoost: Growth-Optimal Portfolio Construction with Gradient-Boosted
Trees", arXiv:2608.23393. Paper says code exists but gives no URL; re-implemented from Sections 3-5.

KellyBoost: one multi-output XGBoost model (multi_output_tree), logits z(x) -> softmax portfolio
over K legs (incl. cash), trained on loss -log(1 + w'y) with the paper's closed-form gradient
g_k = pi_k (S - y_k)/(1+S) and diagonal Hessian |g_k (1 - 2 pi_k) + g_k^2|.
Deployment (Section 3.4/3.6): K_ens = 4 leave-one-row-out members averaged; decisions every 21
trading days anchored at the last decidable row; expanding window of fully realised labels.
Selection (dev segment only, 2003-02..2012-12): purged walk-forward, single-row test blocks every
11 rows, purge h-1 = 19 rows, embargo 60, score = mean realised log growth -> small grid.
Evaluation: 2013-01 .. latest, gross; net at 5 / 10 bp via measured turnover.

Legs (paper): VIGRX, VIVAX, VUSTX, VGTSX, VGENX, GC=F, SI=F, cash (^IRX accrual).
Features (hand-built, ~170 cols, mirrors the paper's 174-col set): for 17 price series
(7 risky legs, S&P 500, copper, 8 SPDR sectors): momentum 21/63/126/252, vol 21/63,
MA ratio 50/200, 252d drawdown, 63d z-score; yields ^IRX/^FVX/^TNX/^TYX level + 21/63d change;
3 curve slopes; VIX level, 21d trend, 1y percentile. The paper's 7,871-column feature search
(60 min on 30 cores) is not reproduced.
Baselines: unconditional Kelly, equal weight, two-stage LightGBM + plug-in Kelly, multiclass
surrogate (LightGBM on argmax leg), all with the same decision grid.
Regional variant (not in the paper): legs SPY, EZU, EWJ, FXI, TLT, GLD, cash.
"""
from __future__ import annotations

import argparse
import time
import warnings

import cvxpy as cp
import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb

from common import ANN, RES_DIR, fetch, plot_equity, save_rows

warnings.filterwarnings("ignore")

H = 20
K_ENS = 4
DEV_END = "2012-12-31"
EVAL_START = "2013-01-01"

PAPER_LEGS = ["VIGRX", "VIVAX", "VUSTX", "VGTSX", "VGENX", "GC=F", "SI=F"]
REGION_LEGS = ["SPY", "EZU", "EWJ", "FXI", "TLT", "GLD"]
EXTRA_PRICE = ["^GSPC", "HG=F", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
YIELDS = ["^IRX", "^FVX", "^TNX", "^TYX"]

# leaf Hessians of the log-growth loss are tiny (~1e-4 per row), so lambda must be small too
GRID = [dict(eta=e, max_depth=d, rounds=r, lam=l, mcw=20)
        for e, d, r, l in [(0.05, 2, 100, 0.05), (0.05, 3, 100, 0.05), (0.05, 3, 100, 1.0), (0.1, 2, 60, 1.0)]]


# ----------------------------------------------------------------------------- data
def load(legs):
    cal = fetch("^GSPC")["Close"].loc["2000":].index
    def c(t):
        s = fetch(t)["Close"]
        return s.reindex(cal.union(s.index)).ffill(limit=5).reindex(cal)   # causal fill (futures/funds)
    px = pd.DataFrame({t: c(t) for t in legs})
    other = pd.DataFrame({t: c(t) for t in EXTRA_PRICE if t not in legs})
    ylds = pd.DataFrame({t: c(t) for t in YIELDS})
    vix = c("^VIX")
    return cal, px, other, ylds, vix


def features(px, other, ylds, vix):
    P = pd.concat([px, other], axis=1)
    r = P.pct_change(fill_method=None)
    f = {}
    for h in [21, 63, 126, 252]:
        f[f"mom{h}"] = P.pct_change(h, fill_method=None)
    for h in [21, 63]:
        f[f"vol{h}"] = r.rolling(h).std() * np.sqrt(ANN)
    f["ma50_200"] = P.rolling(50).mean() / P.rolling(200).mean() - 1
    f["dd252"] = P / P.rolling(252).max() - 1
    f["z63"] = (P - P.rolling(63).mean()) / P.rolling(63).std()
    F = pd.concat(f, axis=1)
    F.columns = [f"{a}__{b}" for a, b in F.columns]
    Y = pd.DataFrame(index=P.index)
    for t in YIELDS:
        Y[f"{t}_lvl"] = ylds[t]
        Y[f"{t}_d21"] = ylds[t].diff(21)
        Y[f"{t}_d63"] = ylds[t].diff(63)
    Y["slope_10y_3m"] = ylds["^TNX"] - ylds["^IRX"]
    Y["slope_30y_5y"] = ylds["^TYX"] - ylds["^FVX"]
    Y["slope_10y_5y"] = ylds["^TNX"] - ylds["^FVX"]
    Y["vix_lvl"] = vix
    Y["vix_trend21"] = vix - vix.rolling(21).mean()
    Y["vix_pct1y"] = vix.rolling(252).rank(pct=True)
    return pd.concat([F, Y], axis=1)


def labels(px, ylds):
    fwd = px.shift(-H) / px - 1
    cash = (ylds["^IRX"] / 100) * H / ANN                 # known at decision time
    fwd["CASH"] = cash
    return fwd


# ----------------------------------------------------------------------------- KellyBoost
def make_obj(Y):
    def obj(predt, dtrain):
        z = predt.reshape(Y.shape)
        z = z - z.max(axis=1, keepdims=True)
        p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
        S = (p * Y).sum(axis=1, keepdims=True)
        g = p * (S - Y) / (1 + S)
        h = np.abs(g * (1 - 2 * p) + g ** 2) + 1e-6
        return g, h
    return obj


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def fit_kb(X, Y, hp, seed=0):
    dtr = xgb.DMatrix(X, label=Y)
    params = dict(tree_method="hist", multi_strategy="multi_output_tree", num_target=Y.shape[1],
                  eta=hp["eta"], max_depth=hp["max_depth"], reg_lambda=hp["lam"],
                  min_child_weight=hp["mcw"] * 1e-3, base_score=0.0, seed=seed, nthread=4)
    return xgb.train(params, dtr, num_boost_round=hp["rounds"], obj=make_obj(Y))


def kb_weights(Xtr, Ytr, xq, hp, ens=K_ENS):
    """Leave-one-row-out ensemble (member s drops one deterministic row), average simplex weights."""
    ws = []
    n = len(Xtr)
    for s in range(ens):
        drop = np.random.default_rng(s).integers(0, n)
        keep = np.ones(n, bool); keep[drop] = False
        b = fit_kb(Xtr[keep], Ytr[keep], hp, seed=s)
        ws.append(softmax(b.predict(xgb.DMatrix(xq)).reshape(len(xq), -1)))
    return np.mean(ws, axis=0)


# ----------------------------------------------------------------------------- baselines
def uncond_kelly(Ytr):
    K = Ytr.shape[1]
    w = cp.Variable(K)
    prob = cp.Problem(cp.Maximize(cp.sum(cp.log(1 + Ytr @ w))), [w >= 0, cp.sum(w) == 1])
    for solver in (cp.CLARABEL, cp.SCS):                 # Clarabel occasionally fails numerically
        try:
            prob.solve(solver=solver)
            if w.value is not None:
                return np.clip(w.value, 0, 1) / np.clip(w.value, 0, 1).sum()
        except cp.error.SolverError:
            continue
    return None                                          # caller keeps the previous weights


def two_stage(Xtr, Ytr, xq, cov_win=252):
    K = Ytr.shape[1]
    mu = np.zeros(K)
    for k in range(K - 1):                               # cash leg forecast = its known yield
        m = lgb.LGBMRegressor(n_estimators=150, learning_rate=0.03, num_leaves=7, min_child_samples=50,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.5, verbose=-1)
        m.fit(Xtr, Ytr[:, k])
        mu[k] = m.predict(xq)[0]
    mu[-1] = Ytr[-1, -1]
    Sig = np.cov(Ytr[-cov_win:].T) + 1e-8 * np.eye(K)
    w = cp.Variable(K)
    cp.Problem(cp.Maximize(mu @ w - 0.5 * cp.quad_form(w, cp.psd_wrap(Sig))), [w >= 0, cp.sum(w) == 1]).solve()
    return np.clip(w.value, 0, 1) / np.clip(w.value, 0, 1).sum()


def multiclass(Xtr, Ytr, xq):
    yb = Ytr.argmax(axis=1)
    m = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, num_leaves=7, min_child_samples=50,
                           subsample=0.8, subsample_freq=1, colsample_bytree=0.5, verbose=-1)
    m.fit(Xtr, yb)
    p = np.zeros(Ytr.shape[1])
    p[m.classes_] = m.predict_proba(xq)[0]
    return p


# ----------------------------------------------------------------------------- selection (dev only)
def select_hp(X, Y, dates):
    dev = np.where(dates <= pd.Timestamp(DEV_END))[0]
    tests = dev[300::11]                                  # single-row test blocks every 11 rows
    scores = []
    t0 = time.time()
    for gi, hp in enumerate(GRID):
        lg = []
        for ti, t in enumerate(tests):
            if ti % 25 == 0:
                print(f"  dev grid {gi+1}/{len(GRID)} test {ti}/{len(tests)}  elapsed {(time.time()-t0)/60:.1f} min", flush=True)
            tr = np.r_[0:max(0, t - (H - 1)), min(len(dev), t + 61):len(dev)]   # purge h-1, embargo 60
            tr = tr[tr < len(dev)]
            b = fit_kb(X[dev][tr], Y[dev][tr], hp)
            w = softmax(b.predict(xgb.DMatrix(X[t:t + 1])).reshape(1, -1))[0]
            lg.append(np.log1p(w @ Y[t]))
        scores.append(np.mean(lg))
        print("  dev score", hp, round(scores[-1] * 100, 3))
    return GRID[int(np.argmax(scores))], scores


# ----------------------------------------------------------------------------- deployment
def deploy(legs, region, refresh_hp=None):
    cal, px, other, ylds, vix = load(legs)
    F = features(px, other, ylds, vix)
    L = labels(px, ylds)
    ok = F.notna().all(axis=1) & px.notna().all(axis=1)
    F, L, pxo = F[ok], L[ok], px[ok]
    dates = F.index
    X = F.to_numpy(np.float32)
    Yall = L.to_numpy()
    cols = list(L.columns)
    print(f"[{region}] panel {X.shape}, {dates[0].date()}..{dates[-1].date()}")
    hp = refresh_hp or select_hp(X[:-H], Yall[:-H], dates[:-H])[0]
    print(f"[{region}] selected", hp)

    # decision grid anchored at the last decidable row, every 21 rows, inside the eval segment
    last = len(dates) - 1
    grid = [i for i in range(last, 0, -21) if dates[i] >= pd.Timestamp(EVAL_START)][::-1]
    t_dep = time.time()
    methods = ["KellyBoost", "Two-stage LGBM + Kelly", "Multiclass surrogate", "Unconditional Kelly", "Equal weight"]
    Wd = {m: {} for m in methods}
    for j, i in enumerate(grid):
        realised = np.where(np.arange(len(dates)) + H <= i)[0]         # labels fully realised by row i
        Xtr, Ytr = X[realised], Yall[realised]
        xq = X[i:i + 1]
        Wd["KellyBoost"][dates[i]] = kb_weights(Xtr, Ytr, xq, hp)[0]
        Wd["Two-stage LGBM + Kelly"][dates[i]] = two_stage(Xtr, Ytr, xq)
        Wd["Multiclass surrogate"][dates[i]] = multiclass(Xtr, Ytr, xq)
        uk = uncond_kelly(Ytr)
        if uk is None:
            print(f"  [{region}] unconditional Kelly solver failed at {dates[i].date()}; keeping previous weights", flush=True)
            prev = list(Wd["Unconditional Kelly"].values())
            uk = prev[-1] if prev else np.full(len(cols), 1 / len(cols))
        Wd["Unconditional Kelly"][dates[i]] = uk
        Wd["Equal weight"][dates[i]] = np.full(len(cols), 1 / len(cols))
        if j % 5 == 0:
            print(f"  [{region}] decision {j+1}/{len(grid)} {dates[i].date()} elapsed {(time.time()-t_dep)/60:.1f} min KB w=",
                  dict(zip(cols, np.round(Wd['KellyBoost'][dates[i]], 2))))

    for m in methods:
        pd.DataFrame(Wd[m], index=cols).T.to_csv(RES_DIR / f"p4_{region.lower().replace(' ', '_')}_{m.split()[0].lower()}_weights.csv",
                                                 float_format="%.4f")
    return evaluate(legs, region, {m: pd.DataFrame(Wd[m], index=cols).T for m in methods}, hp)


METHODS = ["KellyBoost", "Two-stage LGBM + Kelly", "Multiclass surrogate", "Unconditional Kelly", "Equal weight"]


def weights_file(region, m):
    return RES_DIR / f"p4_{region.lower().replace(' ', '_')}_{m.split()[0].lower()}_weights.csv"


def evaluate(legs, region, W_by_method, hp=None):
    """Daily drifted equity from decision-date weights; gross and net of 5/10 bp."""
    cal, px, other, ylds, vix = load(legs)
    pxo = px.dropna()
    dates = pxo.index
    cols = list(next(iter(W_by_method.values())).columns)
    methods = list(W_by_method)
    # daily equity with drift between decisions; decided at close i, held from i+1
    dr = pxo.pct_change(fill_method=None).fillna(0.0)
    dr["CASH"] = (ylds["^IRX"].reindex(dates).ffill() / 100 / ANN).shift(1).fillna(0.0)
    rows, curves = [], {}
    for m in methods:
        Wt = W_by_method[m]
        ret, to = drift_sim(Wt, dr.loc[Wt.index[0]:])
        for c_bps in (0, 5, 10):
            net = ret - to * c_bps / 1e4
            rows.append(dict(region=region, method=m, cost_bps=c_bps, **summ(net, dr["CASH"]),
                             log_growth_20d_x100=np.log1p(net).mean() * H * 100,
                             turnover_ann=to.sum() / (len(to) / ANN), hp=str(hp) if m == "KellyBoost" else ""))
        curves[m] = ret
    return rows, curves, hp


def drift_sim(Wt, dr):
    idx = dr.index
    dec = set(Wt.index)
    w = np.zeros(dr.shape[1])
    R = dr.to_numpy()
    out, tos = np.zeros(len(idx)), np.zeros(len(idx))
    pending = None
    for i, t in enumerate(idx):
        if pending is not None:                              # execute at today's open≈yesterday's close
            tos[i] = np.abs(pending - w).sum() / 2; w = pending; pending = None
        g = float(w @ R[i])
        out[i] = g
        w = w * (1 + R[i]) / (1 + g)
        if t in dec:
            pending = Wt.loc[t].to_numpy()
    return pd.Series(out, idx).iloc[1:], pd.Series(tos, idx).iloc[1:]


def summ(r, rf):
    from common import ann_stats
    s = ann_stats(r, rf.reindex(r.index).fillna(0.0))
    return {k: s[k] for k in ("CAGR", "Vol", "Sharpe", "MaxDD")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-only", action="store_true")
    ap.add_argument("--regional-only", action="store_true")
    ap.add_argument("--paper-from-weights", action="store_true",
                    help="rebuild the paper-legs metrics from saved weight CSVs instead of re-deploying")
    a = ap.parse_args(argv)
    all_rows = []
    if a.paper_from_weights:
        W = {m: pd.read_csv(weights_file("Paper legs (US)", m) if weights_file("Paper legs (US)", m).exists()
                            else RES_DIR / f"p4_paper legs (us)_{m.split()[0].lower()}_weights.csv",
                            index_col=0, parse_dates=True) for m in METHODS}
        rows, curves, _ = evaluate(PAPER_LEGS, "Paper legs (US)", W)
    elif not a.regional_only:
        rows, curves, hp = deploy(PAPER_LEGS, "Paper legs (US)")
    if not a.regional_only:
        all_rows += rows
        save_rows(all_rows, "p4_metrics_paper_legs.csv")
    if not a.regional_only:
        plot_equity(curves, "Paper 4: KellyBoost vs baselines (paper's 8 legs, 2013-2026, gross)", "p4_paper_legs.png")
        print(pd.DataFrame(rows).query("cost_bps == 0")[["method", "CAGR", "Vol", "Sharpe", "MaxDD", "log_growth_20d_x100", "turnover_ann"]].to_string(index=False))
    if not a.paper_only and not a.paper_from_weights:
        rows, curves, _ = deploy(REGION_LEGS, "Regional ETFs")
        all_rows += rows
        save_rows(rows, "p4_metrics_regional.csv")
        plot_equity(curves, "Paper 4: KellyBoost on US/Europe/Japan/China ETFs + TLT/GLD/cash", "p4_regional.png")
        print(pd.DataFrame(rows).query("cost_bps == 0")[["method", "CAGR", "Vol", "Sharpe", "MaxDD", "turnover_ann"]].to_string(index=False))
    parts = [RES_DIR / "p4_metrics_paper_legs.csv", RES_DIR / "p4_metrics_regional.csv"]
    pd.concat([pd.read_csv(f) for f in parts if f.exists()]).to_csv(RES_DIR / "p4_metrics.csv", index=False,
                                                                     float_format="%.4f")


if __name__ == "__main__":
    main()
