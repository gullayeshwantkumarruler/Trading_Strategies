"""Step 2 — residual ladder and published rules on one harness (report priority 2).

Residual models (all out-of-sample: loadings estimated with data <= t, applied to the return of t+1
via the cached convention eps_t = R_t - (exposures_{t-1}) f_t):
  FF5      : paper 8's 60-day rolling FF5 regressions + cross-sectional projection (cached)
  PCA-K    : Avellaneda-Lee eigenportfolios from the 252-day correlation matrix (K = 3, 5), loadings
             by 60-day time-series regression on the eigenportfolio returns, re-estimated daily
  CharProj : "IPCA-lite" — residual of a daily cross-sectional regression of returns on ranked
             characteristics known at t-1 (12-1 momentum, 1-month reversal, 60d vol, 252d beta,
             dollar-volume size proxy, constant). Static-Gamma simplification of IPCA.
Signals per residual model:
  rev5     : -(sum of last 5 residuals)
  NFE rule : z = standardised cumulative residual over L = 60; w ∝ -clip(z, ±3); held H = 20 days
             non-overlapping (Korean NFE paper's no-tuning baseline, arXiv 2610.25802)
Other published rules:
  Robeco residual reversal (Blitz et al. 2023): FF3 residual return over the last 21 days, 3-factor
             betas over a rolling 756-day (36-month) window, scaled by residual vol, sector-demeaned,
             monthly rebalance
  SPONGE graph clustering (Cartea-Cucuringu 2023 / Korniejczuk-Slepaczuk 2024): signed correlation
             graph of 30-day residual returns, SPONGE-sym spectral clustering (k = 20), re-clustered every
             10 days; within-cluster mean reversion signal -(5d residual - cluster mean). TP/SL omitted.
Each signal is traded two ways: daily full rebalance and Garleanu-Pedersen partial trading (tau = 0.1).
IC decay by lag is measured for every residual model first.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import eigh
from sklearn.cluster import KMeans

import core
from step1_construction import partial, resid_rev


# ----------------------------------------------------------------------------- residual models
def pca_residuals(R: pd.DataFrame, K: int, corr_win=252, beta_win=60) -> np.ndarray:
    p = core.DATA / f"resid_pca{K}.npy"
    if p.exists():
        return np.load(p)
    X = R.to_numpy()
    T, N = X.shape
    eps = np.full((T, N), np.nan)
    for t in range(corr_win, T - 1):
        win = X[t - corr_win + 1:t + 1]
        mu, sd = win.mean(0), win.std(0) + 1e-12
        C = np.corrcoef(((win - mu) / sd).T)
        vals, vecs = np.linalg.eigh(C)
        V = vecs[:, ::-1][:, :K]
        Q = V / sd[:, None]                                   # eigenportfolio weights
        Fw = X[t - beta_win + 1:t + 1] @ Q                    # 60 x K factor returns
        Rw = X[t - beta_win + 1:t + 1]
        Fx = np.column_stack([np.ones(beta_win), Fw])
        coef = np.linalg.lstsq(Fx, Rw, rcond=None)[0]          # (K+1) x N
        f_next = X[t + 1] @ Q
        eps[t + 1] = X[t + 1] - coef[1:].T @ f_next           # intercept excluded (A-L)
    np.save(p, eps.astype(np.float32))
    return eps


def characteristics(P) -> np.ndarray:
    R, px = P["R"], P["px"]
    r = px.pct_change(fill_method=None)
    mkt = r.mean(axis=1)
    ch = {
        "mom": px.shift(21) / px.shift(252) - 1,
        "rev": px / px.shift(21) - 1,
        "vol": r.rolling(60).std(),
        "beta": r.rolling(252).cov(mkt).div(mkt.rolling(252).var(), axis=0),
        "size": np.log((px * P["vol"]).rolling(21).mean()),
    }
    Z = np.stack([v.rank(axis=1, pct=True).to_numpy() - 0.5 for v in ch.values()], axis=2)
    return np.nan_to_num(Z)


def charproj_residuals(P) -> np.ndarray:
    p = core.DATA / "resid_charproj.npy"
    if p.exists():
        return np.load(p)
    X = P["R"].to_numpy()
    Z = characteristics(P)
    T, N = X.shape
    eps = np.full((T, N), np.nan)
    for t in range(253, T):
        z = np.column_stack([np.ones(N), Z[t - 1]])           # characteristics known at t-1
        f = np.linalg.lstsq(z, X[t], rcond=None)[0]
        eps[t] = X[t] - z @ f
    np.save(p, eps.astype(np.float32))
    return eps


def ff3_long_residuals(P, W=756) -> np.ndarray:
    """FF3 residuals with 756-day rolling betas (Robeco recipe)."""
    p = core.DATA / "resid_ff3_756.npy"
    if p.exists():
        return np.load(p)
    import p8_attribution_statarb as p8
    B = p8.rolling_betas(P["R"], P["ff"][["mkt_rf", "smb", "hml"]], W=W)
    X, F = P["R"].to_numpy(), P["ff"][["mkt_rf", "smb", "hml"]].to_numpy()
    eps = np.full_like(X, np.nan)
    for t in range(W, len(X)):
        eps[t] = X[t] - B[t - 1] @ F[t]
    np.save(p, eps.astype(np.float32))
    return eps


# ----------------------------------------------------------------------------- signals
def nfe_rule(eps, L=60, H=20):
    cs = pd.DataFrame(np.cumsum(np.nan_to_num(eps), 0))
    z = ((cs - cs.rolling(L).mean()) / cs.rolling(L).std()).to_numpy()
    aim = core.to_book(-np.clip(z, -3, 3))
    W = np.zeros_like(aim)
    for t in range(len(aim)):
        W[t] = aim[t] if t % H == 0 else W[t - 1]
    return W


def robeco_signal(P, eps3):
    e = pd.DataFrame(eps3)
    s = -(e.rolling(21).sum() / (e.rolling(756, min_periods=252).std() * np.sqrt(21))).to_numpy()
    sec = core.sectors(P["R"].columns).to_numpy()
    for g in np.unique(sec):
        m = sec == g
        s[:, m] = s[:, m] - np.nanmean(s[:, m], axis=1, keepdims=True)
    aim = core.to_book(s)
    idx = P["R"].index
    month_end = pd.Series(idx, idx).groupby([idx.year, idx.month]).transform("max").to_numpy() == idx.to_numpy()
    W = np.zeros_like(aim)
    for t in range(len(aim)):
        W[t] = aim[t] if month_end[t] else W[t - 1]
    return W


def sponge_clusters(C, k=20, tau=1.0):
    Ap, An = np.clip(C, 0, None), np.clip(-C, 0, None)
    np.fill_diagonal(Ap, 0); np.fill_diagonal(An, 0)
    Dp, Dn = np.diag(Ap.sum(1)), np.diag(An.sum(1))
    Lp, Ln = Dp - Ap, Dn - An
    A = Lp + tau * Dn + 1e-6 * np.eye(len(C))
    Bm = Ln + tau * Dp + 1e-6 * np.eye(len(C))
    vals, vecs = eigh(A, Bm, subset_by_index=[0, k - 1])
    return KMeans(n_clusters=k, n_init=4, random_state=0).fit_predict(vecs)


def sponge_signal(eps, look=30, every=10, k=20):
    e = np.nan_to_num(eps)
    T, N = e.shape
    rev5 = resid_rev(eps, 5)
    s = np.full((T, N), np.nan)
    lab = None
    for t in range(look, T):
        if lab is None or t % every == 0:
            C = np.corrcoef(e[t - look + 1:t + 1].T)
            lab = sponge_clusters(np.nan_to_num(C), k=k)
        x = rev5[t]
        cm = np.array([x[lab == c].mean() for c in range(k)])
        s[t] = x - cm[lab]
    return s


def ic_decay(eps, R, name, lags=(1, 2, 3, 5, 10, 20)):
    S = pd.DataFrame(resid_rev(eps, 5), R.index, R.columns).loc[core.START:]
    out = {"residual": name}
    for lag in lags:
        out[f"IC_lag{lag}"] = S.rank(axis=1).corrwith(R.shift(-lag).loc[core.START:].rank(axis=1), axis=1).mean()
    return out


def main():
    log = core.Timer()
    P = core.panel()
    R = P["R"]
    res = {"FF5": P["eps"]}
    log("PCA-3 residuals"); res["PCA3"] = pca_residuals(R, 3)
    log("PCA-5 residuals"); res["PCA5"] = pca_residuals(R, 5)
    log("char-projection residuals"); res["CharProj"] = charproj_residuals(P)
    decay = [ic_decay(e, R, n) for n, e in res.items()]
    core.save(decay, "step2_ic_decay.csv")
    print(pd.DataFrame(decay).round(4).to_string(index=False), flush=True)

    rows, curves = [], {}
    for n, e in res.items():
        aim = core.to_book(resid_rev(e, 5))
        for how, W in [("daily", aim), ("partial0.1", partial(aim, 0.1))]:
            bt = core.backtest(W)
            rows.append(core.summarize(bt, f"{n} rev5 {how}", "s2_residuals", {"resid": n, "trade": how}))
            if how == "partial0.1":
                curves[f"{n} rev5 partial"] = bt["net"]
        bt = core.backtest(nfe_rule(e))
        rows.append(core.summarize(bt, f"{n} NFE rule L60 H20", "s2_residuals", {"resid": n, "rule": "NFE"}))
        log(f"{n} done")
    core.show(pd.DataFrame(rows))

    log("Robeco residual reversal (FF3, 756d betas, monthly)")
    e3 = ff3_long_residuals(P)
    W = robeco_signal(P, e3)
    bt = core.backtest(W)
    rows.append(core.summarize(bt, "Robeco residual reversal monthly", "s2_published", {"paper": "Blitz et al. 2023"}))
    curves["Robeco monthly"] = bt["net"]

    log("SPONGE graph clustering (PCA5 residuals)")
    s = sponge_signal(res["PCA5"])
    aim = core.to_book(s)
    for how, Wc in [("daily", aim), ("partial0.1", partial(aim, 0.1))]:
        bt = core.backtest(Wc)
        rows.append(core.summarize(bt, f"SPONGE clusters {how}", "s2_published", {"paper": "Cartea-Cucuringu/KS 2024", "trade": how}))
    curves["SPONGE partial"] = bt["net"]
    df = core.save(rows, "step2_residuals.csv")
    core.show(df)
    core.plot(curves, "Step 2: residual models and published rules (net of 5bp + 1bp/day shorts)", "step2_residuals.png")
    log("done")


if __name__ == "__main__":
    main()
