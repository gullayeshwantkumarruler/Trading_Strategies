"""Strategy 5: Sector ETF momentum with a market-trend-gated short
(Quantpedia, Beluska, Oct 2024, "How to Improve ETF Sector Momentum").

Rules implemented
-----------------
* Universe: 9 SPDR sectors XLB XLE XLF XLI XLK XLP XLU XLV XLY (from Dec-1998);
  11-sector variant adds XLRE (2015) and XLC (2018) once they have 12 months of data.
* Signal at month-end close: 12-month total return (252 trading days).
* Long the top-5 sectors equally (20% each). Short the bottom-1 sector at 25% only when
  the equal-weight sector benchmark (monthly-rebalanced EW index) is below its 12-month
  moving average of month-end values (market-trend gate).
* Executed at the next close, monthly holding; 5 bp per side; long cash at T-bill;
  short proceeds earn nothing extra and pay 25 bp/yr borrow (short cost ~ T-bill as in
  the paper, since the 25% short is financed out of the T-bill sleeve).
* Variants: top-5 long-only, top-5 + gated short (paper's best), top-5 + always-on
  short, top-4 / top-6 + gated short, 11-sector top-5 + gated short.
* This strategy is also run end-to-end through ml4t-backtest's Engine (see ml4t_engine.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import (closes, deflated_sharpe, metrics, month_end_flags, plot_equity, returns,
                    simulate, tbill_daily, trim_start)

SECT9 = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
SECT11 = SECT9 + ["XLRE", "XLC"]
COST_BPS = 5.0


def ew_index(r: pd.DataFrame) -> pd.Series:
    """Monthly-rebalanced equal-weight index level (approx. via daily EW of available)."""
    me = month_end_flags(r.index)
    rf0 = pd.Series(0.0, index=r.index)
    w = r.notna().astype(float)
    w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0).where(me)
    res = simulate(w, r, rf0, cost_bps=0.0, rebal=me, lag=0)
    return (1 + res["ret"]).cumprod(), res


def sector_weights(px: pd.DataFrame, r: pd.DataFrame, top_n=5, short_w=0.25, gate=True):
    me = month_end_flags(px.index)
    mom = (px / px.shift(252) - 1).where(px.notna().cumsum() >= 253)
    lvl, _ = ew_index(r)
    lvl_me = lvl[me]
    sma12 = lvl_me.rolling(12).mean()
    bear = (lvl_me < sma12).reindex(px.index).fillna(False)
    W = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    for d in px.index[me.values]:
        s = mom.loc[d].dropna()
        if len(s) < top_n + 1:
            continue
        w = pd.Series(0.0, index=px.columns)
        w[s.nlargest(top_n).index] = 1.0 / top_n
        if short_w > 0 and (bear[d] if gate else True):
            w[s.idxmin()] -= short_w
        W.loc[d] = w
    return W, me, bear


def run():
    px = closes(SECT11 + ["SPY"], calendar="SPY")
    px = px.loc[px.index >= "1998-12-01"]
    r = returns(px)
    rf = tbill_daily(r.index)
    rows, variants, curves = [], [], {}
    specs = [
        ("9S:top5:LO", SECT9, dict(top_n=5, short_w=0.0)),
        ("9S:top5+short25%(gated)", SECT9, dict(top_n=5, short_w=0.25, gate=True)),
        ("9S:top5+short25%(always)", SECT9, dict(top_n=5, short_w=0.25, gate=False)),
        ("9S:top4+short25%(gated)", SECT9, dict(top_n=4, short_w=0.25, gate=True)),
        ("9S:top6+short25%(gated)", SECT9, dict(top_n=6, short_w=0.25, gate=True)),
        ("11S:top5+short25%(gated)", SECT11, dict(top_n=5, short_w=0.25, gate=True)),
    ]
    start, gate_share = None, None
    for name, uni, kw in specs:
        W, me, bear = sector_weights(px[uni], r[uni], **kw)
        res = trim_start(simulate(W, r[uni], rf, cost_bps=COST_BPS, rebal=me, lag=2))
        if start is None:
            start = res.index[0]
        res = res.loc[res.index >= start]
        if name == "9S:top5+short25%(gated)":
            gate_share = float(bear[me].loc[start:].mean())
        nm = f"Sector:{name}"
        rows.append(metrics(res, rf, nm, "5_SectorMomentum", "US", f"12m mom; monthly; 5bp; {kw}"))
        variants.append(res["ret"].rename(nm))
        curves[name] = res["ret"]
    _, ewres = ew_index(r[SECT9])
    ew = ewres["ret"].loc[start:]
    spy = r["SPY"].loc[start:]
    rows.append(metrics(ew, rf, "Sector:Bench:EW-9 sectors", "5_SectorMomentum", "US", "monthly EW, no cost"))
    rows.append(metrics(spy, rf, "Sector:Bench:SPY", "5_SectorMomentum", "US", "SPY B&H"))
    curves["EW 9 sectors"] = ew
    curves["SPY"] = spy
    plot_equity(curves, "Sector ETF momentum with trend-gated short (SPDR sectors)", "sector_momentum.png")
    dsr = deflated_sharpe(variants, "5_SectorMomentum", rf, bench=ew.rename("EW9"))
    return pd.DataFrame(rows), dsr, {"bear_gate_share": gate_share}


if __name__ == "__main__":
    df, dsr, extra = run()
    pd.set_option("display.width", 250)
    print(df[["strategy", "start", "CAGR", "Vol", "Sharpe", "MaxDD", "Turnover", "IS_Sharpe", "OOS_Sharpe"]]
          .round(3).to_string())
    print(dsr, extra)
