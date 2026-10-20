"""Paper 2 — Boukardagha (2026), "Explainable Regime-Aware Investing", arXiv:2603.04441.
No code released; re-implemented from Algorithm 1.

Universe (paper: SPX, BOND, GOLD, OIL, USD proxies from Yahoo): SPY, AGG, GLD, USO, UUP.
Features x_t = [r_{t-1}; 60d vol_{t-1}; 20d mean_{t-1}] (3N dims, strictly causal),
standardised with the mean/std of the initial calibration window (fixed, so templates live in
one coordinate system).

Wasserstein HMM:
  * Gaussian HMM (full cov) on the expanding history, refit every REFIT days
  * order K in [K_MIN, K_MAX] re-selected every ORDER_EVERY days by one-step predictive
    log-likelihood on the last VAL days minus KAPPA * (#free params)
  * filtered p(z_t | F_{t-1}) via a forward pass with the current model
  * each component mapped to the nearest of G templates by the closed-form 2-Wasserstein
    distance; template probs = sum of mapped component probs; templates EMA-updated (ETA)
  * mixture moments of the return block -> daily MVO:
      max mu'w - GAMMA w'Sw - TAU ||w - w_prev||_1   s.t. 1'w = 1, 0 <= w <= W_MAX
KNN baseline (Algorithm 2): K_NN neighbours in feature space, Ledoit-Wolf cov, same MVO,
rebalanced every 5 days.

Hyperparameters NOT given in the paper (fixed a priori here, not tuned on test data):
  GAMMA=10, TAU=0.0005, W_MAX=0.5, G=6, ETA=0.05, KAPPA=0.5, VAL=63, K in [2,4], K_NN=50.
Execution: weights use data through t-1 and earn r_t (paper's convention); realised costs of
5 bp per unit turnover are charged (paper only puts TAU in the objective; gross also shown).
"""
from __future__ import annotations

import argparse
import warnings

import cvxpy as cp
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy.linalg import sqrtm
from scipy.special import logsumexp
from scipy.stats import multivariate_normal
from sklearn.covariance import LedoitWolf
from sklearn.neighbors import NearestNeighbors

from common import ANN, RES_DIR, fetch, plot_equity, save_rows, tbill_daily

warnings.filterwarnings("ignore")

GAMMA, TAU, W_MAX = 10.0, 0.0005, 0.5
G, ETA, KAPPA, VAL = 6, 0.05, 0.5, 63
K_MIN, K_MAX = 2, 4
REFIT, ORDER_EVERY = 5, 21
CALIB = 756            # 3y initial calibration window (templates + scaling)
MAX_HIST = 2520        # cap the expanding window at 10y for speed
COST = 0.0005
K_NN = 50


def load(equity="SPY"):
    assets = [equity, "AGG", "GLD", "USO", "UUP"]
    px = pd.DataFrame({a: fetch(a)["Close"] for a in assets})
    px = px.reindex(fetch(equity)["Close"].index).dropna()
    lr = np.log(px).diff().dropna()
    return assets, lr


def make_features(lr: pd.DataFrame) -> pd.DataFrame:
    vol = lr.rolling(60).std()
    mom = lr.rolling(20).mean()
    X = pd.concat([lr, vol, mom], axis=1).shift(1)   # info up to t-1
    X.columns = [f"{c}_{k}" for k in ("r", "vol", "mom") for c in lr.columns]
    return X.dropna()


def w2(m1, S1, m2, S2):
    r2 = sqrtm(S2)
    cross = sqrtm(r2 @ S1 @ r2)
    return float(np.sum((m1 - m2) ** 2) + np.trace(S1 + S2 - 2 * np.real(cross)))


def fit_hmm(X, K, seed=0):
    m = GaussianHMM(n_components=K, covariance_type="full", n_iter=60, tol=1e-3,
                    random_state=seed, min_covar=1e-4)
    m.fit(X)
    return m


def n_params(K, d):
    return K * (K - 1) + (K - 1) + K * d + K * d * (d + 1) / 2


def select_order(X):
    best, bestK = -np.inf, K_MIN
    d = X.shape[1]
    for K in range(K_MIN, K_MAX + 1):
        try:
            m = fit_hmm(X[:-VAL], K)
            pll = m.score(X) - m.score(X[:-VAL])          # sum log p(x_s | F_{s-1}) on V
            sc = pll - KAPPA * n_params(K, d) / 10.0
            if sc > best:
                best, bestK = sc, K
        except Exception:  # noqa: BLE001
            continue
    return bestK


def forward_filter(m: GaussianHMM, X: np.ndarray, log_alpha0=None):
    """Filtered P(z_t | x_1..t) for rows of X, continuing from log_alpha0 (prior row)."""
    K = m.n_components
    logB = np.column_stack([multivariate_normal(m.means_[k], m.covars_[k], allow_singular=True).logpdf(X)
                            for k in range(K)]).reshape(len(X), K)
    logA = np.log(m.transmat_ + 1e-300)
    la = np.log(m.startprob_ + 1e-300) if log_alpha0 is None else log_alpha0
    out = np.zeros((len(X), K))
    for i in range(len(X)):
        prior = logsumexp(la[:, None] + logA, axis=0) if (i > 0 or log_alpha0 is not None) else la
        la = prior + logB[i]
        la -= logsumexp(la)
        out[i] = np.exp(la)
    return out, la


def mvo(mu, Sig, w_prev):
    n = len(mu)
    w = cp.Variable(n)
    Sig = 0.5 * (Sig + Sig.T) + 1e-8 * np.eye(n)
    obj = mu @ w - GAMMA * cp.quad_form(w, cp.psd_wrap(Sig)) - TAU * cp.norm1(w - w_prev)
    prob = cp.Problem(cp.Maximize(obj), [cp.sum(w) == 1, w >= 0, w <= W_MAX])
    try:
        prob.solve(solver=cp.CLARABEL)
    except Exception:  # noqa: BLE001
        prob.solve(solver=cp.OSQP)
    return w_prev if w.value is None else np.clip(w.value, 0, W_MAX) / np.clip(w.value, 0, W_MAX).sum()


def run_hmm(lr, X, test_start, test_end=None):
    """Wasserstein-HMM + MVO. Returns daily weights (applied to r_t) and diagnostics."""
    N = lr.shape[1]
    idx = X.index
    t0 = idx.get_indexer([pd.Timestamp(test_start)], method="bfill")[0]
    t_end = len(idx) if test_end is None else idx.get_indexer([pd.Timestamp(test_end)], method="pad")[0] + 1
    calib = X.iloc[max(0, t0 - CALIB):t0]
    mu_s, sd_s = calib.mean(), calib.std()
    Z = ((X - mu_s) / sd_s).to_numpy()
    # templates initialised from a G-state HMM on the calibration window
    m0 = fit_hmm(Z[max(0, t0 - CALIB):t0], G, seed=1)
    T_mu, T_S = m0.means_.copy(), m0.covars_.copy()

    W, labels, Ks = [], [], []
    w_prev = np.full(N, 1.0 / N)
    model, K, la = None, None, None
    last_fit = -10 ** 9
    for i in range(t0, t_end):
        hist = Z[max(0, i - MAX_HIST):i]                  # rows < i (features already lag 1)
        if K is None or (i - t0) % ORDER_EVERY == 0:
            K = select_order(hist)
        if model is None or i - last_fit >= REFIT or model.n_components != K:
            model = fit_hmm(hist, K)
            last_fit = i
            # mapping component -> template
            dist = np.array([[w2(model.means_[k], model.covars_[k], T_mu[g], T_S[g]) for g in range(G)]
                             for k in range(K)])
            cmap = dist.argmin(axis=1)
            filt, la = forward_filter(model, hist[-252:])  # warm the filter on recent history
        # predictive regime probs for day i: P(z_i | F_{i-1}) — features row i uses data <= i-1
        filt_i, la = forward_filter(model, Z[i:i + 1], la)
        pk = filt_i[0]
        pg = np.zeros(G)
        for k in range(K):
            pg[cmap[k]] += pk[k]
        # template EMA update with posterior-weighted component averages
        for g in range(G):
            ks = np.where(cmap == g)[0]
            if len(ks) == 0 or pk[ks].sum() < 1e-6:
                continue
            wk = pk[ks] / pk[ks].sum()
            T_mu[g] = (1 - ETA) * T_mu[g] + ETA * (wk @ model.means_[ks])
            T_S[g] = (1 - ETA) * T_S[g] + ETA * np.einsum("k,kij->ij", wk, model.covars_[ks])
        # return-block moments (unscale to log-return units)
        sd_r, mu_r0 = sd_s.to_numpy()[:N], mu_s.to_numpy()[:N]
        m_mix = pg @ T_mu[:, :N]
        S_mix = np.einsum("g,gij->ij", pg, T_S[:, :N, :N]) + \
            np.einsum("g,gi,gj->ij", pg, T_mu[:, :N] - m_mix, T_mu[:, :N] - m_mix)
        mu = m_mix * sd_r + mu_r0
        Sig = S_mix * np.outer(sd_r, sd_r)
        w = mvo(mu, Sig, w_prev)
        W.append(w); labels.append(int(pg.argmax())); Ks.append(K)
        w_prev = w
    ix = idx[t0:t_end]
    return pd.DataFrame(W, ix, lr.columns), pd.Series(labels, ix), pd.Series(Ks, ix)


def run_knn(lr, X, test_start, test_end=None, every=5):
    N = lr.shape[1]
    idx = X.index
    t0 = idx.get_indexer([pd.Timestamp(test_start)], method="bfill")[0]
    t_end = len(idx) if test_end is None else idx.get_indexer([pd.Timestamp(test_end)], method="pad")[0] + 1
    Xs = ((X - X.iloc[:t0].mean()) / X.iloc[:t0].std()).to_numpy()
    R = lr.reindex(idx).to_numpy()
    W, w_prev = [], np.full(N, 1.0 / N)
    for i in range(t0, t_end):
        if (i - t0) % every == 0:
            # feature row s uses data <= s-1 and pairs with return r_s; rows < i are all realised
            nn = NearestNeighbors(n_neighbors=K_NN).fit(Xs[:i])
            nb = nn.kneighbors(Xs[i:i + 1], return_distance=False)[0]
            Rn = R[nb]
            mu = Rn.mean(axis=0)
            Sig = LedoitWolf().fit(Rn).covariance_
            w_prev = mvo(mu, Sig, w_prev)
        W.append(w_prev)
    return pd.DataFrame(W, idx[t0:t_end], lr.columns)


def realise(W: pd.DataFrame, lr: pd.DataFrame, cost=COST):
    r = np.exp(lr.reindex(W.index)) - 1
    gross = (W * r).sum(axis=1)
    to = W.diff().abs().sum(axis=1).fillna(0.0)
    return gross - cost * to, gross, to


def stats(r, rf):
    from common import ann_stats
    return ann_stats(r, rf)


def run_window(equity, region, start, end, do_knn=True):
    assets, lr = load(equity)
    X = make_features(lr)
    rf = tbill_daily(lr.index)
    W, lab, Ks = run_hmm(lr, X, start, end)
    net, gross, to = realise(W, lr)
    rows, curves = [], {}
    def add(name, r, turnover=None):
        s = stats(r, rf)
        rows.append(dict(region=region, window=f"{start}..{end or 'latest'}", strategy=name,
                         start=r.index[0].date(), end=r.index[-1].date(),
                         avg_daily_turnover=(turnover.mean() if turnover is not None else 0.0), **s))
        curves[name] = r
    add("W-HMM + MVO (net 5bp)", net, to)
    add("W-HMM + MVO (gross)", gross, to)
    simple = np.exp(lr.reindex(W.index)) - 1
    ew = simple.mean(axis=1)
    add("Equal weight (daily rebal)", ew)
    add(f"{equity} buy & hold", simple[equity])
    if do_knn:
        Wk = run_knn(lr, X, start, end)
        kn, kg, kto = realise(Wk, lr)
        add("KNN + MVO (net 5bp)", kn, kto)
    avg_w = W.mean().rename("avg_weight")
    return rows, curves, W, lab, Ks, avg_w


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args(argv)
    all_rows = []
    # (1) paper-like window: the paper's regime table covers ~480 OOS days ending early 2026
    rows, cv, W, lab, Ks, aw = run_window("SPY", "US", "2024-03-01", "2026-02-27")
    all_rows += rows
    plot_equity(cv, "Paper 2: Wasserstein HMM vs benchmarks (paper-like window 2024-03..2026-02)",
                "p2_us_paper_window.png")
    W.to_csv(RES_DIR / "p2_us_paper_window_weights.csv", float_format="%.4f")
    print(pd.DataFrame(rows)[["strategy", "CAGR", "Vol", "Sharpe", "MaxDD"]].to_string(index=False))
    print("avg weights:", aw.round(3).to_dict(), "| K path:", Ks.value_counts().to_dict())
    if not a.quick:
        # (2) long out-of-sample test 2012 -> latest
        rows, cv, W, lab, Ks, aw = run_window("SPY", "US", "2012-01-03", None)
        all_rows += rows
        plot_equity(cv, "Paper 2: Wasserstein HMM, long OOS 2012-2026 (US)", "p2_us_long.png")
        # (3) regions: swap the equity leg
        for eq, reg in [("EZU", "Europe"), ("EWJ", "Japan"), ("FXI", "China")]:
            rows, cv, *_ = run_window(eq, reg, "2012-01-03", None, do_knn=False)
            all_rows += rows
            plot_equity(cv, f"Paper 2: Wasserstein HMM, {reg} ({eq}/AGG/GLD/USO/UUP)", f"p2_{reg.lower()}.png")
    df = save_rows(all_rows, "p2_metrics.csv")
    return df


if __name__ == "__main__":
    main()
