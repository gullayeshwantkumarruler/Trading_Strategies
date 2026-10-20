"""Paper 3 — Le Grice (2026), "Tabular Deep Learning for Algorithmic Trading: Cross-Regime Bayesian
Optimisation for Equity Signal Generation", arXiv:2608.27076. No code released.

Faithful to the paper:
  * ~300 large-cap S&P 500 stocks, 2015-2025 (+ 2026 YTD as an extra, truly unseen year)
  * target: next-day log return ranked cross-sectionally; top decile = long (2), bottom = short (0), else hold (1)
  * RobustScaler fitted on each training fold; balanced class weights
  * models: Logistic regression, XGBoost, TabNet; Hybrid = rank-average of XGBoost & TabNet long/short probabilities
  * cross-regime Bayesian optimisation (Optuna TPE) over validation folds 2022, 2023, 2024 (expanding
    train from 2015, 1-day purge), objective = paper eq. (2): 0.4 r/0.15 + 0.4 s/1.5 - 0.2 d/0.10
    minus quadratic penalties for any negative fold / drawdown > 15% and a hard floor at -20%;
    portfolio size n tuned jointly
  * portfolio: top-n by P(long) long, top-n by P(short) short, equal weight, 50/50 dollar neutral,
    daily rebalance at the close, 2.2 bp per leg per trade
  * final model retrained on 2015-2024, evaluated on 2025 (paper's OOS year) and 2026 YTD

Deviations (data the paper licensed from Bloomberg / Google is not free):
  * no fundamentals, analyst ratings, news sentiment or Google Trends; features are price/volume
    technicals expressed in relative terms + FRED macro (VIX regime, curve slope, 10y, credit spread,
    core inflation, unemployment trend; monthly series lagged one month for publication)
  * Optuna budget: XGB_TRIALS for XGBoost, TAB_TRIALS for TabNet (paper's budget not stated)
  * the paper trades at the close with features from a pre-close snapshot; we use the close itself
    (same assumption the paper makes for execution). A stricter 1-day-lag variant is also reported.
"""
from __future__ import annotations

import argparse
import json
import warnings

import numpy as np
import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler
from xgboost import XGBClassifier

from common import ANN, DATA_DIR, RES_DIR, fred, plot_equity, save_rows, sp500_universe, stock_panel

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

N_STOCKS = 300
COST = 0.00022
FOLDS = [2022, 2023, 2024]
XGB_TRIALS, TAB_TRIALS = 16, 4
SEED = 7


# ----------------------------------------------------------------------------- features
def build_panel():
    p = DATA_DIR / "p3_panel.parquet"
    if p.exists():
        return pd.read_parquet(p)
    u = sp500_universe(350)
    px, vol = stock_panel(u)
    dv = (px * vol).loc["2015":"2024"].median().sort_values(ascending=False)
    u = dv.index[:N_STOCKS].tolist()
    px, vol = px[u].loc["2013":], vol[u].loc["2013":]
    r = px.pct_change(fill_method=None)
    lr = np.log(px).diff()

    def rank(df):
        return df.rank(axis=1, pct=True)

    f = {}
    f["ret_rank_1d"] = rank(r)
    for h in [5, 21, 63, 126, 252]:
        f[f"mom_{h}d_rank"] = rank(px.pct_change(h, fill_method=None))
    f["dist_52w_high"] = px / px.rolling(252, min_periods=200).max() - 1
    f["dist_50d_ma"] = px / px.rolling(50).mean() - 1
    d = px.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / 14).mean(), (-d.clip(upper=0)).ewm(alpha=1 / 14).mean()
    rsi = 100 - 100 / (1 + up / dn)
    f["rsi14"] = rsi
    f["rel_rsi"] = rsi.sub(rsi.mean(axis=1), axis=0)
    f["rel_volume"] = vol / vol.rolling(20).mean()
    f["vol_5d"] = r.rolling(5).std()
    f["vol_21d"] = r.rolling(21).std()
    f["vol_ratio_5_63"] = r.rolling(5).std() / r.rolling(63).std()
    ma20, sd20 = px.rolling(20).mean(), px.rolling(20).std()
    f["bb_width"] = 4 * sd20 / ma20
    f["bb_pos"] = (px - ma20) / (2 * sd20)
    ema12, ema26 = px.ewm(span=12).mean(), px.ewm(span=26).mean()
    macd = ema12 - ema26
    f["macd_hist_norm"] = (macd - macd.ewm(span=9).mean()) / px
    mkt = r.mean(axis=1)
    beta = r.rolling(63).cov(mkt).div(mkt.rolling(63).var(), axis=0)
    f["beta_63d"] = beta
    f["resid_ret_5d"] = (r - beta.mul(mkt, axis=0)).rolling(5).sum()
    f["amihud_rank"] = rank((r.abs() / (px * vol)).rolling(21).mean())
    f["dollar_vol_rank"] = rank((px * vol).rolling(21).mean())
    f["max_ret_21d"] = r.rolling(21).max()

    long = pd.concat({k: v.stack(future_stack=True) for k, v in f.items()}, axis=1)
    long.index.names = ["date", "ticker"]
    # label: next-day log return decile
    nxt = lr.shift(-1)
    nrank = rank(nxt)
    long["fwd_lr"] = nxt.stack(future_stack=True)
    long["fwd_lr_2"] = lr.shift(-2).stack(future_stack=True)        # for the 1-day-lag variant
    long["y"] = np.select([nrank.stack(future_stack=True) > 0.9, nrank.stack(future_stack=True) < 0.1], [2, 0], 1)
    long.loc[long["fwd_lr"].isna(), "y"] = -1

    # macro (market-wide) features
    cal = px.index
    def ff(s, lag_days=0):
        s = s.copy()
        s.index = s.index + pd.Timedelta(lag_days, "D")
        return s.reindex(cal.union(s.index)).ffill().reindex(cal)
    vix = ff(fred("VIXCLS"))
    m = pd.DataFrame(index=cal)
    m["vix_regime"] = (vix.rolling(252, min_periods=126).rank(pct=True) > 0.75).astype(float)
    m["vix_pct_1y"] = vix.rolling(252, min_periods=126).rank(pct=True)
    m["curve_10y2y"] = ff(fred("T10Y2Y"))
    m["y10"] = ff(fred("DGS10"))
    m["credit_baa10y"] = ff(fred("BAA10Y"))
    cpi = fred("CPILFESL")
    m["core_infl_yoy"] = ff(cpi.pct_change(12), lag_days=45)          # published ~mid next month
    un = fred("UNRATE")
    m["unemp_trend"] = ff(un.diff(3), lag_days=35)
    long = long.join(m, on="date")
    long = long.loc["2014-01-01":]
    long.to_parquet(p)
    return long


FEATS = None


def feat_cols(df):
    return [c for c in df.columns if c not in ("fwd_lr", "fwd_lr_2", "y")]


# ----------------------------------------------------------------------------- portfolio
def portfolio(pred: pd.DataFrame, n: int, ret_col="fwd_lr", cost=COST):
    """pred: index (date,ticker) with p_long, p_short, fwd returns. Equal weight, dollar neutral,
    daily rebalance; cost per leg per unit of weight traded."""
    rows = []
    prev = pd.Series(dtype=float)
    for d, g in pred.groupby(level="date"):
        g = g.droplevel("date")
        L = g["p_long"].nlargest(n).index
        Sx = g["p_short"].nlargest(n).index
        both = L.intersection(Sx)
        L, Sx = L.difference(both), Sx.difference(both)
        w = pd.Series(0.0, index=g.index)
        if len(L):
            w[L] = 0.5 / len(L)
        if len(Sx):
            w[Sx] = -0.5 / len(Sx)
        idx = w.index.union(prev.index)
        to = (w.reindex(idx, fill_value=0) - prev.reindex(idx, fill_value=0)).abs().sum()
        simple = np.expm1(g[ret_col].fillna(0.0))
        gross = float((w * simple).sum())
        rows.append((d, gross - cost * to, gross, to))
        # drift weights to next close
        prev = w * (1 + simple)
    out = pd.DataFrame(rows, columns=["date", "ret", "gross", "turnover"]).set_index("date")
    return out


def perf(r: pd.Series):
    if len(r) < 5 or r.std() == 0:
        return dict(ann_ret=np.nan, sharpe=np.nan, mdd=np.nan)
    eq = (1 + r).cumprod()
    ann = eq.iloc[-1] ** (ANN / len(r)) - 1
    return dict(ann_ret=ann, sharpe=r.mean() / r.std() * np.sqrt(ANN), mdd=-(eq / eq.cummax() - 1).min())


def paper_score(fold_perf: list[dict]):
    r = np.array([p["ann_ret"] for p in fold_perf])
    s = np.array([p["sharpe"] for p in fold_perf])
    d = np.array([p["mdd"] for p in fold_perf])
    if np.isnan(r).any():
        return -1e9
    base = 0.4 * r.mean() / 0.15 + 0.4 * s.mean() / 1.5 - 0.2 * d.mean() / 0.10
    Pr = 1.5 * (np.max(np.abs(np.minimum(0, r))) / 0.15) ** 2
    Ps = 1.5 * (np.max(np.abs(np.minimum(0, s))) / 1.5) ** 2
    Pd = 1.0 * (np.max(np.maximum(0, d - 0.15)) / 0.15) ** 2
    Pf = 10.0 if (r < -0.20).any() else 0.0
    return base - (Pr + Ps + Pd + Pf)


# ----------------------------------------------------------------------------- models
def class_weights(y):
    cnt = np.bincount(y, minlength=3).astype(float)
    w = len(y) / (3 * np.maximum(cnt, 1))
    return w[y]


def split(df, train_end_year, test_year):
    tr = df[(df.index.get_level_values("date").year >= 2015) &
            (df.index.get_level_values("date").year <= train_end_year) & (df.y >= 0)]
    te = df[df.index.get_level_values("date").year == test_year]
    last = tr.index.get_level_values("date").max()
    tr = tr[tr.index.get_level_values("date") < last]          # purge last row (label spans into test)
    return tr, te


def fit_xgb(tr, params):
    cols = FEATS
    sc = RobustScaler().fit(tr[cols].fillna(0.0))
    X = np.clip(sc.transform(tr[cols].fillna(0.0)), -10, 10)
    y = tr["y"].to_numpy().astype(int)
    n = len(X)
    cut = int(n * 0.9)                                          # time-ordered early-stopping slice
    m = XGBClassifier(objective="multi:softprob", num_class=3, tree_method="hist", n_jobs=-1,
                      eval_metric="mlogloss", early_stopping_rounds=30, random_state=SEED,
                      n_estimators=params["n_estimators"], learning_rate=params["learning_rate"],
                      max_depth=params["max_depth"], min_child_weight=params["min_child_weight"],
                      gamma=params["gamma"], reg_lambda=params["reg_lambda"], reg_alpha=params["reg_alpha"],
                      subsample=params["subsample"], colsample_bytree=params["colsample_bytree"])
    m.fit(X[:cut], y[:cut], sample_weight=class_weights(y[:cut]),
          eval_set=[(X[cut:], y[cut:])], sample_weight_eval_set=[class_weights(y[cut:])], verbose=False)
    return lambda d: m.predict_proba(np.clip(sc.transform(d[cols].fillna(0.0)), -10, 10))


def fit_tabnet(tr, params):
    import torch
    from pytorch_tabnet.tab_model import TabNetClassifier
    torch.manual_seed(SEED)
    cols = FEATS
    sc = RobustScaler().fit(tr[cols].fillna(0.0))
    X = np.clip(sc.transform(tr[cols].fillna(0.0)), -10, 10).astype(np.float32)
    y = tr["y"].to_numpy().astype(int)
    cut = int(len(X) * 0.9)
    m = TabNetClassifier(n_d=params["nd"], n_a=params["nd"], n_steps=params["steps"], gamma=params["gamma"],
                         optimizer_fn=torch.optim.AdamW,
                         optimizer_params=dict(lr=params["lr"], weight_decay=params["wd"]),
                         # paper: ReduceLROnPlateau; pytorch-tabnet 4.1 cannot pass the metric to it,
                         # so a step decay (x0.5 every 4 epochs) is used instead
                         scheduler_fn=torch.optim.lr_scheduler.StepLR,
                         scheduler_params=dict(step_size=4, gamma=0.5),
                         seed=SEED, verbose=0, device_name="cpu")
    m.fit(X[:cut], y[:cut], eval_set=[(X[cut:], y[cut:])], eval_metric=["logloss"], weights=1,
          max_epochs=params.get("max_epochs", 15), patience=4, batch_size=params["batch"],
          virtual_batch_size=256, drop_last=False)
    return lambda d: m.predict_proba(np.clip(sc.transform(d[cols].fillna(0.0)), -10, 10).astype(np.float32))


def fit_lr(tr, params):
    cols = FEATS
    sc = RobustScaler().fit(tr[cols].fillna(0.0))
    X = np.clip(sc.transform(tr[cols].fillna(0.0)), -10, 10)
    y = tr["y"].to_numpy().astype(int)
    m = LogisticRegression(C=params["C"], class_weight="balanced", max_iter=300)
    m.fit(X, y)
    return lambda d: m.predict_proba(np.clip(sc.transform(d[cols].fillna(0.0)), -10, 10))


def predict(fitter, tr, te, params):
    f = fitter(tr, params)
    P = f(te)
    out = te[["fwd_lr", "fwd_lr_2"]].copy()
    out["p_short"], out["p_long"] = P[:, 0], P[:, 2]
    return out


def xgb_space(t):
    return dict(n_estimators=t.suggest_int("n_estimators", 1000, 1300),
                learning_rate=t.suggest_float("learning_rate", 0.005, 0.1, log=True),
                max_depth=t.suggest_int("max_depth", 3, 5),
                min_child_weight=t.suggest_int("min_child_weight", 15, 50),
                gamma=t.suggest_float("gamma", 0.5, 2.0), reg_lambda=t.suggest_float("reg_lambda", 0.5, 3.0),
                reg_alpha=t.suggest_float("reg_alpha", 1.0, 2.0), subsample=t.suggest_float("subsample", 0.7, 1.0),
                colsample_bytree=t.suggest_float("colsample_bytree", 0.5, 1.0))


def tab_space(t):
    return dict(nd=t.suggest_categorical("nd", [8, 16, 32]), steps=t.suggest_categorical("steps", [3, 4]),
                gamma=t.suggest_float("gamma", 1.0, 2.0), lr=t.suggest_float("lr", 5e-4, 1e-2, log=True),
                batch=t.suggest_categorical("batch", [4096, 8192]), wd=t.suggest_float("wd", 1e-5, 1e-3, log=True))


def cross_regime_search(df, name, fitter, space, n_trials):
    cache = RES_DIR / f"p3_best_{name}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    preds_cache = {}

    def objective(t):
        params = space(t)
        n = t.suggest_int("n", 5, 30)
        key = json.dumps({k: v for k, v in params.items()}, sort_keys=True)
        if key not in preds_cache:
            preds_cache[key] = [predict(fitter, *split(df, y - 1, y), params) for y in FOLDS]
        fp = [perf(portfolio(p, n)["ret"]) for p in preds_cache[key]]
        t.set_user_attr("folds", fp)
        return paper_score(fp)

    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    st.optimize(objective, n_trials=n_trials)
    best = dict(st.best_trial.params, score=st.best_value, folds=st.best_trial.user_attrs["folds"])
    cache.write_text(json.dumps(best, indent=1, default=float))
    return best


def strip(best, keys):
    return {k: best[k] for k in keys if k in best}


def main(argv=None):
    global FEATS
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tabnet", action="store_true")
    a = ap.parse_args(argv)
    df = build_panel()
    FEATS = feat_cols(df)
    print("panel", df.shape, "features", len(FEATS))

    bx = cross_regime_search(df, "xgb", fit_xgb, xgb_space, XGB_TRIALS)
    print("XGB best", {k: bx[k] for k in ("score", "n")}, bx["folds"])
    bl = cross_regime_search(df, "lr", fit_lr, lambda t: dict(C=t.suggest_float("C", 1e-5, 1e4, log=True)), 10)
    print("LR best", {k: bl[k] for k in ("score", "n")})
    models = {"LogReg": (fit_lr, strip(bl, ["C"]), bl["n"]),
              "XGBoost": (fit_xgb, strip(bx, ["n_estimators", "learning_rate", "max_depth", "min_child_weight",
                                              "gamma", "reg_lambda", "reg_alpha", "subsample", "colsample_bytree"]), bx["n"])}
    if not a.no_tabnet:
        bt = cross_regime_search(df, "tabnet", fit_tabnet, tab_space, TAB_TRIALS)
        print("TabNet best", {k: bt[k] for k in ("score", "n")}, bt["folds"])
        models["TabNet"] = (fit_tabnet, strip(bt, ["nd", "steps", "gamma", "lr", "batch", "wd"]), bt["n"])

    rows, curves = [], {}
    # validation-fold performance of the hybrid (selection-period numbers, like the paper's Table 2)
    # 2022-24: validation folds (expanding train). 2025 and 2026: the paper's final model,
    # trained once on 2015-2024 and frozen (2026 YTD was never seen by the paper's author either).
    for test_year, train_end in [(2022, 2021), (2023, 2022), (2024, 2023), (2025, 2024), (2026, 2024)]:
        oos = test_year >= 2025
        preds = {}
        for name, (fitter, params, n) in models.items():
            tr, te = split(df, train_end, test_year)
            preds[name] = (predict(fitter, tr, te, params), n)
        if "TabNet" in preds:
            px_, nx = preds["XGBoost"]
            pt_, nt = preds["TabNet"]
            hy = px_.copy()
            g = hy.groupby(level="date")
            hy["p_long"] = (g["p_long"].rank(pct=True) + pt_.groupby(level="date")["p_long"].rank(pct=True)) / 2
            hy["p_short"] = (g["p_short"].rank(pct=True) + pt_.groupby(level="date")["p_short"].rank(pct=True)) / 2
            preds["Hybrid"] = (hy, int((nx + nt) / 2))
        for name, (p, n) in preds.items():
            for variant, col, cost in [("MOC t (paper)", "fwd_lr", COST), ("MOC t, 5bp", "fwd_lr", 0.0005),
                                       ("1-day lag", "fwd_lr_2", COST)]:
                pf = portfolio(p, n, ret_col=col, cost=cost)
                pr = perf(pf["ret"])
                prec_l = (p.join(df["y"]).groupby(level="date").apply(
                    lambda g: (g.nlargest(n, "p_long")["y"] == 2).mean())).mean()
                rows.append(dict(model=name, year=test_year, sample="OOS" if oos else "validation",
                                 variant=variant, n=n, ann_ret=pr["ann_ret"], sharpe=pr["sharpe"],
                                 mdd=-pr["mdd"], gross_ann=perf(pf["gross"])["ann_ret"],
                                 turnover_daily=pf["turnover"].mean(), long_precision=prec_l))
                if variant == "MOC t (paper)" and oos:
                    curves[f"{name} {test_year}"] = pf["ret"]
        print(pd.DataFrame(rows).query("year == @test_year and variant == 'MOC t (paper)'")
              [["model", "ann_ret", "sharpe", "mdd", "turnover_daily", "long_precision"]].to_string(index=False))
    df_out = save_rows(rows, "p3_metrics.csv")
    spy = np.log(px_close_spy()).diff()
    for y in (2025, 2026):
        c = {k: v for k, v in curves.items() if k.endswith(str(y))}
        c["SPY"] = np.expm1(spy.loc[str(y)])
        plot_equity(c, f"Paper 3: tabular models, {y} out-of-sample (US 300, long-short)", f"p3_oos_{y}.png", logy=False)
    return df_out


def px_close_spy():
    from common import fetch
    return fetch("SPY")["Close"]


if __name__ == "__main__":
    main()
