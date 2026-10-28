"""Formulaic-alpha DSL (Qlib / Alpha101 style) and the frozen referee.

Expressions are nested tuples:  ("op", arg1, arg2, ...); leaves are field names (str) or ints (windows).
  cross-sectional : rank(x), zscore(x), neg(x), abs(x), sign(x), slog(x) = sign*log1p|x|
  arithmetic      : add, sub, mul, div (safe)
  time-series     : ts_mean, ts_std, ts_sum, ts_delta, ts_delay, ts_max, ts_min, ts_rank, ts_zscore, decay(x, d)
  two-series      : ts_corr(x, y, d), ts_cov(x, y, d)
Evaluation is vectorised over the full (dates x stocks) grid with a per-run memo.

Referee (protocol fixed before any mining; the sealed test is never read here). Validity safeguards were added after
the first GP run admitted constant/ultra-sparse expressions whose 'IC' was floating-point tie noise:
  data      : month-end factor values vs the next-21-day excess return, monthly rank IC
  TRAIN     : 2010-01 .. 2017-12   -> sign and |IC t| >= 3.0 (>= 24 valid months)
  VALID     : 2018-01 .. 2021-12   -> same sign and IC t >= 1.5 (>= 18 valid months)
  redundancy: |mean cross-sectional rank corr| < 0.6 with every previously admitted alpha (TRAIN months)
  complexity: depth <= 4
Fields that start late (svr 2018-08, wiki 2015-07) are judged on the months they cover; an alpha needs >= 24 TRAIN
months, so svr-based alphas cannot be admitted (documented).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRAIN = ("2010-01-01", "2017-12-31")
VALID = ("2018-01-01", "2021-12-31")
TEST = ("2022-01-01", "2026-12-31")
T_TRAIN, T_VALID, MAX_CORR, MAX_DEPTH = 3.0, 1.5, 0.6, 4
H = 21

UNARY = ["rank", "zscore", "neg", "abs", "sign", "slog"]
BINARY = ["add", "sub", "mul", "div"]
TS = ["ts_mean", "ts_std", "ts_sum", "ts_delta", "ts_delay", "ts_max", "ts_min", "ts_rank", "ts_zscore", "decay"]
TS2 = ["ts_corr", "ts_cov"]
WINDOWS = [5, 10, 21, 63, 126, 252]


def to_str(e) -> str:
    if isinstance(e, (str, int, float)):
        return str(e)
    return f"{e[0]}(" + ", ".join(to_str(a) for a in e[1:]) + ")"


def depth(e) -> int:
    if not isinstance(e, tuple):
        return 0
    return 1 + max(depth(a) for a in e[1:])


def fields_used(e) -> set:
    if isinstance(e, str):
        return {e}
    if isinstance(e, tuple):
        return set().union(*[fields_used(a) for a in e[1:]])
    return set()


class Evaluator:
    def __init__(self, F: dict[str, pd.DataFrame]):
        self.F = F
        self.memo: dict[str, pd.DataFrame] = {}

    def __call__(self, e) -> pd.DataFrame:
        if isinstance(e, str):
            return self.F[e]
        key = to_str(e)
        if key in self.memo:
            return self.memo[key]
        op, args = e[0], e[1:]
        if op in UNARY:
            x = self(args[0])
            out = {"rank": lambda: x.rank(axis=1, pct=True) - 0.5,
                   "zscore": lambda: x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1) + 1e-12, axis=0),
                   "neg": lambda: -x, "abs": lambda: x.abs(), "sign": lambda: np.sign(x),
                   "slog": lambda: np.sign(x) * np.log1p(x.abs())}[op]()
        elif op in BINARY:
            a, b = self(args[0]), self(args[1])
            if op == "div":
                out = a / b.where(b.abs() > 1e-12)
            else:
                out = {"add": a + b, "sub": a - b, "mul": a * b}[op]
        elif op in TS:
            x, d = self(args[0]), int(args[1])
            r = x.rolling(d, min_periods=min(d, max(2, d // 2)))
            if op == "ts_mean":
                out = r.mean()
            elif op == "ts_std":
                out = r.std()
            elif op == "ts_sum":
                out = r.sum()
            elif op == "ts_delta":
                out = x - x.shift(d)
            elif op == "ts_delay":
                out = x.shift(d)
            elif op == "ts_max":
                out = r.max()
            elif op == "ts_min":
                out = r.min()
            elif op == "ts_rank":
                out = r.rank(pct=True)
            elif op == "ts_zscore":
                out = (x - r.mean()) / (r.std() + 1e-12)
            else:                                                           # decay: linearly weighted mean
                w = np.arange(1, d + 1, dtype=float)
                w /= w.sum()
                arr = x.to_numpy()
                res = np.full_like(arr, np.nan, dtype=float)
                for i in range(d - 1, len(arr)):
                    res[i] = np.nansum(arr[i - d + 1:i + 1] * w[:, None], axis=0)
                out = pd.DataFrame(res, x.index, x.columns)
        elif op in TS2:
            a, b, d = self(args[0]), self(args[1]), int(args[2])
            out = a.rolling(d, min_periods=d // 2).corr(b) if op == "ts_corr" else a.rolling(d, min_periods=d // 2).cov(b)
        else:
            raise ValueError(op)
        out = out.replace([np.inf, -np.inf], np.nan)
        if len(self.memo) > 400:
            self.memo.clear()
        self.memo[key] = out
        return out


class Referee:
    """Frozen admission protocol. Never reads TEST months."""

    def __init__(self, F, P):
        R = P["R"]
        idx = R.index
        me = pd.Series(idx, idx).groupby([idx.year, idx.month]).max()
        me = [d for d in me if d <= pd.Timestamp(VALID[1])]                    # TEST months excluded by design
        self.months = pd.DatetimeIndex(me)
        fwd = R.shift(-1).rolling(H).sum().shift(-(H - 1))
        self.fwd_rank = fwd.loc[self.months].rank(axis=1, pct=True)
        self.train = self.months[(self.months >= TRAIN[0]) & (self.months <= TRAIN[1])]
        self.valid = self.months[(self.months >= VALID[0]) & (self.months <= VALID[1])]
        self.admitted: list[dict] = []
        self.admitted_ranks: list[pd.DataFrame] = []
        self.log: list[dict] = []

    @staticmethod
    def _t(ic):
        ic = ic.dropna()
        return (ic.mean() / ic.std() * np.sqrt(len(ic)) if len(ic) > 2 and ic.std() > 0 else 0.0), len(ic)

    @staticmethod
    def valid_months(x: pd.DataFrame) -> pd.Series:
        """Deterministic validity safeguard (Hubble-style): a month counts only if >= 100 names have values,
        >= 10 distinct values exist and no single value covers > 90% of names (rejects constants, floating-point
        noise and ultra-sparse event factors whose 'IC' is a tie artefact)."""
        a = x.to_numpy(dtype=float)
        ok = []
        for row in a:
            v = row[np.isfinite(row)]
            if len(v) < 100:
                ok.append(False)
                continue
            scale = np.abs(v).max()
            v = np.round(v / scale, 9) if scale > 0 else v        # relative rounding: kills fp noise, keeps tiny-unit fields
            _, cnt = np.unique(v, return_counts=True)
            ok.append(len(cnt) >= 10 and cnt.max() / len(v) <= 0.9)
        return pd.Series(ok, index=x.index)

    def ic_series(self, f: pd.DataFrame) -> pd.Series:
        x = f.loc[self.months]
        ok = self.valid_months(x)
        return x.rank(axis=1, pct=True).corrwith(self.fwd_rank, axis=1).where(ok)

    @staticmethod
    def degenerate(ic: pd.Series) -> bool:
        ic = ic.dropna()
        return len(ic) < 3 or ic.std() < 1e-4 or abs(ic.mean()) < 0.005

    def judge(self, e, F_eval: Evaluator, source: str, rationale: str = "") -> dict:
        rec = dict(expr=to_str(e), source=source, rationale=rationale, depth=depth(e), admitted=False, reason="")
        if depth(e) > MAX_DEPTH:
            rec["reason"] = "too deep"
            self.log.append(rec)
            return rec
        try:
            f = F_eval(e)
        except Exception as ex:  # noqa: BLE001
            rec["reason"] = f"eval error {ex}"
            self.log.append(rec)
            return rec
        ic = self.ic_series(f)
        t_tr, n_tr = self._t(ic.loc[self.train])
        t_va, n_va = self._t(ic.loc[self.valid])
        sign = np.sign(t_tr) if t_tr != 0 else 1.0
        rec.update(IC_train=float(ic.loc[self.train].mean()), t_train=float(t_tr), n_train=n_tr,
                   IC_valid=float(ic.loc[self.valid].mean()), t_valid=float(t_va), n_valid=n_va, sign=float(sign))
        if self.degenerate(ic.loc[self.train]):
            rec["reason"] = "degenerate (constant / sparse / |IC| < 0.005)"
        elif n_tr < 24 or abs(t_tr) < T_TRAIN:
            rec["reason"] = f"train |t| {abs(t_tr):.2f} < {T_TRAIN} or months {n_tr}"
        elif n_va < 18 or sign * t_va < T_VALID:
            rec["reason"] = f"valid signed t {sign * t_va:.2f} < {T_VALID}"
        else:
            rk = (sign * f.loc[self.train]).rank(axis=1, pct=True)
            mx = 0.0
            for other in self.admitted_ranks:
                mx = max(mx, abs(rk.corrwith(other, axis=1).mean()))
            rec["max_corr_admitted"] = float(mx)
            if mx >= MAX_CORR:
                rec["reason"] = f"redundant (|rho| {mx:.2f})"
            else:
                rec["admitted"] = True
                rec["reason"] = "admitted"
                self.admitted.append(dict(rec, tree=e))
                self.admitted_ranks.append(rk)
        self.log.append(rec)
        return rec

    def fitness(self, e, F_eval: Evaluator) -> float:
        """GP fitness: TRAIN months only (|IC t| minus a depth penalty minus redundancy); never VALID/TEST."""
        try:
            f = F_eval(e)
        except Exception:  # noqa: BLE001
            return -9.0
        ic = self.ic_series(f).loc[self.train]
        t, n = self._t(ic)
        if n < 24 or self.degenerate(ic):
            return -9.0
        pen = 0.0
        if self.admitted_ranks:
            rk = (np.sign(t) * f.loc[self.train[::3]]).rank(axis=1, pct=True)
            pen = max(abs(rk.corrwith(o.loc[self.train[::3]], axis=1).mean()) for o in self.admitted_ranks)
        return abs(t) - 0.15 * depth(e) - 3.0 * max(0.0, pen - 0.4)
