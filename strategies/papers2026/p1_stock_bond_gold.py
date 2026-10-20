"""Paper 1 — Devanathan, Tzikas & Boyd (2026), "Simple Dynamic Stock/Bond/Gold Portfolios",
arXiv:2609.07946. Official code: github.com/cvxgrp/simple-portfolio-code (needs a FRED API key
and pandas 3, so this is a re-implementation of the paper's spec, using the repo's feature list).

Portfolios (long-only, SPY/AGG/GLD + cash, cost = 5 bp spread -> 2.5 bp half-spread per unit traded):
  60/40, 50/30/20          fixed weights, rebalanced on the last trading day of each year
  60/40 VC, 50/30/20 VC    monthly; scale benchmark by min(1, sigma_tgt / sigma_hat), sigma_hat = 11-day vol
  Simple Markowitz         monthly convex problem (3), mu = EWMA(daily ret, hl 252) * 21
  Markowitz                same, mu = ridge forecast of 100-day fwd return on 42 features (Appendix B)
Problem (3): max mu'w + rf(1-1'w) - s/2 ||w - w_prev||_1
             s.t. w >= 0, 1'w <= 1, ||w - (1'w) w_tgt||_1 <= 1'w, sqrt(w' Sigma w) <= sigma_tgt
Sigma = 11-day uncentred covariance (repo's construction), sigma_tgt = 7%.
Decisions use data through the close of the rebalance day and trade at that close (paper's
convention); a 1-day-lag variant (decide at t, trade at t+1) is also reported.

Regional extension (not in the paper): swap SPY for EZU (Europe), EWJ (Japan), FXI (China),
keeping AGG/GLD and a USD investor's cash; Fama-French factors stay US.
"""
from __future__ import annotations

import argparse

import cvxpy as cp
import numpy as np
import pandas as pd

from common import ANN, RES_DIR, fetch, fred, french_factors, plot_equity, save_rows

S = 0.0005            # bid-ask spread
TGT_VOL = 0.07
COV_WIN = 11
EWMA_HL = 252
FWD = 100
TRAIN_MAX = 512
TRAIN_MIN = 63
RIDGE_LAM = 10.0
RIDGE_HL = 252
W_TGT = np.array([0.5, 0.3, 0.2])
START, END_PAPER = "2006-01-01", "2026-01-01"

FRED_FEATS = {"DGS3MO": "y_3m", "DGS2": "y_2y", "DGS5": "y_5y", "DGS10": "y_10y", "DGS30": "y_30y",
              "DFII10": "real_y_10y", "T10YIE": "breakeven_10y", "VIXCLS": "vix", "DTWEXBGS": "dollar_index"}


# ----------------------------------------------------------------------------- data
def load(equity: str = "SPY"):
    assets = [equity, "AGG", "GLD"]
    px, vol = {}, {}
    for a in assets:
        d = fetch(a)
        px[a], vol[a] = d["Close"], d["Volume"]
    px, vol = pd.DataFrame(px), pd.DataFrame(vol)
    cal = px[equity].dropna().index
    px, vol = px.reindex(cal), vol.reindex(cal)
    ffr = fred("DFF").reindex(cal.union(fred("DFF").index)).ffill().reindex(cal)
    rf = (1 + ffr / 100) ** (1 / ANN) - 1
    return assets, px, vol, rf.fillna(0.0)


def features(px: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
    """Appendix B / repo feature set: 8 per asset (24) + 10 macro + 8 Fama-French = 42."""
    cal = px.index
    r = px.pct_change(fill_method=None)
    blocks = {}
    for h in [63, 126, 252]:
        blocks[f"ret_{h}d"] = px.pct_change(h, fill_method=None)
    # the repo overwrites vol_adjusted_ret inside its loop, so only h=252 survives -> replicate that
    blocks["vol_adj_ret"] = px.pct_change(252, fill_method=None) / r.rolling(252).std()
    blocks["vol_21_vs_252"] = np.log(r.rolling(21).std()) - np.log(r.rolling(252).std())
    lv = np.log(vol.replace(0, np.nan))
    for h in [21, 63, 126]:
        blocks[f"logvol_{h}d"] = lv.rolling(h, min_periods=h // 2).mean()
    asset_f = pd.concat(blocks, axis=1)
    asset_f.columns = [f"{a}__{b}" for a, b in asset_f.columns]

    m = {}
    for sid, name in FRED_FEATS.items():
        s = fred(sid)
        m[name] = s.reindex(cal.union(s.index)).ffill().reindex(cal)
    m = pd.DataFrame(m)
    macro = m[["y_3m", "y_2y", "y_5y", "y_10y", "y_30y", "real_y_10y", "breakeven_10y"]].copy()
    macro["log_vix"] = np.log(m["vix"]).rolling(63).mean()
    macro["dollar_index"] = m["dollar_index"].rolling(512, min_periods=252).mean()
    macro["slope_3m_2y"] = macro["y_2y"] - macro["y_3m"]

    ff = french_factors()[["mkt_rf", "smb", "hml", "rmw", "cma", "mom", "st_rev", "lt_rev"]]
    ff = ff.reindex(cal.union(ff.index)).ffill().reindex(cal).rolling(63).mean().add_prefix("ff_")
    return pd.concat([asset_f, macro, ff], axis=1)


# ----------------------------------------------------------------------------- forecasts
def ridge_forecast(F: pd.DataFrame, px: pd.DataFrame, dates) -> pd.DataFrame:
    """Causal multivariate ridge (Appendix B): target = 100d fwd return * 252/100; train on the
    last <=512 rows whose target ends by t; features scaled (not centred) by window std;
    exp. weights hl 252 (normalised); lambda = 10; no intercept."""
    fwd = (px.shift(-FWD) / px - 1) * (ANN / FWD)
    idx = F.index
    out = {}
    for t in dates:
        i = idx.get_loc(t)
        hi = i - FWD                      # last row whose label is fully realised at t
        if hi < 0:
            out[t] = np.zeros(px.shape[1]); continue
        lo = max(0, hi - TRAIN_MAX + 1)
        Z, Y = F.iloc[lo:hi + 1], fwd.iloc[lo:hi + 1]
        cols = Z.columns[Z.notna().all() & F.loc[t].notna()]
        ok = Y.notna().all(axis=1)
        Z, Y = Z.loc[ok, cols], Y.loc[ok]
        if len(Z) < TRAIN_MIN or len(cols) == 0:
            out[t] = np.zeros(px.shape[1]); continue
        d = Z.std().clip(lower=1e-8)
        Zs = (Z / d).to_numpy()
        age = np.arange(len(Zs))[::-1]
        pi = 0.5 ** (age / RIDGE_HL)
        pi /= pi.sum()
        A = Zs.T @ (Zs * pi[:, None]) + RIDGE_LAM * np.eye(Zs.shape[1])
        B = np.linalg.solve(A, Zs.T @ (Y.to_numpy() * pi[:, None])).T   # (3, p)
        out[t] = B @ (F.loc[t, cols] / d).to_numpy()
    return pd.DataFrame(out, index=px.columns).T


def cov11(r: pd.DataFrame, t) -> np.ndarray:
    """Repo construction: uncentred vols over 11 days, correlation of vol-scaled returns."""
    x = r.loc[:t].tail(COV_WIN).dropna()
    v = np.sqrt((x ** 2).mean())
    c = (x / v).cov().to_numpy()
    return np.outer(v, v) * c * ANN


# ----------------------------------------------------------------------------- optimiser
def solve(mu, Sig, rf_m, w_prev, tgt=TGT_VOL):
    w = cp.Variable(3)
    L = np.linalg.cholesky(Sig + 1e-10 * np.eye(3))
    obj = mu @ w + rf_m * (1 - cp.sum(w)) - (S / 2) * cp.norm1(w - w_prev)
    cons = [w >= 0, cp.sum(w) <= 1, cp.norm1(w - cp.sum(w) * W_TGT) <= cp.sum(w),
            cp.norm(L.T @ w, 2) <= tgt]
    prob = cp.Problem(cp.Maximize(obj), cons)
    try:
        prob.solve(solver=cp.CLARABEL)
    except Exception:  # noqa: BLE001
        prob.solve(solver=cp.SCS)
    return np.clip(w.value, 0, 1) if w.value is not None else w_prev


# ----------------------------------------------------------------------------- simulator
def simulate_daily(r: pd.DataFrame, rf: pd.Series, decide, rebal_dates, lag: int = 0):
    """Appendix A style: daily drift, cash earns FFR, cost = S/2 * ||dw||_1 at rebalance.
    decide(t, w_drifted) -> target weights using data through close t; executed at close
    t (lag=0) or the next close (lag=1, decision still uses data through t)."""
    idx = r.index
    R, RF = r.fillna(0.0).to_numpy(), rf.reindex(idx).fillna(0.0).to_numpy()
    rb = set(rebal_dates)
    w = np.zeros(r.shape[1])
    pending = None
    rets, tos, W = np.zeros(len(idx)), np.zeros(len(idx)), np.zeros((len(idx), r.shape[1]))
    for i, t in enumerate(idx):
        # 1) earn today's return on yesterday's closing weights
        cash = 1 - w.sum()
        g = float(w @ R[i]) + cash * RF[i]
        w = w * (1 + R[i]) / (1 + g) if (1 + g) > 0 else w
        cost = 0.0
        # 2) trade at today's close
        if pending is not None:
            cost = S / 2 * np.abs(pending - w).sum(); tos[i] = np.abs(pending - w).sum() / 2
            w = pending; pending = None
        if t in rb:
            tgt = decide(t, w.copy())
            if lag == 0:
                cost += S / 2 * np.abs(tgt - w).sum(); tos[i] = np.abs(tgt - w).sum() / 2
                w = tgt
            else:
                pending = tgt
        rets[i] = (1 + g) * (1 - cost) - 1
        W[i] = w
    return pd.Series(rets, idx), pd.Series(tos, idx), pd.DataFrame(W, idx, r.columns)


def paper_stats(ret: pd.Series, rf: pd.Series, to: pd.Series) -> dict:
    yrs = len(ret) / ANN
    eq, eqf = (1 + ret).cumprod(), (1 + rf.reindex(ret.index).fillna(0)).cumprod()
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    cagr_f = eqf.iloc[-1] ** (1 / yrs) - 1
    vol = ret.std() * np.sqrt(ANN)
    ex = ret - rf.reindex(ret.index).fillna(0)
    dd = eq / eq.cummax() - 1
    return dict(CAGR=cagr, Vol=vol, Sharpe_geo=(cagr - cagr_f) / vol,
                Sharpe=ex.mean() / ex.std() * np.sqrt(ANN), MaxDD=dd.min(), MeanDD=dd.mean(),
                Turnover=to.sum() / yrs)


def run_region(equity: str, region: str, end: str | None, lag: int = 0):
    assets, px, vol, rf = load(equity)
    r = px.pct_change(fill_method=None)
    start = max(pd.Timestamp(START), px.dropna().index[0] + pd.Timedelta(400, "D"))
    idx = r.loc[start:end].index
    r_eval, rf_eval = r.loc[idx], rf.loc[idx]
    me = sorted(set(pd.Series(idx, idx).groupby([idx.year, idx.month]).max().tolist()) | {idx[0]})
    ye = pd.Series(idx, idx).groupby(idx.year).max().tolist()
    rf_m = (1 + rf).rolling(21).apply(np.prod, raw=True) - 1   # contemporaneous FFR over 21d

    F = features(px, vol)
    mu_ridge = ridge_forecast(F, px, me) * (21 / ANN)
    mu_simple = r.ewm(halflife=EWMA_HL, min_periods=63).mean() * 21

    def fixed(wt):
        return lambda t, w: np.array(wt, float)

    def vc(wt):
        wt = np.array(wt, float)
        def f(t, w):
            sig = (r.loc[:t].tail(COV_WIN) @ wt).std() * np.sqrt(ANN)
            return wt * min(1.0, TGT_VOL / sig) if sig > 0 else wt
        return f

    def mk(mu_df):
        def f(t, w):
            mu = mu_df.loc[t].fillna(0.0).to_numpy()
            return solve(mu, cov11(r, t), float(rf_m.loc[t]), w)
        return f

    ports = {
        "60/40": (fixed([0.6, 0.4, 0.0]), ye),
        "50/30/20": (fixed([0.5, 0.3, 0.2]), ye),
        "60/40 VC": (vc([0.6, 0.4, 0.0]), me),
        "50/30/20 VC": (vc([0.5, 0.3, 0.2]), me),
        "Simple Markowitz": (mk(mu_simple), me),
        "Markowitz": (mk(mu_ridge), me),
    }
    rows, curves, weights = [], {}, {}
    # fixed-weight books start invested on day 1
    for name, (fn, dates) in ports.items():
        d = sorted(set(dates) | {idx[0]})
        ret, to, W = simulate_daily(r_eval, rf_eval, fn, d, lag=lag)
        st = paper_stats(ret, rf_eval, to)
        rows.append(dict(region=region, equity=equity, portfolio=name, lag=lag,
                         start=idx[0].date(), end=idx[-1].date(), **st))
        curves[name], weights[name] = ret, W
    for a in assets:
        st = paper_stats(r_eval[a].fillna(0), rf_eval, pd.Series(0.0, idx))
        rows.append(dict(region=region, equity=equity, portfolio=a, lag=lag,
                         start=idx[0].date(), end=idx[-1].date(), **st))
    return rows, curves, weights, rf_eval


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="US replication only")
    a = ap.parse_args(argv)
    rows, all_curves = [], {}
    # (1) replication window 2006-01-01 .. 2026-01-01 (paper Table 1)
    rr, cv, W, rf = run_region("SPY", "US", END_PAPER)
    rows += [dict(x, window="paper 2006-2025") for x in rr]
    plot_equity({k: cv[k] for k in ["60/40", "50/30/20", "50/30/20 VC", "Simple Markowitz", "Markowitz"]},
                "Paper 1 replication (US, 2006-2025): stock/bond/gold", "p1_us_replication.png")
    W["Markowitz"].to_csv(RES_DIR / "p1_us_markowitz_weights.csv", float_format="%.4f")
    all_curves["US"] = cv["Markowitz"]
    # (2) 1-day execution lag robustness
    rr, _, _, _ = run_region("SPY", "US", END_PAPER, lag=1)
    rows += [dict(x, window="paper 2006-2025, 1d lag") for x in rr if x["portfolio"] in
             ("Markowitz", "Simple Markowitz", "50/30/20 VC", "60/40 VC")]
    if not a.quick:
        # (3) true out-of-sample extension: 2026-01-01 .. latest
        rr, _, _, _ = run_region("SPY", "US", None)
        rows += [dict(x, window="2006-latest") for x in rr]
        # (4) regions
        for eq, reg in [("EZU", "Europe"), ("EWJ", "Japan"), ("FXI", "China")]:
            rr, cv, _, _ = run_region(eq, reg, None)
            rows += [dict(x, window="2006-latest") for x in rr]
            all_curves[reg] = cv["Markowitz"]
            plot_equity({k: cv[k] for k in ["60/40", "50/30/20", "50/30/20 VC", "Markowitz"]},
                        f"Paper 1 extension ({reg}: {eq}/AGG/GLD)", f"p1_{reg.lower()}.png")
    df = save_rows(rows, "p1_metrics.csv")
    show = df[df.window == "paper 2006-2025"][["portfolio", "CAGR", "Vol", "Sharpe_geo", "MaxDD", "MeanDD", "Turnover"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    return df, all_curves


if __name__ == "__main__":
    main()
