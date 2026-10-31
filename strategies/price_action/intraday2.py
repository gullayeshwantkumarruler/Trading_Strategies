"""Phase 4 — intraday hybrids on Alpaca 1-minute SIP bars (report: "Price action hybrid strategies").

  noise_{base,vwap}_{1x,voltarget}   Noise Area ablation (round-5 code) extended to IWM and DIA
  noise_vwap_vix     Noise Area + VWAP stop, traded only when the prior close of VIX is above its expanding median
                     up to that day (walk-forward threshold; the paper reports Sharpe rising with VIX at the open)
  noise_vwap_nr4     traded only on days after an NR4 daily bar (paper: +22 bp average, t = 5.1, in-sample)
  vwap_trend         Zarattini & Aziz VWAP trend: at each minute close long above session VWAP, short below, fill at
                     the next minute's open, flat at 16:00 [bar size / sizing not on the fetched page: 1-minute, 1x]
Costs: $0.0035/share commission + slippage 0.1 / 0.5 / 1 cent per share per side. Splits as round 5
(dev 2016-2022, holdout 2023-2026).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import data
import engine as E
import intraday as I

SYMS = ("SPY", "QQQ", "IWM", "DIA")
SLIPS = (0.001, 0.005, 0.01)


def vix_gate(days) -> np.ndarray:
    vix = data.daily("^VIX")["Close"]
    med = vix.expanding(252).median()
    prev = (vix > med).shift(1)                       # known at the prior close
    return prev.reindex(pd.DatetimeIndex(days)).fillna(False).to_numpy(bool)


def nr4_gate(G) -> np.ndarray:
    rng = pd.Series(np.nanmax(G["High"], 1) - np.nanmin(G["Low"], 1))
    nr4 = rng <= rng.rolling(4).min()
    return nr4.shift(1, fill_value=False).to_numpy(bool)


def vwap_trend(G, s):
    O, C, V, VW = G["Open"], G["Close"], G["Volume"], G["Vwap"]
    vwap = np.cumsum(VW * V, axis=1) / np.maximum(np.cumsum(V, axis=1), 1)
    p = np.zeros_like(C)
    p[:, 1:] = np.sign(C - vwap)[:, :-1]              # decided at the close of minute m-1, filled at the open of m
    prev = np.c_[np.zeros(len(C)), p[:, :-1]]
    prevC = np.c_[O[:, :1], C[:, :-1]]
    gross = prev * (O / prevC - 1) + p * (C / O - 1)  # old position to the fill, new position from the fill
    cost = np.abs(p - prev) * (I.COMM + s) / O
    exit_cost = np.abs(p[:, -1]) * (I.COMM + s) / C[:, -1]   # flat at the 16:00 close
    r = gross.sum(1) - cost.sum(1) - exit_cost
    ntr = (np.abs(p - prev) > 0).sum(1) / 2
    return r, np.where(ntr > 0, r, np.nan), ntr


def main():
    rows, series = [], {}
    for sym in SYMS:
        try:
            G = I.grid(sym)
        except Exception as e:  # noqa: BLE001
            print("skip", sym, e, flush=True)
            continue
        days = G["days"]
        gv, gn = vix_gate(days), nr4_gate(G)
        print(sym, len(days), "VIX-gate days", gv.mean().round(2), "NR4 days", gn.mean().round(2), flush=True)
        for s in SLIPS:
            for ex in ("base", "vwap"):
                for sz in ("1x", "voltarget"):
                    r, t, n = I.noise_area(G, s, ex, sz)
                    o, rs = I.summarize(f"noise_{ex}_{sz}", sym, days, r, t, s, {"trades_per_day": float(n.mean())})
                    rows += o
                    series[f"noise_{ex}_{sz}|{sym}|{s}"] = rs
                    if ex == "vwap":
                        for gname, g in (("vix", gv), ("nr4", gn)):
                            rg = np.where(g, r, 0.0)
                            tg = np.where(g, t, np.nan)
                            o, rs = I.summarize(f"noise_vwap_{sz}_{gname}", sym, days, rg, tg, s,
                                                {"active_days": float(g.mean())})
                            rows += o
                            series[f"noise_vwap_{sz}_{gname}|{sym}|{s}"] = rs
            r, t, n = vwap_trend(G, s)
            o, rs = I.summarize("vwap_trend", sym, days, r, t, s, {"trades_per_day": float(n.mean())})
            rows += o
            series[f"vwap_trend|{sym}|{s}"] = rs
            print(f"  {sym} slippage {s} done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(data.RES / "intraday2_all.csv", index=False, float_format="%.5f")
    pd.DataFrame(series).to_parquet(data.DATA / "intraday2_series.parquet")
    base = {k: v for k, v in series.items() if k.endswith("|0.001")}
    print(json.dumps(E.deflated_sharpe([v.rename(k) for k, v in base.items()], 252), indent=1), flush=True)


if __name__ == "__main__":
    main()
