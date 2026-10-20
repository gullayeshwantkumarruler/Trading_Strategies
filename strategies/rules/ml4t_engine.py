"""End-to-end ML4T workflow: run two of the rules strategies through ml4t-backtest's
event-driven Engine and analyse them with ml4t-diagnostic.

 (a) Sector momentum, top-5 + 25% trend-gated short (strategy 5), 9 SPDR sectors
 (b) Jump-model regime filter on SPY (signal from ^GSPC JM, strategy 1)

Engine settings (verified against ml4t-backtest 0.1.12 source):
  BacktestConfig(commission_type=CommissionType.PERCENTAGE, commission_rate=0.0003,
                 slippage_type=SlippageType.PERCENTAGE, slippage_rate=0.0002,   # = 5 bp/side
                 share_type=ShareType.FRACTIONAL, allow_short_selling=True, allow_leverage=True,
                 execution_mode=ExecutionMode.NEXT_BAR)
  The feed has close prices only, so NEXT_BAR "open" fills fall back to the next bar's
  close: decision at close t -> fill at close t+1 (same as the vectorised simulator).
  The Engine pays no interest on cash, so the parity check compares against the
  vectorised simulator run with rf = 0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl

from common import RES_DIR, closes, metrics, plot_equity, returns, simulate, tbill_daily, trim_start


def _engine_cfg(cost_comm=0.0003, cost_slip=0.0002, short=True):
    from ml4t.backtest import BacktestConfig
    from ml4t.backtest.config import CommissionType, ShareType, SlippageType
    from ml4t.backtest.types import ExecutionMode
    return BacktestConfig(initial_cash=1_000_000.0,
                          commission_type=CommissionType.PERCENTAGE, commission_rate=cost_comm,
                          slippage_type=SlippageType.PERCENTAGE, slippage_rate=cost_slip,
                          share_type=ShareType.FRACTIONAL, allow_short_selling=short,
                          allow_leverage=True,  # margin account: avoids cash-check rejections at 100% long + 25% short
                          execution_mode=ExecutionMode.NEXT_BAR)


def _to_feed(px: pd.DataFrame) -> pl.DataFrame:
    long = (px.stack().rename("close").reset_index()
            .rename(columns={px.index.name or "level_0": "timestamp", "level_1": "asset"}))
    long.columns = ["timestamp", "asset", "close"]
    return pl.from_pandas(long).sort(["timestamp", "asset"])


def _make_strategy(target_by_date: dict):
    from ml4t.backtest import Strategy

    class TargetWeights(Strategy):
        """Rebalances to precomputed (causal) target weights on signal dates."""

        def __init__(self, targets):
            self.targets = targets

        def on_data(self, timestamp, data, context, broker):
            w = self.targets.get(pd.Timestamp(timestamp))
            if w is not None:
                broker.rebalance_to_weights({a: float(x) for a, x in w.items() if a in data or x == 0})

    return TargetWeights(target_by_date)


def _run_engine(px: pd.DataFrame, W: pd.DataFrame, cfg):
    from ml4t.backtest import DataFeed, Engine
    targets = {d: row for d, row in W.dropna(how="all").iterrows()}
    eng = Engine(DataFeed(prices_df=_to_feed(px)), _make_strategy(targets), cfg)
    res = eng.run()
    eq = res.to_equity_dataframe().to_pandas().set_index("timestamp")
    return res, eq


def run():
    from sector import SECT9, sector_weights
    rows, notes = [], {}
    # ------------------------------------------------------------ (a) sector momentum
    px = closes(SECT9, calendar="SPY")
    px = px.loc[px.index >= "1998-12-01"]
    r = returns(px)
    rf = tbill_daily(r.index)
    W, me, _ = sector_weights(px, r, top_n=5, short_w=0.25, gate=True)
    Wm = W[me].dropna(how="all")
    res, eq = _run_engine(px, Wm, _engine_cfg())
    eng_ret = eq["return"].fillna(0.0)
    first = Wm.index[0]
    eng_ret = eng_ret.loc[eng_ret.index > first]
    vec0 = simulate(W, r, None, cost_bps=5.0, rebal=me, lag=2).loc[eng_ret.index]
    rows.append(metrics(eng_ret, rf, "ENGINE:Sector:9S:top5+short25%(gated)", "5_SectorMomentum", "US",
                        "ml4t-backtest Engine, 3bp comm + 2bp slippage, NEXT_BAR, no cash interest"))
    rows.append(metrics(vec0, rf, "VECTOR(rf=0):Sector:9S:top5+short25%(gated)", "5_SectorMomentum", "US",
                        "vectorised simulator, 5bp, rf=0 (parity check)"))
    corr = float(np.corrcoef(eng_ret, vec0["ret"])[0, 1])
    te = float((eng_ret - vec0["ret"]).std() * np.sqrt(252))
    notes["sector_parity"] = dict(daily_corr=corr, tracking_error_ann=te,
                                  engine_final_value=float(res.metrics["final_value"]),
                                  engine_total_commission=float(res.metrics["total_commission"]),
                                  engine_total_slippage=float(res.metrics["total_slippage"]),
                                  engine_num_fills=int(res.metrics["num_fills"]),
                                  engine_sharpe_reported=float(res.metrics["sharpe"]),
                                  engine_cagr_reported=float(res.metrics["cagr"]))
    plot_equity({"ml4t Engine": eng_ret, "Vectorised (rf=0)": vec0["ret"]},
                "Sector momentum top5 + gated short: ml4t-backtest Engine vs vectorised", "engine_sector.png")
    # ml4t-diagnostic portfolio analysis on the engine result
    try:
        from ml4t.diagnostic.integration import portfolio_analysis_from_result
        pa = portfolio_analysis_from_result(res)
        stats = pa.compute_summary_stats()
        d = stats.to_dict() if hasattr(stats, "to_dict") else {k: getattr(stats, k) for k in dir(stats)
                                                             if not k.startswith("_")}
        notes["sector_diag_summary"] = {k: (round(float(v), 4) if isinstance(v, (int, float, np.floating)) else v)
                                        for k, v in d.items() if isinstance(v, (int, float, np.floating))}
    except Exception as e:
        notes["sector_diag_summary"] = f"FAILED: {e.__class__.__name__}: {e}"

    # ------------------------------------------------------------ (b) JM regime filter on SPY
    try:
        from jump_model import compute_signals
        S = compute_signals()["US"]["jm_cv"].dropna()
        spx = closes(["SPY"], calendar="SPY")
        spx = spx.loc[spx.index >= "1999-01-01"]
        sr = returns(spx)
        sig = S.reindex(S.index.union(spx.index)).ffill().reindex(spx.index)
        st = sig.first_valid_index()
        sig = sig.loc[st:]
        chg = sig.diff().fillna(1.0) != 0
        Wj = sig.to_frame("SPY").where(chg)
        cfg = _engine_cfg(cost_comm=0.0005, cost_slip=0.0005, short=False)  # 10 bp / side as paper
        resj, eqj = _run_engine(spx.loc[st:], Wj, cfg)
        ej = eqj["return"].fillna(0.0)
        ej = ej.loc[ej.index > st]
        vj = simulate(sig.to_frame("SPY"), sr, None, cost_bps=10.0, lag=2).loc[ej.index]
        srf = tbill_daily(ej.index)
        rows.append(metrics(ej, srf, "ENGINE:JM:US:SPY:JM(CV-lambda)", "1_JumpModel", "US",
                            "ml4t-backtest Engine, 5bp comm + 5bp slippage, NEXT_BAR, cash earns 0"))
        rows.append(metrics(vj, srf, "VECTOR(rf=0):JM:US:SPY:JM(CV-lambda)", "1_JumpModel", "US",
                            "vectorised, 10bp, rf=0 (parity check)"))
        notes["jm_parity"] = dict(daily_corr=float(np.corrcoef(ej, vj["ret"])[0, 1]),
                                  tracking_error_ann=float((ej - vj["ret"]).std() * np.sqrt(252)),
                                  engine_num_fills=int(resj.metrics["num_fills"]),
                                  engine_total_costs=float(resj.metrics["total_costs"]))
        plot_equity({"ml4t Engine JM": ej, "Vectorised JM (rf=0)": vj["ret"],
                     "SPY B&H": sr["SPY"].loc[ej.index]},
                    "Jump-model filter on SPY: ml4t-backtest Engine vs vectorised", "engine_jm_spy.png")
    except Exception as e:
        notes["jm_engine"] = f"FAILED: {e.__class__.__name__}: {e}"
    return pd.DataFrame(rows), None, notes


if __name__ == "__main__":
    df, _, notes = run()
    pd.set_option("display.width", 250)
    print(df[["strategy", "start", "CAGR", "Vol", "Sharpe", "MaxDD", "Turnover", "IS_Sharpe", "OOS_Sharpe"]]
          .round(3).to_string())
    print(notes)
