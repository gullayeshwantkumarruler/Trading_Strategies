"""Strategy 1: Statistical jump-model regime filter (Shu, Yu & Mulvey 2024, arXiv 2402.05272).

Rules implemented
-----------------
* Features on daily excess returns r: EWM downside deviation (halflife 10)
  dd_h = sqrt(EWM_h(r^2 * 1{r<0})), EWM Sortino (halflife 20 and 60) = EWM_h(r) / dd_h.
* 2-state statistical jump model (jumpmodels.JumpModel, discrete, n_init=5).
  Features clipped at +/-3 sd and standardised on the training window.
* Training window: trailing 3000 days (expanding from a 1500-day minimum); refit every
  6 months (end-June / end-December); online state inference (forward DP) over a
  3000-day lookback - jumpmodels.JumpModel.predict_online.
* Jump penalty lambda chosen at each month end from a grid by the trailing 8-year Sharpe
  of each lambda's own walk-forward (online, out-of-sample) 0/1 strategy (min 3 years).
  [Paper: monthly time-series CV on an 8-year window - ours is the same idea, but
  reuses the walk-forward online labels instead of re-fitting inside the validation window.]
* Bull state = the state with the higher mean training return. Risk-on = 100% index,
  risk-off = cash. Signal at close t, traded at close t+1. 10 bp per one-way trade.
* Baselines (same lag/costs): buy & hold, 200-day SMA filter, 2-state Gaussian
  Markov-switching model (statsmodels MarkovRegression, switching mean+variance, refit
  every 6 months on 3000 days, filtered probabilities, 10-day smoothing, p(bear)>0.5).

Two implementations per market
  (a) "index": local price index, local currency (signal + returns on the index)
  (b) "etf"  : signal from the local index (long training history), traded on the
               US-listed USD ETF (SPY, EWG, EWJ, ASHR/FXI); ETF closes are later in
               the day than the Asian/European index closes, so no look-ahead.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from common import (DATA_DIR, closes, deflated_sharpe, fetch, metrics, plot_equity,
                    simulate, tbill_daily, trim_start)

warnings.filterwarnings("ignore")

MARKETS = {  # name: (index ticker, [ETFs], cash earns US T-bill?)
    "US": ("^GSPC", ["SPY"], True),
    "Europe": ("^GDAXI", ["EWG", "EZU"], False),
    "Japan": ("^N225", ["EWJ"], False),
    "China": ("000300.SS", ["ASHR", "FXI"], False),
}
LAMBDAS = [5.0, 15.0, 30.0, 50.0, 100.0]
TRAIN = 3000
MIN_TRAIN = 1500
VAL_YEARS = 8
MIN_VAL_YEARS = 3
COST_BPS = 10.0
N_INIT = 5               # k-means++ restarts per fit (jumpmodels default 10; 5 for speed)
REFIT_START = pd.Timestamp("1981-01-01")  # 9y before the 1990 evaluation start (8y CV window)
EVAL_START_INDEX = pd.Timestamp("1990-01-01")


def jm_features(r: pd.Series) -> pd.DataFrame:
    neg2 = (r.clip(upper=0) ** 2)
    f = {}
    f["dd10"] = np.sqrt(neg2.ewm(halflife=10).mean())
    for h in (20, 60):
        dd = np.sqrt(neg2.ewm(halflife=h).mean())
        f[f"sortino{h}"] = r.ewm(halflife=h).mean() / dd.replace(0, np.nan)
    return pd.DataFrame(f).replace([np.inf, -np.inf], np.nan)


def refit_dates(index: pd.DatetimeIndex) -> list[pd.Timestamp]:
    s = pd.Series(index, index=index)
    me = s.groupby([index.year, index.month]).max()
    return [d for d in me.values if pd.Timestamp(d).month in (6, 12)]


def _standardise(train: pd.DataFrame, x: pd.DataFrame) -> pd.DataFrame:
    mu, sd = train.mean(), train.std()
    lo, hi = mu - 3 * sd, mu + 3 * sd
    return (x.clip(lo, hi, axis=1) - mu) / sd


def jm_online_labels(r: pd.Series, lambdas=LAMBDAS) -> pd.DataFrame:
    """Walk-forward online JM bull(1)/bear(0) indicator for each lambda."""
    from jumpmodels.jump import JumpModel

    X = jm_features(r).dropna()
    rr = r.reindex(X.index)
    out = pd.DataFrame(np.nan, index=X.index, columns=[f"lam{l:g}" for l in lambdas])
    rds = [d for d in refit_dates(X.index) if X.index.get_loc(d) + 1 >= MIN_TRAIN and d >= REFIT_START]
    for j, d in enumerate(rds):
        pos = X.index.get_loc(d)
        tr = X.iloc[max(0, pos + 1 - TRAIN): pos + 1]
        end = rds[j + 1] if j + 1 < len(rds) else X.index[-1]
        end_pos = X.index.get_loc(end)
        if end_pos <= pos:
            continue
        look = X.iloc[max(0, pos + 1 - TRAIN): end_pos + 1]
        trs = _standardise(tr, tr)
        looks = _standardise(tr, look)
        new_idx = X.index[pos + 1: end_pos + 1]
        for lam in lambdas:
            jm = JumpModel(n_components=2, jump_penalty=lam, cont=False, n_init=N_INIT, random_state=0)
            jm.fit(trs, ret_ser=rr.loc[tr.index], sort_by="cumret")
            bull = int(np.argmax(np.asarray(jm.ret_)))
            lab = np.asarray(jm.predict_online(looks))
            lab = pd.Series(lab, index=look.index).loc[new_idx]
            out.loc[new_idx, f"lam{lam:g}"] = (lab == bull).astype(float).to_numpy()
    return out.dropna(how="all")


def _ret_01(sig: pd.Series, r: pd.Series, rf: pd.Series, cost: float) -> pd.Series:
    """Fast 0/1 strategy returns (lag 2, cost per change) for lambda selection."""
    pos = sig.shift(2).fillna(0)
    return pos * r + (1 - pos) * rf - pos.diff().abs().fillna(0) * cost


def select_lambda(labels: pd.DataFrame, r: pd.Series, rf: pd.Series) -> pd.Series:
    """Month-end selection of the lambda with the best trailing-8y Sharpe; the chosen
    lambda's label is used for the following month. Uses only information up to t."""
    r = r.reindex(labels.index).fillna(0)
    rf_ = rf.reindex(labels.index).fillna(0)
    strat = pd.DataFrame({c: _ret_01(labels[c], r, rf_, COST_BPS / 1e4) - rf_ for c in labels})
    idx = labels.index
    me = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).max().values
    chosen = pd.Series(np.nan, index=idx, dtype=object)
    first_valid = labels.dropna().index[0]
    for k, d in enumerate(me):
        d = pd.Timestamp(d)
        win = strat.loc[(strat.index > d - pd.DateOffset(years=VAL_YEARS)) & (strat.index <= d)
                        & (strat.index >= first_valid)]
        if len(win) < MIN_VAL_YEARS * 252:
            continue
        sr = win.mean() / win.std()
        nxt = pd.Timestamp(me[k + 1]) if k + 1 < len(me) else idx[-1] + pd.Timedelta(days=1)
        chosen.loc[(idx > d) & (idx <= nxt)] = sr.idxmax()
    sig = pd.Series(np.nan, index=idx)
    for c in labels.columns:
        m = chosen == c
        sig[m] = labels.loc[m, c]
    return sig, chosen


def hmm_online_bull(r: pd.Series, smooth: int = 10) -> pd.Series:
    """2-state Markov-switching (Gaussian) baseline with filtered probabilities."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    x = (r.dropna() * 100.0)
    out = pd.Series(np.nan, index=x.index)
    rds = [d for d in refit_dates(x.index) if x.index.get_loc(d) + 1 >= MIN_TRAIN and d >= REFIT_START]
    params = None
    for j, d in enumerate(rds):
        pos = x.index.get_loc(d)
        tr = x.iloc[max(0, pos + 1 - TRAIN): pos + 1]
        end = rds[j + 1] if j + 1 < len(rds) else x.index[-1]
        end_pos = x.index.get_loc(end)
        if end_pos <= pos:
            continue
        try:
            m = MarkovRegression(tr.to_numpy(), k_regimes=2, trend="c", switching_variance=True)
            fit = m.fit(disp=False, start_params=params) if params is not None else m.fit(disp=False)
            params = fit.params
        except Exception:
            if params is None:
                continue
        look = x.iloc[max(0, pos + 1 - TRAIN): end_pos + 1]
        m2 = MarkovRegression(look.to_numpy(), k_regimes=2, trend="c", switching_variance=True)
        f2 = m2.filter(params)
        probs = np.asarray(f2.filtered_marginal_probabilities)
        if probs.shape[0] != len(look):
            probs = probs.T
        # identify bear regime = higher variance
        names = list(m2.param_names)
        s2 = [params[names.index(f"sigma2[{k}]")] for k in range(2)]
        bear = int(np.argmax(s2))
        pb = pd.Series(probs[:, bear], index=look.index)
        pb = pb.rolling(smooth, min_periods=1).mean()  # causal smoothing
        new_idx = x.index[pos + 1: end_pos + 1]
        out.loc[new_idx] = (pb.loc[new_idx] < 0.5).astype(float).to_numpy()
    return out.dropna()


def ma_bull(price: pd.Series, n: int = 200) -> pd.Series:
    return (price > price.rolling(n).mean()).astype(float).where(price.rolling(n).count() >= n)


def _run_01(sig: pd.Series, r: pd.Series, rf: pd.Series, name: str, start) -> pd.DataFrame:
    tgt = sig.to_frame(name)
    rets = r.to_frame(name)
    res = simulate(tgt, rets, rf, cost_bps=COST_BPS, lag=2)
    return res.loc[res.index >= start]


def _compute_market(mkt: str) -> pd.DataFrame:
    idx_t = MARKETS[mkt][0]
    cache = DATA_DIR / f"signals_jm_{mkt}.parquet"
    px = fetch(idx_t)["Close"]
    r = px.pct_change().dropna()
    use_rf = MARKETS[mkt][2]
    rf = tbill_daily(r.index) if use_rf else pd.Series(0.0, index=r.index)
    ex = r - rf
    print(f"  [JM] fitting {mkt} ({idx_t}) ...", flush=True)
    labels = jm_online_labels(ex)
    sig_cv, chosen = select_lambda(labels, r, rf)
    print(f"  [HMM] fitting {mkt} ...", flush=True)
    hmm = hmm_online_bull(ex)
    df = labels.copy()
    df["jm_cv"] = sig_cv
    df["lam_chosen"] = chosen.astype(str)
    df = df.join(hmm.rename("hmm"), how="outer").join(ma_bull(px).rename("ma200"), how="outer")
    df.to_parquet(cache)
    return df


def compute_signals(refresh_signals: bool = False, parallel: bool = True) -> dict:
    """Compute (and cache to data/signals_jm_<mkt>.parquet) JM / HMM / MA signals for
    each local index. Markets are fitted in parallel processes (slow part: ~1-2 s per
    jump-model fit x 5 lambdas x ~90 semi-annual refits)."""
    sigs, todo = {}, []
    for mkt, (idx_t, _, _) in MARKETS.items():
        cache = DATA_DIR / f"signals_jm_{mkt}.parquet"
        px = fetch(idx_t)["Close"]
        if cache.exists() and not refresh_signals:
            df = pd.read_parquet(cache)
            if df.index[-1] >= px.index[-1] - pd.Timedelta(days=10):
                sigs[mkt] = df
                continue
        todo.append(mkt)
    if todo and parallel and len(todo) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=min(4, len(todo))) as ex:
            for mkt, df in zip(todo, ex.map(_compute_market, todo)):
                sigs[mkt] = df
    else:
        for mkt in todo:
            sigs[mkt] = _compute_market(mkt)
    return sigs


def run(refresh_signals: bool = False):
    sigs = compute_signals(refresh_signals)
    rows, curves_all, dsr = [], {}, []
    for mkt, (idx_t, etfs, use_rf) in MARKETS.items():
        S = sigs[mkt]
        # ---------- (a) local index
        px = fetch(idx_t)["Close"]
        r = px.pct_change()
        rf = tbill_daily(r.index) if use_rf else pd.Series(0.0, index=r.index)
        start = max(EVAL_START_INDEX, S["jm_cv"].first_valid_index() + pd.Timedelta(days=3))
        curves, variants = {}, []
        bh = r.loc[r.index >= start]
        curves["Buy&Hold"] = bh
        rows.append(metrics(bh, rf, f"JM:{mkt}:index:BuyHold", "1_JumpModel", mkt,
                            f"{idx_t} price index, local ccy"))
        specs = ([("jm_cv", "JM(CV-lambda)"), ("hmm", "HMM-2state"), ("ma200", "SMA200")]
                 + [(c, f"JM({c})") for c in S.columns if c.startswith("lam") and c != "lam_chosen"])
        for col, lab in specs:
            sig = S[col].reindex(r.index).ffill()
            res = _run_01(sig.fillna(0), r, rf, lab, start)
            nm = f"JM:{mkt}:index:{lab}"
            rows.append(metrics(res, rf, nm, "1_JumpModel", mkt,
                                f"{idx_t}; 10bp; lag1d; cash={'T-bill' if use_rf else '0%'}"))
            variants.append(res["ret"].rename(nm))
            if not col.startswith("lam"):
                curves[lab] = res["ret"]
        plot_equity(curves, f"Jump-model regime filter - {mkt} ({idx_t}, local index)",
                    f"jm_{mkt}_index.png")
        n_mkt = len(variants) + 3 * len(etfs)  # all variants tried on this market
        dsr.append(deflated_sharpe(variants, f"1_JumpModel:{mkt}:index", rf, n_trials=n_mkt, bench=bh.rename("BuyHold")))
        curves_all[f"{mkt} index"] = curves
        # ---------- (b) US-listed ETF, signal from the local index
        for etf in etfs:
            epx = closes([etf], calendar=etf)[etf]
            er = epx.pct_change()
            erf = tbill_daily(er.index)
            st = max(er.first_valid_index() + pd.Timedelta(days=5),
                     S["jm_cv"].first_valid_index() + pd.Timedelta(days=3))
            ec = {"Buy&Hold": er.loc[er.index >= st]}
            evars = []
            rows.append(metrics(ec["Buy&Hold"], erf, f"JM:{mkt}:{etf}:BuyHold", "1_JumpModel", mkt,
                                f"{etf} USD total return"))
            # index-calendar signal -> ETF calendar (as-of; index close precedes US close)
            for col, lab in [("jm_cv", "JM(CV-lambda)"), ("hmm", "HMM-2state"), ("ma200", "SMA200")]:
                sig = S[col].dropna()
                sig = sig.reindex(sig.index.union(er.index)).ffill().reindex(er.index)
                res = _run_01(sig.fillna(0), er, erf, lab, st)
                nm = f"JM:{mkt}:{etf}:{lab}"
                rows.append(metrics(res, erf, nm, "1_JumpModel", mkt,
                                    f"signal {idx_t}, trade {etf}; 10bp; lag1d; cash=T-bill"))
                evars.append(res["ret"].rename(nm))
                ec[lab] = res["ret"]
            plot_equity(ec, f"Jump-model regime filter - {mkt}: signal {idx_t}, traded {etf} (USD)",
                        f"jm_{mkt}_{etf}.png")
            dsr.append(deflated_sharpe(evars, f"1_JumpModel:{mkt}:{etf}", erf, n_trials=n_mkt, bench=ec["Buy&Hold"].rename(f"{etf} BuyHold")))
    lam_usage = {m: sigs[m]["lam_chosen"].replace("nan", np.nan).dropna().value_counts(normalize=True)
                 .round(2).to_dict() for m in sigs}
    return pd.DataFrame(rows), dsr, {"lambda_usage": lam_usage}


if __name__ == "__main__":
    df, dsr, extra = run()
    pd.set_option("display.width", 250)
    print(df[["strategy", "start", "CAGR", "Vol", "Sharpe", "MaxDD", "Turnover", "IS_Sharpe", "OOS_Sharpe"]]
          .round(3).to_string())
    print(dsr, extra)
