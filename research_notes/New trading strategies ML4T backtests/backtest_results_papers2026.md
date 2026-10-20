# Backtests of five 2026 papers (1, 2, 3, 4, 8)

Code: `strategies/papers2026/` (`p1_stock_bond_gold.py`, `p2_wasserstein_hmm.py`, `p3_tabular_hybrid.py`,
`p4_kellyboost.py`, `p8_attribution_statarb.py`, `ml4t_check.py`, `run_all.py`). Results (CSVs, logs, PNGs):
`strategies/papers2026/results/`. PDFs: `papers/2026/`. Environment: the existing `.venv` (Python 3.13), plus
cvxpy 1.9.3, hmmlearn 0.3.3, xgboost 3.4.1, optuna 5.0, torch 2.14 (CPU), pytorch-tabnet 4.1, lxml.
All data free: Yahoo Finance (yfinance), FRED (public `fredgraph.csv`, no key), Ken French data library,
Wikipedia S&P 500 list. Code availability: only paper 1 publishes code (github.com/cvxgrp/simple-portfolio-code),
which needs a FRED key and pandas 3; all five were re-implemented from the papers.

ML4T use: `ml4t.backtest.Engine` replay of paper 1's Markowitz weights (NEXT_BAR fills, 2.5 bp slippage) matches the
vectorised simulator (daily return correlation 0.998, tracking error 0.6%/yr, CAGR 10.34% vs 10.37%) —
`results/ml4t_engine_check.csv`. `ml4t.diagnostic` deflated Sharpe is used for paper 8's variant family
(`results/dsr_papers2026.csv`).

## Summary

| Paper | Claim | Our result | Verdict |
|---|---|---|---|
| 1 Devanathan, Tzikas, Boyd — dynamic stock/bond/gold | Markowitz Sharpe 1.08 vs 0.56 (60/40), 2006–2025 | Sharpe 1.10, CAGR 11.5%, vol 8.9%, max DD −18.1% (paper 11.6% / 9.0% / −18.1%); 1-day-lag 1.03; through Oct 2026 1.01 | **Reproduced.** Holds with lag and in 2026. Abroad (EZU/EWJ/FXI in place of SPY) Sharpe only 0.38–0.57, but still ≥ fixed-weight benchmarks |
| 2 Boukardagha — Wasserstein HMM regime MVO | Sharpe 2.18 vs 1.59 EW, 1.18 SPX; max DD −5.4% | Paper-like window (2024-03..2026-02): Sharpe 1.25, max DD −4.6%, below EW 1.40; KNN baseline 2.05. 2012–2026: Sharpe 0.59, vol 4%, max DD −8% | **Not reproduced.** Drawdown control is real; the Sharpe claim and the HMM > KNN ranking are not |
| 3 Le Grice — XGBoost+TabNet Hybrid | 2025: +51.3%, Sharpe 2.44, alpha 0.42 | Hybrid 2025: +0.6%, Sharpe 0.11; XGBoost 2025 +13.0% (Sharpe 1.08); 2026 YTD all four models negative (Hybrid −13.8%) | **Not reproduced** (without the paper's Bloomberg fundamentals/sentiment). Costs dominate (1.1–1.5× daily turnover) |
| 4 Li — KellyBoost | Growth objective beats predict-then-optimise and surrogates (Sharpe ≈ 0.30, gross) | KellyBoost Sharpe 0.23, CAGR 4.4%, max DD −40%; beats two-stage (−0.07), multiclass (0.21), unconditional Kelly (0.10); **equal weight 0.58, CAGR 7.7%, DD −24%** | **Relative claim reproduced on the paper's legs only** (regional ETFs: KellyBoost last, Sharpe 0.10); naive 1/N beats every learned method in both universes |
| 8 Liang, Zohren, Cucuringu — attribution-guided interventions | Baseline net Sharpe 0.62 (XGB) / 0.58 (FFN); interventions raise net SR in 8/8 cases (7 significant) | Gross SR 1.28 / 1.37 (paper 1.02 / 1.31) but turnover 70–80%/day → baseline **net SR −1.53 / −0.25**. Stabilised rules raise net SR in 3 of 4 cases (XGB +1.19 and +0.82, p < 0.001); unstabilised rules do not. Best variant net SR 0.09; deflated-Sharpe prob ≈ 0 | **Mechanism partly reproduced** (stabilised exposure adjustments cut turnover and help); **profitability not** — nothing is tradable at 5 bp |

## Paper 1 — Simple Dynamic Stock/Bond/Gold Portfolios (arXiv 2609.07946)

Setup exactly as the paper: SPY/AGG/GLD + cash (Fed funds), monthly, long-only, 5 bp spread (2.5 bp half-spread),
11-day covariance, 7% vol target, problem (3) solved with CVXPY/Clarabel; ridge forecast of 100-day forward returns on
the repo's 42 features (λ = 10, half-life 252, ≤ 512 rows, causal). Decisions at the rebalance close (paper's
convention); 1-day-lag variant also run.

| Portfolio (2006–2025) | CAGR | Vol | Sharpe (paper's geometric) | Max DD | Turnover | Paper Sharpe |
|---|---|---|---|---|---|---|
| 60/40 | 8.1% | 11.4% | 0.57 | −33.7% | 0.06 | 0.56 |
| 50/30/20 | 9.1% | 10.3% | 0.71 | −27.1% | 0.07 | 0.70 |
| 50/30/20 VC | 7.7% | 7.3% | 0.83 | −15.9% | 0.81 | 0.82 |
| Simple Markowitz | 10.3% | 9.3% | 0.93 | −15.8% | 2.79 | 0.91 |
| **Markowitz** | **11.5%** | **8.9%** | **1.10** | **−18.1%** | 2.81 | **1.08** |
| Markowitz, 1-day lag | 11.0% | 9.0% | 1.03 | −16.5% | 2.78 | — |

Through Oct 2026 (10 extra months the paper never saw): Markowitz Sharpe 1.03 vs 60/40 0.57.
The optimiser held 100% cash Sep 2022 – Jan 2023 (forecasts below the Fed funds rate): 11 of 240 months.

Regional extension (equity leg swapped, AGG/GLD/cash kept, USD investor, 2006–Oct 2026):

| Region (equity) | 60/40 | 50/30/20 | 50/30/20 VC | Markowitz | Equity B&H |
|---|---|---|---|---|---|
| Europe (EZU) | 0.22 | 0.34 | 0.32 | 0.34 (max DD −22%) | 0.15 |
| Japan (EWJ) | 0.19 | 0.33 | 0.32 | **0.54** (−21%) | 0.13 |
| China (FXI) | 0.16 | 0.26 | 0.37 | 0.40 (−24%) | 0.09 |

Most of the gain abroad is gold + volatility control; the return forecast adds little outside the US
(the Fama-French and FRED features are US-specific).

## Paper 2 — Explainable Regime-Aware Investing (arXiv 2603.04441)

Re-implemented Algorithm 1: rolling Gaussian HMM (full cov) on [r, 60d vol, 20d mean] of SPY/AGG/GLD/USO/UUP,
predictive order selection K ∈ {2,3,4} every 21 days, 2-Wasserstein template tracking (G = 6, EMA 0.05),
mixture moments → daily MVO (max μ'w − 10 w'Σw − 5bp‖Δw‖₁, 0 ≤ w ≤ 0.5). Unpublished hyperparameters were fixed
a priori (not tuned on test data). KNN baseline per Algorithm 2.

| Window | Strategy | CAGR | Vol | Sharpe | Max DD |
|---|---|---|---|---|---|
| 2024-03..2026-02 (paper-like) | W-HMM + MVO (net) | 10.3% | 4.5% | 1.25 | −4.6% |
| | Equal weight | 18.2% | 9.1% | 1.40 | −7.8% |
| | SPY | 17.8% | 16.4% | 0.81 | −18.8% |
| | KNN + MVO (net) | 31.6% | 11.6% | 2.05 | −5.4% |
| 2012..2026-10 | W-HMM + MVO (net) | 4.0% | 4.0% | 0.59 | −7.9% |
| | Equal weight | 5.8% | 9.6% | 0.46 | −27.0% |
| | SPY | 15.0% | 16.5% | 0.83 | −33.7% |
| | KNN + MVO (net) | 6.7% | 10.5% | 0.51 | −27.9% |
| Europe / Japan / China 2012– | W-HMM (net) | 2.6% / 3.7% / 3.9% | ~4–5% | 0.25 / 0.42 / 0.46 | ≈ −9% |
| | Equity B&H | | | 0.44 / 0.47 / 0.15 | −41% / −33% / −61% |

Average weights (paper window): UUP 48%, AGG 25%, SPY 16%, GLD 11%, USO 0% — a dollar/bond-heavy defensive book.
Turnover is tiny (0.1–0.2%/day), consistent with the paper's "smooth weights" claim; the Sharpe is not.

## Paper 3 — Tabular DL, cross-regime Bayesian optimisation (arXiv 2608.27076)

300 S&P 500 large caps (current constituents → survivorship bias), 29 price/volume/FRED features (no fundamentals,
analyst ratings, news sentiment or Google Trends — the paper's licensed data), 3-class next-day decile target,
RobustScaler, balanced weights; Optuna TPE on folds 2022/2023/2024 with the paper's eq. (2) score (16 XGBoost,
4 TabNet, 10 LogReg trials); Hybrid = rank-average of XGBoost & TabNet; top-n long / top-n short, daily, 2.2 bp/leg,
trade at the close (paper's assumption). Final models trained on 2015–2024, frozen, tested on 2025 and 2026 YTD.

| Model | 2022 | 2023 | 2024 | **2025 (paper OOS)** | **2026 YTD** |
|---|---|---|---|---|---|
| Hybrid | −4.6% (−0.36) | −4.0% (−0.60) | +7.1% (0.96) | **+0.6% (0.11)** | **−13.8% (−0.79)** |
| XGBoost | −8.6% (−0.51) | −7.2% (−0.63) | −4.4% (−0.35) | +13.0% (1.08) | −4.6% (−0.14) |
| TabNet | −3.3% (−0.37) | −4.9% (−0.92) | −5.1% (−1.01) | −1.8% (−0.17) | −9.4% (−0.82) |
| LogReg | −1.6% (−0.03) | +6.6% (0.58) | +10.7% (0.95) | +3.8% (0.38) | −32.4% (−1.59) |

(annual return, Sharpe in brackets). Paper: Hybrid 2025 +51.3%, Sharpe 2.44; its own validation years were weak too
(Hybrid Sharpe 0.22 / 0.08 / 1.32 in 2022–24). At 5 bp per leg every model is negative in every year except XGBoost
2025; with a 1-day execution lag results flip sign erratically (e.g. XGBoost 2026 +39%, Hybrid 2025 −22.5%) —
the signal is too fragile to trade. Long-side precision 17–25% vs 10% random.

## Paper 4 — KellyBoost (arXiv 2608.23393)

Multi-output XGBoost (`multi_output_tree`) with the paper's exact log-growth gradient/Hessian, 4-member
leave-one-row-out ensemble, 21-day decisions anchored at the last decidable row, expanding window of realised labels;
hyperparameters picked on 2001–2012 only by the paper's purged walk-forward (single-row tests every 11 rows,
purge 19, embargo 60) over a 4-point grid → η 0.05, depth 3, 100 rounds, λ 1. ~171 hand-built features (paper: 174;
its 7,871-column feature search was not reproduced). Same 8 legs as the paper. Evaluation 2013-01 → 2026-10.

| Method (gross) | CAGR | Vol | Sharpe | Max DD | log growth /20d ×100 | Turnover/yr |
|---|---|---|---|---|---|---|
| KellyBoost | 4.4% | 20.4% | 0.23 | −40.1% | 0.34 | 3.2× |
| Multiclass surrogate | 3.9% | 17.2% | 0.21 | −37.3% | 0.31 | 2.8× |
| Unconditional Kelly | 1.9% | 19.0% | 0.10 | −52.3% | 0.15 | 0.7× |
| Two-stage LGBM + Kelly | −3.3% | 25.6% | −0.07 | −63.2% | −0.27 | 8.4× |
| **Equal weight (1/8)** | **7.7%** | 10.7% | **0.58** | **−23.9%** | **0.59** | 0.2× |

Costs barely matter (KellyBoost Sharpe 0.22 at 5 bp, 0.21 at 10 bp). The growth objective wins its comparison
against other learned methods as the paper says, but the allocations are erratic (e.g. 88% silver in Mar 2017,
80% FXI in the regional run in 2024) and 1/N dominates on growth, Sharpe and drawdown.
Regional run (not in the paper; legs SPY/EZU/EWJ/FXI/TLT/GLD/cash, same protocol, selected η 0.05, depth 3,
100 rounds, λ 0.05; 2013-01 → 2026-10, gross):

| Method | CAGR | Vol | Sharpe | Max DD | log growth /20d ×100 | Turnover/yr |
|---|---|---|---|---|---|---|
| KellyBoost | 2.1% | 16.2% | **0.10** | −35.6% | 0.17 | 4.0× |
| Two-stage LGBM + Kelly | 3.3% | 19.7% | 0.17 | −50.8% | 0.26 | 8.0× |
| Multiclass surrogate | 6.5% | 13.7% | 0.40 | −32.3% | 0.50 | 3.0× |
| Unconditional Kelly | 4.3% | 15.4% | 0.23 | −36.9% | 0.33 | 0.7× |
| **Equal weight (1/7)** | 6.4% | 10.3% | **0.49** | −24.5% | 0.50 | 0.2× |

Here even the relative claim fails: KellyBoost is last on Sharpe and log growth (0.09 net of 5 bp). Its allocations
swing between concentrated bets (65–79% EZU in 2017–21, 80% FXI in 2024, 58% GLD in 2025). The first attempt
crashed when Clarabel failed on one unconditional-Kelly problem; the rerun retries with SCS and would keep the previous
weights if both solvers failed (that never happened; KellyBoost weights match the first attempt up to the crash).

## Paper 8 — attribution-guided feature-exposure interventions (arXiv 2610.15144)

337 S&P 500 large caps with full history 2004 → Aug 2026 (Ken French data end). FF5 betas from 60-day rolling
regressions; tradable residual portfolios ε_t = Φ_{t−1}R_t (eqs. 2–4); 18 signals per stock from the last 30
residuals (OU/AR(1) fit, s-score, R², residual moments, predicted residual, 2-state-HMM regime entropy/duration/
transition prob, liquidity), cross-sectionally standardised; XGB (custom net-Sharpe objective, autograd gradient)
and FFN (32-16-8-4) trained to maximise net Sharpe at 5 bp; 4y train / 1y validation / 1y trade, re-estimated
yearly, trading 2010 → Aug 2026. Attribution = central-difference ∂SR_net/∂θ on the validation year; exposures
f = 1 + 0.5·tanh(T/sd(T)), θ ∈ [0, 3]; unstabilised / stabilised × model-specific / cross-model, as in the paper.
Simplifications: 2-state HMM instead of HDP-HMM regime-switching OU; dollar-volume proxies instead of market cap and
share turnover; XGB uses first-order boosting with normalised gradients.

| Model | Rule | SR gross | SR net (5 bp) | Daily turnover | ΔSR net vs baseline | bootstrap p |
|---|---|---|---|---|---|---|
| XGB | baseline | 1.28 | −1.53 | 81% | — | — |
| XGB | model-specific unstabilised | 1.08 | −1.43 | 71% | +0.10 | 0.60 |
| XGB | **model-specific stabilised** | 1.30 | **−0.34** | 43% | **+1.19** | **<0.001** |
| XGB | cross-model unstabilised | 1.22 | −1.32 | 72% | +0.21 | 0.24 |
| XGB | **cross-model stabilised** | 1.00 | −0.72 | 46% | **+0.82** | **<0.001** |
| FFN | baseline | 1.37 | −0.25 | 71% | — | — |
| FFN | model-specific unstabilised | 1.15 | −0.42 | 60% | −0.18 | 0.43 |
| FFN | model-specific stabilised | 1.20 | −0.14 | 49% | +0.11 | 0.73 |
| FFN | cross-model unstabilised | 1.37 | −0.25 | 64% | −0.01 | 0.96 |
| FFN | cross-model stabilised | 1.30 | **+0.09** | 45% | +0.34 | 0.17 |

Paper (Table 2 / 7): gross SR 1.02 (XGB) / 1.31 (FFN), net 0.62 / 0.58, daily turnover 13% / 27%; interventions
+0.05 to +0.25 net SR. Our gross edge matches the paper, but our Sharpe-trained allocators trade 3–6× more, so the
5 bp cost wipes it out; training on in-sample net Sharpe did not learn the paper's low turnover. The stabilised
rules help mostly by cutting turnover (≈ 80% → 45%/day), matching the paper's own explanation of why they work.
Year by year the baselines are positive in only 6 (FFN) and 3 (XGB) of 17 years, and 2022–2026 are all negative
for XGB: the residual-reversal edge in large caps has been weak recently. Deflated Sharpe (ml4t.diagnostic,
80 trials) of the best variant: probability ≈ 0; active vs FFN baseline: 0.004.
Files: `results/p8_summary.csv`, `p8_by_year.csv`, `p8_attributions.csv`, `p8_daily_*.csv`, `p8_cumulative.png`.

## Caveats

- Survivorship bias in papers 3 and 8 (current S&P 500 constituents); ETF-based papers 1, 2, 4 avoid it.
- Paper 2's and paper 3's hyperparameters/budgets are partly ours (the papers do not publish them); choices were
  fixed before looking at test data and are listed in each script's header.
- Paper 3 without the licensed fundamental/sentiment data is not a full replication; the gap to +51% may be partly
  data, but the paper's own weak 2022–24 validation folds and our negative 2026 suggest 2025 was favourable luck.
- Single-path backtests; only paper 8 has a bootstrap test, and only paper 1 reproduces closely enough to treat
  the paper's own significance analysis as confirmed.
