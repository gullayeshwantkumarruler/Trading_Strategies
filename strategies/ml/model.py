"""Walk-forward model training with purged splits (ml4t-diagnostic splitters).

Splits are generated on the region's array of trading DATES (not panel rows),
then mapped to panel rows, so `label_horizon` is measured in trading days:
  * label y_h uses open[t+1] -> open[t+1+h]  => information up to t+1+h,
    so label_horizon = h + 1 trading days is purged before every test fold.
  * embargo_size = 5 trading days (only matters for CPCV; WF train precedes test).

Outer loop: ml4t.diagnostic.splitters.WalkForwardCV, expanding window,
consecutive ~annual test folds covering 2017-01 -> end of data (OOS).
Inner (in-sample only, 2013-2016): ml4t.diagnostic.splitters.CombinatorialCV
(6 groups, 2 test groups = 15 paths) used once to choose LightGBM n_estimators
from a 3-value grid by mean daily rank IC. The chosen value is then frozen.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge

from features import FEATURES

warnings.filterwarnings("ignore")

OOS_START = pd.Timestamp("2017-01-01")
LGB_BASE = dict(objective="regression", learning_rate=0.03, num_leaves=15,
                min_child_samples=400, subsample=0.7, subsample_freq=1,
                colsample_bytree=0.7, reg_lambda=5.0, n_jobs=-1, verbose=-1,
                random_state=42)
N_EST_GRID = [100, 300, 600]


def date_splits(dates: np.ndarray, horizon: int, years_per_fold: float = 1.0):
    """WalkForwardCV over the unique-date axis -> list of (train_date_idx, test_date_idx)."""
    from ml4t.diagnostic.splitters import WalkForwardCV

    n = len(dates)
    first = int(np.searchsorted(dates, np.datetime64(OOS_START)))
    k = max(1, int(round((n - first) / (252 * years_per_fold))))
    test_size = (n - first) // k
    train0 = n - k * test_size
    cv = WalkForwardCV(n_splits=k, train_size=train0, test_size=test_size,
                       label_horizon=horizon + 1, embargo_size=5,
                       expanding=True, consecutive=True)
    X = np.arange(n).reshape(-1, 1)
    splits = list(cv.split(X))
    # sanity: purge respected
    for tr, te in splits:
        assert tr.max() + horizon + 1 <= te.min(), "purge violated"
    return splits


def daily_ic(pred: np.ndarray, y: np.ndarray, d: np.ndarray) -> float:
    df = pd.DataFrame({"p": pred, "y": y, "d": d}).dropna()
    ics = df.groupby("d").apply(lambda g: g["p"].corr(g["y"], method="spearman") if len(g) > 5 else np.nan)
    return float(ics.mean())


def select_n_estimators(mf: pd.DataFrame, horizon: int) -> tuple[int, dict]:
    """CPCV on the pre-OOS period only."""
    from ml4t.diagnostic.splitters import CombinatorialCV

    ycol = f"y_{horizon}"
    is_df = mf[(mf["date"] < OOS_START) & mf[ycol].notna()]
    udates = np.sort(is_df["date"].unique())
    didx = np.searchsorted(udates, is_df["date"].values)
    cv = CombinatorialCV(n_groups=6, n_test_groups=2, label_horizon=horizon + 1,
                         embargo_size=5, isolate_groups=False)
    scores = {n: [] for n in N_EST_GRID}
    X = is_df[FEATURES].values
    y = is_df[ycol].values
    for tr_d, te_d in cv.split(np.arange(len(udates)).reshape(-1, 1)):
        tr = np.isin(didx, tr_d)
        te = np.isin(didx, te_d)
        m = LGBMRegressor(n_estimators=max(N_EST_GRID), **LGB_BASE).fit(X[tr], y[tr])
        for n in N_EST_GRID:
            p = m.predict(X[te], num_iteration=n)
            scores[n].append(daily_ic(p, y[te], didx[te]))
    mean_scores = {n: float(np.mean(v)) for n, v in scores.items()}
    best = max(mean_scores, key=mean_scores.get)
    return best, mean_scores


def walk_forward_predict(mf: pd.DataFrame, horizon: int, n_est: int) -> tuple[pd.DataFrame, list[dict]]:
    """Strictly out-of-sample predictions for LightGBM and Ridge."""
    ycol = f"y_{horizon}"
    udates = np.sort(mf["date"].unique())
    didx = np.searchsorted(udates, mf["date"].values)
    splits = date_splits(udates, horizon)
    preds, folds = [], []
    X_all = mf[FEATURES].values
    y_all = mf[ycol].values
    for tr_d, te_d in splits:
        tr = np.isin(didx, tr_d) & ~np.isnan(y_all)
        te = np.isin(didx, te_d)
        lgb = LGBMRegressor(n_estimators=n_est, **LGB_BASE).fit(X_all[tr], y_all[tr])
        rdg = Ridge(alpha=10.0).fit(X_all[tr], y_all[tr])
        out = mf.loc[te, ["date", "asset"]].copy()
        out["lgbm"] = lgb.predict(X_all[te])
        out["ridge"] = rdg.predict(X_all[te])
        preds.append(out)
        imp = pd.Series(lgb.booster_.feature_importance("gain"), index=FEATURES)
        folds.append(dict(train_start=pd.Timestamp(udates[tr_d.min()]).date(),
                          train_end=pd.Timestamp(udates[tr_d.max()]).date(),
                          test_start=pd.Timestamp(udates[te_d.min()]).date(),
                          test_end=pd.Timestamp(udates[te_d.max()]).date(),
                          n_train_rows=int(tr.sum()), n_test_rows=int(te.sum()),
                          importance=imp / imp.sum(),
                          ridge_coef=pd.Series(rdg.coef_, index=FEATURES)))
    return pd.concat(preds, ignore_index=True), folds
