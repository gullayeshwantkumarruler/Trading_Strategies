"""Phase 1 — swing (daily-bar) price-action strategies on US ETFs (report: "Price action strategies by horizon").

Rules are taken as published (no parameter search). Each runs per ETF with two fill conventions (signal-day close =
market-on-close proxy; next-day open) and three cost levels (2 / 6 / 10 bp per side). Development 1993-2015,
sealed holdout 2016-2026 (pullback rule: 2020-2026, per the report).

Evidence-backed (report priorities 1-3):
  rsi2      long when RSI(2) < 10 and Close > SMA200; exit Close > SMA5                      (Connors; EmpiricaLab)
  rsi2_ibs  rsi2 with an extra IBS < 0.2 entry filter
  rsi3_ibs  enter RSI(3) < 10 and IBS <= 0.5; hold while RSI(3) <= 40 and IBS <= 0.5           (Pagonidis 2013)
  pullback  5-day return in the bottom decile of its trailing 252-day distribution and Close > SMA200;
            exit Close > prior High; 10-bar time stop                                          (QuantifiedStrategies)
Popular setups the report found no verifiable support for (tested here to settle it):
  ibs_low   enter IBS < 0.2, exit IBS > 0.8 or 5 bars                                          (Pagonidis daily IBS)
  down3     3 consecutive lower closes and Close > SMA200; exit Close > SMA5                  (Connors)
  nr7       NR7 bar (narrowest range of 7) above SMA200 -> buy-stop at its High next bar; stop at its Low;
            exit after 5 bars
  inside    inside bar above SMA200 -> buy-stop at the mother High; stop at mother Low; exit 5 bars
  engulf    bullish engulfing after a 3-day decline; exit after 5 bars (Caginalp-Laurent-style fixed hold)
  hammer    hammer (lower shadow >= 2x body, close in top third) after a 3-day decline; exit 5 bars
  brk20     Close above prior 20-day High and Close > SMA200; exit Close below 10-day Low
Combined book: equal capital across (rsi2, rsi3_ibs, pullback) x (SPY, QQQ, IWM, DIA, SMH, XLK, MTUM).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import data
import engine as E

UNIVERSE = ["SPY", "QQQ", "IWM", "DIA", "SMH", "XLK", "MTUM", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY"]
CORE = ["SPY", "QQQ", "IWM", "DIA", "SMH", "XLK", "MTUM"]
COSTS = (2.0, 6.0, 10.0)
FILLS = ("close", "next_open")
DEV_END = "2015-12-31"
HOLD = {"pullback": "2020-01-01"}
HOLD_DEFAULT = "2016-01-01"
PPY = 252


def signals(name: str, df: pd.DataFrame) -> pd.DataFrame:
    c, h, l, o = df["Close"], df["High"], df["Low"], df["Open"]
    s200, s5 = E.sma(c, 200), E.sma(c, 5)
    up = c > s200
    S = pd.DataFrame(index=df.index)
    S["exit"] = False
    if name in ("rsi2", "rsi2_ibs"):
        r = E.rsi(c, 2)
        S["entry"] = (r < 10) & up
        if name == "rsi2_ibs":
            S["entry"] &= E.ibs(df) < 0.2
        S["exit"] = c > s5
    elif name == "rsi3_ibs":
        r, ib = E.rsi(c, 3), E.ibs(df)
        S["entry"] = (r < 10) & (ib <= 0.5)
        S["exit"] = ~((r <= 40) & (ib <= 0.5))
    elif name == "pullback":
        r5 = c / c.shift(5) - 1
        q10 = r5.rolling(252, min_periods=200).quantile(0.10)
        S["entry"] = (r5 <= q10) & up
        S["exit"] = c > h.shift(1)
        S["max_hold"] = 10.0
    elif name == "ibs_low":
        ib = E.ibs(df)
        S["entry"] = ib < 0.2
        S["exit"] = ib > 0.8
        S["max_hold"] = 5.0
    elif name == "down3":
        S["entry"] = (c < c.shift(1)) & (c.shift(1) < c.shift(2)) & (c.shift(2) < c.shift(3)) & up
        S["exit"] = c > s5
    elif name in ("nr7", "inside"):
        rng = h - l
        setup = (rng == rng.rolling(7).min()) if name == "nr7" else ((h < h.shift(1)) & (l > l.shift(1)))
        ref_h = h if name == "nr7" else h.shift(1)
        ref_l = l if name == "nr7" else l.shift(1)
        # breakout must trade through the setup high on the NEXT bar: emulate a buy-stop by entering at next
        # bar's open only if that bar's high exceeds the level; the engine fills next_open, so require the
        # breakout bar itself to be known -> entry signal on the breakout bar's close (conservative: we pay the
        # close of the breakout day rather than the stop price)
        brk = (h > ref_h.shift(1)) & setup.shift(1).fillna(False) & up
        S["entry"] = brk
        S["stop"] = ref_l.shift(1)
        S["max_hold"] = 5.0
    elif name == "engulf":
        dec = (c.shift(1) < c.shift(2)) & (c.shift(2) < c.shift(3))
        S["entry"] = dec & (c.shift(1) < o.shift(1)) & (c > o) & (c >= o.shift(1)) & (o <= c.shift(1))
        S["max_hold"] = 5.0
    elif name == "hammer":
        body = (c - o).abs()
        lower = np.minimum(c, o) - l
        dec = (c.shift(1) < c.shift(2)) & (c.shift(2) < c.shift(3))
        S["entry"] = dec & (lower >= 2 * body) & ((c - l) >= 2 / 3 * (h - l)) & ((h - l) > 0)
        S["max_hold"] = 5.0
    elif name == "brk20":
        S["entry"] = (c > h.shift(1).rolling(20).max()) & up
        S["exit"] = c < l.shift(1).rolling(10).min()
    else:
        raise ValueError(name)
    S["entry"] = S["entry"].fillna(False).astype(bool)
    S["exit"] = S["exit"].fillna(False).astype(bool)
    return S


STRATS = ["rsi2", "rsi2_ibs", "rsi3_ibs", "pullback", "ibs_low", "down3", "nr7", "inside", "engulf", "hammer", "brk20"]


def period_metrics(rets, trades, pos, start=None, end=None, cost=2.0):
    r, p = rets.loc[start:end], pos.loc[start:end]
    tr = trades[(trades.entry_time >= (pd.Timestamp(start) if start else trades.entry_time.min())) &
                (trades.entry_time <= (pd.Timestamp(end) if end else trades.entry_time.max()))] if len(trades) else trades
    return E.metrics(r, tr, p, PPY, cost)


def main():
    rows, series = [], {}
    for tk in UNIVERSE:
        df = data.daily(tk)
        bh_full = E.buy_hold(df, PPY)
        for name in STRATS:
            S = signals(name, df)
            hold_start = HOLD.get(name, HOLD_DEFAULT)
            for fill in FILLS:
                for cost in COSTS:
                    tr, rets, pos = E.run(df, S, fill=fill, cost_bps=cost, periods_per_year=PPY)
                    key = f"{name}|{tk}|{fill}|{cost:g}bp"
                    series[key] = rets
                    for per, (a, b) in {"full": (None, None), "dev": (None, DEV_END), "holdout": (hold_start, None)}.items():
                        m = period_metrics(rets, tr, pos, a, b, cost)
                        bh = E.buy_hold(df.loc[a:b], PPY)
                        rows.append(dict(strategy=name, ticker=tk, fill=fill, cost_bps=cost, period=per,
                                         start=str((rets.loc[a:b].index[0]).date()), **m,
                                         BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"], BH_maxDD=bh["maxDD"]))
        print(f"{tk} done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(data.RES / "swing_all.csv", index=False, float_format="%.4f")
    pd.DataFrame(series).to_parquet(data.DATA / "swing_series.parquet")

    # ---- combined book (equal capital, cost 6 bp, next-open and close)
    comb_rows = []
    for fill in FILLS:
        keys = [f"{s}|{t}|{fill}|6bp" for s in ("rsi2", "rsi3_ibs", "pullback") for t in CORE]
        R = pd.DataFrame({k: series[k] for k in keys}).loc["2000-01-01":]
        avail = pd.DataFrame({k: data.daily(k.split("|")[1])["Close"] for k in keys}).reindex(R.index).notna()
        book = (R.where(avail)).mean(axis=1).fillna(0.0)
        pos = (R != 0).any(axis=1).astype(int)
        for per, (a, b) in {"full": (None, None), "dev": (None, DEV_END), "holdout": (HOLD_DEFAULT, None)}.items():
            m = E.metrics(book.loc[a:b], pd.DataFrame(), pos.loc[a:b], PPY, 6.0)
            spy = E.buy_hold(data.daily("SPY").loc[book.loc[a:b].index[0]:b], PPY)
            comb_rows.append(dict(strategy="combined book", fill=fill, period=per, **m, SPY_Sharpe=spy["Sharpe"],
                                  SPY_maxDD=spy["maxDD"], SPY_CAGR=spy["CAGR"]))
        series[f"combined|{fill}|6bp"] = book
    pd.DataFrame(comb_rows).to_csv(data.RES / "swing_combined.csv", index=False, float_format="%.4f")

    # ---- deflated Sharpe over every variant run (full period)
    dsr = E.deflated_sharpe([v.rename(k) for k, v in series.items()], PPY)
    (data.RES / "swing_dsr.json").write_text(json.dumps(dsr, indent=1))
    print(dsr, flush=True)


if __name__ == "__main__":
    main()
