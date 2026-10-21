# Equity stat-arb build — results of all six steps (+ MOSEK)

Code: `strategies/statarb/` (`core.py`, `step1_construction.py`, `step2_residuals.py`, `step3_dlsa.py`,
`step3b_attention_factors.py`, `edgar.py`, `step4_alpha_library.py`, `step5_altdata.py`, `collect_daily.py`,
`mosek_bench.py`, `dsr_check.py`, `run_all.py`). Results: `strategies/statarb/results/` (CSVs, logs, PNGs,
`trials/` = daily net returns of every variant tried).

Common setup (the literature's standard): 337 current S&P 500 large caps (survivorship bias → upper bounds),
2010-01 → 2026-08 (Ken French data end), weights decided at the close of d earn the excess return of d+1, costs
5 bp per unit one-way turnover + 1 bp/day on short notional, unit gross leverage, 2022–2026 reported separately.
Data: yfinance, Ken French, SEC EDGAR (companyfacts XBRL, 10-K/10-Q text, Form 3/4/5 datasets — User-Agent with
the account owner's contact email, read from the `SEC_USER_AGENT` environment variable, not stored in the repo),
FINRA consolidated short-volume files.

## Headline

| Rank | Strategy | Net SR 2010/13–2026 | 2010–21 | 2022–26 | Daily turnover | Max DD |
|---|---|---|---|---|---|---|
| 1 | **Slow alpha composite (LightGBM over 27 signals) → cost-aware optimiser, γ_trade 0.5** (step 4) | **1.03** (from 2013) | 1.16 | **0.80** | 1% | −5.9% |
| 2 | **Attention Factors lite, cost in loss** (step 3b) | **0.86** | 1.03 | **0.38** | 6% | −36.5% (Mar 2020) |
| 3 | DLSA CNN-Transformer on FF5 residuals, cost in loss (step 3) | 0.21 | 0.50 | −0.29 | 20% | −12.7% |
| 4 | LightGBM composite, plain monthly long-short (step 4) | 0.18 | 0.27 | 0.04 | 5% | −5.8% |
| — | every parametric residual-reversal rule (steps 1–2), insiders, Lazy Prices, FINRA | ≤ 0.03 | ≤ 0.30 | all < 0 except FINRA 0.15 | | |

The two leaders are nearly uncorrelated (daily ρ = 0.075); an equal-risk mix has SR 1.27.
Deflated Sharpe (`results/deflated_sharpe_full_window.csv`, 2013-03 → 2026-08): under the noise-only null with
K = 74 candidate trials, P(true SR > 0) = 0.998 (slow optimiser) and 0.957 (Attention Factors); within their own
families (correlation-adjusted K_eff) 0.982 and 0.987. Using the cross-trial Sharpe variance of all trials — which
is dominated by deliberately naive daily-rebalance variants at SR −3 to −4 — both collapse to ≈ 0; the realistic
nulls clear the plan's 0.9 bar, the strict one does not.

Survivorship bias, a single universe and US-only data mean these are upper bounds; the next check is a
point-in-time universe.

## Step 1 — cost-aware construction around residual reversal

Signals: −(sum of last k FF5 residuals), k = 1, 5, 10, FF5-neutralised. IC of the 5-day signal: 0.007 at lag 1,
≈ 0 by lag 10 (all residual models, table below) — the edge is real but tiny and fast.

| Variant (best of each family) | Gross SR | Net SR | Turnover/day | 2010–21 | 2022–26 |
|---|---|---|---|---|---|
| k1 daily full rebalance | 1.17 | −3.38 | 145% | −3.28 | −3.64 |
| k5 partial trading τ = 0.05 (Gârleanu-Pedersen) | 0.47 | −0.14 | 5% | +0.05 | −0.52 |
| k10 no-trade band 1/N | 0.75 | −0.30 | 25% | −0.11 | −0.75 |
| k5 CVXPY+Clarabel optimiser, γ_trade 0.5 (Markowitz++-style, factor risk, dollar/beta/sector/FF5 limits) | 0.74 | **+0.03** | 20% | +0.30 | −0.60 |

Partial trading, bands, holds and the optimiser all cut turnover 7–30× but the gross edge decays almost as fast;
nothing makes fast residual reversal pay after 2021. (γ_trade = 5 left the optimiser empty: 1–2 bp/day of alpha
never pays a 5 bp trade; γ < 1 = amortising the cost over ~1/γ days.)

## Step 2 — residual ladder and published rules

| Residuals | IC lag 1 | lag 5 | rev5 daily net SR | rev5 partial τ=0.1 net SR (2010–21 / 2022–26) | NFE rule L60 H20 |
|---|---|---|---|---|---|
| FF5 | 0.0072 | 0.0042 | −1.14 | −0.08 (+0.06 / −0.40) | −0.09 |
| PCA-3 | 0.0087 | 0.0040 | −0.98 | −0.04 (+0.18 / −0.52) | −0.30 |
| PCA-5 | 0.0071 | 0.0037 | −1.24 | −0.12 (+0.21 / −0.89) | −0.31 |
| Char-projection ("IPCA-lite") | 0.0089 | 0.0036 | −0.97 | −0.12 (+0.09 / −0.62) | −0.16 |

Published rules: Robeco residual reversal (FF3, 36-month betas, monthly) net −0.34; SPONGE graph clustering
(Cartea-Cucuringu / Korniejczuk-Ślepaczuk) partial net −0.12 (+0.20 / −0.90). The NFE paper's ordering
(PCA > FF) does not reproduce here; differences between residual models are small next to costs.

## Step 3 — DLSA (Guijarro-Ordonez, Pelger & Zanotti) and 3b Attention Factors (Epstein et al. 2025)

DLSA re-implemented from `dlsa-public` (CNN [1,8] k2 + 1-layer 4-head Transformer on 30-day cumulative residuals,
residual-weight mapping to stocks, −Sharpe loss with 5 bp + 1 bp costs). CPU budget: retrain yearly with
warm-start (15 epochs, then 5/year) instead of 100 epochs every 125 days.

| Model | Gross SR | Net SR | 2010–21 | 2022–26 | Turnover |
|---|---|---|---|---|---|
| DLSA, FF5 residuals | 0.94 | 0.21 | 0.50 | −0.29 | 20% |
| DLSA, PCA-5 residuals | 0.92 | −0.42 | −0.36 | −0.54 | 22% |
| **Attention Factors lite** (K = 10 learned attention factors from 9 ranked price/volume characteristics, joint training) | 0.90 | **0.86** | 1.03 | 0.38 | 6% |

Putting costs in the loss is what works: the learned policies keep most of their gross Sharpe (AF: 0.90 → 0.86)
because they learn to trade slowly. Attention Factors is positive in 15 of 17 years (losers 2018 and 2022, SR −0.35
and −0.28); its −36.5% drawdown is the Feb–Mar 2020 crash at 17% annual vol. Paper: net SR 2.28 (K = 30, ~46
characteristics incl. fundamentals, CRSP 500, 1998–2021) — ours is a deliberately reduced CPU version.

## Step 4 — alpha library, point-in-time EDGAR fundamentals, combination

18 price/volume + 9 fundamental signals (SEC companyfacts, first-reported values only, usable from filing + 1 day).
Month-end rank IC vs next-21-day return, 2010–2026 (198 months): Amihud illiquidity t = 3.6 is the only strong single
signal; net issuance 1.7, accruals 1.6, gross profitability 1.5, SUE 1.1; low-vol / low-beta / low-MAX / low
idio-vol are significantly *negative* in these large caps (t −1.9 to −2.4).

| Composite (walk-forward, refit yearly, sector+FF5-neutralised) | IC | IC t | IC 2022–26 | ρ with rev5 | Monthly L/S net SR |
|---|---|---|---|---|---|
| Equal-weight (sign of training IC) | 0.003 | 0.4 | −0.019 | 0.32 | −0.61 |
| IC-weighted (36 months) | 0.006 | 0.9 | −0.015 | 0.19 | −0.34 |
| Ridge | 0.011 | 1.9 | 0.000 | 0.23 | −0.43 |
| **LightGBM** | **0.016** | **3.2** | 0.003 | 0.15 | **0.18** |

Cost-aware optimiser with the LightGBM composite as the slow alpha (Grinold scaling IC·σ·z/√21 per day):

| γ_trade | slow only: net SR (2010–21 / 2022–26), turnover | slow + fast rev5: net SR (2010–21 / 2022–26) |
|---|---|---|
| 0.05 | 0.45 (0.69 / 0.09), 6% | −0.76 (−0.52 / −1.19) |
| 0.1 | 0.55 (0.71 / 0.32), 5% | −0.55 (−0.28 / −1.01) |
| 0.2 | 0.53 (0.61 / 0.39), 3% | −0.25 (+0.03 / −0.74) |
| 0.5 | **1.03 (1.16 / 0.80), 1%** | 0.37 (0.62 / −0.06) |

All slow-only settings are positive in both periods; adding the fast reversal leg always hurts. The report's
"slow aim + fast timing" blend is therefore half-confirmed: the slow composite traded through a cost-aware optimiser
is the best book built; the fast leg adds only turnover. (A first run with mis-scaled slow alpha left the book
empty; fixed, and `avg_gross_lev` is now reported for every row.)

## Step 5 — free alternative data

| Signal | Net SR | 2010–21 | 2022–26 | FF5 alpha (ann.) | t (NW) |
|---|---|---|---|---|---|
| FINRA short-volume ratio (−SVR20), monthly quintile L/S, 2018-10 → | −0.31 | −1.18 (2018–21) | 0.15 | −1.1% | −0.9 |
| Insider opportunistic purchases (Form 3/4/5 datasets, CMP 2012 routine filter, 8,782 events), 21-day hold | −0.62 | −0.85 | −0.07 | −2.1% | **−2.7** |
| same, 5-day hold | −0.65 | −0.95 | −0.02 | −3.9% | −2.6 |
| Lazy Prices, cosine similarity of 10-K/10-Q vs year-ago filing (24,579 filings), monthly quintile L/S | −0.82 | −0.54 | −1.45 | −2.2% | **−3.2** |
| Lazy Prices, Jaccard similarity | −0.14 | 0.15 | −0.88 | −0.3% | −0.5 |

None works in large caps 2010–2026. Insider purchases have significantly *negative* alpha (insiders buy after
declines that keep going in this universe). Whole-document similarities cluster at ≈ 0.995 (boilerplate dominates);
the paper's section-level (e.g. MD&A, risk-factor) comparison would be the next refinement.

## Step 6 — forward data collection

`collect_daily.py` archives Yahoo Finance RSS headlines (337 names) + Google News RSS (top 50), yfinance option-chain
snapshots (top 100 by dollar volume; 2 nearest + ~30-day expiries) and the FINRA daily short-volume file into
`data/archive/YYYY-MM-DD/` (gitignored). First run (2026-10-21): 11,363 headlines, 28,518 option rows, 49,271 FINRA
rows, ~3.6 MB, 9 minutes. Scheduled with Windows Task Scheduler as `TradingStrategies_DailyCollect`, daily 03:00
local (after the US close), start-when-available. A news-conditioned test needs 12–24 months of archive.

## MOSEK (Personal Academic licence, valid to 2027-10-21)

| Test | Result |
|---|---|
| Continuous step-1 problem, 2024-01 → 2026-08 (≈680 solves) | Clarabel 0.074 s/solve, MOSEK 0.113 s/solve, both optimal, max weight difference 0.0005 |
| MIP: at most 100 names (2010 → 2026), MOSEK | 0.84 s/solve, net SR 0.02 (2022–26 −0.60) vs 0.03 for the continuous book — no gain |
| MIP: minimum trade 0.1% of gross (2022 → 2026, 5 s limit) | 5.1 s/solve (always hits the limit), 158 of ~1,150 days no feasible solution in time (previous weights kept); net SR −1.18 vs −0.60 for the continuous book over the same window; turnover 34% vs 22%/day — worse |

Conclusion: for every continuous formulation used here Clarabel is as accurate and faster; MOSEK is only needed for
the mixed-integer variants, and neither cardinality nor minimum-trade constraints improved the residual book.

## Reproduce

```
set SEC_USER_AGENT=Your Name your.email@example.com
.venv\Scripts\python strategies\statarb\run_all.py --only 1 2 3 3b 4 5
.venv\Scripts\python strategies\statarb\dsr_check.py
.venv\Scripts\python strategies\statarb\mosek_bench.py          (needs %USERPROFILE%\mosek\mosek.lic)
```
