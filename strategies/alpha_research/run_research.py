"""Alpha-research pipeline: mining (agent + GP) under a frozen referee, then a one-shot sealed test.

Phase A (mining, data truncated at 2021-12-31):
  1. agent proposals (agent_alphas.py)            -> library "agent"
  2. GP miner                                      -> library "gp"
  3. union: agent admits first, then GP admits re-checked for redundancy -> library "union"
Phase B (sealed test 2022-01 -> 2026-08, run once):
  per-alpha test IC; composites per library (EW sign-weighted rank, ridge, LightGBM; models trained on months
  <= 2021-12 then frozen); monthly quintile L/S net of 5 bp + 1 bp/day shorts; cost-aware optimiser (step 4) with
  gamma chosen on 2018-2021; comparison with the round-3 composite on the same months; deflated Sharpe.
"""
from __future__ import annotations

import argparse
import json
import pickle

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

import dsl
import fields
import gp
from agent_alphas import PROPOSALS

core = fields.core
CUT = pd.Timestamp("2021-12-31")


def mining(F_full, P, gens, pop, log):
    F_mine = {k: v.loc[:CUT] for k, v in F_full.items()}             # sealed test physically removed
    ev = dsl.Evaluator(F_mine)
    libs, logs = {}, []
    ref_a = dsl.Referee(F_mine, P)
    for e, why in PROPOSALS:
        ref_a.judge(e, ev, "agent", why)
    libs["agent"] = ref_a.admitted
    logs += ref_a.log
    log(f"agent: {len(ref_a.admitted)}/{len(PROPOSALS)} admitted")
    ref_g = dsl.Referee(F_mine, P)
    gp.run(ev, ref_g, pop_size=pop, gens=gens, seed=0, log=log)
    libs["gp"] = ref_g.admitted
    logs += [r for r in ref_g.log]
    log(f"gp: {len(ref_g.admitted)} admitted of {len(ref_g.log)} judged")
    ref_u = dsl.Referee(F_mine, P)
    for r in libs["agent"] + libs["gp"]:
        ref_u.judge(r["tree"], ev, "union:" + r["source"], r.get("rationale", ""))
    libs["union"] = ref_u.admitted
    log(f"union: {len(ref_u.admitted)} admitted")
    pd.DataFrame(logs).drop(columns=["tree"], errors="ignore").to_csv(fields.RES / "referee_log.csv", index=False)
    with open(fields.DATA / "libraries.pkl", "wb") as f:
        pickle.dump({k: [dict(r) for r in v] for k, v in libs.items()}, f)
    return libs


def month_ends(idx):
    return pd.DatetimeIndex(pd.Series(idx, idx).groupby([idx.year, idx.month]).max().to_list())


def sealed_test(F_full, P, libs, log):
    R = P["R"]
    ev = dsl.Evaluator(F_full)
    me = month_ends(R.index)
    me = me[me < R.index[-dsl.H - 1]]
    fwd = R.shift(-1).rolling(dsl.H).sum().shift(-(dsl.H - 1)).loc[me]
    fr = fwd.rank(axis=1, pct=True)
    test_m = me[me >= dsl.TEST[0]]
    fit_m = me[(me >= dsl.TRAIN[0]) & (me <= pd.Timestamp("2021-11-30"))]   # labels realised by 2021-12-31
    per_alpha, rows, curves = [], [], {}
    for name, lib in libs.items():
        if not lib:
            continue
        X = {}
        for r in lib:
            f = ev(r["tree"]).loc[me]
            X[r["expr"]] = (r["sign"] * f).rank(axis=1, pct=True) - 0.5
            ic = X[r["expr"]].corrwith(fr, axis=1)
            icT = ic.loc[test_m].dropna()
            per_alpha.append(dict(library=name, expr=r["expr"], source=r["source"], IC_train=r["sign"] * r["IC_train"],
                                  IC_valid=r["sign"] * r["IC_valid"], IC_test=icT.mean(),
                                  t_test=icT.mean() / icT.std() * np.sqrt(len(icT)) if len(icT) > 2 else np.nan))
        names = list(X)
        comps = {"EW": sum(X[n].fillna(0) for n in names) / len(names)}
        stack = lambda ds: np.nan_to_num(np.stack([X[n].loc[ds].to_numpy() for n in names], 2).reshape(-1, len(names)))
        ytr = (fr.loc[fit_m] - 0.5).to_numpy().reshape(-1)
        ok = np.isfinite(ytr)
        Xtr = stack(fit_m)
        models = {"ridge": Ridge(alpha=100.0).fit(Xtr[ok], ytr[ok]),
                  "LightGBM": lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=200,
                                                subsample=0.8, subsample_freq=1, colsample_bytree=0.7,
                                                verbose=-1).fit(Xtr[ok], ytr[ok])}
        for mname, m in models.items():
            comps[mname] = pd.DataFrame(m.predict(stack(me)).reshape(len(me), -1), me, R.columns)
        for cname, C in comps.items():
            C = C.where(F_full["close"].loc[me].notna())
            ic = C.rank(axis=1, pct=True).corrwith(fr, axis=1)
            icT = ic.loc[test_m].dropna()
            import step5_altdata as s5
            Wm = s5.monthly_ls(C, P)
            bt = core.backtest(Wm, start=dsl.TEST[0])
            d = core.summarize(bt, f"{name} {cname} monthly L/S [test]", "ar_test", {"lib": name, "comb": cname})
            d.update(library=name, combiner=cname, n_alphas=len(names), IC_test=icT.mean(),
                     IC_t_test=icT.mean() / icT.std() * np.sqrt(len(icT)))
            rows.append(d)
            curves[f"{name} {cname}"] = bt["net"]
            pd.to_pickle(C, fields.DATA / f"composite_{name}_{cname}.pkl")
        log(f"{name}: composites done")
    pa = pd.DataFrame(per_alpha)
    pa.to_csv(fields.RES / "alpha_test_ic.csv", index=False, float_format="%.4f")
    df = pd.DataFrame(rows)
    df.to_csv(fields.RES / "composites_test.csv", index=False, float_format="%.4f")
    return pa, df, curves


def optimiser_stage(P, libs_df, log):
    """Cost-aware optimiser (round-3 step 4) on the best composite per library; gamma chosen on 2018-2021."""
    import step4_alpha_library as s4
    rows, curves = [], {}
    for (lib, comb), _ in libs_df.groupby(["library", "combiner"]):
        if comb != "LightGBM" and comb != "EW":
            continue
        C = pd.read_pickle(fields.DATA / f"composite_{lib}_{comb}.pkl").loc["2017-12-01":]
        best, best_val = None, -9
        for g in (0.2, 0.5, 1.0):
            W = s4.blended_optimiser(P, C, 0.0, g)
            bt = core.backtest(W, start="2018-01-01")
            val = core.sr(bt.net.loc[:"2021-12-31"])
            if val > best_val:
                best, best_val, bestW = g, val, W
        bt = core.backtest(bestW, start=dsl.TEST[0])
        d = core.summarize(bt, f"{lib} {comb} optimiser g={best} [test]", "ar_test_opt",
                           {"lib": lib, "comb": comb, "g_trade": best, "val_SR": best_val})
        d.update(library=lib, combiner=comb, g_trade=best, val_SR_2018_21=best_val)
        rows.append(d)
        curves[f"{lib} {comb} opt"] = bt["net"]
        log(f"optimiser {lib}/{comb}: g={best} val SR {best_val:.2f} -> test SR {d['SR_net']:.2f}")
    return pd.DataFrame(rows), curves


def baseline_round3():
    out = []
    for key in ["s4_blend__optimiser_slow=LightGBM_fast_w=0.0_g=0.5", "s4_alpha__composite_LightGBM_monthly_L-S",
                "s3_dlsa__Attention_Factors_lite_K=10_cost-in-loss"]:
        p = core.TRIALS / f"{key}.parquet"
        if p.exists():
            s = pd.read_parquet(p).iloc[:, 0].loc[dsl.TEST[0]:]
            out.append(dict(strategy=f"round 3: {key}", SR_net_test=core.sr(s), ann_net=s.mean() * core.ANN))
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=30)
    ap.add_argument("--pop", type=int, default=200)
    ap.add_argument("--skip-mining", action="store_true")
    a = ap.parse_args(argv)
    log = core.Timer()
    P = core.panel()
    F = fields.build()
    log(f"fields: {len(F)}")
    if a.skip_mining:
        with open(fields.DATA / "libraries.pkl", "rb") as f:
            libs = pickle.load(f)
    else:
        libs = mining(F, P, a.gens, a.pop, log)
    for k, v in libs.items():
        print(f"\n== {k}: {len(v)} admitted", flush=True)
        for r in v:
            print(f"  t_tr {r['t_train']:+.2f} t_va {r['sign'] * r['t_valid']:+.2f}  {r['expr']}", flush=True)
    log("PHASE B — unsealing 2022-2026 (one shot)")
    pa, comp, curves = sealed_test(F, P, libs, log)
    opt, oc = optimiser_stage(P, comp, log)
    curves.update(oc)
    opt.to_csv(fields.RES / "optimiser_test.csv", index=False, float_format="%.4f")
    base = baseline_round3()
    base.to_csv(fields.RES / "baseline_round3_test.csv", index=False, float_format="%.4f")
    print(pa.to_string(index=False, float_format=lambda x: f"{x:.3f}"), flush=True)
    core.show(comp)
    core.show(opt)
    print(base.to_string(index=False), flush=True)
    # deflated Sharpe over all test-period variants
    from common import deflated_sharpe
    series = [c.rename(k) for k, c in curves.items()]
    d = deflated_sharpe(series, "alpha research test variants", n_trials=len(series))
    pd.DataFrame([d]).to_csv(fields.RES / "deflated_sharpe_test.csv", index=False)
    print(pd.Series(d).to_string(), flush=True)
    import shutil
    core.plot(curves, "Alpha research: sealed test 2022-2026 (net of 5bp + 1bp/day)", "alpha_research_test.png")
    src = core.RES / "alpha_research_test.png"
    if src.exists():
        shutil.move(str(src), str(fields.RES / "alpha_research_test.png"))
    log("done")


if __name__ == "__main__":
    main()
