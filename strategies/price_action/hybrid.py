"""Phase 4 — additional price-action rules and price action combined with volume, volatility, regime, breadth,
seasonality and cross-asset signals (report: "Price action hybrid strategies"). Daily bars, US ETFs.

Rules are taken as published where a source gives them; parameters marked [unpublished] were fixed here before any
run and never tuned. Signals use the close of day t; execution at that close (market-on-close proxy, the base) or the
next open (fill stress, engine-based rules only). Costs 2 / 6 / 10 bp per side; cash earns 0. Development to 2015,
sealed holdout 2016 -> Oct 2026.

Swing (SPY, QQQ, IWM, DIA)
  double7      Close = 7-day closing low and Close > SMA200 -> buy; exit Close = 7-day closing high      (Connors)
  double7_s5   same entry, exit Close > SMA5 (the more robust exit in independent tests)
  cum_rsi      RSI(2) summed over 2 days < 35 and Close > SMA200; exit RSI(2) > 65                  (Connors)
  pctb         %b(BB 5, 2sd) < 0.2 three days running and Close > SMA200; exit %b > 0.8              (Connors)
  tuesday      Monday close below Friday close -> buy Monday close, sell Tuesday close ("turnaround Tuesday")
  vix_stretch  Close > SMA200 and VIX >= 5% above its SMA10 for 3+ days; exit RSI(2) > 65    (Connors VIX stretch)
  rsi2_hv      RSI(2) < 10 above SMA200 AND volume > SMA20(volume) (Llorente et al.: high-volume moves reverse in
               large liquid names) [threshold unpublished]; exit Close > SMA5
  rsi2_jm      RSI(2) < 10 with the jump-model bull state instead of SMA200; exit Close > SMA5
  lw_vbo       Larry Williams volatility breakout: buy stop at Open + 0.25 x prior range if prior Close > SMA200,
               exit at the close (day trade)
Calendar (SPY)
  tom3         turn of the month: hold from the close of trading day L-1 to the close of day +3 (L = last day)
  tom_wide     hold the last 3 and first 3 trading days of the month
  fomc         pre-FOMC drift: close before the scheduled decision day -> close of the decision day (Lucca-Moench)
  seasonal     tom3 OR fomc, as one 0/1 weight
  overnight    close -> next open every day (two trades a day)
  halloween    hold Nov-Apr, cash May-Oct
Regime / breadth / cross-asset timing of SPY (weight 0/1, rebalanced at the close)
  jm           statistical jump model on ^GSPC (round-1 implementation, Shu-Yu-Mulvey 2024; trade the day after)
  breadth      share of the 9 original sector SPDRs above their SMA200: >= 60% long, <= 40% flat, else hold
  credit       HYG/IEF price ratio above its SMA200 -> long [lookback unpublished]
  vix_ts       flat after VIX/VIX3M > 1 for 3 consecutive days, back long when it falls below 1
  faber_vt     Faber 10-month SMA on SPY, long weight scaled to 10% vol (21-day realised, cap 1.5x)
  spy_vt       SPY volatility-targeted to 10% (reference for faber_vt; Harvey et al. 2018)
Rotation (monthly, at the last close of the month)
  gem          dual momentum (Antonacci): SPY 12m return > SHY's -> hold the better of SPY/EFA, else IEF
  tsmom        12-month time-series momentum, long/flat, 9 ETFs, each sized to 10% vol / 9
  daa          Defensive Asset Allocation G12 (Keller-Keuning): canary EEM, AGG (VWO/BND proxies); 13612W
               momentum; cash share = min(1, bad canaries / 2) into the best of SHY/IEF/LQD; top 6 risky equal weight
Ensemble
  ensemble     four books - mean reversion (double7_s5, cum_rsi, rsi2_jm on the 4 index ETFs), jm, daa, seasonal -
               inverse-vol weighted (63-day), scaled to 10% vol (cap 1.5x), weights lagged 1 day, turnover costed
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import data
import engine as E

COSTS = (2.0, 6.0, 10.0)
IDX = ["SPY", "QQQ", "IWM", "DIA"]
SECTORS9 = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
TSMOM_U = ["SPY", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ"]
DAA_RISKY = ["SPY", "IWM", "QQQ", "VGK", "EWJ", "EEM", "VNQ", "DBC", "GLD", "TLT", "HYG", "LQD"]
DAA_SAFE = ["SHY", "IEF", "LQD"]
DAA_CANARY = ["EEM", "AGG"]
DEV_END = "2015-12-31"
PPY = 252


# ----------------------------------------------------------------------------- helpers
def close(t):
    return data.daily(t)["Close"]


def timing(r: pd.Series | pd.DataFrame, w, cost_bps: float, lag: int = 1) -> pd.Series:
    """Weights decided at close t earn the return of t+lag; cost on every weight change."""
    if isinstance(r, pd.Series):
        r, w = r.to_frame("a"), w.to_frame("a")
    w = w.reindex(r.index).ffill().fillna(0.0)
    pos = w.shift(lag).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    return (pos * r.fillna(0.0)).sum(1) - turn.sum(1) * cost_bps / 1e4


def month_end_mask(idx: pd.DatetimeIndex) -> pd.Series:
    s = pd.Series(idx, index=idx)
    return pd.Series(idx.isin(s.groupby([idx.year, idx.month]).max().values), index=idx)


def ret_n(c: pd.Series, n: int) -> pd.Series:
    return c / c.shift(n) - 1


def vol_target(r: pd.Series, target=0.10, n=21, cap=1.5) -> pd.Series:
    v = r.rolling(n).std() * np.sqrt(PPY)
    return (target / v).clip(upper=cap)


_JM = None


def jm_bull() -> pd.Series:
    """Jump-model bull(1)/bear(0) on ^GSPC, lambda chosen monthly by trailing 8-year Sharpe (cached)."""
    global _JM
    if _JM is not None:
        return _JM
    p = data.DATA / "jm_gspc.parquet"
    if p.exists():
        _JM = pd.read_parquet(p)["bull"]
        return _JM
    sys.path.insert(0, str(data.REPO / "strategies" / "rules"))
    import jump_model as JM
    r = close("^GSPC").pct_change().dropna()
    labels = JM.jm_online_labels(r)
    sig, _ = JM.select_lambda(labels, r, pd.Series(0.0, index=r.index))
    _JM = sig.dropna().rename("bull")
    _JM.to_frame().to_parquet(p)
    return _JM


def fomc_days() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.read_csv(data.DATA / "fomc_dates.csv")["decision_day"])


def pre_fomc(idx) -> pd.Series:
    """True on the trading day before a scheduled FOMC decision day."""
    return pd.Series(idx.isin(fomc_days()), index=idx).shift(-1, fill_value=False)


def days_to_month_end(idx) -> pd.Series:
    """0 on the month's last trading day, 1 the day before, ..."""
    n = pd.Series(np.arange(len(idx)), index=idx)
    return n.groupby([idx.year, idx.month]).transform(lambda s: s.max() - s)


def seasonal_w(idx) -> pd.Series:
    """Union of tom3 and fomc as weights decided at the close: hold the returns of L, +1, +2, +3 and decision days."""
    k = days_to_month_end(idx)
    first = pd.Series(np.arange(len(idx)), index=idx).groupby([idx.year, idx.month]).transform(lambda s: s - s.min())
    tom = (k <= 1) | (first <= 1)
    return (tom | pre_fomc(idx)).astype(float)


# ----------------------------------------------------------------------------- engine-based swing rules
def swing_signals(name: str, df: pd.DataFrame) -> pd.DataFrame:
    c, h, l, o, v = df["Close"], df["High"], df["Low"], df["Open"], df["Volume"]
    up = c > E.sma(c, 200)
    S = pd.DataFrame(index=df.index)
    S["exit"] = False
    if name in ("double7", "double7_s5"):
        S["entry"] = (c <= c.rolling(7).min()) & up
        S["exit"] = (c >= c.rolling(7).max()) if name == "double7" else (c > E.sma(c, 5))
    elif name == "cum_rsi":
        r2 = E.rsi(c, 2)
        S["entry"] = ((r2 + r2.shift(1)) < 35) & up
        S["exit"] = r2 > 65
    elif name == "pctb":
        m, sd = E.sma(c, 5), c.rolling(5).std()
        b = (c - (m - 2 * sd)) / (4 * sd)
        S["entry"] = (b < 0.2) & (b.shift(1) < 0.2) & (b.shift(2) < 0.2) & up
        S["exit"] = b > 0.8
    elif name == "tuesday":
        S["entry"] = (df.index.dayofweek == 0) & (c < c.shift(1))
        S["max_hold"] = 1.0
    elif name == "vix_stretch":
        vix = close("^VIX").reindex(df.index).ffill()
        st = vix >= 1.05 * E.sma(vix, 10)
        S["entry"] = st & st.shift(1, fill_value=False) & st.shift(2, fill_value=False) & up
        S["exit"] = E.rsi(c, 2) > 65
    elif name == "rsi2_hv":
        S["entry"] = (E.rsi(c, 2) < 10) & up & (v > E.sma(v, 20))
        S["exit"] = c > E.sma(c, 5)
    elif name == "rsi2_jm":
        bull = jm_bull().reindex(df.index).ffill()
        S["entry"] = (E.rsi(c, 2) < 10) & (bull == 1)
        S["exit"] = c > E.sma(c, 5)
    elif name in ("tom3", "tom_wide"):
        k_to_end = days_to_month_end(df.index)
        S["entry"] = (k_to_end == 1) if name == "tom3" else (k_to_end == 3)
        S["max_hold"] = 4.0 if name == "tom3" else 6.0
    elif name == "fomc":
        S["entry"], S["max_hold"] = pre_fomc(df.index), 1.0
    else:
        raise ValueError(name)
    S["entry"] = S["entry"].fillna(False).astype(bool)
    S["exit"] = S["exit"].fillna(False).astype(bool)
    return S


SWING = ["double7", "double7_s5", "cum_rsi", "pctb", "tuesday", "vix_stretch", "rsi2_hv", "rsi2_jm"]
CAL = ["tom3", "tom_wide", "fomc"]


# ----------------------------------------------------------------------------- custom rules
def lw_vbo(df, cost):
    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]
    lvl = o + 0.25 * (h.shift(1) - l.shift(1))
    ok = (c.shift(1) > E.sma(c, 200).shift(1)) & (h >= lvl)
    px = np.maximum(lvl, o)
    return ((c / px - 1) - 2 * cost / 1e4).where(ok, 0.0).fillna(0.0)


def overnight(df, cost):
    return (df["Open"] / df["Close"].shift(1) - 1 - 2 * cost / 1e4).fillna(0.0)


def halloween_w(idx):
    return pd.Series(np.where(idx.month.isin([11, 12, 1, 2, 3, 4]), 1.0, 0.0), index=idx)


def breadth_w(idx):
    above = pd.DataFrame({s: close(s) > E.sma(close(s), 200) for s in SECTORS9}).reindex(idx)
    share = above.mean(1)
    w = pd.Series(np.nan, index=idx)
    w[share >= 0.6], w[share <= 0.4] = 1.0, 0.0
    return w.ffill().fillna(0.0)


def credit_w(idx):
    ratio = (close("HYG") / close("IEF")).dropna()
    return (ratio > E.sma(ratio, 200)).astype(float).where(E.sma(ratio, 200).notna()).reindex(idx).ffill()


def vix_ts_w(idx):
    r = (close("^VIX") / close("^VIX3M")).reindex(idx).ffill()
    back3 = (r > 1) & (r.shift(1) > 1) & (r.shift(2) > 1)
    w = pd.Series(np.nan, index=idx)
    w[back3], w[r < 1] = 0.0, 1.0
    return w.ffill().where(r.notna())


def faber_w(idx, c):
    me = month_end_mask(c.index)
    mc = c[me]
    sig = (mc > mc.rolling(10).mean()).astype(float).where(mc.rolling(10).mean().notna())
    return sig.reindex(idx).ffill()


def gem_w(idx):
    U = ["SPY", "EFA", "SHY", "IEF"]
    C = pd.DataFrame({u: close(u) for u in U}).reindex(idx).ffill()
    m12 = C / C.shift(252) - 1
    W = pd.DataFrame(0.0, index=idx, columns=U)
    me = month_end_mask(idx) & m12.notna().all(1)
    for d in idx[me]:
        if m12.at[d, "SPY"] > m12.at[d, "SHY"]:
            W.loc[d, "SPY" if m12.at[d, "SPY"] >= m12.at[d, "EFA"] else "EFA"] = 1.0
        else:
            W.loc[d, "IEF"] = 1.0
    W[~me] = np.nan
    return W.ffill(), C.pct_change()


def tsmom_w(idx):
    C = pd.DataFrame({u: close(u) for u in TSMOM_U}).reindex(idx).ffill()
    R = C.pct_change()
    sig = (C.shift(21) / C.shift(252) - 1 > 0).astype(float)
    vol = R.rolling(63).std() * np.sqrt(PPY)
    W = (sig * (0.10 / vol).clip(upper=2.0) / len(TSMOM_U)).where(C.shift(252).notna(), 0.0)
    me = month_end_mask(idx)
    W[~me] = np.nan
    return W.ffill(), R


def m13612w(C):
    return (12 * (C / C.shift(21) - 1) + 4 * (C / C.shift(63) - 1) + 2 * (C / C.shift(126) - 1)
            + (C / C.shift(252) - 1)) / 4


def daa_w(idx):
    U = sorted(set(DAA_RISKY + DAA_SAFE + DAA_CANARY))
    C = pd.DataFrame({u: close(u) for u in U}).reindex(idx).ffill()
    M = m13612w(C)
    W = pd.DataFrame(np.nan, index=idx, columns=U)
    me = month_end_mask(idx) & M[U].notna().all(1)
    for d in idx[me]:
        b = int((M.loc[d, DAA_CANARY] < 0).sum())
        cf = min(1.0, b / 2)
        w = pd.Series(0.0, index=U)
        if cf < 1:
            top = M.loc[d, DAA_RISKY].nlargest(6).index
            w[top] += (1 - cf) / 6
        if cf > 0:
            w[M.loc[d, DAA_SAFE].idxmax()] += cf
        W.loc[d] = w
    return W.ffill(), C.pct_change()


# ----------------------------------------------------------------------------- build all series
def build(cost: float, fill: str = "close") -> tuple[dict, dict]:
    """Returns ({key: daily net return series}, {key: trades DataFrame or None})."""
    S, T = {}, {}
    spy = data.daily("SPY")
    idx = spy.index
    rspy = spy["Close"].pct_change()
    for tk in IDX:
        df = data.daily(tk)
        for name in SWING:
            tr, r, _ = E.run(df, swing_signals(name, df), fill=fill, cost_bps=cost, periods_per_year=PPY)
            S[f"{name}|{tk}"], T[f"{name}|{tk}"] = r, tr
        if fill == "close":
            S[f"lw_vbo|{tk}"], T[f"lw_vbo|{tk}"] = lw_vbo(df, cost), None
    for name in CAL:
        tr, r, _ = E.run(spy, swing_signals(name, spy), fill=fill, cost_bps=cost, periods_per_year=PPY)
        S[f"{name}|SPY"], T[f"{name}|SPY"] = r, tr
    if fill != "close":
        return S, T
    for tk in ("SPY", "QQQ"):
        S[f"overnight|{tk}"], T[f"overnight|{tk}"] = overnight(data.daily(tk), cost), None
    S["seasonal|SPY"] = timing(rspy, seasonal_w(idx), cost)
    S["halloween|SPY"] = timing(rspy, halloween_w(idx), cost)
    S["jm|SPY"] = timing(rspy, jm_bull().reindex(idx).ffill().fillna(0.0), cost, lag=2)
    S["breadth|SPY"] = timing(rspy, breadth_w(idx), cost)
    S["credit|SPY"] = timing(rspy, credit_w(idx).fillna(0.0), cost)
    S["vix_ts|SPY"] = timing(rspy, vix_ts_w(idx).fillna(0.0), cost)
    vt = vol_target(rspy)
    S["spy_vt|SPY"] = timing(rspy, vt.fillna(0.0), cost)
    S["faber_vt|SPY"] = timing(rspy, (faber_w(idx, spy["Close"]) * vt).fillna(0.0), cost)
    for name, fn in (("gem", gem_w), ("tsmom", tsmom_w), ("daa", daa_w)):
        W, R = fn(idx)
        S[f"{name}|multi"] = timing(R, W.fillna(0.0), cost)
    for k in list(S):
        T.setdefault(k, None)
    # ---- ensemble of four books
    mr = pd.DataFrame({f"{n}|{t}": S[f"{n}|{t}"] for n in ("double7_s5", "cum_rsi", "rsi2_jm") for t in IDX})
    avail = pd.DataFrame({k: close(k.split("|")[1]) for k in mr}).reindex(idx).notna()
    books = pd.DataFrame({"mr": mr.where(avail).mean(1), "jm": S["jm|SPY"], "daa": S["daa|multi"],
                          "seasonal": S["seasonal|SPY"]}).loc["1999-04-01":]
    vol = books.rolling(63, min_periods=63).std()
    inv = (1 / vol.where(vol > 1e-6)).where(books.notna())    # a book flat for 63 days (zero vol) gets no weight
    w = inv.div(inv.sum(1), axis=0).fillna(0.0)
    gross = (w.shift(1) * books.fillna(0)).sum(1)
    scale = vol_target(gross, 0.10, 63, 1.5).shift(1)
    W = w.mul(scale, axis=0).fillna(0.0)
    turn = W.shift(1).diff().abs().sum(1).fillna(0)
    S["ensemble|multi"] = ((W.shift(1) * books.fillna(0)).sum(1) - turn * cost / 1e4).reindex(idx).fillna(0.0)
    T["ensemble|multi"] = None
    return S, T


def main():
    out = {}
    for cost in COSTS:
        S, T = build(cost)
        out[cost] = pd.DataFrame(S)
        out[cost].to_parquet(data.DATA / f"hybrid_series_{cost:g}bp.parquet")
        tr_rows = []
        for k, tr in T.items():
            if tr is not None and len(tr):
                tr_rows.append(tr.assign(key=k))
        if tr_rows:
            pd.concat(tr_rows).to_parquet(data.DATA / f"hybrid_trades_{cost:g}bp.parquet")
        print(f"cost {cost:g} done: {len(S)} series", flush=True)
    S_no, _ = build(2.0, fill="next_open")
    pd.DataFrame(S_no).to_parquet(data.DATA / "hybrid_series_2bp_next_open.parquet")
    print("next_open done", flush=True)
    # quick per-strategy summary (full / dev / holdout) at 2 bp
    rows = []
    for k, r in out[2.0].items():
        r = r.loc[r.ne(0).idxmax():] if r.ne(0).any() else r
        for per, (a, b) in {"full": (None, None), "dev": (None, DEV_END), "holdout": ("2016-01-01", None)}.items():
            m = E.metrics(r.loc[a:b], pd.DataFrame(), (r.loc[a:b] != 0).astype(int), PPY, 2.0)
            rows.append(dict(key=k, period=per, start=str(r.index[0].date()), **m))
    pd.DataFrame(rows).to_csv(data.RES / "hybrid_summary_2bp.csv", index=False, float_format="%.4f")
    print(json.dumps({k: round(v, 3) for k, v in pd.DataFrame(rows).query("period=='holdout'")
                      .set_index("key")["Sharpe"].items()}, indent=0), flush=True)


if __name__ == "__main__":
    main()
