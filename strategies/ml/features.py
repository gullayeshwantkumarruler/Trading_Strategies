"""Price/volume features and labels (no look-ahead).

All features for date t use information up to and including the CLOSE of t.
Labels are forward returns measured from the OPEN of t+1 (the first price at
which a signal computed at the close of t can be traded) to the OPEN of t+1+h.

Feature computation: ml4t-engineer `compute_features` is used for RSI(14),
realized volatility (21d), downside deviation (63d); everything else in pandas
(lagged returns, residual returns, MAX, Amihud with true traded value, volume
z-scores, 52w-high distance). Amihud is computed in pandas because the
ml4t-engineer version uses close*volume, which is wrong for back-adjusted
(hfq) China prices; we use the traded `amount` instead.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl

LAGS = [1, 5, 10, 21, 63, 126, 252]
HORIZONS = [5, 21]

FEATURES = (
    [f"r_{k}" for k in LAGS]
    + ["mom_12_1", "resid_5", "resid_21", "resid_63", "beta_252",
       "vol_21", "vol_63", "dvol_63", "max_21", "min_21", "amihud_21",
       "volz_21", "volz_5", "turn_21", "dist_52w_high", "rsi_14", "gap_1"]
)


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """RSI, realized vol and downside deviation via ml4t-engineer (per asset)."""
    from ml4t.engineer import compute_features

    pdf = pl.from_pandas(df[["date", "asset", "open", "high", "low", "close", "volume", "ret1"]])
    pdf = pdf.rename({"date": "timestamp", "ret1": "returns"})
    out = compute_features(
        pdf,
        [
            {"name": "rsi", "params": {"period": 14}},
            {"name": "realized_volatility", "params": {"period": 21, "annualize": False}},
            {"name": "downside_deviation", "params": {"window": 63}},
        ],
        group_col="asset",
        timestamp_col="timestamp",
    )
    out = out.select(
        pl.col("timestamp").alias("date"), "asset",
        pl.col("rsi").alias("rsi_14"),
        pl.col("realized_volatility").alias("vol_21"),
        pl.col("downside_deviation").alias("dvol_63"),
    ).to_pandas()
    return out


def build_panel(px: pd.DataFrame) -> pd.DataFrame:
    """Return long panel with raw features, labels and helper columns."""
    df = px.sort_values(["asset", "date"]).reset_index(drop=True).copy()
    g = df.groupby("asset", sort=False)
    df["ret1"] = g["close"].pct_change(fill_method=None).clip(-0.5, 0.5)
    for k in LAGS:
        df[f"r_{k}"] = g["close"].pct_change(k, fill_method=None)
    df["mom_12_1"] = g["close"].shift(21) / g["close"].shift(252) - 1
    df["gap_1"] = df["open"] / g["close"].shift(1) - 1  # overnight gap of day t

    # market (equal-weight region) return and rolling beta -> residual returns
    mkt = df.groupby("date")["ret1"].mean().rename("mkt")
    df = df.join(mkt, on="date")
    g = df.groupby("asset", sort=False)
    cov = g[["ret1", "mkt"]].apply(
        lambda x: x["ret1"].rolling(252, min_periods=126).cov(x["mkt"])).reset_index(level=0, drop=True)
    var = g["mkt"].transform(lambda s: s.rolling(252, min_periods=126).var())
    df["beta_252"] = cov.sort_index() / var
    beta_lag = df.groupby("asset", sort=False)["beta_252"].shift(1)
    df["resid1"] = df["ret1"] - beta_lag.fillna(1.0) * df["mkt"]
    g = df.groupby("asset", sort=False)
    for k in (5, 21, 63):
        df[f"resid_{k}"] = g["resid1"].transform(lambda s: s.rolling(k, min_periods=k).sum())

    df["vol_63"] = g["ret1"].transform(lambda s: s.rolling(63, min_periods=42).std())
    df["max_21"] = g["ret1"].transform(lambda s: s.rolling(21, min_periods=21).max())
    df["min_21"] = g["ret1"].transform(lambda s: s.rolling(21, min_periods=21).min())
    amt = df["amount"].where(df["amount"] > 0)
    df["illiq_d"] = df["ret1"].abs() / amt * 1e9
    g = df.groupby("asset", sort=False)
    df["amihud_21"] = np.log1p(g["illiq_d"].transform(lambda s: s.rolling(21, min_periods=15).mean()))
    lv = np.log1p(df["volume"].astype(float))
    df["lvol"] = lv
    g = df.groupby("asset", sort=False)
    m252 = g["lvol"].transform(lambda s: s.rolling(252, min_periods=126).mean())
    s252 = g["lvol"].transform(lambda s: s.rolling(252, min_periods=126).std())
    df["volz_21"] = (g["lvol"].transform(lambda s: s.rolling(21, min_periods=15).mean()) - m252) / s252
    df["volz_5"] = (g["lvol"].transform(lambda s: s.rolling(5, min_periods=5).mean()) - m252) / s252
    df["turn_21"] = g["turnover"].transform(lambda s: s.rolling(21, min_periods=15).mean())
    df["dist_52w_high"] = df["close"] / g["close"].transform(lambda s: s.rolling(252, min_periods=126).max()) - 1

    eng = _engineer_features(df)
    df = df.merge(eng, on=["date", "asset"], how="left")
    g = df.groupby("asset", sort=False)

    # Labels: from open of t+1 to open of t+1+h
    o_next = g["open"].shift(-1)
    for h in HORIZONS:
        df[f"fwd_{h}"] = (g["open"].shift(-1 - h) / o_next - 1).clip(-0.6, 1.5)
    df["fwd_1"] = g["open"].shift(-2) / o_next - 1  # next trading day open->open
    df["hist_ok"] = g.cumcount() >= 252  # need a year of history
    return df


def rank_cs(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Cross-sectional percentile rank per date, centred to [-0.5, 0.5]; NaN -> 0."""
    r = df.groupby("date")[cols].rank(pct=True) - 0.5
    return r.fillna(0.0)


def make_model_frame(px: pd.DataFrame) -> pd.DataFrame:
    panel = build_panel(px)
    panel = panel[panel["hist_ok"]].copy()
    X = rank_cs(panel, FEATURES)
    out = panel[["date", "asset", "open", "close", "ret1", "mkt", "amount"] + [f"fwd_{h}" for h in HORIZONS] + ["fwd_1"]].copy()
    out[FEATURES] = X.values
    for h in HORIZONS:
        lab = panel.groupby("date")[f"fwd_{h}"].rank(pct=True) - 0.5
        out[f"y_{h}"] = lab.values  # NaN where forward return unknown
    out["raw_r_5"] = panel["r_5"].values
    out["raw_resid_5"] = panel["resid_5"].values
    out["raw_r_21"] = panel["r_21"].values
    return out.reset_index(drop=True)
