"""Strategy 4: Turn-of-the-month on country ETFs / local indices
(QuantSeeker Feb 2025; Etula et al. 2020 [-3:+3]; Lakonishok & Smidt [0:+3]; Kayacetin 2024-26).

Rules implemented
-----------------
* Day 0 = last trading day of the month on the instrument's own calendar.
* [-3:+3]: long from the close of day -4 to the close of day +3 (earns the returns of
  days -3..+3, 7 sessions); otherwise cash at T-bill (USD ETFs) / 0% (local indices).
* [0:+3]:  long from the close of day -1 to the close of day +3 (returns of days 0..+3).
* The window is a calendar rule known in advance -> positions are set directly on the
  holding days (no signal lag needed). 5 bp per side.
* Also reports mean daily return inside vs outside the window with a Welch t-stat.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from common import (REGION, closes, deflated_sharpe, fetch, metrics, plot_equity, returns,
                    simulate, tbill_daily)

ETFS = ["SPY", "QQQ", "IWM", "EZU", "VGK", "EWG", "EWU", "EWQ", "EWJ", "DXJ", "FXI", "MCHI",
        "ASHR", "EWH"]
INDICES = ["^GSPC", "^GDAXI", "^STOXX50E", "^N225", "000300.SS"]
COST_BPS = 5.0
START = pd.Timestamp("2000-01-01")


def tom_position(index: pd.DatetimeIndex, lo: int, hi: int) -> pd.Series:
    """1 on return days whose offset from the month's last trading day is in [lo, hi]."""
    n = len(index)
    s = pd.Series(index, index=index)
    is_last = (s.groupby([index.year, index.month]).transform("max") == s).to_numpy()
    last_pos = np.flatnonzero(is_last)
    pos = np.zeros(n)
    for p in last_pos:
        a, b = max(0, p + lo), min(n - 1, p + hi)
        pos[a:b + 1] = 1.0
    return pd.Series(pos, index=index)


def run():
    rows, variants, region_rows = [], [], []
    curves_etf = {}
    instruments = [(t, "etf") for t in ETFS] + [(t, "index") for t in INDICES]
    for t, kind in instruments:
        if kind == "etf":
            px = closes([t], calendar=t)[t]
        else:
            px = fetch(t)["Close"]
        px = px.loc[px.index >= START - pd.Timedelta(days=10)].dropna()
        r = px.pct_change().loc[px.index >= START].dropna()
        if len(r) < 500:
            continue
        rf = tbill_daily(r.index) if (kind == "etf" or t == "^GSPC") else pd.Series(0.0, index=r.index)
        reg = REGION.get(t, "?")
        bh = r
        rows.append(metrics(bh, rf, f"TOM:{t}:BuyHold", "4_TOM", reg, f"{kind} B&H"))
        for lo, hi in [(-3, 3), (0, 3)]:
            pos = tom_position(r.index, lo, hi)
            res = simulate(pos.to_frame(t), r.to_frame(t), rf, cost_bps=COST_BPS, lag=0)
            nm = f"TOM:{t}:[{lo}:+{hi}]"
            rows.append(metrics(res, rf, nm, "4_TOM", reg, f"{kind}; 5bp; cash={'T-bill' if rf.sum() else '0'}"))
            variants.append(res["ret"].rename(nm))
            inn, out = r[pos == 1], r[pos == 0]
            tt = stats.ttest_ind(inn, out, equal_var=False)
            oos = r.index >= pd.Timestamp("2018-01-01")
            inn2, out2 = r[(pos == 1) & oos], r[(pos == 0) & oos]
            region_rows.append(dict(ticker=t, kind=kind, region=reg, window=f"[{lo}:+{hi}]",
                                    start=r.index[0].date(),
                                    bp_day_in=inn.mean() * 1e4, bp_day_out=out.mean() * 1e4,
                                    t_stat=tt.statistic, p_value=tt.pvalue,
                                    oos_bp_day_in=inn2.mean() * 1e4, oos_bp_day_out=out2.mean() * 1e4,
                                    share_of_days=pos.mean()))
            if kind == "etf" and (lo, hi) == (-3, 3) and t in ("SPY", "EZU", "EWJ", "FXI"):
                curves_etf[f"{t} TOM[-3:+3]"] = res["ret"]
        if kind == "etf" and t in ("SPY", "EZU", "EWJ", "FXI"):
            curves_etf[f"{t} B&H"] = bh
    # equal-weight multi-country TOM portfolio of US-listed ETFs (NYSE calendar)
    px = closes(ETFS, calendar="SPY")
    px = px.loc[px.index >= START - pd.Timedelta(days=10)]
    r = returns(px).loc[lambda x: x.index >= START]
    rf = tbill_daily(r.index)
    pos = tom_position(r.index, -3, 3)
    avail = r.notna().astype(float)
    W = avail.div(avail.sum(axis=1), axis=0).mul(pos, axis=0)
    res = simulate(W, r, rf, cost_bps=COST_BPS, lag=0)
    rows.append(metrics(res, rf, "TOM:EW-14-ETF:[-3:+3]", "4_TOM", "Multi", "equal weight, 5bp"))
    variants.append(res["ret"].rename("TOM:EW-14-ETF:[-3:+3]"))
    ew = avail.div(avail.sum(axis=1), axis=0)
    me = pd.Series(True, index=r.index)
    bh = simulate(ew, r, rf, cost_bps=0.0, rebal=me, lag=0)
    rows.append(metrics(bh, rf, "TOM:EW-14-ETF:BuyHold", "4_TOM", "Multi", "EW daily-rebal, no cost"))
    plot_equity(curves_etf, "Turn-of-month [-3:+3] vs buy & hold (US / Europe / Japan / China ETFs)",
                "tom.png")
    plot_equity({"EW TOM [-3:+3]": res["ret"], "EW buy & hold": bh["ret"]},
                "Turn-of-month, equal-weight 14 country ETFs", "tom_ew.png")
    # DSR: variants trade different instruments/calendars -> use the NYSE-calendar ETF variants
    etf_vars = [v for v in variants if v.name.split(":")[1] in ETFS + ["EW-14-ETF"]]
    dsr = deflated_sharpe(etf_vars, "4_TOM", tbill_daily(pd.DatetimeIndex(sorted(set().union(*[v.index for v in etf_vars])))))
    return pd.DataFrame(rows), dsr, {"tom_stats": pd.DataFrame(region_rows)}


if __name__ == "__main__":
    df, dsr, extra = run()
    pd.set_option("display.width", 250)
    print(df[["strategy", "region", "start", "CAGR", "Vol", "Sharpe", "MaxDD", "Turnover", "IS_Sharpe", "OOS_Sharpe"]]
          .round(3).to_string())
    print(extra["tom_stats"].round(3).to_string())
    print(dsr)
