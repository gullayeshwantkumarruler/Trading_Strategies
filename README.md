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
