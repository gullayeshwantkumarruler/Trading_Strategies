# Trading Strategies — research and ML4T backtests

Research into recent (2023–2026) trading strategies from papers and practitioner blogs, re-implemented and
backtested with the [ML4T](https://www.ml4trading.io/) libraries (`ml4t-engineer`, `ml4t-diagnostic`,
`ml4t-backtest`) on free data for US, European, Japanese and Chinese markets.

**Headline:** only one strategy survives an honest test. The Devanathan–Tzikas–Boyd (2026) stock/bond/gold
Markowitz portfolio reproduces (Sharpe 1.10 vs the paper's 1.08, and still 1.01 through Oct 2026). Everything
else either fails to beat a simple baseline (equal weight, buy-and-hold) or loses its edge to trading costs.

## Layout

| Path | Contents |
|---|---|
| `reports/New trading strategies ML4T backtests.md` | Round 1 report: literature review + rules-based and ML backtests |
| `research_notes/New trading strategies ML4T backtests/` | Research notes (sources linked inline) and results write-ups, incl. `backtest_results_papers2026.md` |
| `strategies/rules/` | Round 1 rules-based strategies: jump-model regime filter, vol-targeted trend, cross-asset/sector momentum, turn-of-month |
| `strategies/ml/` | Round 1 ML cross-sectional models (LightGBM/Ridge) for US, Europe, Japan, China |
| `strategies/papers2026/` | Round 2: replications of five 2026 papers (1 stock/bond/gold, 2 Wasserstein HMM, 3 tabular DL hybrid, 4 KellyBoost, 8 attribution-guided stat-arb) + ML4T engine cross-check |
| `strategies/statarb/` | Round 3: equity stat arb (cost-aware construction, residual ladder, DLSA, Attention Factors), alpha library with point-in-time EDGAR fundamentals, free alt data (FINRA, Form 4, Lazy Prices), daily collector, MOSEK benchmark |
| `strategies/alpha_research/` | Round 4: formulaic-alpha DSL, frozen referee, agent + GP alpha mining, Wikipedia/8-K alt data, sealed-test backtests |
| `reports/Price action strategies by horizon.md` | Round 5 report: price action strategies on intraday, swing (daily) and positional (weekly+) horizons |
| `strategies/price_action/` | Round 5: trade-level engine (stops, targets, trailing stops, MOC/next-open fills), swing, positional and intraday (Alpaca 1-minute) backtests |
| `strategies/*/results/` | Metrics CSVs, logs and equity-curve PNGs from the runs |
| `papers/README.md` | Links to every paper used (PDFs not redistributed) |

## Round 2 results (2026 papers)

| Paper | Paper's claim | This replication |
|---|---|---|
| 1 Stock/bond/gold Markowitz ([2609.07946](https://arxiv.org/abs/2609.07946)) | Sharpe 1.08 | **Reproduced**: 1.10 (1.03 with 1-day lag); abroad 0.34–0.54 |
| 2 Wasserstein HMM ([2603.04441](https://arxiv.org/abs/2603.04441)) | Sharpe 2.18 | 1.25 on a similar window, below equal weight and its own KNN baseline; 0.59 over 2012–2026 |
| 3 XGBoost+TabNet Hybrid ([2608.27076](https://arxiv.org/abs/2608.27076)) | +51% in 2025 | +0.6% in 2025; all models negative in 2026 YTD |
| 4 KellyBoost ([2608.23393](https://arxiv.org/abs/2608.23393)) | beats other learners | true on the paper's assets (0.23), last on regional ETFs (0.10); 1/N wins both (0.58 / 0.49) |
| 8 Attribution interventions ([2610.15144](https://arxiv.org/abs/2610.15144)) | +net Sharpe in 8/8 | gross edge matches, but 70–80%/day turnover makes it net-negative; stabilised rules help significantly |

## Round 3 results (equity stat arb, alpha signals, alt data, MOSEK)

Report: `reports/Equity stat arb alpha and alt data.md`; results: `research_notes/Equity stat arb alpha and alt data/backtest_results_statarb.md`;
code: `strategies/statarb/`. 337 current S&P 500 large caps, 2010–2026, net of 5 bp/turnover + 1 bp/day shorts.

| Strategy | Net Sharpe | 2022–26 | Turnover/day |
|---|---|---|---|
| Slow alpha composite (LightGBM over 18 price/volume + 9 point-in-time EDGAR signals) through a cost-aware CVXPY optimiser | **1.03** | 0.80 | 1% |
| Attention Factors lite (Epstein et al. 2025), costs in the training loss | **0.86** | 0.38 | 6% |
| DLSA CNN-Transformer (Guijarro-Ordonez et al.), FF5 residuals | 0.21 | −0.29 | 20% |
| Every parametric residual-reversal rule (OU, partial trading, bands, optimiser, PCA/char residuals, NFE, Robeco, SPONGE) | ≤ 0.03 | < 0 | |
| Free alt data: FINRA short volume, insider purchases, Lazy Prices | < 0 | | |

The leaders pass a noise-null deflated Sharpe (0.998 / 0.957) but not one using the full cross-trial variance;
universe survivorship bias makes all numbers upper bounds. Step 6 archives headlines, option chains and FINRA
files daily (`strategies/statarb/collect_daily.py`, scheduled task). MOSEK (academic licence) matched Clarabel on the
continuous problems and its mixed-integer extensions did not improve results.

SEC EDGAR steps need `set SEC_USER_AGENT=Your Name your.email@example.com` (SEC policy).

## Round 4 results (AI alpha-research pipeline + new alt data)

Notes: `research_notes/AI alpha research pipelines/` (survey of 2025–26 LLM/agent alpha miners and results);
code: `strategies/alpha_research/`. A formulaic-alpha DSL over 25 fields (price/volume, point-in-time fundamentals,
insider, FINRA, Lazy Prices, plus new Wikipedia page-view attention and SEC 8-K event data), two proposers (40 frozen
agent hypotheses, genetic programming) and one frozen referee (train 2010–17 t ≥ 3, valid 2018–21, redundancy and
validity checks), then a one-shot sealed test 2022–26.

- 6 of 190 candidates admitted; mined alphas' IC roughly halves train → valid → test; no alt-data alpha passed.
- Best sealed-test book: union library, LightGBM, monthly L/S net Sharpe 0.54 (deflated-Sharpe probability 0.73),
  below the round-3 slow optimiser's 0.80 on the same window.
- A first run's referee admitted 62 degenerate GP formulas (floating-point tie noise); fixed with validity
  safeguards and re-mined — documented in the notes.

## Round 5 results (price action by horizon, US ETFs)

Notes: `research_notes/Price action strategies by horizon/` (`backtest_results_price_action.md` has every table);
code: `strategies/price_action/`. Rules are run as published, with no parameter search. Every rule has a sealed
holdout, a cost sweep and a deflated Sharpe ratio over all variants tried.

- **Intraday** (Alpaca SIP 1-minute bars, 2016–Oct 2026): Noise Area breakout with a VWAP stop
  (Zarattini, Aziz & Barbon 2024) holds up on QQQ (Sharpe 1.28 full, 1.31 out of sample, break-even cost > 3¢/share).
  The same rule on SPY drops to Sharpe 0.00 out of sample. Opening-range breakout is weak after costs;
  last-half-hour momentum and gap rules show no edge.
- **Swing** (daily, 15 ETFs, holdout 2016–26): short-term mean reversion (RSI(2), RSI(3)+IBS, large-decline
  pullback) keeps profit factor 1.5–1.9 and ~70% wins. Because it is in the market so little, its Sharpe trails
  buy-and-hold: the combined book's holdout Sharpe is 0.72 vs SPY 0.87, with max drawdown −8% vs −34%.
  Candlestick and bar patterns (NR7, inside bar, hammer, engulfing) show no edge.
- **Positional** (weekly+): Faber 10-month SMA / GTAA5 and weekly trend filters give about buy-and-hold Sharpe with
  smaller drawdowns. The all-time-high breakout with a 10×ATR trailing stop has positive per-trade
  expectancy (+0.47R) but returns only 4–7%/yr as a portfolio.

The intraday script needs a free Alpaca account. Put `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in a repo-root `.env`
(git-ignored, never committed).

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

Data is downloaded on first run (Yahoo Finance via yfinance, FRED public CSV endpoint, Ken French data library,
akshare for China) and cached in `strategies/*/data/` (not committed).

```bash
.venv\Scripts\python strategies\rules\run_all.py
.venv\Scripts\python strategies\ml\run_all.py
.venv\Scripts\python strategies\papers2026\run_all.py --only 1 4
```

`papers2026/run_all.py` with no arguments runs everything (several hours on CPU; papers 3 and 8 are the slow ones).

## Caveats

Backtests, not investment advice. Stock universes use current index constituents (survivorship bias); papers 2 and
3 leave some settings unpublished, which were chosen before looking at test data and are documented in each script.
