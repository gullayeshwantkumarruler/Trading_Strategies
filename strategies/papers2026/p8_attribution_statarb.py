"""Paper 8 — Liang, Zohren & Cucuringu (2026), "From Economic Explanation to Performance
Improvement in Machine-Learning Portfolios", arXiv:2610.15144. No code released.

Pipeline (Sections 2-3):
  1. Arbitrage portfolios: excess returns R; FF5 loadings beta from 60-day rolling regressions;
     tradable residuals eps_t = Phi_{t-1} R_t, Phi = I - beta (beta'beta)^-1 beta'   (eqs. 2-4)
  2. 18 signals per stock from the last L = 30 residuals (Table 1): OU fit on cumulative
     residuals (kappa, mu, sigma_OU, cum_res, R2, s-score), regime features (entropy, expected
     duration, max transition prob), residual moments, predicted residual, entropy x |pred|,
     liquidity; cross-sectionally standardised
  3. Allocation g(z) -> residual weights; stock weights w^R = Phi w / ||Phi w||_1; trained to
     maximise the NET Sharpe ratio at c = 5 bp per unit turnover; XGB (shallow trees, custom
     objective) and FFN (32-16-8-4, ReLU)
  4. Rolling: 4y train + 1y validation (hyperparameters), re-estimated every year, trade next year
  5. Attribution: local first-order sensitivity of validation net Sharpe to feature-exposure
     multipliers theta (theta = 1 baseline), by central differences
  6. Intervention (eqs. 42-45): magnitude transform, f = 1 + eta*tanh(T / sd_j T_j), eta = 0.5,
     theta in [0, 3]; unstabilised / stabilised (theta_y = theta_{y-1} f) x model-specific /
     cross-model (average of XGB and FFN multipliers)

Simplifications (documented in the write-up):
  * universe: 350 current S&P 500 large caps with full history (paper: 346 stocks, 2000-2024);
    sample 2004 -> Aug 2026 (Ken French data end), OOS 2010 -> 2026-08
  * HDP-HMM regime-switching OU -> one OU fit per window + a 2-state Gaussian HMM on residuals
    (fitted per stock on each training window, forward-filtered causally) for the regime features
  * market cap / share turnover need shares outstanding (not free): replaced by log 30-day
    dollar volume and volume / 252-day average volume
  * XGB with a non-additive Sharpe objective: gradient from autograd of -SR_net w.r.t. the
    predictions, RMS-normalised, unit Hessian (first-order boosting)
"""
from __future__ import annotations

import argparse
import json
import time
import warnings

import numpy as np
import pandas as pd
import torch
import xgboost as xgb
from hmmlearn.hmm import GaussianHMM
from numpy.lib.stride_tricks import sliding_window_view

from common import ANN, DATA_DIR, RES_DIR, french_factors, plot_equity, save_rows, sp500_universe, stock_panel

warnings.filterwarnings("ignore")
torch.set_num_threads(4)

L = 30
BETA_WIN = 60
C = 0.0005
ETA = 0.5
TH_MIN, TH_MAX = 0.0, 3.0
FIRST_TRADE_YEAR = 2010
FEATS = ["kappa", "mu", "sigma_ou", "cum_res", "R2", "prob_signal", "regime_entropy", "regime_duration",
         "regime_trans_prob", "pre_res", "pred_res", "res_std", "res_skew", "res_kurt", "entropy_pred_res",
         "avg_daily_vol", "log_dollar_vol", "turnover"]


# ----------------------------------------------------------------------------- 1. residuals
def load_panel():
    u = sp500_universe(350)
    px, vol = stock_panel(u)
    ff = french_factors()
    px, vol = px.loc["2004-01-01":ff.index[-1]], vol.loc["2004-01-01":ff.index[-1]]
    full = px.notna().all() & (vol > 0).mean().gt(0.99)
    px, vol = px.loc[:, full], vol.loc[:, full]
    r = px.pct_change(fill_method=None).iloc[1:]
    ffa = ff.reindex(r.index).ffill()
    R = r.sub(ffa["rf"], axis=0)
    return R, px.iloc[1:], vol.iloc[1:], ffa


def rolling_betas(R: pd.DataFrame, F: pd.DataFrame, W=BETA_WIN):
    """beta_t (T x N x 5) from a W-day OLS with intercept using data <= t."""
    Fa, Ra = F.to_numpy(), R.to_numpy()
    T, N = Ra.shape
    K = Fa.shape[1]
    cF = np.vstack([np.zeros(K), np.cumsum(Fa, 0)])
    cFF = np.concatenate([np.zeros((1, K, K)), np.cumsum(Fa[:, :, None] * Fa[:, None, :], 0)])
    cR = np.vstack([np.zeros(N), np.cumsum(Ra, 0)])
    cFR = np.concatenate([np.zeros((1, K, N)), np.cumsum(Fa[:, :, None] * Ra[:, None, :], 0)])
    B = np.full((T, N, K), np.nan)
    for t in range(W - 1, T):
        sF = cF[t + 1] - cF[t + 1 - W]
        sFF = cFF[t + 1] - cFF[t + 1 - W]
        sR = cR[t + 1] - cR[t + 1 - W]
        sFR = cFR[t + 1] - cFR[t + 1 - W]
        covFF = sFF / W - np.outer(sF, sF) / W ** 2
        covFR = sFR / W - np.outer(sF, sR) / W ** 2
        B[t] = np.linalg.solve(covFF + 1e-12 * np.eye(K), covFR).T
    return B


def residuals(R: pd.DataFrame, B: np.ndarray):
    """eps_t = R_t - beta_{t-1} (beta'beta)^-1 beta' R_t ; also P_{t-1} = (beta'beta)^-1 beta'."""
    Ra = R.to_numpy()
    T, N = Ra.shape
    eps = np.full((T, N), np.nan)
    P = np.full((T, B.shape[2], N), np.nan)
    for t in range(1, T):
        b = B[t - 1]
        if np.isnan(b).any():
            continue
        Pt = np.linalg.solve(b.T @ b, b.T)
        P[t] = Pt
        eps[t] = Ra[t] - b @ (Pt @ Ra[t])
    return eps, P


# ----------------------------------------------------------------------------- 2. signals
def ou_features(eps: np.ndarray):
    """OU / AR(1) on the cumulative residual over the last L days, for every (t, n)."""
    T, N = eps.shape
    out = {k: np.full((T, N), np.nan) for k in ["kappa", "mu", "sigma_ou", "cum_res", "R2", "prob_signal",
                                                 "pre_res", "pred_res", "res_std", "res_skew", "res_kurt"]}
    e = np.nan_to_num(eps).astype(np.float32)
    win = sliding_window_view(e, L, axis=0)            # (T-L+1, N, L): rows t-L+1..t
    X = np.cumsum(win, axis=2)
    x0, x1 = X[:, :, :-1], X[:, :, 1:]
    mx0, mx1 = x0.mean(2, keepdims=True), x1.mean(2, keepdims=True)
    sxx = ((x0 - mx0) ** 2).sum(2)
    b = ((x0 - mx0) * (x1 - mx1)).sum(2) / np.maximum(sxx, 1e-18)
    a = mx1[..., 0] - b * mx0[..., 0]
    res = x1 - (a[..., None] + b[..., None] * x0)
    ve = res.var(2)
    vy = x1.var(2)
    bc = np.clip(b, 1e-4, 0.9999)
    kappa = -np.log(bc) * ANN
    mu = a / (1 - bc)
    s_eq = np.sqrt(ve / (1 - bc ** 2))
    XL = X[:, :, -1]
    sl = slice(L - 1, T)
    out["kappa"][sl] = kappa
    out["mu"][sl] = mu
    out["sigma_ou"][sl] = np.sqrt(ve * 2 * kappa / ANN / (1 - bc ** 2))
    out["cum_res"][sl] = XL
    out["R2"][sl] = 1 - ve / np.maximum(vy, 1e-18)
    out["prob_signal"][sl] = (XL - mu) / np.maximum(s_eq, 1e-12)
    out["pre_res"][sl] = win[:, :, -1]
    out["pred_res"][sl] = a + (b - 1) * XL                    # E[X_{L+1} - X_L]
    m, s = win.mean(2), win.std(2)
    z = (win - m[..., None]) / np.maximum(s[..., None], 1e-12)
    out["res_std"][sl] = s
    out["res_skew"][sl] = (z ** 3).mean(2)
    out["res_kurt"][sl] = (z ** 4).mean(2) - 3
    for k in out:
        out[k][np.isnan(eps)] = np.nan
    return out


def regime_features(eps: np.ndarray, fit_rows: np.ndarray, filt_rows: np.ndarray):
    """2-state Gaussian HMM per stock fitted on fit_rows; causal forward filter over filt_rows.
    Returns entropy (normalised), expected duration of the most likely state, max transition prob."""
    T, N = eps.shape
    ent, dur, tp = (np.full((len(filt_rows), N), np.nan) for _ in range(3))
    for n in range(N):
        x = eps[fit_rows, n]
        x = x[~np.isnan(x)].reshape(-1, 1)
        try:
            m = GaussianHMM(2, covariance_type="diag", n_iter=30, random_state=0, min_covar=1e-8).fit(x * 100)
        except Exception:  # noqa: BLE001
            continue
        A = m.transmat_
        mu, sd = m.means_[:, 0] / 100, np.sqrt(m.covars_[:, 0, 0]) / 100
        y = np.nan_to_num(eps[filt_rows, n])
        lik = np.exp(-0.5 * ((y[:, None] - mu) / sd) ** 2) / sd + 1e-300
        p = m.startprob_.copy()
        P = np.zeros((len(y), 2))
        for i in range(len(y)):
            p = (p @ A) * lik[i]
            p /= p.sum()
            P[i] = p
        H = -(P * np.log(P + 1e-12)).sum(1) / np.log(2)
        s = P.argmax(1)
        ent[:, n] = H
        dur[:, n] = 1 / np.maximum(1 - A[s, s], 1e-3)
        tp[:, n] = A[s].max(1)
    return ent, dur, tp


def liquidity(px: pd.DataFrame, vol: pd.DataFrame):
    dv = (px * vol)
    return dict(avg_daily_vol=np.log(vol.rolling(L).mean()).to_numpy(),
                log_dollar_vol=np.log(dv.rolling(L).mean()).to_numpy(),
                turnover=(vol / vol.rolling(252, min_periods=60).mean()).to_numpy())


def zscore_cs(a):
    m = np.nanmean(a, axis=1, keepdims=True)
    s = np.nanstd(a, axis=1, keepdims=True)
    z = (a - m) / np.where(s > 0, s, 1)
    return np.clip(np.nan_to_num(z), -5, 5)


# ----------------------------------------------------------------------------- 3. portfolio maths
class Block:
    """Tensors for a contiguous set of decision days d (signals at close d, earn eps_{d+1})."""

    def __init__(self, rows, Z, eps, B, P):
        self.rows = rows
        self.Z = torch.tensor(Z[rows], dtype=torch.float32)                 # D x N x 18
        self.eps = torch.tensor(np.nan_to_num(eps[rows + 1]), dtype=torch.float32)
        self.B = torch.tensor(np.nan_to_num(B[rows]), dtype=torch.float32)  # beta_d (used for eps_{d+1})
        self.P = torch.tensor(np.nan_to_num(P[rows + 1]), dtype=torch.float32)

    def returns(self, W, c=C):
        """W: D x N residual weights -> net and gross daily returns, turnover."""
        Pw = torch.einsum("dkn,dn->dk", self.P, W)
        wR = W - torch.einsum("dnk,dk->dn", self.B, Pw)                     # Phi w
        nrm = wR.abs().sum(1, keepdim=True).clamp_min(1e-8)
        wRn = wR / nrm
        gross = (W * self.eps).sum(1) / nrm[:, 0]                          # w' Phi R = w' eps
        to = torch.cat([wRn[:1].abs().sum(1), (wRn[1:] - wRn[:-1]).abs().sum(1)])
        return gross - c * to, gross, to


def sharpe(r):
    return r.mean() / (r.std() + 1e-12) * np.sqrt(ANN)


# ----------------------------------------------------------------------------- 4. models
class FFN(torch.nn.Module):
    def __init__(self, p=18, drop=0.0):
        super().__init__()
        dims, layers = [p, 32, 16, 8, 4], []
        for a, b in zip(dims[:-1], dims[1:]):
            layers += [torch.nn.Linear(a, b), torch.nn.ReLU(), torch.nn.Dropout(drop)]
        self.net = torch.nn.Sequential(*layers, torch.nn.Linear(4, 1))

    def forward(self, z):
        return self.net(z).squeeze(-1)


def train_ffn(tr: Block, lr, drop, epochs, seed=0):
    torch.manual_seed(seed)
    m = FFN(drop=drop)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        m.train(); opt.zero_grad()
        net, _, _ = tr.returns(m(tr.Z))
        loss = -sharpe(net)
        loss.backward(); opt.step()
    m.eval()
    return lambda Z: m(Z).detach()


def train_xgb(tr: Block, depth, rounds, eta=0.1, seed=0):
    D, N, p = tr.Z.shape
    X = tr.Z.reshape(-1, p).numpy()
    dtr = xgb.DMatrix(X)

    def obj(pred, _):
        W = torch.tensor(pred.reshape(D, N), dtype=torch.float32, requires_grad=True)
        net, _, _ = tr.returns(W)
        (-sharpe(net)).backward()
        g = W.grad.numpy().reshape(-1).astype(np.float64)
        g = g / (np.sqrt((g ** 2).mean()) + 1e-18)
        return g, np.ones_like(g)

    bst = xgb.train(dict(tree_method="hist", max_depth=depth, eta=eta, min_child_weight=200,
                         reg_lambda=1.0, base_score=0.0, seed=seed, nthread=4),
                    dtr, num_boost_round=rounds, obj=obj)

    def f(Z, k=rounds):
        Dz, Nz, _ = Z.shape
        return torch.tensor(bst.predict(xgb.DMatrix(Z.reshape(-1, p).numpy()), iteration_range=(0, k))
                            .reshape(Dz, Nz), dtype=torch.float32)
    return f


def eval_block(f, blk: Block, theta=None):
    Z = blk.Z if theta is None else blk.Z * torch.tensor(theta, dtype=torch.float32)
    with torch.no_grad():
        return blk.returns(f(Z))


def attribution(f, blk: Block, h=0.05):
    """d SR_net / d theta_i at theta = 1 (central differences), plus turnover / gross SR."""
    p = blk.Z.shape[2]
    g = np.zeros(p)
    for i in range(p):
        up, dn = np.ones(p), np.ones(p)
        up[i] += h; dn[i] -= h
        g[i] = (float(sharpe(eval_block(f, blk, up)[0])) - float(sharpe(eval_block(f, blk, dn)[0]))) / (2 * h)
    return g


def exposure(T):
    sd = np.std(T)
    return np.clip(1 + ETA * np.tanh(T / (sd if sd > 0 else 1)), 1 - ETA, 1 + ETA)


# ----------------------------------------------------------------------------- 5. driver
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args(argv)
    cache = DATA_DIR / "p8_signals.npz"
    R, px, vol, ffa = load_panel()
    dates = R.index
    years = dates.year.to_numpy()
    T, N = R.shape
    print(f"panel: {T} days x {N} stocks, {dates[0].date()}..{dates[-1].date()}")
    if cache.exists() and not a.rebuild:
        z = np.load(cache)
        Bt, Pm, eps = z["B"], z["P"], z["eps"]
        base = {k: z[k] for k in z.files if k not in ("B", "P", "eps")}
    else:
        Bt = rolling_betas(R, ffa[["mkt_rf", "smb", "hml", "rmw", "cma"]])
        eps, Pm = residuals(R, Bt)
        base = ou_features(eps)
        base.update(liquidity(px, vol))
        np.savez_compressed(cache, B=Bt, P=Pm, eps=eps, **base)
    print("residuals + OU features ready")

    trade_years = [y for y in range(FIRST_TRADE_YEAR, years.max() + 1)]
    th_prev = {"XGB": np.ones(len(FEATS)), "FFN": np.ones(len(FEATS))}
    rows_year, daily = [], {}
    attr_log = []
    t_start = time.time()
    def log(msg):
        print(f"[{(time.time() - t_start) / 60:6.1f} min] {msg}", flush=True)
    for y in trade_years:
        log(f"year {y}: building regime features ({trade_years.index(y)+1}/{len(trade_years)})")
        tr_rows = np.where((years >= y - 5) & (years <= y - 2))[0]
        va_rows = np.where(years == y - 1)[0]
        te_rows = np.where(years == y)[0]
        te_rows = te_rows[te_rows + 1 < T]
        span = np.r_[tr_rows, va_rows, te_rows]
        tr_rows = tr_rows[tr_rows >= L + BETA_WIN + 2]
        # regime features: HMM fitted on the training window, filtered causally over the whole span
        ent, dur, tp = regime_features(eps, tr_rows, span)
        feat = {k: base[k][span] for k in FEATS if k in base}
        feat["regime_entropy"], feat["regime_duration"], feat["regime_trans_prob"] = ent, dur, tp
        feat["entropy_pred_res"] = ent * np.abs(feat["pred_res"])
        Zspan = np.stack([zscore_cs(feat[k]) for k in FEATS], axis=2)
        Z = np.zeros((T, N, len(FEATS)), np.float32)
        Z[span] = Zspan
        tr, va, te = (Block(r_, Z, eps, Bt, Pm) for r_ in (tr_rows, va_rows, te_rows))

        # ---- hyperparameter selection on validation net SR
        log(f"year {y}: training FFN / XGB candidates")
        best = {}
        cand = []
        for lr in (1e-3, 3e-3):
            for drop in (0.0, 0.1):
                f = train_ffn(tr, lr, drop, epochs=300)
                cand.append((float(sharpe(eval_block(f, va)[0])), dict(lr=lr, drop=drop), f))
        best["FFN"] = max(cand, key=lambda x: x[0])
        cand = []
        for depth in (2, 3):
            f = train_xgb(tr, depth, rounds=150)
            for k in (25, 75, 150):
                fk = (lambda Z, f=f, k=k: f(Z, k))
                cand.append((float(sharpe(eval_block(fk, va)[0])), dict(depth=depth, rounds=k), fk))
        best["XGB"] = max(cand, key=lambda x: x[0])

        # ---- attribution on the validation window -> exposure multipliers
        log(f"year {y}: attribution + interventions (val SR FFN {best['FFN'][0]:.2f}, XGB {best['XGB'][0]:.2f})")
        th = {}
        for m in ("XGB", "FFN"):
            T_m = attribution(best[m][2], va)
            attr_log.append(dict(year=y, model=m, **dict(zip(FEATS, T_m))))
            f_m = exposure(T_m)
            th[(m, "unstab")] = np.clip(f_m, TH_MIN, TH_MAX)
            th[(m, "stab")] = np.clip(th_prev[m] * f_m, TH_MIN, TH_MAX)
            th_prev[m] = th[(m, "stab")]
        for rule in ("unstab", "stab"):
            th[("CROSS", rule)] = 0.5 * (th[("XGB", rule)] + th[("FFN", rule)])

        # ---- trade year
        for m in ("XGB", "FFN"):
            f = best[m][2]
            variants = {"baseline": None,
                        "model-specific unstabilised": th[(m, "unstab")],
                        "model-specific stabilised": th[(m, "stab")],
                        "cross-model unstabilised": th[("CROSS", "unstab")],
                        "cross-model stabilised": th[("CROSS", "stab")]}
            for v, theta in variants.items():
                net, gross, to = eval_block(f, te, theta)
                idx = dates[te_rows + 1]
                key = (m, v)
                daily.setdefault(key, []).append(pd.DataFrame(
                    {"net": net.numpy(), "gross": gross.numpy(), "turnover": to.numpy()}, index=idx))
                rows_year.append(dict(year=y, model=m, rule=v, sr_net=float(sharpe(net)), sr_gross=float(sharpe(gross)),
                                      avg_turnover=float(to.mean()), val_sr=best[m][0], hp=json.dumps(best[m][1])))
        yr = pd.DataFrame([r_ for r_ in rows_year if r_["year"] == y])
        log(f"year {y} done")
        print(y, yr.pivot(index="rule", columns="model", values="sr_net").round(2).to_dict())

    save_rows(rows_year, "p8_by_year.csv")
    save_rows(attr_log, "p8_attributions.csv")
    summary, curves = [], {}
    for (m, v), parts in daily.items():
        d = pd.concat(parts)
        d.to_csv(RES_DIR / f"p8_daily_{m}_{v.replace(' ', '_')}.csv", float_format="%.6f")
        base_net = pd.concat(daily[(m, "baseline")])["net"]
        diff_p = boot_sr_diff(d["net"], base_net) if v != "baseline" else np.nan
        summary.append(dict(model=m, rule=v, SR_gross=float(sharpe(torch.tensor(d["gross"].values))),
                            mu_gross=d["gross"].mean() * ANN, sigma=d["gross"].std() * np.sqrt(ANN),
                            SR_net=float(sharpe(torch.tensor(d["net"].values))), mu_net=d["net"].mean() * ANN,
                            avg_daily_turnover=d["turnover"].mean(), dSR_net_vs_base=np.nan, p_value_boot=diff_p,
                            start=d.index[0].date(), end=d.index[-1].date()))
        curves[f"{m} {v}"] = d["net"]
    s = pd.DataFrame(summary)
    for m in ("XGB", "FFN"):
        b = s[(s.model == m) & (s.rule == "baseline")]["SR_net"].iloc[0]
        s.loc[s.model == m, "dSR_net_vs_base"] = s.loc[s.model == m, "SR_net"] - b
    s.to_csv(RES_DIR / "p8_summary.csv", index=False, float_format="%.4f")
    print(s[["model", "rule", "SR_gross", "SR_net", "avg_daily_turnover", "dSR_net_vs_base", "p_value_boot"]]
          .to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    plot_equity({k: v for k, v in curves.items() if "baseline" in k or "cross-model stabilised" in k},
                "Paper 8: FF5 residual stat-arb, net of 5bp (baseline vs cross-model stabilised)",
                "p8_cumulative.png", logy=False)


def boot_sr_diff(a: pd.Series, b: pd.Series, n=2000, block=21, seed=0):
    """Two-sided p-value of SR(a) - SR(b) = 0 via a moving-block bootstrap of the paired days."""
    x = pd.concat([a, b], axis=1, join="inner").to_numpy()
    T = len(x)
    rng = np.random.default_rng(seed)
    sr = lambda v: v.mean(0) / v.std(0)
    obs = sr(x)[0] - sr(x)[1]
    d = []
    for _ in range(n):
        st = rng.integers(0, T - block, T // block + 1)
        idx = (st[:, None] + np.arange(block)).reshape(-1)[:T]
        s_ = sr(x[idx])
        d.append(s_[0] - s_[1])
    d = np.array(d) - np.mean(d)            # centre under H0
    return float((np.abs(d) >= abs(obs)).mean())


if __name__ == "__main__":
    main()
