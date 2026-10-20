"""End-to-end ML cross-sectional pipeline: ml4t-engineer -> ml4t-diagnostic -> ml4t-backtest.

Usage (from the project root):
    .venv\\Scripts\\python strategies\\ml\\run_all.py            # uses cached data/predictions
    .venv\\Scripts\\python strategies\\ml\\run_all.py --refresh  # re-download data, retrain everything
    .venv\\Scripts\\python strategies\\ml\\run_all.py --regions US JP --no-analyze

Outputs: strategies/ml/results/*.csv, *.png
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import polars as pl  # noqa: E402
import statsmodels.api as sm  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
warnings.filterwarnings("ignore")

from backtest import (build_weights, cn_limit, perf, run_engine,  # noqa: E402
                      vectorized, weekly_signal_dates)
from data_loader import load_region  # noqa: E402
from features import FEATURES, make_model_frame  # noqa: E402
from model import select_n_estimators, walk_forward_predict  # noqa: E402

RES = HERE / "results"
DATA = HERE / "data"
RES.mkdir(exist_ok=True)

REGIONS = ["US", "EU", "JP", "CN"]
SIGNALS = ["lgbm_5", "ridge_5", "lgbm_21", "rev_5"]  # rev_5 = pure short-term reversal baseline
BASE_COST = {"US": 10.0, "EU": 10.0, "JP": 10.0, "CN": 15.0}  # bp per side (commission+slippage)
COSTS = [0.0, 10.0, 20.0]
SPLIT = pd.Timestamp("2022-01-01")  # OOS first half vs second half


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ----------------------------------------------------------------------------- signals
def get_signals(region: str, mf: pd.DataFrame, refresh: bool) -> tuple[pd.DataFrame, dict]:
    path = DATA / f"preds_{region}.parquet"
    meta_path = DATA / f"preds_{region}_meta.json"
    if path.exists() and meta_path.exists() and not refresh:
        return pd.read_parquet(path), json.loads(meta_path.read_text())
    sig = None
    meta = {"folds": [], "cpcv": {}}
    imps = []
    for h in (5, 21):
        t0 = time.time()
        n_est, scores = select_n_estimators(mf, h)
        log(f"  {region} h={h}: CPCV (2013-2016 only) IC by n_estimators {scores} -> {n_est}")
        p, folds = walk_forward_predict(mf, h, n_est)
        log(f"  {region} h={h}: walk-forward {len(folds)} folds, {len(p):,} OOS rows ({time.time() - t0:.0f}s)")
        p = p.rename(columns={"lgbm": f"lgbm_{h}", "ridge": f"ridge_{h}"})
        sig = p if sig is None else sig.merge(p, on=["date", "asset"], how="outer")
        meta["cpcv"][str(h)] = {"chosen": n_est, "scores": {str(k): v for k, v in scores.items()}}
        for f in folds:
            meta["folds"].append({"h": h, **{k: str(v) for k, v in f.items() if k not in ("importance", "ridge_coef")}})
            imps.append(f["importance"].rename(f"h{h}_{f['test_start']}"))
    meta["importance_h5"] = pd.concat([i for i in imps if i.name.startswith("h5")], axis=1).mean(axis=1).to_dict()
    meta["importance_h21"] = pd.concat([i for i in imps if i.name.startswith("h21")], axis=1).mean(axis=1).to_dict()
    sig.to_parquet(path, index=False)
    meta_path.write_text(json.dumps(meta, indent=1, default=str))
    return sig, meta


# ----------------------------------------------------------------------------- IC
def nw_tstat(x: pd.Series, lags: int) -> float:
    x = x.dropna()
    if len(x) < 30:
        return np.nan
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(m.tvalues[0])


def daily_ic_series(df: pd.DataFrame, col: str, ycol: str) -> pd.Series:
    d = df[["date", col, ycol]].dropna()
    return d.groupby("date").apply(lambda g: g[col].corr(g[ycol], method="spearman"))


def run_analyze_signal(region, px, sig, col):
    """ml4t-diagnostic analyze_signal. price_t := open_{t+1}, so forward returns are
    open(t+1)->open(t+1+k), i.e. tradable after the close-t signal."""
    from ml4t.diagnostic import analyze_signal

    cache = RES / f"analyze_signal_{region}_{col}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    p = px.sort_values(["asset", "date"]).copy()
    p["price"] = p.groupby("asset")["open"].shift(-1)
    fac = pl.from_pandas(sig[["date", "asset", col]].dropna().rename(columns={col: "factor"}))
    pr = pl.from_pandas(p[["date", "asset", "price"]].dropna())
    res = analyze_signal(fac, pr, periods=(1, 5, 21), quantiles=5, filter_zscore=None)
    d = res.to_dict()
    keep = {k: d[k] for k in ("ic", "ic_t_stat", "ic_ir", "ic_positive_pct", "spread", "spread_t_stat",
                              "monotonicity", "turnover", "quantile_returns", "n_assets", "n_dates")}
    cache.write_text(json.dumps(keep, default=str))
    return keep


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download data and retrain")
    ap.add_argument("--retrain", action="store_true", help="retrain models (keep cached data)")
    ap.add_argument("--regions", nargs="*", default=REGIONS)
    ap.add_argument("--no-analyze", action="store_true", help="skip ml4t analyze_signal (slow)")
    args = ap.parse_args()
    if args.refresh:
        for f in RES.glob("analyze_signal_*.json"):
            f.unlink()

    rows_ic, rows_as, rows_bt, rows_cost, rows_sub, rows_rev, rows_imp, rows_fold, rows_cpcv = ([] for _ in range(9))
    base_returns = {}  # (region, signal, kind) -> net daily returns at base cost
    all_returns_for_plot = {}
    ic_ts = {}

    for region in args.regions:
        t_reg = time.time()
        log(f"=== {region} ===")
        px = load_region(region, refresh=args.refresh)
        mf = make_model_frame(px)
        log(f"  model frame {mf.shape}, {mf['asset'].nunique()} assets, features={len(FEATURES)}")
        sig, meta = get_signals(region, mf, args.refresh or args.retrain)
        for h, c in meta["cpcv"].items():
            rows_cpcv.append({"region": region, "horizon": int(h), "chosen_n_estimators": c["chosen"],
                              **{f"cpcv_ic_n{k}": v for k, v in c["scores"].items()}})
        for f in meta["folds"]:
            rows_fold.append({"region": region, **f})
        for h in ("5", "21"):
            for k, v in meta[f"importance_h{h}"].items():
                rows_imp.append({"region": region, "horizon": int(h), "feature": k, "gain_share": v})

        # attach labels, reversal baseline, helper data
        sig = sig.merge(mf[["date", "asset", "y_5", "y_21", "fwd_5", "fwd_21", "raw_r_5", "raw_resid_5", "ret1"]],
                        on=["date", "asset"], how="left")
        sig["rev_5"] = -sig["raw_r_5"]
        oos_start = sig["date"].min()

        # ---------------- IC (own, with Newey-West t-stats) ----------------
        for col in SIGNALS:
            for h in (5, 21):
                ics = daily_ic_series(sig, col, f"fwd_{h}")
                if col == "lgbm_5" and h == 5 or col == "rev_5" and h == 5:
                    ic_ts[(region, col)] = ics
                rows_ic.append({
                    "region": region, "signal": col, "horizon": h, "mean_ic": ics.mean(),
                    "ic_t_naive": ics.mean() / ics.std() * np.sqrt(len(ics)),
                    "ic_t_newey_west": nw_tstat(ics, lags=h),
                    "ic_nonoverlap_t": (lambda s: s.mean() / s.std() * np.sqrt(len(s)))(ics.iloc[::h]),
                    "ic_2017_2021": ics[ics.index < SPLIT].mean(), "ic_2022_2026": ics[ics.index >= SPLIT].mean(),
                    "pct_pos": (ics > 0).mean(), "n_days": len(ics)})
        # how much of the ML signal is reversal?
        cs_corr = sig.dropna(subset=["lgbm_5", "rev_5"]).groupby("date").apply(
            lambda g: g["lgbm_5"].corr(g["rev_5"], method="spearman")).mean()
        cs_corr_r = sig.dropna(subset=["ridge_5", "rev_5"]).groupby("date").apply(
            lambda g: g["ridge_5"].corr(g["rev_5"], method="spearman")).mean()

        # ---------------- ml4t analyze_signal ----------------
        if not args.no_analyze:
            for col in SIGNALS:
                t0 = time.time()
                d = run_analyze_signal(region, px, sig, col)
                for per in ("1D", "5D", "21D"):
                    rows_as.append({"region": region, "signal": col, "period": per, "ic": d["ic"][per],
                                    "ic_t_stat(lib,overlapping)": d["ic_t_stat"][per], "ic_ir": d["ic_ir"][per],
                                    "spread_Q5_Q1": d["spread"][per], "spread_t(lib)": d["spread_t_stat"][per],
                                    "monotonicity": d["monotonicity"][per], "turnover": d["turnover"][per],
                                    **{f"Q{q}": v for q, v in d["quantile_returns"][per].items()}})
                log(f"  analyze_signal {col} ({time.time() - t0:.0f}s)")

        # ---------------- backtests ----------------
        rd = [d for d in weekly_signal_dates(sig["date"]) if pd.Timestamp(d) >= oos_start]
        cn_flags = None
        if region == "CN":
            s = sig[["date", "asset", "ret1"]].dropna()
            lim = np.array([cn_limit(a, d) for a, d in zip(s["asset"], s["date"])])
            flag = np.where(s["ret1"].values >= lim - 0.003, 1, np.where(s["ret1"].values <= -lim + 0.003, -1, 0))
            s = s.assign(flag=flag)
            s = s[s["flag"] != 0]
            cn_flags = {}
            for d, a, f in zip(s["date"], s["asset"], s["flag"]):
                cn_flags.setdefault(pd.Timestamp(d), {})[a] = int(f)
            log(f"  CN limit flags: {sum(len(v) for v in cn_flags.values())} stock-days at +/- limit")
        kinds = ["LO"] if region == "CN" else ["LS", "LO"]
        configs = [(c, k) for c in SIGNALS for k in kinds] + [("ew", "EW")]
        sig["ew"] = 1.0
        for col, kind in configs:
            w = build_weights(sig, col, kind, region, rd)
            for cost in sorted(set(COSTS + [BASE_COST[region]])):
                r, res, strat = run_engine(px, w, cost, kind == "LS", oos_start, cn_flags if region == "CN" else None)
                pm = perf(r)
                row = {"region": region, "signal": col, "kind": kind, "cost_bp_per_side": cost, **pm,
                       "engine_trades": res.metrics.get("num_trades"),
                       "engine_costs_pct_init": (res.metrics.get("total_commission", 0) + res.metrics.get("total_slippage", 0)) / 1e7}
                if region == "CN":
                    row.update(blocked_limitup_buys=strat.blocked_buys, blocked_limitdown_sells=strat.blocked_sells)
                rows_cost.append(row)
                if cost == BASE_COST[region]:
                    base_returns[(region, col, kind)] = r
                    v, tov = vectorized(px, w, cost / 1e4, cost / 1e4, oos_start)
                    pv = perf(v)
                    brow = {**row, "vec_sharpe": pv["sharpe"], "vec_ann_ret": pv["ann_ret"],
                            "avg_oneway_turnover_per_rebal": tov.mean(),
                            "ann_turnover": tov.mean() * 52}
                    if region == "CN":
                        # exact cost: buy 2.5bp comm + 10bp slip; sell + stamp duty 10bp (<2023-08-28) / 5bp after
                        vs, _ = vectorized(px, w, 12.5e-4, lambda d: (12.5 + (10 if d < pd.Timestamp("2023-08-28") else 5)) * 1e-4, oos_start)
                        brow["vec_exact_stamp_sharpe"] = perf(vs)["sharpe"]
                        brow["vec_exact_stamp_ann_ret"] = perf(vs)["ann_ret"]
                    rows_bt.append(brow)
                    for name, sub in (("2017-2021", r[r.index < SPLIT]), ("2022-2026", r[r.index >= SPLIT])):
                        rows_sub.append({"region": region, "signal": col, "kind": kind, "period": name, **perf(sub)})
            log(f"  backtest {col}/{kind} done")
        # long-only: active return vs the EW universe benchmark (same costs, same rebalance)
        ew_r = base_returns[(region, "ew", "EW")]
        for row in rows_bt:
            if row["region"] == region and row["kind"] == "LO":
                a = (base_returns[(region, row["signal"], "LO")] - ew_r).dropna()
                row["active_ann_ret_vs_EW"] = a.mean() * 252
                row["tracking_err"] = a.std() * np.sqrt(252)
                row["info_ratio_vs_EW"] = a.mean() / a.std() * np.sqrt(252)
                row["active_t"] = nw_tstat(a, 5)
        # ML vs reversal regression on base-cost returns
        for kind in kinds:
            rv = base_returns[(region, "rev_5", kind)]
            for col in ("lgbm_5", "ridge_5", "lgbm_21"):
                y = base_returns[(region, col, kind)]
                dfr = pd.concat([y.rename("y"), rv.rename("rev")], axis=1).dropna()
                if kind == "LO":
                    ew = base_returns[(region, "ew", "EW")]
                    dfr = dfr.join(ew.rename("ew")).dropna()
                    Xr = sm.add_constant(dfr[["rev", "ew"]])
                else:
                    Xr = sm.add_constant(dfr[["rev"]])
                m = sm.OLS(dfr["y"], Xr).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
                rows_rev.append({"region": region, "kind": kind, "signal": col,
                                 "corr_with_rev_returns": dfr["y"].corr(dfr["rev"]),
                                 "avg_cs_rank_corr_pred_vs_rev5": cs_corr if col == "lgbm_5" else (cs_corr_r if col == "ridge_5" else np.nan),
                                 "alpha_ann": m.params["const"] * 252, "alpha_t": m.tvalues["const"],
                                 "beta_rev": m.params["rev"], "beta_rev_t": m.tvalues["rev"],
                                 "beta_ew": m.params.get("ew", np.nan), "r2": m.rsquared})
        all_returns_for_plot[region] = {k: v for k, v in base_returns.items() if k[0] == region}
        log(f"  {region} done in {time.time() - t_reg:.0f}s")

    # ---------------- DSR ----------------
    from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio

    rows_dsr = []
    strat_keys = [k for k in base_returns if k[1] != "ew"]

    def series_for(k, active):
        r = base_returns[k]
        if active and k[2] == "LO":  # long-only judged on return in excess of the EW universe
            r = (r - base_returns[(k[0], "ew", "EW")]).dropna()
        return r.rename("/".join(k))

    def dsr_rows(scope, keys, active, n_extra):
        mat = pd.concat([series_for(k, active) for k in keys], axis=1).fillna(0.0)
        cols = list(mat.columns)
        out = []
        for c in cols:
            psr = deflated_sharpe_ratio(mat[c].values, frequency="daily")
            out.append({"scope": scope, "returns": "active_vs_EW_for_LO" if active else "raw",
                        "strategy": c, "sharpe_ann": psr.sharpe_ratio_annualized,
                        "PSR_prob": psr.probability, "n_days": psr.n_samples})
        K = len(cols) + n_extra
        d_raw = deflated_sharpe_ratio([mat[c].values for c in cols], frequency="daily")
        d_k = deflated_sharpe_ratio([mat[c].values for c in cols], frequency="daily", effective_trials=K)
        d_er = deflated_sharpe_ratio([mat[c].values for c in cols], frequency="daily",
                                     correlation_method="effective_rank")
        best = cols[int(np.argmax((mat.mean() / mat.std()).values))]
        out.append({"scope": scope, "returns": "active_vs_EW_for_LO" if active else "raw",
                    "strategy": f"BEST={best}", "sharpe_ann": d_raw.sharpe_ratio_annualized,
                    "K_backtested": len(cols), "DSR_prob_K_backtested": d_raw.probability,
                    "K_incl_cpcv_grid": K, "DSR_prob_K_incl_grid": d_k.probability,
                    "K_eff_effective_rank": d_er.n_trials_effective, "DSR_prob_K_eff": d_er.probability})
        return out

    # trials: backtested configs + 3-value n_estimators grid x 2 horizons tried in CPCV per region
    for active in (False, True):
        for region in args.regions:
            rows_dsr += dsr_rows(region, [k for k in strat_keys if k[0] == region], active, 6)
        if len(args.regions) > 1:
            rows_dsr += [r for r in dsr_rows("ALL", strat_keys, active, 6 * len(args.regions))
                         if r["strategy"].startswith("BEST")]

    # ---------------- save tables ----------------
    def save(rows, name):
        if rows:
            pd.DataFrame(rows).to_csv(RES / name, index=False, float_format="%.5g")

    suffix = "" if args.regions == REGIONS else "_" + "_".join(args.regions)
    save(rows_bt, f"backtest_metrics{suffix}.csv")
    save(rows_cost, f"cost_sensitivity{suffix}.csv")
    save(rows_sub, f"subperiod_metrics{suffix}.csv")
    save(rows_ic, f"ic_summary{suffix}.csv")
    save(rows_as, f"analyze_signal_summary{suffix}.csv")
    save(rows_rev, f"ml_vs_reversal{suffix}.csv")
    save(rows_dsr, f"deflated_sharpe{suffix}.csv")
    save(rows_imp, f"feature_importance{suffix}.csv")
    save(rows_fold, f"walk_forward_folds{suffix}.csv")
    save(rows_cpcv, f"cpcv_model_selection{suffix}.csv")

    # ---------------- plots ----------------
    regs = args.regions
    fig, axes = plt.subplots(len(regs), 1, figsize=(11, 3.6 * len(regs)), squeeze=False)
    colors = {"lgbm_5": "C0", "ridge_5": "C1", "lgbm_21": "C2", "rev_5": "C3", "ew": "k"}
    for ax, region in zip(axes[:, 0], regs):
        for (rg, col, kind), r in all_returns_for_plot[region].items():
            ls = "-" if kind in ("LS",) else ("--" if kind == "LO" else ":")
            ax.plot((1 + r).cumprod(), ls, color=colors[col], lw=1.2 if col != "ew" else 1.8,
                    label=f"{col} {kind}")
        ax.set_yscale("log")
        ax.set_title(f"{region}: net cumulative return, weekly rebalance, {BASE_COST[region]:.0f} bp/side "
                     f"(solid = long-short, dashed = long-only, dotted = EW benchmark)")
        ax.legend(fontsize=7, ncol=5)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RES / f"cumulative_returns{suffix}.png", dpi=110)
    plt.close(fig)

    fig, axes = plt.subplots(len(regs), 1, figsize=(11, 2.8 * len(regs)), squeeze=False)
    for ax, region in zip(axes[:, 0], regs):
        for col, c in (("lgbm_5", "C0"), ("rev_5", "C3")):
            s = ic_ts.get((region, col))
            if s is not None:
                ax.plot(s.rolling(126).mean(), color=c, label=f"{col}: 126d rolling mean daily rank IC vs fwd 5d")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_title(f"{region}: out-of-sample information coefficient")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RES / f"ic_timeseries{suffix}.png", dpi=110)
    plt.close(fig)

    if rows_imp:
        imp = pd.DataFrame(rows_imp)
        imp = imp[imp["horizon"] == 5].pivot(index="feature", columns="region", values="gain_share")
        imp = imp.loc[imp.mean(axis=1).sort_values().index]
        ax = imp.plot.barh(figsize=(9, 8))
        ax.set_title("LightGBM (5d label) gain share, averaged over walk-forward folds")
        plt.tight_layout()
        plt.savefig(RES / f"feature_importance{suffix}.png", dpi=110)
        plt.close()

    if rows_cost:
        cs = pd.DataFrame(rows_cost)
        cs = cs[cs["cost_bp_per_side"].isin(COSTS) & (cs["signal"] != "ew")]
        cs["cfg"] = cs["region"] + " " + cs["signal"] + " " + cs["kind"]
        pv = cs.pivot(index="cfg", columns="cost_bp_per_side", values="sharpe")
        ax = pv.plot.barh(figsize=(9, 10))
        ax.set_xlabel("annualised Sharpe (net)")
        ax.set_title("Cost sensitivity (bp per side)")
        plt.tight_layout()
        plt.savefig(RES / f"cost_sensitivity{suffix}.png", dpi=110)
        plt.close()

    # console summary
    if rows_bt:
        bt = pd.DataFrame(rows_bt)
        print(bt[["region", "signal", "kind", "cost_bp_per_side", "ann_ret", "ann_vol", "sharpe", "max_dd",
                  "vec_sharpe", "ann_turnover"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    log("done")


if __name__ == "__main__":
    main()
