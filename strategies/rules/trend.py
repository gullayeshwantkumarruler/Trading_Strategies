"""Strategy 2: Vol-targeted trend following on a multi-region ETF set
(Sepp & Lucic 2026, "The Science and Practice of Trend-Following Systems", arXiv 2607.19497).

Rules implemented (ETF proxy of the paper's futures systems)
-----------------------------------------------------------
* sigma_t  = EWMA volatility of daily returns, span 33 (lambda = 1 - 2/34), annualised x sqrt(252)
* z_t      = r_t / sigma_{t-1}(daily)        (vol-normalised returns, clipped at +/-5)
* European EWMA system: x_t = cumsum(z) (vol-normalised price); raw_t = EWMA_20(x) - EWMA_250(x)
  (EWMA crossover), divided by its theoretical
  standard deviation under iid unit-variance z  -> S_t, clipped to [-2, 2]
* TSMOM system (L=10, M=10): S_t = sum of the last L*M = 100 z's / sqrt(100), clipped [-2, 2]
  [approximation of the paper's "M periods of L days" aggregation: equal-weighted blocks]
* Asset weight  w_i = S_i * (sigma_target / sqrt(N_t)) / sigma_i   with sigma_target = 10%
* Portfolio vol targeting: scale = 10% / EWMA(63d) realised vol of the unscaled book
  (causal), clipped to [0.25, 3]; gross exposure capped at 2.0x (ETF account, no futures).
* Long-short and long-only (negative signal -> cash) variants; daily or weekly rebalance.
* Signals at close t, executed close t+1, 5 bp per side, cash at T-bill, shorts pay 25 bp/yr.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import (REGION, closes, deflated_sharpe, metrics, plot_equity, returns, simulate,
                    tbill_daily, trim_start)

UNIVERSE = ["SPY", "QQQ", "IWM", "EZU", "VGK", "EWG", "EWU", "EWJ", "DXJ", "FXI", "MCHI",
            "ASHR", "KWEB", "TLT", "IEF", "GLD"]
VOL_SPAN = 33
TARGET = 0.10
COST_BPS = 5.0
GROSS_CAP = 2.0
MIN_HIST = 260


def ewma_std_theory(s1: int, s2: int, n: int = 20000) -> float:
    """Std of EWMA_s1(x) - EWMA_s2(x) for x = cumsum of iid unit-variance z:
    the coefficient on z_{t-k} is (1-a2)^(k+1) - (1-a1)^(k+1)."""
    a1, a2 = 2 / (s1 + 1), 2 / (s2 + 1)
    k = np.arange(n)
    c = (1 - a2) ** (k + 1) - (1 - a1) ** (k + 1)
    return float(np.sqrt((c ** 2).sum()))


def signals(r: pd.DataFrame, kind: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    sig_d = np.sqrt((r ** 2).ewm(span=VOL_SPAN, adjust=False, ignore_na=True).mean())
    z = (r / sig_d.shift(1)).clip(-5, 5)
    if kind == "ewma":
        x = z.fillna(0.0).cumsum().where(z.notna().cumsum() > 0)  # vol-normalised "price"
        raw = x.ewm(span=20, adjust=False, ignore_na=True).mean() - \
              x.ewm(span=250, adjust=False, ignore_na=True).mean()
        S = raw / ewma_std_theory(20, 250)
    elif kind == "tsmom":
        S = z.rolling(100, min_periods=100).sum() / np.sqrt(100)
    else:
        raise ValueError(kind)
    S = S.clip(-2, 2)
    # need a year of history before trading an asset
    S = S.where(r.notna().cumsum() >= MIN_HIST)
    return S, sig_d * np.sqrt(252)


def build_weights(r: pd.DataFrame, kind: str, long_only: bool) -> pd.DataFrame:
    S, vol = signals(r, kind)
    if long_only:
        S = S.clip(lower=0)
    n_active = S.notna().sum(axis=1).replace(0, np.nan)
    w = S.mul(TARGET / np.sqrt(n_active), axis=0) / vol
    w = w.fillna(0.0)
    # causal portfolio-level vol targeting on the pro-forma (unscaled) book
    pro = (w.shift(2) * r.fillna(0)).sum(axis=1)
    pvol = np.sqrt((pro ** 2).ewm(span=63, adjust=False).mean()) * np.sqrt(252)
    scale = (TARGET / pvol.replace(0, np.nan)).clip(0.25, 3.0).fillna(1.0)
    w = w.mul(scale, axis=0)
    gross = w.abs().sum(axis=1)
    w = w.div(np.maximum(gross / GROSS_CAP, 1.0), axis=0)
    return w


def run():
    px = closes(UNIVERSE, calendar="SPY")
    px = px.loc[px.index >= "2002-01-01"]
    r = returns(px)
    rf = tbill_daily(r.index)
    rows, variants, curves = [], [], {}
    weekly = pd.Series(r.index.dayofweek == 4, index=r.index)  # Friday-close signals
    start = None
    contrib_rows = []
    for kind in ["ewma", "tsmom"]:
        for lo in [False, True]:
            w = build_weights(r, kind, lo)
            for freq, rb in [("daily", None), ("weekly", weekly)]:
                res, W = simulate(w, r, rf, cost_bps=COST_BPS, rebal=rb, lag=2, return_weights=True)
                res = trim_start(res)
                start = res.index[0] if start is None else start
                nm = f"Trend:{kind.upper()}:{'LO' if lo else 'LS'}:{freq}"
                rows.append(metrics(res, rf, nm, "2_Trend", "Multi",
                                    f"{kind}; vol span 33; target 10%; gross<=2; 5bp; "
                                    f"{'long-only' if lo else 'long-short'}; {freq}"))
                variants.append(res["ret"].rename(nm))
                if freq == "daily":
                    curves[nm.replace("Trend:", "")] = res["ret"]
                    # P&L contribution per region (gross, annualised)
                    pnl = (W.loc[res.index] * r.loc[res.index].fillna(0))
                    yrs = len(res) / 252
                    by_reg = pnl.T.groupby(lambda c: REGION.get(c, c)).sum().T.sum() / yrs
                    contrib_rows.append({"strategy": nm, **by_reg.round(4).to_dict()})
    # benchmarks
    s0 = start
    ew = r.loc[r.index >= s0]
    eqw = pd.DataFrame(1.0, index=ew.index, columns=r.columns).where(px.loc[ew.index].notna())
    eqw = eqw.div(eqw.sum(axis=1), axis=0)
    me = pd.Series(ew.index.to_series().groupby([ew.index.year, ew.index.month]).transform("max")
                   == ew.index, index=ew.index)
    bench = trim_start(simulate(eqw, ew, rf, cost_bps=COST_BPS, rebal=me, lag=2))
    rows.append(metrics(bench, rf, "Trend:Bench:EW-universe B&H(monthly)", "2_Trend", "Multi",
                        "equal-weight available ETFs, monthly rebalance"))
    spy = r["SPY"].loc[r.index >= s0]
    rows.append(metrics(spy, rf, "Trend:Bench:SPY B&H", "2_Trend", "US", "SPY"))
    w6040 = pd.DataFrame({"SPY": 0.6, "IEF": 0.4}, index=ew.index)
    b6040 = simulate(w6040, r[["SPY", "IEF"]].loc[ew.index], rf, cost_bps=COST_BPS, rebal=me, lag=2)
    rows.append(metrics(b6040, rf, "Trend:Bench:60/40 SPY/IEF", "2_Trend", "Multi", "monthly rebal"))
    curves["EW universe"] = bench["ret"]
    curves["SPY"] = spy
    curves["60/40"] = b6040["ret"]
    plot_equity(curves, "Vol-targeted trend following (Sepp-Lucic ETF proxy), 16 ETFs", "trend.png")
    dsr = deflated_sharpe(variants, "2_Trend", rf, bench=b6040["ret"].rename("60/40"))
    return pd.DataFrame(rows), dsr, {"region_contrib": pd.DataFrame(contrib_rows)}


if __name__ == "__main__":
    df, dsr, extra = run()
    pd.set_option("display.width", 250)
    print(df[["strategy", "start", "CAGR", "Vol", "Sharpe", "MaxDD", "Turnover", "IS_Sharpe", "OOS_Sharpe"]]
          .round(3).to_string())
    print(dsr)
    print(extra["region_contrib"].to_string())
