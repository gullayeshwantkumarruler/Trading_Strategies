"""Phase 3 — positional (weekly / monthly) price-action strategies (report: "Price action strategies by horizon").

  faber       Faber 10-month SMA: at each monthly decision day hold if Close > SMA of the last 10 monthly closes,
              else cash (0%). Fills next open, 5 bp/side. Timing luck: all 21 trading-day offsets in the month.
              Assets SPY QQQ IWM EFA TLT GLD VNQ + a 5-ETF GTAA (SPY EFA IEF VNQ DBC, equal weight).
  wk_cross    weekly 10/40-week SMA cross (weekly golden cross), long/flat, next weekly open, 5 bp
  wk_sma43    weekly close vs 43-week SMA, long/flat
  donchian    weekly Donchian: enter on a close above the prior 20-week high, exit on a close below the prior
              10-week low (Turtle-style, long only)
  ath_atr     Zarattini, Pagani & Wilcox (2025): enter when the daily close makes a new all-time high (data
              start), exit on a trailing stop at ATH x (1 - 10 x ATR42 / Close); next-open fills; 0.5% round trip
              (25 bp/side); also a weekly-bar variant. ~40 ETFs (no survivorship issue), then current S&P 500
              members (survivorship-biased, close-only ATR proxy) as a labelled comparison.
  rs_rotation monthly: hold the 3 SPDR sector ETFs with the highest 26-week return (equal weight)
  hi52_rank   monthly: hold the 3 sector/country ETFs closest to their 52-week high (George-Hwang ranking)
Holdout: 2013-2026 for the trend filters, 2015-2026 for ath_atr (as the report specifies).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import data
import engine as E

ETF40 = ["SPY", "QQQ", "IWM", "DIA", "MDY", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLRE",
         "XLC", "SMH", "IBB", "XBI", "KRE", "XHB", "ITB", "XRT", "EFA", "EEM", "EWJ", "EWG", "EWU", "EWZ", "FXI",
         "INDA", "TLT", "IEF", "LQD", "HYG", "GLD", "SLV", "DBC", "VNQ", "MTUM", "QUAL", "USMV"]
SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
COUNTRY_SECTOR = SECTORS + ["EFA", "EEM", "EWJ", "EWG", "EWU", "EWZ", "FXI", "QQQ", "IWM", "SMH"]
PPY_D, PPY_W = 252, 52


def faber_series(df: pd.DataFrame, offset: int, cost=5.0) -> tuple[pd.Series, pd.Series]:
    """Daily returns of the Faber rule deciding on the `offset`-th trading day of each month."""
    c = df["Close"]
    idx = c.index
    grp = pd.Series(np.arange(len(idx)), idx).groupby([idx.year, idx.month])
    dec = [g.iloc[min(offset, len(g) - 1)] for _, g in grp]
    dec_dates = idx[dec]
    mon = c.loc[dec_dates]
    hold = (mon > mon.rolling(10).mean()).astype(float)
    pos = hold.reindex(idx).ffill().shift(1).fillna(0.0)             # decided at close, effective from next open
    o = df["Open"]
    ret_cc = c.pct_change().fillna(0.0)
    ret_on = (c / o - 1)                                              # open->close on the switch-on day
    r = pos * ret_cc
    switch = pos.diff().fillna(pos)
    r = r.where(switch <= 0, pos * ret_on)                           # buy at next open: earn only open->close
    exit_day = switch < 0
    r = r.where(~exit_day, (o / c.shift(1) - 1).fillna(0.0))         # sell at next open: earn close->open
    r -= switch.abs() * cost / 1e4
    return r, (pos > 0).astype(int)


def wk_signals(name, w: pd.DataFrame) -> pd.DataFrame:
    c = w["Close"]
    S = pd.DataFrame(index=w.index)
    if name == "wk_cross":
        a, b = c.rolling(10).mean(), c.rolling(40).mean()
        S["entry"], S["exit"] = a > b, a < b
    elif name == "wk_sma43":
        m = c.rolling(43).mean()
        S["entry"], S["exit"] = c > m, c < m
    elif name == "donchian":
        S["entry"] = c > w["High"].shift(1).rolling(20).max()
        S["exit"] = c < w["Low"].shift(1).rolling(10).min()
    S["entry"], S["exit"] = S["entry"].fillna(False), S["exit"].fillna(False)
    return S


def ath_signals(df: pd.DataFrame, atr_n=42, mult=10.0, close_only=False) -> pd.DataFrame:
    c = df["Close"]
    ath = c.cummax()
    a = (c.diff().abs().rolling(atr_n).mean() if close_only else E.atr(df, atr_n))
    S = pd.DataFrame(index=df.index)
    S["entry"] = (c >= ath) & (c.index >= c.index[min(252, len(c) - 1)])   # need a year of history first
    S["exit"] = False
    S["trail"] = ath * (1 - mult * a / c)
    S["entry"] = S["entry"].fillna(False)
    return S


def r_multiples(trades: pd.DataFrame, df: pd.DataFrame, mult=10.0, atr_n=42) -> pd.Series:
    """Trade P&L in units of initial risk R = 10 x ATR42 / entry price (Zarattini et al.)."""
    a = E.atr(df, atr_n)
    out = []
    for _, t in trades.iterrows():
        risk = mult * a.asof(t.entry_time) / t.entry
        out.append(t.ret / risk if risk and np.isfinite(risk) and risk > 0 else np.nan)
    return pd.Series(out)


def open_position_book(rets: dict, poss: dict, k_min: int) -> tuple[pd.Series, pd.Series]:
    """Portfolio of per-instrument trade streams: each open position gets 1/max(#open, k_min) of capital
    (entries fill at the open, so the number of positions held during bar t is known at t's open)."""
    R = pd.DataFrame(rets).fillna(0.0)
    P = (pd.DataFrame(poss).reindex(R.index).fillna(0) != 0).astype(float)
    n = P.sum(axis=1)
    w = 1.0 / np.maximum(n, k_min)
    book = (R * P).sum(axis=1) * w
    # exit-day returns are booked on bars where pos is already 0: add them at the same weight
    exit_part = (R * (1 - P)).sum(axis=1) * (1.0 / np.maximum(n.shift(1).fillna(0), k_min))
    return book + exit_part, (n > 0).astype(int)


def rotation(tickers, score_fn, k=3, cost=5.0):
    px = pd.DataFrame({t: data.daily(t)["Close"] for t in tickers}).dropna(how="all")
    op = pd.DataFrame({t: data.daily(t)["Open"] for t in tickers}).reindex(px.index)
    idx = px.index
    me = pd.Series(idx, idx).groupby([idx.year, idx.month]).max()
    score = score_fn(px).loc[me.values]
    W = pd.DataFrame(0.0, index=me.values, columns=tickers)
    for d in me.values:
        s = score.loc[d].dropna()
        if len(s) >= k:
            W.loc[d, s.nlargest(k).index] = 1.0 / k
    Wd = W.reindex(idx).ffill().shift(1).fillna(0.0)                  # decided at month-end close, held from next day
    r = (Wd * px.pct_change().fillna(0.0)).sum(axis=1)
    to = Wd.diff().abs().sum(axis=1).fillna(0.0)
    return r - to * cost / 1e4, (Wd.sum(axis=1) > 0).astype(int), to


def main():
    rows, series = [], {}
    # ---------------------------------------------------------------- Faber SMA10 with timing luck
    faber_assets = ["SPY", "QQQ", "IWM", "EFA", "TLT", "GLD", "VNQ"]
    gtaa = ["SPY", "EFA", "IEF", "VNQ", "DBC"]
    for tk in sorted(set(faber_assets + gtaa)):
        data.daily(tk)
    for tk in faber_assets + ["GTAA5"]:
        sh, mdds = [], []
        for off in range(21):
            if tk == "GTAA5":
                parts = [faber_series(data.daily(t), off)[0] for t in gtaa]
                r = pd.concat(parts, axis=1).dropna().mean(axis=1)
                pos = pd.Series(1, index=r.index)
                bh_r = pd.concat([data.daily(t)["Close"].pct_change() for t in gtaa], axis=1).dropna().mean(axis=1)
            else:
                df = data.daily(tk)
                r, pos = faber_series(df, off)
                r = r.iloc[252:]
                pos = pos.iloc[252:]
                bh_r = df["Close"].pct_change().iloc[252:]
            for per, (a, b) in {"full": (None, None), "holdout": ("2013-01-01", None)}.items():
                m = E.metrics(r.loc[a:b], pd.DataFrame(), pos.loc[a:b], PPY_D, 5.0)
                bh = E.metrics(bh_r.loc[a:b].fillna(0.0), pd.DataFrame(), pd.Series(1, index=bh_r.loc[a:b].index), PPY_D, 0)
                rows.append(dict(strategy="faber_sma10", ticker=tk, variant=f"offset{off}", period=per, **m,
                                 BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"], BH_maxDD=bh["maxDD"]))
            series[f"faber|{tk}|off{off}"] = r
    print("faber done", flush=True)
    # ---------------------------------------------------------------- weekly trend rules
    for tk in ["SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "TLT"]:
        w = data.weekly(data.daily(tk))
        for name in ("wk_cross", "wk_sma43", "donchian"):
            tr, r, pos = E.run(w, wk_signals(name, w), fill="next_open", cost_bps=5.0, periods_per_year=PPY_W)
            # weekly series are kept out of the daily deflated-Sharpe family (different annualisation)
            for per, (a, b) in {"full": (None, None), "holdout": ("2013-01-01", None)}.items():
                m = E.metrics(r.loc[a:b], tr[tr.entry_time >= pd.Timestamp(a)] if a else tr, pos.loc[a:b], PPY_W, 5.0)
                bh = E.buy_hold(w.loc[a:b], PPY_W)
                rows.append(dict(strategy=name, ticker=tk, variant="weekly", period=per, **m,
                                 BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"], BH_maxDD=bh["maxDD"]))
    print("weekly trend done", flush=True)
    # ---------------------------------------------------------------- ATH + 10x ATR42 on ~40 ETFs
    trade_rows, ath_series, ath_pos = [], {}, {}
    for tk in ETF40:
        try:
            df = data.daily(tk)
        except Exception as e:  # noqa: BLE001
            print("skip", tk, e)
            continue
        if len(df) < 400:
            continue
        for bar, frame, ppy in (("daily", df, PPY_D), ("weekly", data.weekly(df), PPY_W)):
            atr_n = 42 if bar == "daily" else 9
            S = ath_signals(frame, atr_n=atr_n)
            tr, r, pos = E.run(frame, S, fill="next_open", cost_bps=25.0, periods_per_year=ppy)
            ath_series[f"{bar}|{tk}"] = r
            ath_pos[f"{bar}|{tk}"] = pos
            if bar == "daily":
                series[f"ath_atr|{tk}"] = r
            if len(tr):
                tr = tr.assign(ticker=tk, bar=bar, R=r_multiples(tr, frame, atr_n=atr_n).to_numpy())
                trade_rows.append(tr)
            for per, (a, b) in {"full": (None, None), "holdout": ("2015-01-01", None)}.items():
                m = E.metrics(r.loc[a:b], tr[tr.entry_time >= pd.Timestamp(a)] if (a and len(tr)) else tr,
                              pos.loc[a:b], ppy, 25.0)
                bh = E.buy_hold(frame.loc[a:b], ppy)
                rows.append(dict(strategy="ath_atr", ticker=tk, variant=bar, period=per, **m,
                                 BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"], BH_maxDD=bh["maxDD"]))
    T = pd.concat(trade_rows, ignore_index=True)
    T.to_csv(data.RES / "positional_ath_trades.csv", index=False, float_format="%.5f")
    rs = []
    for bar in ("daily", "weekly"):
        t = T[T.bar == bar]
        for per, a in (("full", None), ("holdout", "2015-01-01")):
            tt = t[t.entry_time >= pd.Timestamp(a)] if a else t
            w, l = tt[tt.R > 0], tt[tt.R <= 0]
            rs.append(dict(bar=bar, period=per, trades=len(tt), win_rate=(tt.R > 0).mean(), avg_win_R=w.R.mean(),
                           avg_loss_R=l.R.mean(), expectancy_R=tt.R.mean(), payoff=w.R.mean() / -l.R.mean(),
                           median_hold_bars=tt.bars.median(), top7pct_share_of_profit=
                           tt.ret.nlargest(max(1, int(0.07 * len(tt)))).sum() / tt.ret[tt.ret > 0].sum()))
        keys = [k for k in ath_series if k.startswith(bar)]
        ppy = PPY_D if bar == "daily" else PPY_W
        for kmin in (5, 10):
            book, inv = open_position_book({k: ath_series[k] for k in keys}, {k: ath_pos[k] for k in keys}, kmin)
            book = book.loc["2000-01-01":]
            if bar == "daily":
                series[f"ath_atr|ETF40book|k{kmin}"] = book
            spy = data.daily("SPY") if bar == "daily" else data.weekly(data.daily("SPY"))
            for per, a in (("full", "2000-01-01"), ("holdout", "2015-01-01")):
                m = E.metrics(book.loc[a:], pd.DataFrame(), inv.loc[a:], ppy, 25.0)
                bh = E.buy_hold(spy.loc[a:], ppy)
                rows.append(dict(strategy="ath_atr", ticker=f"ETF40 book (1/max(open,{kmin}))", variant=bar,
                                 period=per, **m, BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"], BH_maxDD=bh["maxDD"]))
    pd.DataFrame(rs).to_csv(data.RES / "positional_ath_R_stats.csv", index=False, float_format="%.4f")
    print("ath etf done", flush=True)
    # ---------------------------------------------------------------- ATH on current S&P 500 members (biased)
    try:
        import sys
        sys.path.insert(0, str(data.ROOT.parent / "papers2026"))
        from common import sp500_universe, stock_panel
        px, vol = stock_panel(sp500_universe(350))
        bk, bp = {}, {}
        st_tr = []
        for tk in px.columns:
            c = px[tk].dropna()
            if len(c) < 600:
                continue
            f = pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c})
            S = ath_signals(f, close_only=True)
            tr, r, pos = E.run(f, S, fill="close", cost_bps=25.0, periods_per_year=PPY_D)
            bk[tk], bp[tk] = r, pos
            if len(tr):
                st_tr.append(tr)
        book, inv = open_position_book(bk, bp, 20)
        book = book.loc["2005-01-01":]
        stt = pd.concat(st_tr)
        spy = data.daily("SPY")
        for per, a in (("full", "2005-01-01"), ("holdout", "2015-01-01")):
            m = E.metrics(book.loc[a:], stt[stt.entry_time >= pd.Timestamp(a)], inv.loc[a:], PPY_D, 25.0)
            bh = E.buy_hold(spy.loc[a:], PPY_D)
            rows.append(dict(strategy="ath_atr", ticker="S&P500 current members (SURVIVORSHIP-BIASED), 1/max(open,20)",
                             variant="daily close-only", period=per, **m, BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"],
                             BH_maxDD=bh["maxDD"]))
        print("ath stocks done", flush=True)
    except Exception as e:  # noqa: BLE001
        print("stock ATH skipped:", e)
    # ---------------------------------------------------------------- rotations
    for tk in COUNTRY_SECTOR:
        data.daily(tk)
    for name, univ, fn in (("rs_rotation", SECTORS, lambda p: p / p.shift(126) - 1),
                           ("hi52_rank", COUNTRY_SECTOR, lambda p: p / p.rolling(252).max())):
        r, pos, to = rotation(univ, fn)
        r = r.loc["2000-01-01":]
        series[f"{name}"] = r
        ew = pd.DataFrame({t: data.daily(t)["Close"] for t in univ}).pct_change().mean(axis=1).loc[r.index]
        for per, a in (("full", None), ("holdout", "2013-01-01")):
            m = E.metrics(r.loc[a:], pd.DataFrame(), pos.loc[a:], PPY_D, 5.0)
            bh = E.metrics(ew.loc[a:].fillna(0), pd.DataFrame(), pd.Series(1, index=ew.loc[a:].index), PPY_D, 0)
            rows.append(dict(strategy=name, ticker="universe", variant="top3 monthly", period=per, **m,
                             BH_CAGR=bh["CAGR"], BH_Sharpe=bh["Sharpe"], BH_maxDD=bh["maxDD"],
                             annual_turnover=float(to.loc[a:].sum() / (len(r.loc[a:]) / PPY_D))))
    df = pd.DataFrame(rows)
    df.to_csv(data.RES / "positional_all.csv", index=False, float_format="%.4f")
    pd.DataFrame(series).to_parquet(data.DATA / "positional_series.parquet")
    dsr = E.deflated_sharpe([v.rename(k) for k, v in series.items()], PPY_D)
    (data.RES / "positional_dsr.json").write_text(json.dumps(dsr, indent=1))
    print(dsr, flush=True)


if __name__ == "__main__":
    main()
