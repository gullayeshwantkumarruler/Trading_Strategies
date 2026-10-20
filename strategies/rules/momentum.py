"""Strategy 3: Cross-asset / country ETF momentum (Quantpedia, Pauchlyova & Vojtko, Jan 2025,
"Refining ETF Asset Momentum Strategy").

Rules implemented
-----------------
* Score at each month-end close = mean of the 3-, 6-, 9- and 12-month total returns
  (63/126/189/252 trading days). An ETF is eligible once it has 252 days of history.
* Long the top-N ETFs equally weighted; rebalanced monthly; signal at month-end close t,
  executed at close t+1; 5 bp per side; cash earns T-bill.
* Quantpedia variant with selective short: short the bottom-1 ETF at 30% when the
  average pairwise 20-day correlation of the universe exceeds the 250-day average
  pairwise correlation (paper: "short works better when short-term > long-term
  correlation"; exact threshold not published -> simple '>' rule, no tuning).
* Universes
  A. Quantpedia-13: SPY IWM EFA EEM IYR QQQ LQD IEF TIP GLD USO DBC FXE   (top 4)
  B. Country/regional equity ETFs: SPY QQQ IWM EZU VGK EWG EWU EWQ EWJ DXJ FXI MCHI ASHR
     KWEB EWH (top 3), and B+abs: same, but a selected ETF with negative score goes to IEF.
  C. Countries + diversifiers: B + TLT IEF GLD (top 4)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import (closes, deflated_sharpe, metrics, month_end_flags, plot_equity, returns,
                    simulate, tbill_daily, trim_start)

QP13 = ["SPY", "IWM", "EFA", "EEM", "IYR", "QQQ", "LQD", "IEF", "TIP", "GLD", "USO", "DBC", "FXE"]
COUNTRY = ["SPY", "QQQ", "IWM", "EZU", "VGK", "EWG", "EWU", "EWQ", "EWJ", "DXJ", "FXI", "MCHI",
           "ASHR", "KWEB", "EWH"]
DIVERS = ["TLT", "IEF", "GLD"]
COST_BPS = 5.0


def score(px: pd.DataFrame) -> pd.DataFrame:
    s = sum(px / px.shift(n) - 1 for n in (63, 126, 189, 252)) / 4
    return s.where(px.notna().cumsum() >= 253)


def avg_pair_corr(r: pd.DataFrame, win: int) -> pd.Series:
    out = pd.Series(np.nan, index=r.index)
    me = month_end_flags(r.index)
    for d in r.index[me.values]:
        sub = r.loc[:d].tail(win).dropna(axis=1, thresh=int(win * 0.9))
        if sub.shape[1] < 3:
            continue
        c = sub.corr().to_numpy()
        out[d] = c[np.triu_indices_from(c, 1)].mean()
    return out


def momentum_weights(px, r, top_n, short_w=0.0, corr_filter=False, abs_filter_asset=None):
    rank_cols = [c for c in px.columns if c != abs_filter_asset]
    sc = score(px[rank_cols])
    r = r[rank_cols]
    me = month_end_flags(px.index)
    W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    if corr_filter:
        c20, c250 = avg_pair_corr(r, 20), avg_pair_corr(r, 250)
    for d in px.index[me.values]:
        s = sc.loc[d].dropna()
        if len(s) < top_n + 1:
            continue
        top = s.nlargest(top_n).index
        for a in top:
            if abs_filter_asset and s[a] <= 0:
                W.loc[d, abs_filter_asset] += 1.0 / top_n
            else:
                W.loc[d, a] += 1.0 / top_n
        if short_w > 0 and (not corr_filter or (c20[d] > c250[d])):
            W.loc[d, s.idxmin()] -= short_w
    first = W.index[W.abs().sum(axis=1) > 0]
    W = W.where(me, np.nan)
    return W, me, (first[0] if len(first) else None)


def run():
    rows, variants, curves = [], [], {}
    all_t = sorted(set(QP13 + COUNTRY + DIVERS))
    pxa = closes(all_t, calendar="SPY")
    pxa = pxa.loc[pxa.index >= "2000-01-01"]
    ra = returns(pxa)
    rf = tbill_daily(ra.index)
    specs = [
        ("QP13:top4:LO", QP13, dict(top_n=4)),
        ("QP13:top4+short30%(corr-filter)", QP13, dict(top_n=4, short_w=0.3, corr_filter=True)),
        ("QP13:top4+short30%(always)", QP13, dict(top_n=4, short_w=0.3)),
        ("Country:top3:LO", COUNTRY, dict(top_n=3)),
        ("Country:top3:LO+abs(IEF)", COUNTRY + ["IEF"], dict(top_n=3, abs_filter_asset="IEF")),
        ("Country+Div:top4:LO", COUNTRY + DIVERS, dict(top_n=4)),
    ]
    starts = {}
    for name, uni, kw in specs:
        px, r = pxa[uni], ra[uni]
        W, me, st = momentum_weights(px, r, **kw)  # abs-filter asset (IEF) is not ranked
        res = simulate(W, r, rf, cost_bps=COST_BPS, rebal=me, lag=2)
        res = trim_start(res)
        starts[name] = res.index[0]
        nm = f"Mom:{name}"
        rows.append(metrics(res, rf, nm, "3_XAssetMomentum", "Multi",
                            f"avg(3,6,9,12m) score; monthly; 5bp; {kw}"))
        variants.append(res["ret"].rename(nm))
        curves[name] = res["ret"]
    # benchmarks: equal-weight universes, monthly rebalanced
    for bname, uni in [("EW-QP13", QP13), ("EW-Country", COUNTRY)]:
        px, r = pxa[uni], ra[uni]
        me = month_end_flags(px.index)
        w = px.notna().astype(float)
        w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0).where(me)
        st = starts["QP13:top4:LO"] if "QP13" in bname else starts["Country:top3:LO"]
        res = simulate(w, r, rf, cost_bps=COST_BPS, rebal=me, lag=2)
        res = res.loc[res.index >= st]
        rows.append(metrics(res, rf, f"Mom:Bench:{bname}", "3_XAssetMomentum", "Multi",
                            "equal weight available ETFs, monthly"))
        curves[bname] = res["ret"]
    spy = ra["SPY"].loc[ra.index >= starts["QP13:top4:LO"]]
    rows.append(metrics(spy, rf, "Mom:Bench:SPY", "3_XAssetMomentum", "US", "SPY B&H"))
    curves["SPY"] = spy
    plot_equity(curves, "Cross-asset / country ETF momentum (avg 3/6/9/12m)", "xasset_momentum.png")
    dsr = deflated_sharpe(variants, "3_XAssetMomentum", rf, bench=spy.rename("SPY"))
    return pd.DataFrame(rows), dsr, {}


if __name__ == "__main__":
    df, dsr, _ = run()
    pd.set_option("display.width", 250)
    print(df[["strategy", "start", "CAGR", "Vol", "Sharpe", "MaxDD", "Turnover", "IS_Sharpe", "OOS_Sharpe"]]
          .round(3).to_string())
    print(dsr)
