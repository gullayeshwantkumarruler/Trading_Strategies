"""Robustness and data-snooping tests used to rank the price-action strategies (round 5b).

All functions take daily (or per-bar) net return series. Methods:
  sharpe_ci        stationary-bootstrap 95% CI of the annualised Sharpe (Politis-Romano, arch)
  lo_sharpe        Lo (2002) autocorrelation-adjusted annualised Sharpe
  min_trl          minimum track record length (years) for Sharpe > 0 at 95% (Bailey & Lopez de Prado 2012)
  sharpe_diff      Ledoit-Wolf (2008) studentised-bootstrap test of Sharpe(strategy) - Sharpe(benchmark)
  alpha_beta       OLS on the benchmark with Newey-West t-stats
  spa              Hansen (2005) SPA and White reality-check p-values for "best beats benchmark" (arch)
  stepm            Romano-Wolf StepM: which strategies beat the benchmark controlling FWER (arch)
  pbo              probability of backtest overfitting via CSCV (Bailey, Borwein, Lopez de Prado & Zhu 2017)
  haircut_sharpe   Harvey-Liu (2015) Holm/BHY haircut of a Sharpe for N trials
  yearly_hit       share of calendar years with positive excess return over the benchmark
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats


def _sr(x, ppy):
    s = np.std(x, ddof=1)
    return 0.0 if s == 0 else np.mean(x) / s * np.sqrt(ppy)


def sharpe_ci(r: pd.Series, ppy: float = 252, reps: int = 1000, block: int = 20, seed: int = 0):
    from arch.bootstrap import StationaryBootstrap
    bs = StationaryBootstrap(block, r.values, seed=seed)
    draws = np.array([_sr(d[0][0], ppy) for d in bs.bootstrap(reps)])
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def lo_sharpe(r: pd.Series, ppy: float = 252, q: int | None = None) -> float:
    """Lo (2002): SR_ann = SR_period * ppy / sqrt(ppy + 2 sum_k (ppy-k) rho_k)."""
    x = r.values
    q = int(ppy) if q is None else q
    q = min(q, len(x) // 4)
    sr = np.mean(x) / np.std(x, ddof=1)
    rho = [pd.Series(x).autocorr(k) for k in range(1, q)]
    rho = np.nan_to_num(rho)
    eta = q / np.sqrt(q + 2 * np.sum([(q - k) * rho[k - 1] for k in range(1, q)]))
    return float(sr * eta * np.sqrt(ppy / q))


def min_trl(r: pd.Series, ppy: float = 252, sr_star: float = 0.0, alpha: float = 0.05) -> float:
    x = r.values
    sr = np.mean(x) / np.std(x, ddof=1)
    if sr <= sr_star / np.sqrt(ppy):
        return np.inf
    g3, g4 = stats.skew(x), stats.kurtosis(x, fisher=False)
    z = stats.norm.ppf(1 - alpha)
    n = 1 + (1 - g3 * sr + (g4 - 1) / 4 * sr ** 2) * (z / (sr - sr_star / np.sqrt(ppy))) ** 2
    return float(n / ppy)


def sharpe_diff(r: pd.Series, b: pd.Series, ppy: float = 252, reps: int = 1000, block: int = 20, seed: int = 0):
    """Ledoit-Wolf style: circular block bootstrap of the Sharpe difference; returns (diff, two-sided p)."""
    from arch.bootstrap import CircularBlockBootstrap
    j = pd.concat([r, b], axis=1).dropna().values
    d0 = _sr(j[:, 0], ppy) - _sr(j[:, 1], ppy)
    bs = CircularBlockBootstrap(block, j, seed=seed)
    d = np.array([_sr(x[0][0][:, 0], ppy) - _sr(x[0][0][:, 1], ppy) for x in bs.bootstrap(reps)])
    se = d.std(ddof=1)
    p = 2 * (1 - stats.norm.cdf(abs(d0) / se)) if se > 0 else 1.0
    return float(d0), float(p)


def alpha_beta(r: pd.Series, b: pd.Series, ppy: float = 252, lags: int = 5):
    import statsmodels.api as sm
    j = pd.concat([r, b], axis=1).dropna()
    res = sm.OLS(j.iloc[:, 0], sm.add_constant(j.iloc[:, 1])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return dict(alpha_ann=float(res.params.iloc[0] * ppy), alpha_t=float(res.tvalues.iloc[0]),
                beta=float(res.params.iloc[1]))


def spa(R: pd.DataFrame, bench: pd.Series, reps: int = 1000, block: int = 20, seed: int = 0) -> dict:
    """Losses = -returns. Null: no strategy beats the benchmark."""
    from arch.bootstrap import SPA
    j = R.join(bench.rename("_b"), how="inner").fillna(0.0)
    s = SPA(-j["_b"].values, -j.drop(columns="_b").values, block_size=block, reps=reps, seed=seed)
    s.compute()
    p = s.pvalues
    return dict(spa_consistent=float(p["consistent"]), spa_lower=float(p["lower"]), reality_check=float(p["upper"]))


def stepm(R: pd.DataFrame, bench: pd.Series, reps: int = 1000, block: int = 20, size: float = 0.05,
          seed: int = 0) -> list[str]:
    from arch.bootstrap import StepM
    j = R.join(bench.rename("_b"), how="inner").fillna(0.0)
    m = j.drop(columns="_b")
    s = StepM(-j["_b"].values, -m.values, size=size, block_size=block, reps=reps, seed=seed)
    s.compute()
    return [m.columns[i] for i in s.superior_models] if len(s.superior_models) else []


def pbo(R: pd.DataFrame, n_splits: int = 16, ppy: float = 252) -> dict:
    """CSCV: split time into S blocks; for each half/half combination pick the in-sample best by Sharpe and
    record the relative rank of that pick out of sample. PBO = share of combinations where it ranks below median."""
    X = R.fillna(0.0).values
    T, N = X.shape
    S = n_splits - n_splits % 2
    blocks = np.array_split(np.arange(T), S)
    logits, degr = [], []
    for c in combinations(range(S), S // 2):
        ins = np.concatenate([blocks[i] for i in c])
        oos = np.concatenate([blocks[i] for i in range(S) if i not in c])
        sr_i = np.array([_sr(X[ins, k], ppy) for k in range(N)])
        sr_o = np.array([_sr(X[oos, k], ppy) for k in range(N)])
        best = int(np.argmax(sr_i))
        w = (stats.rankdata(sr_o)[best]) / (N + 1)
        logits.append(np.log(w / (1 - w)))
        degr.append((sr_i[best], sr_o[best]))
    logits = np.array(logits)
    d = np.array(degr)
    slope = np.polyfit(d[:, 0], d[:, 1], 1)[0] if len(d) > 2 else np.nan
    return dict(pbo=float((logits <= 0).mean()), n_combos=len(logits), oos_sr_of_is_best=float(d[:, 1].mean()),
                is_oos_slope=float(slope))


def haircut_sharpe(sr_ann: float, n_obs: int, n_trials: int, ppy: float = 252, method: str = "bhy") -> float:
    """Harvey & Liu (2015): convert SR to a p-value, adjust for n_trials (Holm or BHY), convert back."""
    if sr_ann <= 0:
        return 0.0
    t = sr_ann * np.sqrt(n_obs / ppy)
    p = 2 * (1 - stats.norm.cdf(t))
    if method == "holm":
        p_adj = min(1.0, p * n_trials)
    else:  # BHY with the single-test approximation used by Harvey & Liu for the top-ranked strategy
        c = np.sum(1.0 / np.arange(1, n_trials + 1))
        p_adj = min(1.0, p * n_trials * c)
    if p_adj >= 1:
        return 0.0
    t_adj = stats.norm.ppf(1 - p_adj / 2)
    return float(t_adj / np.sqrt(n_obs / ppy))


def yearly_hit(r: pd.Series, b: pd.Series) -> float:
    j = pd.concat([r, b], axis=1).dropna()
    y = (1 + j).groupby(j.index.year).prod() - 1
    return float((y.iloc[:, 0] > y.iloc[:, 1]).mean())


def implied_spread_bps(df: pd.DataFrame) -> float:
    """Abdi & Ranaldo (2017) close-high-low spread estimator, median over 21-day windows, in bps."""
    c, h, l = np.log(df["Close"]), np.log(df["High"]), np.log(df["Low"])
    eta = (h + l) / 2
    v = 4 * (c - eta) * (c - eta.shift(-1))
    s2 = v.rolling(21).mean().clip(lower=0)
    return float(np.sqrt(s2).median() * 1e4)
