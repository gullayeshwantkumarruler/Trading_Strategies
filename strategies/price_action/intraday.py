"""Phase 2 — intraday price-action strategies on SPY / QQQ 1-minute SIP bars (Alpaca, 2016 -> 2026).

Sessions are reshaped into a (day x 390 minute) grid 09:30..15:59 (bar timestamp = minute start). Half-days and
days with < 380 bars are skipped. Costs: commission $0.0035/share/side + slippage `s` $/share/side (base $0.001,
swept to $0.03); both converted to returns at the fill price and scaled by leverage. Splits: development 2016-2022,
holdout 2023-2026 (Noise Area: replication 2016 -> Feb 2024, true out-of-sample Mar 2024 -> Oct 2026).

  lhh_10   last-half-hour momentum (Gao, Han, Li & Zhou 2018): sign of prev-close -> 10:00 return; enter at the open
           of the 15:31 bar, exit at the 16:00 close (close of the 15:59 bar)
  lhh_1530 same with the prev-close -> 15:30 return as the predictor (Baltussen et al. 'rest of day' variant)
  noise    Noise Area (Zarattini, Aziz & Barbon 2024): sigma(m) = 14-day mean |Close(m)/Open(9:30) - 1|;
           UB = max(Open, PrevClose)(1+sigma), LB = min(Open, PrevClose)(1-sigma); decisions only at HH:00 / HH:30
           (from 10:00) on the close of the bar ending there, fills at the next bar's open; base exit = opposite band;
           'vwap' exit = trailing stop max(UB, VWAP) / min(LB, VWAP) checked on the half-hour; flat at 16:00.
           Sizing 1x, and vol-targeted min(4, 2% / sigma_daily_14d).
  orb5     5-minute opening-range 'direction' trade (Zarattini & Aziz 2023): first 09:30-09:35 candle bullish -> long at
           09:35 open (bearish -> short; doji -> none); stop at the candle's opposite extreme, target 10R, else exit at
           the close; risk 1% of equity per trade, leverage cap 4x; stops pay 2x slippage; stop first if both hit.
  gap_fade / gap_go   untested templates from the notes: |gap| < 0.5% -> fade at 09:31 open, exit when the previous
           close is touched or at the close; |gap| > 1% -> trade with the gap at 09:31, stop at the previous close.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import data
import engine as E

COMM = 0.0035
SLIPS = (0.0, 0.001, 0.005, 0.01, 0.02, 0.03)
DEV_END = "2022-12-31"
NM = 390


def grid(symbol: str):
    p = data.DATA / f"grid_{symbol}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}
    m = data.rth(data.minute(symbol, start="2016-01-01"))
    m = m[~m.index.duplicated()]
    day = m.index.normalize().tz_localize(None)
    mins = (m.index.hour - 9) * 60 + m.index.minute - 30
    days = np.unique(day)
    di = np.searchsorted(days, day)
    G = {k: np.full((len(days), NM), np.nan) for k in ("Open", "High", "Low", "Close", "Volume", "Vwap")}
    for k in G:
        G[k][di, mins] = m[k].to_numpy(float)
    cnt = np.isfinite(G["Close"]).sum(1)
    keep = cnt >= 380
    for k in G:
        G[k] = G[k][keep]
    days = days[keep]
    # forward-fill missing minutes (close -> O/H/L/C of empty minutes, zero volume)
    C = pd.DataFrame(G["Close"]).ffill(axis=1).bfill(axis=1).to_numpy()
    for k in ("Open", "High", "Low"):
        G[k] = np.where(np.isfinite(G[k]), G[k], C)
    G["Close"] = C
    G["Volume"] = np.nan_to_num(G["Volume"])
    G["Vwap"] = np.where(np.isfinite(G["Vwap"]), G["Vwap"], C)
    G["days"] = days.astype("datetime64[ns]")
    np.savez_compressed(p, **G)
    return G


def daily_stats(G):
    o = G["Open"][:, 0]
    c = G["Close"][:, -1]
    pc = np.r_[np.nan, c[:-1]]
    return o, c, pc


def cost_ret(price, s, lev=1.0):
    return lev * (COMM + s) / price


def summarize(name, sym, days, r, trades, s, extra=None):
    idx = pd.DatetimeIndex(days)
    rs = pd.Series(r, idx).fillna(0.0)
    tr = pd.DataFrame({"ret": trades, "bars": 1.0}) if trades is not None else pd.DataFrame()
    tr = tr[np.isfinite(tr["ret"])] if len(tr) else tr
    out = []
    splits = {"full": (None, None), "dev": (None, DEV_END), "holdout": ("2023-01-01", None)}
    if name.startswith("noise"):
        splits = {"full": (None, None), "replication": (None, "2024-02-29"), "oos": ("2024-03-01", None)}
    for per, (a, b) in splits.items():
        sub = rs.loc[a:b]
        trs = pd.DataFrame({"ret": pd.Series(trades, idx).loc[a:b].dropna(), "bars": 1.0}) if trades is not None else pd.DataFrame()
        m = E.metrics(sub, trs, (sub != 0).astype(int), 252, 0)
        tstat = sub[sub != 0].mean() / sub[sub != 0].std() * np.sqrt((sub != 0).sum()) if (sub != 0).sum() > 2 else np.nan
        out.append(dict(strategy=name, symbol=sym, slippage=s, period=per, start=str(sub.index[0].date()),
                        end=str(sub.index[-1].date()), t_mean_active=tstat, **m, **(extra or {})))
    return out, rs


# ----------------------------------------------------------------------------- strategies
def lhh(G, s, predictor="10"):
    o, c, pc = daily_stats(G)
    C = G["Close"]
    sig_px = C[:, 29] if predictor == "10" else C[:, 359]          # close of the 09:59 / 15:29 bar = 10:00 / 15:30
    sign = np.sign(sig_px / pc - 1)
    entry = G["Open"][:, 361]                                       # open of the 15:31 bar
    exitp = C[:, -1]
    r = sign * (exitp / entry - 1) - 2 * cost_ret(entry, s) * (sign != 0)
    return r, r.copy()


def noise_area(G, s, exit_rule="vwap", sizing="1x"):
    o, c, pc = daily_stats(G)
    O, H, L, C, V, VW = (G[k] for k in ("Open", "High", "Low", "Close", "Volume", "Vwap"))
    nD = len(o)
    move = np.abs(C / o[:, None] - 1)                                 # |Close(m)/Open(9:30) - 1|
    sigma = pd.DataFrame(move).rolling(14).mean().shift(1).to_numpy()  # previous 14 days, per minute-of-day
    up_ref = np.maximum(o, pc)[:, None]
    dn_ref = np.minimum(o, pc)[:, None]
    UB, LB = up_ref * (1 + sigma), dn_ref * (1 - sigma)
    vwap = np.cumsum(VW * V, axis=1) / np.maximum(np.cumsum(V, axis=1), 1)
    dret = pd.Series(c / pc - 1)
    vol14 = dret.rolling(14).std().shift(1).to_numpy()
    lev = np.ones(nD) if sizing == "1x" else np.minimum(4.0, 0.02 / vol14)
    checks = list(range(30, 390, 30))                                 # bars ending 10:00, 10:30, ..., 15:30 -> m-1
    r = np.zeros(nD)
    ntr = np.zeros(nD)
    for d in range(nD):
        if not np.isfinite(sigma[d, 0]) or not np.isfinite(pc[d]) or not np.isfinite(lev[d]):
            continue
        pos, px_in, acc, n = 0, 0.0, 0.0, 0
        for m in checks:
            px = C[d, m - 1]                                          # price at HH:00 / HH:30
            fill = O[d, m] if m < NM else C[d, -1]
            ub, lb = UB[d, m - 1], LB[d, m - 1]
            want = pos
            if pos == 1:
                if exit_rule == "vwap" and px < max(ub, vwap[d, m - 1]):
                    want = 0
                if px < lb:
                    want = -1
            elif pos == -1:
                if exit_rule == "vwap" and px > min(lb, vwap[d, m - 1]):
                    want = 0
                if px > ub:
                    want = 1
            else:
                if px > ub:
                    want = 1
                elif px < lb:
                    want = -1
            if want != pos:
                if pos != 0:
                    acc += pos * (fill / px_in - 1) - cost_ret(fill, s)
                if want != 0:
                    px_in = fill
                    acc -= cost_ret(fill, s)
                    n += 1
                pos = want
        if pos != 0:
            ex = C[d, -1]
            acc += pos * (ex / px_in - 1) - cost_ret(ex, s)
        r[d] = lev[d] * acc
        ntr[d] = n
    trades = np.where(ntr > 0, r, np.nan)
    return r, trades, ntr


def orb5(G, s, risk=0.01, cap=4.0):
    O, H, L, C = (G[k] for k in ("Open", "High", "Low", "Close"))
    nD = len(O)
    r = np.zeros(nD)
    tr = np.full(nD, np.nan)
    for d in range(nD):
        co, cc = O[d, 0], C[d, 4]
        hi, lo = H[d, :5].max(), L[d, :5].min()
        if cc == co:
            continue
        side = 1 if cc > co else -1
        entry = O[d, 5]
        stop = lo if side > 0 else hi
        R = abs(entry - stop)
        if R <= 0:
            continue
        lev = min(cap, risk / (R / entry))
        target = entry + side * 10 * R
        exit_px, slip_x = C[d, -1], s
        for m in range(5, NM):
            hit_stop = L[d, m] <= stop if side > 0 else H[d, m] >= stop
            hit_tgt = H[d, m] >= target if side > 0 else L[d, m] <= target
            if hit_stop:
                exit_px = (min(O[d, m], stop) if side > 0 else max(O[d, m], stop))
                slip_x = 2 * s
                break
            if hit_tgt:
                exit_px = target
                break
        g = side * (exit_px / entry - 1)
        net = g - (COMM + s) / entry - (COMM + slip_x) / exit_px
        r[d] = lev * net
        tr[d] = net / (R / entry)                                      # in R units
    return r, tr


def gaps(G, s, kind):
    O, H, L, C = (G[k] for k in ("Open", "High", "Low", "Close"))
    o, c, pc = daily_stats(G)
    g = o / pc - 1
    r = np.zeros(len(o))
    for d in range(1, len(o)):
        if not np.isfinite(g[d]):
            continue
        if kind == "fade" and 0.001 < abs(g[d]) < 0.005:
            side, target, stop = -np.sign(g[d]), pc[d], None
        elif kind == "go" and abs(g[d]) > 0.01:
            side, target, stop = np.sign(g[d]), None, pc[d]
        else:
            continue
        entry, ex = O[d, 1], C[d, -1]
        for m in range(1, NM):
            if stop is not None and ((side > 0 and L[d, m] <= stop) or (side < 0 and H[d, m] >= stop)):
                ex = stop
                break
            if target is not None and ((side > 0 and H[d, m] >= target) or (side < 0 and L[d, m] <= target)):
                ex = target
                break
        r[d] = side * (ex / entry - 1) - cost_ret(entry, s) - cost_ret(ex, s)
    return r, np.where(r != 0, r, np.nan)


def main():
    rows, curves, series = [], {}, {}
    for sym in ("SPY", "QQQ"):
        G = grid(sym)
        days = G["days"]
        print(sym, "days", len(days), str(pd.Timestamp(days[0]).date()), str(pd.Timestamp(days[-1]).date()), flush=True)
        for s in SLIPS:
            for pred in ("10", "1530"):
                r, t = lhh(G, s, pred)
                o, rs = summarize(f"lhh_{pred}", sym, days, r, t, s)
                rows += o
                series[f"lhh_{pred}|{sym}|{s}"] = rs
            for ex in ("base", "vwap"):
                for sz in ("1x", "voltarget"):
                    r, t, n = noise_area(G, s, ex, sz)
                    o, rs = summarize(f"noise_{ex}_{sz}", sym, days, r, t, s, {"trades_per_day": float(n.mean())})
                    rows += o
                    series[f"noise_{ex}_{sz}|{sym}|{s}"] = rs
            r, t = orb5(G, s)
            o, rs = summarize("orb5", sym, days, r, t, s, {"avg_R": float(np.nanmean(t))})
            rows += o
            series[f"orb5|{sym}|{s}"] = rs
            for kind in ("fade", "go"):
                r, t = gaps(G, s, kind)
                o, rs = summarize(f"gap_{kind}", sym, days, r, t, s)
                rows += o
                series[f"gap_{kind}|{sym}|{s}"] = rs
            print(f"  {sym} slippage {s} done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(data.RES / "intraday_all.csv", index=False, float_format="%.5f")
    # break-even slippage per strategy (full period, interpolated where Sharpe crosses 0)
    be = []
    for (st, sym), g in df[df.period == "full"].groupby(["strategy", "symbol"]):
        g = g.sort_values("slippage")
        x, y = g.slippage.to_numpy(), g.Sharpe.to_numpy()
        cross = np.nan
        for i in range(1, len(x)):
            if y[i - 1] > 0 >= y[i]:
                cross = x[i - 1] + (x[i] - x[i - 1]) * y[i - 1] / (y[i - 1] - y[i])
                break
        if np.isnan(cross):
            cross = 0.0 if y[0] <= 0 else f">{x[-1]}"
        be.append(dict(strategy=st, symbol=sym, breakeven_slippage_per_share=cross))
    pd.DataFrame(be).to_csv(data.RES / "intraday_breakeven.csv", index=False)
    base = {k: v for k, v in series.items() if k.endswith("|0.001")}
    dsr = E.deflated_sharpe([v.rename(k) for k, v in base.items()], 252)
    (data.RES / "intraday_dsr.json").write_text(json.dumps(dsr, indent=1))
    pd.DataFrame(base).to_parquet(data.DATA / "intraday_series_base.parquet")
    print(dsr, flush=True)


if __name__ == "__main__":
    main()
