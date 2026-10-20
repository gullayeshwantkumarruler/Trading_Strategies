"""ML4T workflow cross-check for the 2026-paper strategies.

(a) ml4t-backtest Engine: paper 1's monthly Markowitz target weights (SPY/AGG/GLD) are replayed
    through ml4t.backtest.Engine (NEXT_BAR execution = decide at close t, fill at close t+1,
    2.5 bp slippage = the paper's half-spread) and compared with the vectorised simulator from
    strategies/rules/common.py under the same conventions (cash earns 0 in both).
(b) ml4t-diagnostic deflated Sharpe ratio for each paper's family of variants.
"""
from __future__ import annotations

import pandas as pd
import polars as pl

from common import ANN, RES_DIR, closes, deflated_sharpe, returns, save_rows, simulate, tbill_daily


def engine_run(px: pd.DataFrame, W: pd.DataFrame, slip=0.00025):
    from ml4t.backtest import BacktestConfig, DataFeed, Engine, Strategy
    from ml4t.backtest.config import CommissionType, ShareType, SlippageType
    from ml4t.backtest.types import ExecutionMode

    cfg = BacktestConfig(initial_cash=1_000_000.0, commission_type=CommissionType.PERCENTAGE,
                         commission_rate=0.0, slippage_type=SlippageType.PERCENTAGE, slippage_rate=slip,
                         share_type=ShareType.FRACTIONAL, allow_short_selling=False, allow_leverage=True,
                         execution_mode=ExecutionMode.NEXT_BAR)
    long = px.stack().rename("close").reset_index()
    long.columns = ["timestamp", "asset", "close"]
    feed = DataFeed(prices_df=pl.from_pandas(long).sort(["timestamp", "asset"]))
    targets = {pd.Timestamp(d): r for d, r in W.iterrows()}

    class Targets(Strategy):
        def on_data(self, timestamp, data, context, broker):
            w = targets.get(pd.Timestamp(timestamp))
            if w is not None:
                broker.rebalance_to_weights({a: float(x) for a, x in w.items()})

    res = Engine(feed, Targets(), cfg).run()
    eq = res.to_equity_dataframe().to_pandas().set_index("timestamp")
    col = "equity" if "equity" in eq.columns else eq.columns[0]
    return eq[col].pct_change().dropna()


def main():
    Wd = pd.read_csv(RES_DIR / "p1_us_markowitz_weights.csv", index_col=0, parse_dates=True)
    idx = Wd.index
    me = pd.Series(idx, idx).groupby([idx.year, idx.month]).max()
    W = Wd.loc[me.values]                                  # post-trade weights on rebalance days = targets
    px = closes(["SPY", "AGG", "GLD"], calendar="SPY").loc[idx[0]:idx[-1]]
    r_eng = engine_run(px, W)
    sim = simulate(W, returns(px), rf=None, cost_bps=2.5, rebal=pd.Series(True, W.index), lag=2)
    r_sim = sim["ret"].loc[r_eng.index[0]:]
    j = pd.concat([r_eng.rename("engine"), r_sim.rename("vectorised")], axis=1, join="inner").dropna()
    rows = [dict(check="p1 Markowitz: ml4t Engine vs vectorised simulator",
                 corr=j.corr().iloc[0, 1], te_ann=(j.engine - j.vectorised).std() * ANN ** 0.5,
                 sr_engine=j.engine.mean() / j.engine.std() * ANN ** 0.5,
                 sr_vectorised=j.vectorised.mean() / j.vectorised.std() * ANN ** 0.5,
                 cagr_engine=(1 + j.engine).prod() ** (ANN / len(j)) - 1,
                 cagr_vectorised=(1 + j.vectorised).prod() ** (ANN / len(j)) - 1, n_days=len(j))]
    print(pd.DataFrame(rows).T)
    save_rows(rows, "ml4t_engine_check.csv")


if __name__ == "__main__":
    main()
