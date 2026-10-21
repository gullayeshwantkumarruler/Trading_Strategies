"""Step 4 — slow alpha library + point-in-time EDGAR fundamentals + combination (report priority 4).

Signals (all computed from data known at the decision close; fundamentals usable from filing date + 1):
  price/volume (18): mom_12_1, mom_6_1, rev_1m, high_52w, low_vol_60, low_beta_252, amihud, low_max_21,
      low_idio_vol, low_turnover, low_skew_60, resid_mom (FF5 residual 12-1), roc_5, roc_60, ma20_gap,
      ma60_gap, corr_px_logvol_20 (Alpha158 CORR20), vol_trend_20_60
  fundamentals (9, SEC companyfacts, first-reported values only): gross_prof (GP/assets),
      asset_growth (-), accruals (-), net_issuance (-), earnings_yield, book_to_market, roe, cfo_assets, sue
Evaluation: month-end rank IC vs the next 21-day excess return (non-overlapping), t-stat, ICIR,
  correlation with the fast 5-day residual-reversal signal; ml4t-diagnostic analyze_signal on the composite.
Combination (walk-forward, refit every January on all prior months, first composite month 2013-01):
  EW (sign = sign of training IC), IC-weighted (trailing 36 months), ridge, LightGBM; composite neutralised
  to sectors + FF5 betas (FNC-style).
Books: (a) monthly long-short (dollar-neutral, unit gross) from each composite;
       (b) daily optimiser (step 1) with alpha = slow composite (+ fast residual reversal) — the report's
           "slow aim, fast timing" blend.
"""
from __future__ import annotations

import argparse
import os

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

import core
from step1_construction import Optimiser, resid_rev

H = 21


def pv_signals(P) -> dict[str, pd.DataFrame]:
    px, vol, R = P["px"], P["vol"], P["R"]
    r = px.pct_change(fill_method=None)
    mkt = r.mean(axis=1)
    eps = pd.DataFrame(P["eps"], R.index, R.columns)
    lv = np.log(vol.replace(0, np.nan))
    s = {
        "mom_12_1": px.shift(21) / px.shift(252) - 1,
        "mom_6_1": px.shift(21) / px.shift(126) - 1,
        "rev_1m": -(px / px.shift(21) - 1),
        "high_52w": px / px.rolling(252).max(),
        "low_vol_60": -r.rolling(60).std(),
        "low_beta_252": -r.rolling(252).cov(mkt).div(mkt.rolling(252).var(), axis=0),
        "amihud": (r.abs() / (px * vol)).rolling(21).mean(),
        "low_max_21": -r.rolling(21).max(),
        "low_idio_vol": -eps.rolling(60).std(),
        "low_turnover": -(vol / vol.rolling(252).mean()),
        "low_skew_60": -r.rolling(60).skew(),
        "resid_mom": eps.shift(21).rolling(231).sum(),
        "roc_5": -(px / px.shift(5) - 1),
        "roc_60": px / px.shift(60) - 1,
        "ma20_gap": -(px / px.rolling(20).mean() - 1),
        "ma60_gap": px / px.rolling(60).mean() - 1,
        "corr_px_logvol_20": -px.rolling(20).corr(lv),
        "vol_trend_20_60": -(r.rolling(20).std() / r.rolling(60).std()),
    }
    return s


def fund_signals(P) -> dict[str, pd.DataFrame]:
    p = core.DATA / "fund_pit.npz"
    R, px = P["R"], P["px"]
    if p.exists():
        z = np.load(p, allow_pickle=True)
        F = {k: pd.DataFrame(z[k], R.index, R.columns) for k in z.files}
    else:
        import edgar
        raw = edgar.pit_panel(list(R.columns), R.index)
        np.savez_compressed(p, **{k: v.to_numpy() for k, v in raw.items()})
        F = raw
    mcap = px * F["shares"]
    gp = F["gp_ttm"].fillna(F["revenue_ttm"] - F["cogs_ttm"])
    return {
        "gross_prof": gp / F["assets"],
        "asset_growth": -(F["assets"] / F["assets_lag1y"] - 1),
        "accruals": -(F["ni_ttm"] - F["cfo_ttm"]) / F["assets"],
        "net_issuance": -np.log(F["shares"] / F["shares_lag1y"]),
        "earnings_yield": F["ni_ttm"] / mcap,
        "book_to_market": F["equity"] / mcap,
        "roe": F["ni_ttm"] / F["equity"],
        "cfo_assets": F["cfo_ttm"] / F["assets"],
        "sue": F["sue"],
    }


def month_ends(idx):
    return pd.Series(idx, idx).groupby([idx.year, idx.month]).max().to_list()


def rank_cs(df):
    return df.rank(axis=1, pct=True) - 0.5


def neutralise(S: pd.DataFrame, P) -> pd.DataFrame:
    """Project each date's composite off sector dummies and FF5 betas (FNC-style)."""
    sec = pd.get_dummies(core.sectors(S.columns)).astype(float).to_numpy()
    B = P["B"]
    loc = P["R"].index.get_indexer(S.index)
    out = S.copy()
    for i, t in enumerate(loc):
        y = S.iloc[i].to_numpy()
        ok = np.isfinite(y) & np.isfinite(B[t]).all(1)
        if ok.sum() < 50:
            continue
        X = np.column_stack([sec[ok], np.nan_to_num(B[t][ok])])
        y2 = y.copy()
        y2[ok] = y[ok] - X @ np.linalg.lstsq(X, y[ok], rcond=None)[0]
        out.iloc[i] = y2
    return out


def evaluate(signals, fwd, rev5_me):
    rows = []
    for n, S in signals.items():
        ic = rank_cs(S).corrwith(rank_cs(fwd), axis=1).dropna()
        ic = ic.loc[core.START:]
        a, b = ic.loc[:"2021-12-31"], ic.loc[core.SPLIT:]
        corr_rev = rank_cs(S).corrwith(rank_cs(rev5_me), axis=1).loc[core.START:].mean()
        rows.append(dict(signal=n, IC=ic.mean(), IC_t=ic.mean() / ic.std() * np.sqrt(len(ic)), ICIR_ann=ic.mean() / ic.std() * np.sqrt(12),
                         IC_2010_21=a.mean(), IC_2022_26=b.mean(), corr_with_rev5=corr_rev, months=len(ic)))
    return pd.DataFrame(rows).sort_values("IC_t", ascending=False)


def combine(signals, fwd, method, first_year=2013):
    names = list(signals)
    X = {n: rank_cs(signals[n]) for n in names}
    dates = fwd.index
    out = pd.DataFrame(np.nan, index=dates, columns=fwd.columns)
    Y = rank_cs(fwd)
    ics = pd.DataFrame({n: X[n].corrwith(Y, axis=1) for n in names})
    for yr in range(first_year, dates.year.max() + 1):
        test = dates[dates.year == yr]
        train = dates[dates < pd.Timestamp(f"{yr}-01-01") - pd.Timedelta(31, "D")]   # labels realised before Jan
        train = train[train >= pd.Timestamp("2010-01-01")]
        if len(train) < 24 or len(test) == 0:
            continue
        if method in ("EW", "ICW"):
            ic_tr = ics.loc[train] if method == "EW" else ics.loc[train[-36:]]
            w = np.sign(ic_tr.mean()) if method == "EW" else ic_tr.mean() / ic_tr.std()
            for d in test:
                out.loc[d] = sum(w[n] * X[n].loc[d].fillna(0) for n in names)
        else:
            def stack(ds):
                Xs = np.stack([X[n].loc[ds].to_numpy() for n in names], axis=2).reshape(-1, len(names))
                return np.nan_to_num(Xs)
            Xtr, ytr = stack(train), Y.loc[train].to_numpy().reshape(-1)
            ok = np.isfinite(ytr)
            if method == "ridge":
                m = Ridge(alpha=100.0).fit(Xtr[ok], ytr[ok])
            else:
                m = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=200,
                                      subsample=0.8, subsample_freq=1, colsample_bytree=0.7, verbose=-1).fit(Xtr[ok], ytr[ok])
            pred = m.predict(stack(test)).reshape(len(test), -1)
            out.loc[test] = pred
    return out


def monthly_book(C: pd.DataFrame, P) -> np.ndarray:
    """Hold the composite's dollar-neutral book from each month-end to the next."""
    R = P["R"]
    aim = pd.DataFrame(np.nan, R.index, R.columns)
    aim.loc[C.index] = core.to_book(C.to_numpy())
    return aim.ffill().fillna(0.0).to_numpy()


def blended_optimiser(P, slow: pd.DataFrame, w_fast: float, g_trade: float, ic_slow=0.03, ic_fast=0.01):
    R = P["R"]
    T, N = R.shape
    slow_d = slow.reindex(R.index).ffill()
    fast = resid_rev(P["eps"], 5)
    vol = R.rolling(60).std().to_numpy()
    eps = np.nan_to_num(P["eps"])
    rvar = pd.DataFrame(eps).rolling(60).var().to_numpy()
    dv = (P["px"] * P["vol"]).rolling(21).mean().to_numpy()
    ffc = P["ff"][["mkt_rf", "smb", "hml", "rmw", "cma"]]
    S = pd.get_dummies(core.sectors(R.columns)).astype(float).to_numpy()
    S = S[:, S.sum(0) >= 3]
    opt = Optimiser(N, S, g_trade)
    W = np.zeros((T, N))
    start = slow.dropna(how="all").index[0]
    t0 = R.index.get_indexer([start], method="bfill")[0]
    wprev = np.zeros(N)
    zs = lambda x: np.clip(np.nan_to_num((x - np.nanmean(x)) / (np.nanstd(x) + 1e-12)), -3, 3)
    for t in range(t0, T - 1):
        # Grinold: E[21d return] = IC * sigma_21d * z = IC * sigma_d * sqrt(21) * z -> per day / 21
        a = ic_slow / np.sqrt(H) * vol[t] * zs(slow_d.iloc[t].to_numpy()) + w_fast * ic_fast * vol[t] * zs(fast[t])
        cov = np.cov(ffc.iloc[max(0, t - 251):t + 1].to_numpy().T) + 1e-10 * np.eye(5)
        imp = np.nan_to_num(vol[t] / np.sqrt(np.maximum(dv[t], 1e6)) * 1e3, nan=1.0)
        w = opt.solve(alpha=np.nan_to_num(a), wprev=wprev, Bt=np.nan_to_num(P["B"][t]).T,
                      L=np.linalg.cholesky(cov).T, dsq=np.sqrt(np.nan_to_num(rvar[t], nan=1e-4)), ksq=np.sqrt(imp))
        W[t] = wprev = (w if w is not None else wprev)
    return W


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fund", action="store_true")
    ap.add_argument("--no-opt", action="store_true")
    ap.add_argument("--ic-slow", type=float, default=0.03)
    a = ap.parse_args(argv)
    log = core.Timer()
    P = core.panel()
    R = P["R"]
    me = month_ends(R.index)
    me = [d for d in me if d < R.index[-H - 1]]
    fwd = R.shift(-1).rolling(H).sum().shift(-(H - 1)).loc[me]          # next-21-day excess return
    log("price/volume signals")
    sig = {k: v.loc[me] for k, v in pv_signals(P).items()}
    if not a.no_fund:
        log("EDGAR point-in-time fundamentals")
        sig.update({k: v.loc[me] for k, v in fund_signals(P).items()})
    rev5 = pd.DataFrame(resid_rev(P["eps"], 5), R.index, R.columns).loc[me]
    ev = evaluate(sig, fwd, rev5)
    ev.to_csv(core.RES / "step4_signal_ic.csv", index=False, float_format="%.4f")
    print(ev.to_string(index=False, float_format=lambda x: f"{x:.3f}"), flush=True)

    rows, comps, curves = [], {}, {}
    for m in ("EW", "ICW", "ridge", "LightGBM"):
        log(f"combining: {m}")
        C = neutralise(combine(sig, fwd, m), P)
        comps[m] = C
        ic = rank_cs(C).corrwith(rank_cs(fwd), axis=1).dropna()
        bt = core.backtest(monthly_book(C, P), start=str(C.dropna(how="all").index[0].date()))
        d = core.summarize(bt, f"composite {m} monthly L/S", "s4_alpha", {"method": m})
        d.update(IC=ic.mean(), IC_t=ic.mean() / ic.std() * np.sqrt(len(ic)), IC_2022_26=ic.loc[core.SPLIT:].mean(),
                 corr_with_rev5=rank_cs(C).corrwith(rank_cs(rev5), axis=1).mean())
        rows.append(d)
        curves[f"{m} monthly"] = bt["net"]
    df = core.save(rows, "step4_composites.csv")
    core.show(df)
    print(df[["strategy", "IC", "IC_t", "IC_2022_26", "corr_with_rev5"]].to_string(index=False), flush=True)

    best = max(rows, key=lambda r: r["IC_t"])["params"]
    bm = eval(best)["method"]
    try:
        from ml4t.diagnostic import analyze_signal
        C = comps[bm].stack().rename("factor").reset_index()
        C.columns = ["date", "asset", "factor"]
        prices = P["px"].stack().rename("price").reset_index()
        prices.columns = ["date", "asset", "price"]
        res = analyze_signal(C, prices, periods=(21,))
        (core.RES / "step4_ml4t_analyze_signal.txt").write_text(str(res))
        log("ml4t analyze_signal written")
    except Exception as e:  # noqa: BLE001
        log(f"ml4t analyze_signal skipped: {e}")

    if not a.no_opt:
        orows = []
        # g_trade ~ 1 / expected holding period: slow alpha is held ~1 month -> g of 0.05-0.2
        for w_fast in (0.0, 1.0):
            for g in (0.05, 0.1, 0.2, 0.5):
                log(f"blended optimiser ({bm} composite, fast weight {w_fast}, g_trade {g})")
                W = blended_optimiser(P, comps[bm], w_fast, g)
                bt = core.backtest(W, start=str(comps[bm].dropna(how="all").index[0].date()))
                d = core.summarize(bt, f"optimiser slow={bm} fast_w={w_fast} g={g}", "s4_blend",
                                   {"slow": bm, "w_fast": w_fast, "g_trade": g})
                orows.append(d)
                curves[f"opt fast={w_fast} g={g}"] = bt["net"]
                core.save(orows, "step4_blended_optimiser.csv")
        core.show(pd.DataFrame(orows))
    core.plot(curves, "Step 4: alpha-library composites and slow+fast optimiser (net)", "step4_alpha.png")
    log("done")


if __name__ == "__main__":
    main()
