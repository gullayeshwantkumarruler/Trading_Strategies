"""Trade-level backtest engine and metrics for price-action strategies (report: "Price action strategies by horizon").

Single-instrument, long/short/flat, one position at a time; bars are any frequency (1-min, daily, weekly).
Conservative execution rules from the report:
  * signals use information up to the close of bar t
  * fill mode "close": market-on-close at bar t's close; "next_open": bar t+1's open (default)
  * stop/target inside a bar: if both are touched in the same bar, the STOP is assumed first
  * a gap through a stop fills at the bar's open (not the stop price)
  * costs: `cost_bps` per side on traded notional (+ optional per-share slippage)
Strategy interface: a function(df) -> DataFrame with columns
  entry (bool, signal at close t), exit (bool), side (+1/-1, optional, default +1),
  stop (price level or NaN), target (price level or NaN), max_hold (bars, optional per-row),
  trail (optional: trailing-stop level computed at close t, applied from bar t+1, only ever tightened)
Metrics: CAGR, vol, Sharpe, Sortino, Calmar, max DD, DD duration, Ulcer, exposure, turnover/cost drag, skew,
kurtosis, tail ratio, trades, win rate, profit factor, payoff, expectancy, avg trade, avg hold, SQN,
probabilistic Sharpe; deflated Sharpe over a family of variants.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: int
    entry: float
    exit: float
    bars: int
    ret: float          # net return on notional (after costs)
    reason: str


def run(df: pd.DataFrame, sig: pd.DataFrame, fill: str = "next_open", cost_bps: float = 2.0,
        slip_per_share: float = 0.0, periods_per_year: float = 252.0, risk_free: float = 0.0):
    """Simulate. df: OHLC(V) indexed by time. Returns (trades DataFrame, per-bar strategy returns Series)."""
    o, h, l, c = (df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    n = len(df)
    ent = sig["entry"].to_numpy(bool)
    exi = sig["exit"].to_numpy(bool) if "exit" in sig else np.zeros(n, bool)
    side_s = sig["side"].to_numpy(float) if "side" in sig else np.ones(n)
    stop_s = sig["stop"].to_numpy(float) if "stop" in sig else np.full(n, np.nan)
    tgt_s = sig["target"].to_numpy(float) if "target" in sig else np.full(n, np.nan)
    mh_s = sig["max_hold"].to_numpy(float) if "max_hold" in sig else np.full(n, np.nan)
    tr_s = sig["trail"].to_numpy(float) if "trail" in sig else None   # trailing stop level computed at close t
    cost = cost_bps / 1e4
    bar_ret = np.zeros(n)
    pos = np.zeros(n)
    trades = []
    in_pos, side, px_in, t_in, stop, tgt, max_hold = False, 0, 0.0, 0, np.nan, np.nan, np.nan
    pending_entry = pending_exit = False
    prev_mark = 0.0

    def slip(price):
        return slip_per_share / price if price > 0 else 0.0

    for t in range(n):
        # ---- executions at the open of bar t (from signals at t-1)
        if fill == "next_open":
            if in_pos and pending_exit:
                px = o[t]
                bar_ret[t] += side * (px / prev_mark - 1) - cost - slip(px)
                trades.append(Trade(df.index[t_in], df.index[t], side, px_in, px, t - t_in,
                                    side * (px / px_in - 1) - 2 * cost - slip(px) - slip(px_in), "signal"))
                in_pos, pending_exit = False, False
            if not in_pos and pending_entry:
                in_pos, px_in, t_in = True, o[t], t
                side = int(np.sign(side_s[t - 1])) or 1
                stop, tgt, max_hold = stop_s[t - 1], tgt_s[t - 1], mh_s[t - 1]
                bar_ret[t] -= cost + slip(px_in)
                prev_mark = px_in
                pending_entry = False
        # ---- intrabar stop / target (stop first if both touched; gap-through fills at open)
        live = (t >= t_in) if fill == "next_open" else (t > t_in)      # stops live from the entry bar / next bar
        if in_pos and tr_s is not None and t > 0 and np.isfinite(tr_s[t - 1]):
            lvl = tr_s[t - 1]                                            # level known at the previous close
            stop = lvl if not np.isfinite(stop) else (max(stop, lvl) if side > 0 else min(stop, lvl))
        if in_pos and live:
            hit, px = None, None
            if np.isfinite(stop):
                if side > 0 and l[t] <= stop:
                    hit, px = "stop", min(o[t], stop) if t != t_in else stop
                elif side < 0 and h[t] >= stop:
                    hit, px = "stop", max(o[t], stop) if t != t_in else stop
            if hit is None and np.isfinite(tgt):
                if side > 0 and h[t] >= tgt:
                    hit, px = "target", max(o[t], tgt) if t != t_in else tgt
                elif side < 0 and l[t] <= tgt:
                    hit, px = "target", min(o[t], tgt) if t != t_in else tgt
            if hit:
                bar_ret[t] += side * (px / prev_mark - 1) - cost - slip(px)
                trades.append(Trade(df.index[t_in], df.index[t], side, px_in, px, t - t_in,
                                    side * (px / px_in - 1) - 2 * cost - slip(px) - slip(px_in), hit))
                in_pos = False
                pos[t] = 0
                continue
        # ---- mark to close
        if in_pos:
            bar_ret[t] += side * (c[t] / prev_mark - 1)
            prev_mark = c[t]
            pos[t] = side
        # ---- signals at the close of bar t
        held = t - t_in if in_pos else 0
        want_exit = in_pos and (exi[t] or (np.isfinite(max_hold) and held >= max_hold))
        if fill == "close":
            if want_exit:
                px = c[t]
                bar_ret[t] -= cost + slip(px)
                trades.append(Trade(df.index[t_in], df.index[t], side, px_in, px, held,
                                    side * (px / px_in - 1) - 2 * cost - slip(px) - slip(px_in),
                                    "signal" if exi[t] else "time"))
                in_pos = False
                pos[t] = 0
            elif not in_pos and ent[t] and t < n - 1:
                in_pos, px_in, t_in = True, c[t], t
                side = int(np.sign(side_s[t])) or 1
                stop, tgt, max_hold = stop_s[t], tgt_s[t], mh_s[t]
                bar_ret[t] -= cost + slip(px_in)
                prev_mark = px_in
        else:
            if want_exit and t < n - 1:
                pending_exit = True
            elif not in_pos and ent[t] and t < n - 1:
                pending_entry = True
    if in_pos:                                             # close any open trade at the last close
        trades.append(Trade(df.index[t_in], df.index[-1], side, px_in, c[-1], n - 1 - t_in,
                            side * (c[-1] / px_in - 1) - cost, "end"))
    tr = pd.DataFrame([t.__dict__ for t in trades])
    rets = pd.Series(bar_ret, index=df.index)
    return tr, rets, pd.Series(pos, index=df.index)


# ----------------------------------------------------------------------------- metrics
def max_dd_info(eq: pd.Series):
    peak = eq.cummax()
    dd = eq / peak - 1
    under = dd < 0
    dur, cur = 0, 0
    for u in under.to_numpy():
        cur = cur + 1 if u else 0
        dur = max(dur, cur)
    return float(dd.min()), int(dur), float(np.sqrt((dd ** 2).mean()))


def psr(r: pd.Series, sr_bench: float = 0.0) -> float:
    """Probabilistic Sharpe (per-period SR vs benchmark SR), Bailey & Lopez de Prado."""
    r = r.dropna()
    if len(r) < 10 or r.std() == 0:
        return np.nan
    s = r.mean() / r.std()
    g3, g4 = skew(r), kurtosis(r, fisher=False)
    den = np.sqrt(1 - g3 * s + (g4 - 1) / 4 * s ** 2)
    return float(norm.cdf((s - sr_bench) * np.sqrt(len(r) - 1) / den))


def metrics(rets: pd.Series, trades: pd.DataFrame, pos: pd.Series, periods_per_year: float, cost_bps: float) -> dict:
    r = rets.fillna(0.0)
    eq = (1 + r).cumprod()
    yrs = len(r) / periods_per_year
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 and eq.iloc[-1] > 0 else np.nan
    vol = r.std() * np.sqrt(periods_per_year)
    sharpe = r.mean() / r.std() * np.sqrt(periods_per_year) if r.std() > 0 else np.nan
    dn = np.sqrt((np.minimum(r, 0) ** 2).mean()) * np.sqrt(periods_per_year)
    sortino = r.mean() * periods_per_year / dn if dn > 0 else np.nan
    mdd, ddur, ulcer = max_dd_info(eq)
    out = dict(CAGR=cagr, vol=vol, Sharpe=sharpe, Sortino=sortino, Calmar=cagr / abs(mdd) if mdd < 0 else np.nan,
               maxDD=mdd, maxDD_bars=ddur, ulcer=ulcer, exposure=float((pos != 0).mean()),
               skew=float(skew(r)), kurt=float(kurtosis(r)),
               tail_ratio=float(abs(np.percentile(r, 95)) / abs(np.percentile(r, 5))) if np.percentile(r, 5) != 0 else np.nan,
               PSR=psr(r))
    if len(trades):
        tr = trades["ret"]
        wins, losses = tr[tr > 0], tr[tr <= 0]
        out.update(trades=len(tr), trades_per_year=len(tr) / yrs, win_rate=float((tr > 0).mean()),
                   profit_factor=float(wins.sum() / -losses.sum()) if losses.sum() < 0 else np.inf,
                   payoff=float(wins.mean() / -losses.mean()) if len(wins) and len(losses) and losses.mean() < 0 else np.nan,
                   expectancy=float(tr.mean()), avg_win=float(wins.mean()) if len(wins) else np.nan,
                   avg_loss=float(losses.mean()) if len(losses) else np.nan,
                   avg_hold_bars=float(trades["bars"].mean()),
                   SQN=float(np.sqrt(min(len(tr), 100)) * tr.mean() / tr.std()) if tr.std() > 0 else np.nan,
                   cost_drag_ann=float(len(tr) / yrs * 2 * cost_bps / 1e4))
    else:
        out.update(trades=0)
    return out


def deflated_sharpe(series: list[pd.Series], periods_per_year: float) -> dict:
    """DSR of the best variant over K variants (ml4t.diagnostic implementation)."""
    from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio_from_statistics
    df = pd.concat(series, axis=1).fillna(0.0)
    srs = df.mean() / df.std()
    best = srs.idxmax()
    x = df[best]
    res = deflated_sharpe_ratio_from_statistics(
        observed_sharpe=float(srs.max()), n_samples=len(x), n_trials=df.shape[1],
        variance_trials=float(srs.var()) if df.shape[1] > 1 else 0.0, skewness=float(skew(x)),
        excess_kurtosis=float(kurtosis(x)), autocorrelation=float(x.autocorr()),
        periods_per_year=int(periods_per_year))
    return dict(best=best, best_SR_ann=float(srs.max() * np.sqrt(periods_per_year)), n_variants=df.shape[1],
                dsr_prob=float(res.probability))


def buy_hold(df: pd.DataFrame, periods_per_year: float) -> dict:
    r = df["Close"].pct_change().fillna(0.0)
    return metrics(r, pd.DataFrame(), pd.Series(1, index=df.index), periods_per_year, 0.0)


# ----------------------------------------------------------------------------- indicators
def sma(x, n):
    return x.rolling(n).mean()


def rsi(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(df: pd.DataFrame, n: int) -> pd.Series:
    pc = df["Close"].shift()
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - pc).abs(), (df["Low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def ibs(df: pd.DataFrame) -> pd.Series:
    rng = (df["High"] - df["Low"]).replace(0, np.nan)
    return (df["Close"] - df["Low"]) / rng
