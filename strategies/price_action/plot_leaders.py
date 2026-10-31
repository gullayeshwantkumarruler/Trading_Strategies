"""Equity curves for the leaderboard write-up: daily leaders vs SPY over the 2016-2026 holdout, and the Noise Area
rule (VWAP stop, 1x, $0.001 slippage) on four index ETFs 2016-2026."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import data
import leaderboard as LB

C, _ = LB.load()
spy = data.daily("SPY")["Close"].pct_change().loc["2016":]
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for k in ["hybrid:daa|multi", "hybrid:spy_vt|SPY", "hybrid:jm|SPY", "swing:ibs_low|SPY", "swing:rsi2|SPY",
          "hybrid:ensemble|multi"]:
    r = C[k]["base"].loc["2016":].fillna(0)
    ax[0].plot((1 + r).cumprod(), label=k.split(":")[1], lw=1.2)
ax[0].plot((1 + spy.fillna(0)).cumprod(), "k", lw=2, label="SPY buy & hold")
ax[0].set_title("Daily leaders, holdout 2016-2026 (2 bp/side)")
ax[0].legend(fontsize=8)
for s in LB.pd.Index(["QQQ", "SPY", "IWM", "DIA"]):
    r = C[f"intraday:noise_vwap_1x|{s}"]["base"].fillna(0)
    ax[1].plot((1 + r).cumprod(), label=f"Noise Area + VWAP | {s}")
ax[1].axvline(pd.Timestamp("2023-01-01"), color="grey", ls="--", lw=1)
ax[1].set_title("Intraday Noise Area, 2016-2026 (holdout from 2023, dashed)")
ax[1].legend(fontsize=8)
for a in ax:
    a.set_yscale("log")
    a.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(data.RES / "leaderboard_equity.png", dpi=110)
