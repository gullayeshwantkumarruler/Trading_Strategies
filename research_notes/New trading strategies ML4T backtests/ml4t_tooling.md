# ML4T (Machine Learning for Trading, Stefan Jansen) tooling and backtesting workflow on Windows 11 / Python (state as of 2026-10-19)

Research only, nothing installed. I checked PyPI versions and wheel files on 2026-10-19 through the PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`). Code blocks marked "(docs)" come from the official docs or READMEs. Code blocks marked "(illustrative)" are glue code I wrote from the documented APIs and have not tested.

## 1. What is on ml4trading.io/docs and in the book repo; packages and main APIs

### Takeaway
The 3rd-edition ecosystem is six new Polars-based pip packages under the `ml4t.*` namespace: `ml4t-data`, `ml4t-engineer`, `ml4t-models`, `ml4t-diagnostic`, `ml4t-backtest` and `ml4t-live`. The book repo itself (the notebooks) officially supports only Docker or uv on Linux/macOS/WSL2. Its README says "Installing into Windows Python is unsupported and does not work." The six libraries themselves are pure-Python wheels that declare support for Windows on CPython 3.12–3.14.

### Cited Findings

**Docs hub and repo structure**
- The docs hub lists six libraries, each with its own docs and GitHub repo:
  - ML4T Data (`/docs/data/`, github.com/ml4t/data): data from 19+ providers, stored as Parquet.
  - ML4T Engineer (`/docs/engineer/`): 120 indicators, triple-barrier labels, alternative bars, leakage-safe dataset preparation.
  - ML4T Models (`/docs/models/`).
  - ML4T Diagnostic (`/docs/diagnostic/`): signal and strategy validation, Deflated Sharpe Ratio, PBO, FDR.
  - ML4T Backtest (`/docs/backtest/`): event-driven, "47 configurable behavioral parameters".
  - ML4T Live (`/docs/live/`): Interactive Brokers and Alpaca.
  - Source: [ml4trading.io/docs](https://www.ml4trading.io/docs/)
- Book repo README:
  - The 2nd edition lives on the `second-edition` branch (`git checkout second-edition`).
  - Install option A is Docker (`docker compose pull ml4t`). Option B is local uv (`uv sync`) on macOS, Linux or WSL2; it compiles some dependencies from source (e.g., scikit-learn) and needs about 16 GB of disk.
  - For Windows the README says to use WSL2: "Installing into Windows Python is unsupported and does not work."
  - A separate `ml4t-py312` image provides Python 3.12 for signatory, esig, gensim and tfcausalimpact (about 10 notebooks).
  - Source: [GitHub README](https://github.com/stefan-jansen/machine-learning-for-trading)
- The README fetch did not mention zipline-reloaded or Quandl. The 3rd-edition default stack appears to be the ml4t-* libraries, not zipline. — [GitHub README](https://github.com/stefan-jansen/machine-learning-for-trading)

**ml4t-engineer**
- Requirements: Python 3.12, 3.13 or 3.14 and Polars 0.20+.
- Install: `pip install ml4t-engineer`. The `stats` extra (`pip install "ml4t-engineer[stats]"`) adds statsmodels ADF, needed for `find_optimal_d()` and `fdiff_diagnostics()`.
- TA-Lib is optional and used only to validate indicators. The Windows instruction is just "download from ta-lib.org then `pip install TA-Lib`".
- Docs version is 0.1.6. Nav sections: Features, Feature Discovery, Labeling, Alternative Bars, Dataset Builder, Preprocessing, Fractional Differencing, ML Readiness, API, Book Guide.
- Source: [Engineer installation](https://www.ml4trading.io/docs/engineer/getting-started/installation/)
- Verify snippet (docs). Expected output is 120 features in 11 categories: math, microstructure, ml, momentum, price_transform, regime, risk, statistics, trend, volatility, volume.
  ```python
  from ml4t.engineer import feature_catalog
  print(len(feature_catalog.list()), feature_catalog.categories())
  ```
  Source: [Engineer installation](https://www.ml4trading.io/docs/engineer/getting-started/installation/)
- Labeling API (docs). Input is a `pl.DataFrame` of OHLCV bars.
  ```python
  from ml4t.engineer.config import LabelingConfig
  from ml4t.engineer.labeling import triple_barrier_labels, fixed_time_horizon_labels
  cfg = LabelingConfig.triple_barrier(upper_barrier=0.02, lower_barrier=0.01,
                                      max_holding_period=20, side=1, trailing_stop=False)
  tb = triple_barrier_labels(data=df, config=cfg, price_col="close", open_col="open",
                             high_col="high", low_col="low", timestamp_col="timestamp",
                             calculate_uniqueness=False, uniqueness_weight_scheme="returns_uniqueness")
  fh = fixed_time_horizon_labels(data=df, horizon=10, method="binary", threshold=0.01, price_col="close")
  ```
  The docs note an inconsistency: `LabelingConfig.fixed_horizon` uses `return_method` where the function uses `method`. Source: [Engineer labeling](https://www.ml4trading.io/docs/engineer/user-guide/labeling/)

**ml4t-data**
- Install: `pip install ml4t-data`, with extras `yahoo`, `databento`, `oanda`, `cot` (e.g., `pip install "ml4t-data[yahoo]"`). Supports CPython 3.12–3.14 on Linux, macOS and Windows; Python 3.15 is temporarily excluded. — [ml4t/data README](https://github.com/ml4t/data)
- Generic API: `provider.fetch_ohlcv(symbol, start, end, frequency="daily")` returns a Polars DataFrame with columns `timestamp, symbol, open, high, low, close, volume`. `SyntheticProvider(seed=42)` works offline. — [ml4t/data README](https://github.com/ml4t/data); [Providers](https://www.ml4trading.io/docs/data/providers/)
- Providers with no API key: Yahoo Finance, Fama-French, AQR, "Wiki Prices" (static historical), Binance Public, NASDAQ ITCH samples, prediction markets.
- Providers needing a key: Alpaca, Tiingo, Finnhub, EODHD, FRED, TwelveData, DataBento, Massive, Oanda, CryptoCompare.
- Yahoo batch example (docs). The page does not give the import path for `YahooFinanceProvider`.
  ```python
  from ml4t.data.managers.async_batch import async_batch_load
  async with YahooFinanceProvider() as provider:
      df = await async_batch_load(provider, symbols=["AAPL","MSFT","GOOGL"],
                                  start="2024-01-01", end="2024-12-31")
  ```
  Source: [Providers](https://www.ml4trading.io/docs/data/providers/)

**ml4t-diagnostic**
- Install: `pip install ml4t-diagnostic` (or `uv add`). Supports CPython 3.12–3.14 on Windows; 3.15 is not supported yet (issue #45).
- Extras: `viz` (Plotly), `ml` (LightGBM, XGBoost, SHAP), `perf` (Numba), `backtest`, `data`, `factors`, `dashboard` (Streamlit), `all`.
- Public CV workflows: `WalkForwardCV`, `CombinatorialCV`, `ValidatedCrossValidation`.
- Source: [ml4t/diagnostic README](https://github.com/ml4t/diagnostic)
- Signal analysis, the Alphalens replacement (docs). Inputs are long format, one row per date and asset: the factor table has `date, asset, factor` and the price table has `date, asset, price`. The factor must precede the price change it predicts.
  ```python
  from ml4t.diagnostic import analyze_signal
  res = analyze_signal(factor=pl.DataFrame(factor_rows), prices=pl.DataFrame(price_rows), periods=(1, 5))
  res.ic["1D"], res.ic_t_stat["1D"], res.spread["1D"]   # also .quantile_returns, .turnover
  ```
  Source: [Diagnostic quickstart](https://www.ml4trading.io/docs/diagnostic/getting-started/quickstart/)
- Purged/embargoed CV (docs):
  ```python
  from ml4t.diagnostic.splitters import WalkForwardCV, CombinatorialCV
  cv = WalkForwardCV(n_splits=4, train_size=120, test_size=40, label_horizon=5, expanding=False)
  cpcv = CombinatorialCV(n_groups=6, n_test_groups=2, label_horizon=5, embargo_size=2, isolate_groups=False)
  for train_idx, test_idx in cpcv.split(X): ...   # C(6,2)=15 splits
  ```
  `label_horizon` purges training rows whose forward labels overlap the test set. `max_combinations` bounds the CPCV computation. — [CV guide](https://github.com/ml4t/diagnostic/blob/main/docs/user-guide/cross-validation.md)
- Deflated Sharpe: `from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio`. It takes a returns array of shape (periods, strategies) plus kwargs `frequency`, `correlation_method`, `min_k_eff`. — [Diagnostic quickstart](https://www.ml4trading.io/docs/diagnostic/getting-started/quickstart/)
- Migration map from the legacy libraries:

  | Legacy call | ml4t-diagnostic equivalent |
  |---|---|
  | alphalens `get_clean_factor_and_forward_returns` | `analyze_signal(factor, prices, ...)` (recomputes forward returns from prices) |
  | alphalens IC / quantile returns / spread | `SignalResult.ic` / `.quantile_returns` / `.spread` |
  | alphalens full factor tear sheet | none; `SignalResult.to_tear_sheet()` and `SignalDashboard` cover IC and quantiles only |
  | pyfolio `perf_stats` | `PortfolioAnalysis(returns=..., dates=..., periods_per_year=252).compute_summary_stats()` |
  | pyfolio `create_full_tear_sheet` | none; `generate_backtest_tearsheet(returns=..., metrics=...)` (needs `viz` extra) |
  | any ml4t-backtest result | `generate_tearsheet_from_result(result)` |

  The guide says to keep alphalens or pyfolio if you need their full reports (return cones, round-trip analysis, factor-weighted portfolios). — [Migration guide](https://www.ml4trading.io/docs/diagnostic/user-guide/migration/)

**ml4t-backtest**
- README: Python 3.12–3.14 on Linux, macOS and Windows. Install with `uv add ml4t-backtest` (or pip), extras `[viz]`, `[advanced]`, `[comparison]`.
- Strategy interface: subclass `Strategy` and implement `on_data(self, timestamp, data, context, broker)`. Optional hooks are `on_start(self, broker)` and `on_prepare`.
- Broker methods: `get_position`, `get_account_value`, `submit_order(asset, shares)`, `close_position`, `set_position_rules(RuleChain([...]))`.
- Feed: `DataFeed(prices_df=..., signals_df=...)`. Prices need `timestamp, asset, close` (OHLC used if present); signals need `timestamp, asset, prediction`.
- Costs live in `BacktestConfig`: `commission_rate`, `slippage_rate`, `stop_slippage_rate`. Per-share commissions use `commission_type=CommissionType.PER_SHARE`, `commission_per_share`, `commission_minimum`. Spread slippage uses `slippage_type=SlippageType.SPREAD`, `slippage_spread`.
- Presets: `BacktestConfig.from_preset("vectorbt"|"backtrader"|"zipline"|"lean"|"realistic")`. The README reports parity results against Zipline Reloaded 3.1.1.
- Result exports: `to_fills_dataframe()`, `to_trades_dataframe()`, `to_portfolio_state_dataframe()`, `to_predictions_dataframe()`, `to_parquet(path)`.
- Source: [ml4t/backtest README](https://github.com/ml4t/backtest)
- Quickstart (docs). Each `Engine` instance is single-use.
  ```python
  from ml4t.backtest import BacktestConfig, DataFeed, Engine, run_backtest
  from ml4t.backtest.example_data import ExampleRoundTrip, load_example_prices
  prices = load_example_prices("equity").filter(pl.col("asset") == "AAPL")
  result = Engine(DataFeed(prices_df=prices), ExampleRoundTrip("AAPL", 100),
                  BacktestConfig(initial_cash=100_000)).run()
  result = run_backtest(prices, ExampleRoundTrip("AAPL", 100), config="backtrader")
  result.fills, result.metrics["final_value"]
  ```
  Docs nav also includes a "Migrate from Zipline" guide. Source: [Backtest docs](https://www.ml4trading.io/docs/backtest/)
- Rebalancing (docs):
  - `broker.rebalance_to_weights(weights_dict)` inside `on_data`.
  - Alternatively `TargetWeightExecutor(RebalanceConfig(min_trade_value=..., min_weight_change=..., rebalance_mode=RebalanceMode.SNAPSHOT))`, called with `executor.execute(weights, data, broker)`.
  - `RebalanceSchedule.fixed_n_sessions(5)`.
  - A `WeightProvider` protocol with `get_weights(data, broker) -> dict`.
  - Sources: [Rebalancing guide](https://github.com/ml4t/backtest/blob/main/docs/user-guide/rebalancing.md); [README](https://github.com/ml4t/backtest)
- Results (docs):
  - `result.to_equity_dataframe()` returns `timestamp, equity, return, cumulative_return, drawdown, high_water_mark`. Daily returns come from `to_daily_pnl()`.
  - Metrics keys: `total_return, cagr, volatility, max_drawdown, sharpe, sortino, calmar, num_trades, win_rate, profit_factor, total_commission, total_slippage, total_costs, avg_cost_drag`.
  - Handoff: `portfolio_analysis_from_result(result, calendar="NYSE")` and `generate_tearsheet_from_result(result, title=..., template="full", output_path="tearsheet.html")`.
  - Source: [Results guide](https://github.com/ml4t/backtest/blob/main/docs/user-guide/results.md)

**Latest PyPI versions and Python bounds (checked 2026-10-19)**

All six ml4t-* packages ship only pure-Python `py3-none-any` wheels. Source: PyPI JSON API ([ml4t-backtest](https://pypi.org/project/ml4t-backtest/), [ml4t-diagnostic](https://pypi.org/project/ml4t-diagnostic/), [ml4t-data](https://pypi.org/project/ml4t-data/), [ml4t-engineer](https://pypi.org/project/ml4t-engineer/), [ml4t-models](https://pypi.org/project/ml4t-models/)).

| Package | Version | Released | requires_python |
|---|---|---|---|
| ml4t-backtest | 0.1.12 | 2026-09-24 | >=3.12 |
| ml4t-diagnostic | 0.1.9 | 2026-10-15 | >=3.12,<3.15 |
| ml4t-data | 0.2.1 | 2026-10-15 | >=3.12,<3.15 |
| ml4t-engineer | 0.1.6 | 2026-09-25 | >=3.12,<3.15 |
| ml4t-models | 0.1.4 | 2026-09-19 | >=3.12 |

**Legacy "reloaded" stack (maintained by Stefan Jansen)**

| Package | Version | requires_python | Notes |
|---|---|---|---|
| zipline-reloaded | 3.2.0 (uploaded 2026-10-18) | >=3.11,<3.15 | win_amd64 wheels for cp311, cp312, cp313, cp314; requires `pandas<3.0`, `bcolz-zipline>=1.2.6`, `exchange-calendars>=4.2.4`, `empyrical-reloaded>=0.5.7` |
| alphalens-reloaded | 0.5.0 (2026-10-17) | >=3.11,<3.16 | |
| pyfolio-reloaded | 0.10.0 (2026-10-17) | >=3.11,<3.16 | requires `pandas<3` |
| empyrical-reloaded | 0.7.0 (2026-10-17) | >=3.11 | pure wheel |

Sources: [zipline-reloaded](https://pypi.org/project/zipline-reloaded/), [alphalens-reloaded](https://pypi.org/project/alphalens-reloaded/), [pyfolio-reloaded](https://pypi.org/project/pyfolio-reloaded/), [empyrical-reloaded](https://pypi.org/project/empyrical-reloaded/)

### Inferences
- The docs present ml4t-diagnostic as the successor to alphalens/pyfolio/empyrical and ml4t-backtest as the successor to zipline (it has a "Migrate from Zipline" guide and a zipline preset). The reloaded packages are still actively released (Oct 2026), so both stacks are usable.
- The libraries' docs are partly inconsistent and pre-1.0. Examples:
  - The results guide pins `ml4t-diagnostic==0.1.4`, while PyPI is at 0.1.9.
  - The labeling page has the `method` vs `return_method` mismatch.
  - ml4t-backtest is at 0.1.x, and a search snippet reported a 0.1.0b21 beta tag.
  - Pin exact versions in requirements.txt and expect some API churn.

### Gaps
- I did not see the full ml4t-models or ml4t-live APIs, the Engineer features/`compute_features` signature, or the import path for `YahooFinanceProvider` (likely `ml4t.data.providers`, unverified).
- I did not verify the exact pandas/Polars conversion requirements for `analyze_signal`. The migration guide example appears to build pandas long tables; the quickstart uses Polars.

## 2. Which packages work on Python 3.13 on Windows, and which need older Python

### Takeaway
On Python 3.13.3 / Windows x64, every ml4t-* package, alphalens-reloaded, pyfolio-reloaded, empyrical-reloaded and TA-Lib install from wheels. zipline-reloaded 3.2.0 also has a cp313 win_amd64 wheel, but its required dependency `bcolz-zipline` (1.13.0, the latest) has Windows wheels only up to cp312. pip on 3.13 would therefore try to build bcolz from source, which needs MSVC Build Tools. **Use Python 3.12 for any venv that includes zipline**; 3.12 also satisfies every ml4t-* package (>=3.12).

### Cited Findings
- bcolz-zipline 1.13.0 (2025-05-31):
  - PyPI files are win_amd64 wheels for cp39, cp310, cp311 and cp312 only, plus an sdist `bcolz_zipline-1.13.0.tar.gz`. There is no cp313 or cp314 wheel. — [PyPI bcolz-zipline](https://pypi.org/project/bcolz-zipline/)
  - conda-forge has `bcolz-zipline 1.2.12` win-64 builds for py312 and py313. Its zipline-reloaded is stale at 2.4 with no py313 win build. — [anaconda.org conda-forge/bcolz-zipline](https://anaconda.org/conda-forge/bcolz-zipline) (via api.anaconda.org)
- zipline-reloaded 3.2.0 ships win_amd64 wheels for cp311–cp314 and declares requires_python `>=3.11,<3.15`. — [PyPI zipline-reloaded](https://pypi.org/project/zipline-reloaded/)
- Conflicting doc: the zipline install page (zipline.ml4trading.io) still says Python 3.8–3.11 and explains that the C extensions need CPython headers to build. It looks outdated relative to PyPI metadata. — [zipline install docs](https://zipline.ml4trading.io/install.html) vs [PyPI](https://pypi.org/project/zipline-reloaded/)
- TA-Lib 0.8.2 (2026-10-12) ships win_amd64, win32 and win_arm64 wheels for cp311–cp315, including free-threaded builds. Wheels since 0.6.5 bundle the TA-Lib C library, so on Windows `pip install TA-Lib` needs no separate C library download. — [PyPI TA-Lib](https://pypi.org/project/TA-Lib/)
  - The ml4t-engineer install page still tells Windows users to download the C library first; for current wheels that step looks outdated. — [Engineer installation](https://www.ml4trading.io/docs/engineer/getting-started/installation/)
- ml4t-data and ml4t-diagnostic declare `<3.15`; alphalens and pyfolio declare `<3.16`; zipline declares `<3.15`. None of them support Python 3.11 or older except the reloaded packages. — PyPI JSON (see links above)
- yfinance 1.7.0 (2026-08-26) is a pure wheel. — [PyPI yfinance](https://pypi.org/project/yfinance/)

### Inferences
Two recommended venv setups. The commands are standard `py` launcher and uv usage, not from the ML4T docs.

- **Option A: one venv on Python 3.12** (works for everything, including zipline)
  - Get Python 3.12:
    - `winget install Python.Python.3.12`, or the python.org installer, then `py -3.12 -m venv .venv312`
    - or with uv: `uv python install 3.12`, then `uv venv --python 3.12 .venv312`
  - Activate: `.venv312\Scripts\activate`
  - Install: `pip install ml4t-data[yahoo] ml4t-engineer[stats] ml4t-diagnostic[viz,ml] ml4t-backtest zipline-reloaded alphalens-reloaded pyfolio-reloaded TA-Lib yfinance lightgbm scikit-learn`
  - Possible conflict: zipline-reloaded and pyfolio-reloaded require `pandas<3`. If an ml4t-* package ever requires pandas>=3, the resolver will fail. Then split into two venvs.
- **Option B: keep Python 3.13.3** for the ml4t-* stack plus alphalens/pyfolio/TA-Lib, and skip zipline (use ml4t-backtest instead).
  - Installing zipline on 3.13 needs "Microsoft C++ Build Tools" (Desktop development with C++) so bcolz-zipline can compile from sdist. That build is not verified.
- Running the book's notebooks themselves: use WSL2 or Docker, per the README.

### Gaps
- I could not confirm whether the bcolz-zipline sdist actually compiles cleanly on Windows under 3.13. I found no GitHub issue on it.
- I did not check whether every transitive ml4t-* dependency has a cp313/cp312 Windows wheel (e.g., lightgbm, numba, shap). These are generally available, but not verified here.

## 3. Simplest robust path: daily-rebalanced cross-sectional strategy with costs on custom (yfinance) data, plus alphalens/pyfolio diagnostics

### Takeaway
On Windows the simplest robust path is pure Python with no bundle ingestion: yfinance (or ml4t-data's Yahoo provider) to a long Polars panel, then ml4t-engineer features and labels, then a LightGBM/sklearn model with `WalkForwardCV`/`CombinatorialCV` and `label_horizon` purging plus embargo, then `analyze_signal` (or alphalens-reloaded) for IC and quantiles, then an ml4t-backtest `Strategy` that calls `broker.rebalance_to_weights()` daily with `commission_rate`/`slippage_rate`, then `generate_tearsheet_from_result` (or pyfolio-reloaded on the daily returns). Zipline with a custom `csvdir` bundle works too, but adds `extension.py`, ingestion, calendar alignment and dividend/split columns.

### Cited Findings
- Required input schemas, used by the glue code below:
  - ml4t-data output: `timestamp, symbol, open, high, low, close, volume`. — [Providers](https://www.ml4trading.io/docs/data/providers/)
  - ml4t-backtest feed: prices need `timestamp, asset, close`; signals need `timestamp, asset, prediction`. — [ml4t/backtest README](https://github.com/ml4t/backtest)
  - analyze_signal: factor `date, asset, factor`; prices `date, asset, price`. — [Diagnostic quickstart](https://www.ml4trading.io/docs/diagnostic/getting-started/quickstart/)
- Zipline custom-data path (docs):
  - Register in `~/.zipline/extension.py` (on Windows, `%USERPROFILE%\.zipline\extension.py`; root set by `ZIPLINE_ROOT`) with `register('custom-csvdir-bundle', csvdir_equities(['daily'], '/path/to/csvs'), calendar_name='NYSE', start_session=..., end_session=...)`.
  - CSV columns: `date, open, high, low, close, volume, dividend, split`, one file per ticker inside a `daily` subfolder. Use dividend 0.0 and split 1.0 when there is no event.
  - Ingest: `zipline ingest -b custom-csvdir-bundle`; the CSV dir can be passed via the `CSVDIR` env var. Data lands in `$ZIPLINE_ROOT/data/<bundle>/<timestamp>`.
  - Source: [Zipline bundles docs](https://zipline.ml4trading.io/bundles.html)
- ml4t-backtest has a `"zipline"` config preset and reports parity tests against Zipline Reloaded 3.1.1, so zipline-style fill semantics are available without zipline itself. — [ml4t/backtest README](https://github.com/ml4t/backtest)

### Code sketch: yfinance into ml4t-backtest and ml4t-diagnostic (illustrative, untested)
```python
import yfinance as yf, polars as pl, pandas as pd
from ml4t.backtest import Strategy, Engine, DataFeed, BacktestConfig   # Strategy import path assumed
from ml4t.diagnostic import analyze_signal

tickers = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","JPM","XOM","JNJ","PG"]
raw = yf.download(tickers, start="2015-01-01", end="2026-10-01", auto_adjust=True, group_by="column")
long = (raw.stack(level=1, future_stack=True).rename_axis(["timestamp","asset"]).reset_index()
          .rename(columns=str.lower))           # timestamp, asset, open, high, low, close, volume
prices = pl.from_pandas(long).with_columns(pl.col("timestamp").cast(pl.Datetime("us")))

# example factor: 21d momentum skipping last 5d (replace with model prediction)
sig = prices.sort("asset","timestamp").with_columns(
    (pl.col("close").shift(5)/pl.col("close").shift(26)-1).over("asset").alias("prediction"))

# signal diagnostics (alphalens replacement)
res = analyze_signal(
    factor=sig.select(pl.col("timestamp").alias("date"),"asset",pl.col("prediction").alias("factor")).drop_nulls(),
    prices=prices.select(pl.col("timestamp").alias("date"),"asset",pl.col("close").alias("price")),
    periods=(1,5,21))
print(res.ic, res.spread)

class LongShortTopBottom(Strategy):
    def __init__(self, k=3): self.k = k
    def on_data(self, timestamp, data, context, broker):
        # `data` structure per asset: check the Strategies guide; assumed dict asset -> {..., "prediction": x}
        preds = {a: d.get("prediction") for a, d in data.items() if d.get("prediction") is not None}
        if len(preds) < 2*self.k: return
        ranked = sorted(preds, key=preds.get)
        w = {a: -0.5/self.k for a in ranked[:self.k]} | {a: 0.5/self.k for a in ranked[-self.k:]}
        broker.rebalance_to_weights(w)

cfg = BacktestConfig(initial_cash=1_000_000, commission_rate=0.0005, slippage_rate=0.0005)
result = Engine(DataFeed(prices_df=prices, signals_df=sig.select("timestamp","asset","prediction")),
                LongShortTopBottom(3), cfg).run()
eq = result.to_equity_dataframe()        # timestamp, equity, return, drawdown, ...
print(result.metrics["sharpe"], result.metrics["total_costs"])

from ml4t.diagnostic.integration import generate_tearsheet_from_result   # import path not confirmed
generate_tearsheet_from_result(result, title="LS momentum", template="full", output_path="tearsheet.html")

# pyfolio-style alternative
import pyfolio as pf
rets = eq.to_pandas().set_index("timestamp")["return"]; rets.index = rets.index.tz_localize("UTC")
pf.create_returns_tear_sheet(rets)
```
Several details in this sketch are assumptions:
- The `data` dict shape in `on_data`.
- The import paths for `Strategy` and `generate_tearsheet_from_result`.
- Whether `prediction` from `signals_df` is exposed inside `data`.
- Shorting/margin settings, which may need account-policy config (see the "Account Policies" guide).

Check all of these against the API Reference ([backtest docs](https://www.ml4trading.io/docs/backtest/)).

### Code sketch: alphalens-reloaded on the same data (illustrative)
```python
import alphalens as al
factor = sig.to_pandas().set_index(["timestamp","asset"])["prediction"].dropna()
px = prices.to_pandas().pivot(index="timestamp", columns="asset", values="close")
fd = al.utils.get_clean_factor_and_forward_returns(factor, px, quantiles=5, periods=(1,5,21))
al.tears.create_full_tear_sheet(fd)
```
`get_clean_factor_and_forward_returns` is the function the migration guide names as the alphalens entry point. The other calls are standard alphalens API from my prior knowledge, not re-verified this session. — [Migration guide](https://www.ml4trading.io/docs/diagnostic/user-guide/migration/)

### Code sketch: yfinance into a zipline csvdir bundle (illustrative)
```python
# write one CSV per ticker: C:\data\yf_csv\daily\AAPL.csv  with date,open,high,low,close,volume,dividend,split
for t in tickers:
    df = yf.Ticker(t).history(start="2015-01-01", auto_adjust=False, actions=True)
    out = pd.DataFrame({"date": df.index.tz_localize(None).date, "open": df.Open, "high": df.High,
        "low": df.Low, "close": df.Close, "volume": df.Volume,
        "dividend": df["Dividends"], "split": df["Stock Splits"].replace(0, 1.0)})
    out.to_csv(rf"C:\data\yf_csv\daily\{t}.csv", index=False)
```
```python
# %USERPROFILE%\.zipline\extension.py
import pandas as pd
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
register("yf-bundle", csvdir_equities(["daily"], r"C:\data\yf_csv"),
         calendar_name="NYSE", start_session=pd.Timestamp("2015-01-02"), end_session=pd.Timestamp("2026-09-30"))
```
Then run `zipline ingest -b yf-bundle` in PowerShell.

Zipline's split convention: in the csvdir sample, split=1.0 means no split. Whether 1.0 should be the yfinance split ratio or its inverse must be checked against zipline's adjustment semantics before trusting the output. — [Zipline bundles docs](https://zipline.ml4trading.io/bundles.html)

### Inferences
- Costs in ml4t-backtest are config parameters, so cost sensitivity sweeps are easy. In zipline you set `set_commission` and `set_slippage` inside `initialize` (standard zipline API, not re-verified here).
- The end-to-end canonical workflow is:
  1. Data ingestion (ml4t-data or yfinance)
  2. Features (ml4t-engineer `feature_catalog`, TA-Lib)
  3. Labels (`fixed_time_horizon_labels` / `triple_barrier_labels`)
  4. CV (`WalkForwardCV` / `CombinatorialCV` with `label_horizon` and `embargo_size`)
  5. Signal evaluation (`analyze_signal` or alphalens)
  6. Backtest (ml4t-backtest `Engine` with `rebalance_to_weights`)
  7. Tear sheet (`generate_tearsheet_from_result` or pyfolio)
  8. Overfitting check (`deflated_sharpe_ratio`)
- For a vectorized sanity check, compute weights × next-day returns − turnover × cost in Polars, then compare with the event-driven result.

### Gaps
- I did not fetch the full "Multi-asset Rebalancing" tutorial; its URL under `/docs/backtest/getting-started/` returned 404. The exact `data` object shape in `on_data` is unconfirmed.
- I did not fetch the ml4t-backtest "Migrate from Zipline" guide or the configuration guide's full cost and short-selling options.

## 4. Known-broken parts and their replacements

### Takeaway
The Quandl WIKI dataset behind zipline's default `quandl` bundle stopped updating in early 2018. Native Windows installs of the book repo are unsupported, the zipline install page's Python range is stale, and the ml4t-engineer TA-Lib-on-Windows instruction is outdated. The replacements are the ml4t-data providers (Yahoo, Tiingo, EODHD, Alpaca, and others) or custom csvdir bundles, WSL2 or Docker for notebooks, and bundled TA-Lib wheels.

### Cited Findings
- "Quandl discontinued its WIKI dataset in early 2018": the bundle no longer updates, though the docs still call it a starting point. The default `zipline ingest` bundle is still `quandl`. — [Zipline bundles docs](https://zipline.ml4trading.io/bundles.html)
- ml4t-data still lists "Wiki Prices" as a static historical dataset. Free, keyless current alternatives include Yahoo Finance; keyed ones include Tiingo, EODHD, Alpaca and others. — [Providers](https://www.ml4trading.io/docs/data/providers/)
- Windows native Python is "unsupported and does not work" for the book repo environment; use WSL2 or Docker. — [Book README](https://github.com/stefan-jansen/machine-learning-for-trading)
- On macOS Intel, the local uv path cannot resolve because PyTorch publishes no x86_64 macOS wheel. — [Book README](https://github.com/stefan-jansen/machine-learning-for-trading)
- The zipline install page lists Python 3.8–3.11, while PyPI 3.2.0 supports 3.11–3.14, so the docs page is outdated. — [zipline install](https://zipline.ml4trading.io/install.html); [PyPI](https://pypi.org/project/zipline-reloaded/)
- bcolz-zipline has no Python 3.13/3.14 Windows wheel on PyPI. — [PyPI bcolz-zipline](https://pypi.org/project/bcolz-zipline/)
- The conda-forge zipline-reloaded package is stale at 2.4. — api.anaconda.org/package/conda-forge/zipline-reloaded
- Alphalens full tear sheets have no one-call equivalent in ml4t-diagnostic, and neither do pyfolio's return cones or round-trip analysis. Keep the reloaded packages for those. — [Migration guide](https://www.ml4trading.io/docs/diagnostic/user-guide/migration/)

### Inferences
- Avoid the conda ml4t channel and old conda envs from the 2nd edition (`installation/` folder); they target old Pythons. Use pip or uv wheels on Python 3.12.
- yfinance data is split- and dividend-adjusted only when `auto_adjust=True`. It has survivorship bias (current tickers only), which matters for cross-sectional tests. This is general knowledge, not from the ML4T docs.

### Gaps
- I did not review the GitHub issue trackers (ml4t/backtest, ml4t/diagnostic, zipline-reloaded) for open Windows-specific bugs.
- I did not inspect the 2nd-edition `installation/` folder on the `second-edition` branch.
