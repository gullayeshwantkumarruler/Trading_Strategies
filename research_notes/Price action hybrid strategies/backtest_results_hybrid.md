# Backtest results: more price action rules, hybrids and one leaderboard

This round adds 53 daily rules and hybrids and 46 intraday variants (Noise Area on IWM and DIA, VIX/NR4 gates, VWAP
trend). Then every price-action strategy from both rounds is scored on the same scorecard: 318 candidates, 478 distinct
configurations, 1,524 series once cost and fill re-runs are counted. Background research is in
[the report](../../reports/Price%20action%20hybrid%20strategies.md); the earlier round's results are in
[backtest_results_price_action.md](../Price%20action%20strategies%20by%20horizon/backtest_results_price_action.md).

Code is in `strategies/price_action/`:

| File | Contents |
|---|---|
| `hybrid.py` | The new daily rules |
| `intraday2.py` | The new intraday rules |
| `evaluate.py` | Robustness and multiple-testing tests |
| `leaderboard.py` | The scorecard |
| `plot_leaders.py` | Equity-curve charts |

Outputs are in `results/`:

| File | Contents |
|---|---|
| `leaderboard.csv` | Every candidate and every metric |
| `leaderboard_family.json` | PBO, SPA, StepM and DSR by family |
| `hybrid_summary_2bp.csv` | Summary of the daily hybrids |
| `intraday2_all.csv` | Intraday hybrid results |
| `leaderboard_equity.png` | Equity curves of the leaders |

## How it was tested

**Rules and data**
- Rules were run as published. Parameters with no published value are flagged `[unpublished]` in the docstrings. They were fixed before the first run and never tuned.
- The data are US ETFs: yfinance adjusted daily bars and Alpaca SIP 1-minute bars (2016 to Oct 2026), now covering SPY, QQQ, IWM and DIA. FOMC decision days were scraped from federalreserve.gov for 1994–2026 (`data/fomc_dates.csv`).

**Sample windows**
- Daily rules: development up to 2015, sealed holdout 2016 to Oct 2026. Rules whose data start later (credit, VIX term structure, DAA) begin when their data does.
- Intraday rules: development 2016–2022, holdout 2023 to Oct 2026.

**Costs** (every rule is run at a base cost and at a stress cost)

| Family | Base cost | Stress cost | Other checks |
|---|---|---|---|
| Daily | 2 bp per side | 10 bp per side (5x) | 6 bp; a next-open fill for engine-based rules |
| Intraday | $0.0035/share commission + $0.001 slippage | $0.01 slippage | |
| Positional (round 5) | 5 bp | none | |

**Scorecard: every candidate**

| Metric | Window or detail |
|---|---|
| Sharpe | development, holdout, holdout at stress cost, holdout with next-open fill |
| CAGR, max drawdown, exposure | holdout |
| Lo autocorrelation-adjusted Sharpe | full sample |
| 95% confidence interval for Sharpe | holdout, stationary bootstrap |
| PSR and minimum track-record length | |
| Harvey–Liu BHY haircut Sharpe | N = 478 distinct configurations |
| Alpha, beta and alpha t-stat vs SPY | Newey–West |
| Bootstrap test of Sharpe vs SPY | |
| Share of positive years | holdout |

**Scorecard: each family**

| Test | Detail |
|---|---|
| PBO | CSCV with 16 blocks (12,870 splits) |
| Hansen SPA / White Reality Check | holdout, vs cash and vs SPY |
| Romano–Wolf StepM | holdout, vs cash and vs SPY |
| Deflated Sharpe | all 318 candidates |

**Gates.** A strategy passes only if all three hold:
- holdout Sharpe > 0 at stress cost;
- development Sharpe > 0;
- haircut Sharpe > 0.

**Score.** Percentile ranks, weighted:

| Component | Weight |
|---|---|
| Holdout Sharpe | 30% |
| Holdout Sharpe at stress cost | 20% |
| Haircut Sharpe | 15% |
| Alpha t-stat | 10% |
| Lo Sharpe | 10% |
| Holdout max drawdown | 10% |
| Share of positive years | 5% |

The research notes found no published standard for these weights.

## Headline

1. **Nothing beats buy-and-hold SPY once multiple testing is accounted for.** Every family beats cash: the SPA p-value against cash is 0.000 for swing, 0.002 for hybrid, 0.02 for positional and 0.006 for intraday. Against SPY, the SPA p-values are 0.50–0.95 and Romano–Wolf StepM finds no survivor in any family. For reference, SPY's holdout Sharpe is 0.87 for 2016–26 and 1.34 for 2023–26.
2. **27 of 318 candidates pass all three gates.** Fourteen are round-5 swing rules, ten are new hybrids, two are intraday and one is positional. These are real edges over cash, but most are part-time strategies with 4–10% CAGR.
3. **The top score, Noise Area with a VWAP stop on QQQ, is a single-ticker result.** It now has a 3.8-year holdout Sharpe of 1.57, or 1.46 at 10× slippage, an alpha t-stat of 3.2 and positive returns every year. The same rule loses money on IWM (holdout Sharpe −0.69) and DIA (−0.21). On SPY it makes 0.60 for 2023–26 but 0.00 from Mar 2024, the paper's out-of-sample window. Gating it by VIX or NR4 days made it worse on QQQ and SPY.
4. **The hybrids that add value are overlays that decide *when* to hold the index**: volatility targeting, DAA, the jump model, breadth and the VIX term structure. Each matches SPY's Sharpe with 20–40% smaller drawdowns. None adds a new entry signal.
5. **The new pure price action rules mostly repeat RSI(2) or fail.** Double 7s, cumulative RSI and %b behave like RSI(2), and a Larry Williams volatility breakout lost money on all four ETFs. Turnaround Tuesday works gross but dies at 10 bp.

## Leaderboard: all 27 strategies that pass the gates

All figures are net of costs. Holdout Sharpe is at the base cost; "Stress" is the holdout Sharpe at the stress cost.

| # | Strategy | Dev Sharpe | Holdout Sharpe | Stress Sharpe | Holdout CAGR | Holdout max DD | Exposure | Haircut Sharpe | α t-stat | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Noise Area + VWAP, 1x, QQQ (intraday) | 1.14 | 1.57 | 1.46 | 13% | −8% | 57% | 0.52 | 3.24 | 0.99 |
| 2 | Noise Area + VWAP, vol-target, QQQ (intraday) | 1.12 | 1.63 | 1.52 | 25% | −15% | 57% | 0.55 | 3.25 | 0.96 |
| 3 | RSI(3)+IBS, XLK | 0.81 | 0.84 | 0.74 | 6% | −6% | 4% | 0.37 | 2.63 | 0.94 |
| 4 | 3 down days, SMH | 0.56 | 1.02 | 0.91 | 12% | −13% | 15% | 0.23 | 3.39 | 0.93 |
| 5 | IBS < 0.2, QQQ | 0.47 | 1.23 | 0.91 | 18% | −15% | 43% | 0.03 | 2.50 | 0.91 |
| 6 | RSI(3)+IBS, QQQ | 0.90 | 0.76 | 0.64 | 5% | −8% | 5% | 0.42 | 2.11 | 0.91 |
| 7 | **DAA G12 (canary rotation)** | 0.85 | 0.95 | 0.84 | 9% | −19% | 99% | 0.19 | 1.92 | 0.90 |
| 8 | **SPY volatility-targeted to 10%** | 0.64 | 0.95 | 0.89 | 10% | −14% | 100% | 0.33 | 1.25 | 0.89 |
| 9 | RSI(2), XLY | 0.71 | 0.80 | 0.62 | 6% | −12% | 15% | 0.18 | 1.84 | 0.89 |
| 10 | IBS < 0.2, XLK | 0.40 | 1.25 | 0.95 | 21% | −20% | 44% | 0.09 | 2.60 | 0.88 |
| 11 | 3 down days, SPY | 0.71 | 0.80 | 0.55 | 4% | −13% | 15% | 0.31 | 2.04 | 0.88 |
| 12 | RSI(2), SPY | 0.84 | 0.76 | 0.55 | 5% | −11% | 15% | 0.46 | 1.72 | 0.87 |
| 13 | IBS < 0.2, SPY | 0.79 | 0.92 | 0.52 | 10% | −16% | 43% | 0.49 | 1.28 | 0.87 |
| 14 | **RSI(2) + high-volume day, SPY** | 0.77 | 0.74 | 0.53 | 4% | −11% | 14% | 0.36 | 1.63 | 0.86 |
| 15 | IBS < 0.2, DIA | 0.73 | 0.83 | 0.40 | 9% | −16% | 47% | 0.28 | 1.16 | 0.84 |
| 16 | **Double 7s, SPY** | 0.82 | 0.69 | 0.52 | 6% | −13% | 34% | 0.39 | 0.85 | 0.83 |
| 17 | **Jump-model regime, SPY** | 0.75 | 0.78 | 0.77 | 9% | −21% | 73% | 0.07 | 0.96 | 0.83 |
| 18 | RSI(2)+IBS, SPY | 0.82 | 0.69 | 0.52 | 4% | −11% | 9% | 0.39 | 1.64 | 0.82 |
| 19 | IBS < 0.2, XLP | 1.03 | 0.80 | 0.26 | 7% | −19% | 50% | 0.58 | 1.56 | 0.80 |
| 20 | **Four-book ensemble, 10% vol** | 0.90 | 0.71 | 0.34 | 6% | −13% | 100% | 0.37 | 0.51 | 0.80 |
| 21 | **Faber SMA10 + vol target, SPY** | 0.76 | 0.70 | 0.64 | 7% | −19% | 83% | 0.32 | 0.57 | 0.79 |
| 22 | IBS < 0.2, XLB | 0.65 | 0.77 | 0.37 | 10% | −20% | 51% | 0.01 | 1.11 | 0.79 |
| 23 | Large-decline pullback, SPY | 0.79 | 0.58 | 0.42 | 3% | −9% | 12% | 0.28 | 0.99 | 0.78 |
| 24 | **Cumulative RSI(2), SPY** | 0.80 | 0.55 | 0.34 | 3% | −9% | 15% | 0.27 | 0.87 | 0.77 |
| 25 | **Double 7s, SMA5 exit, SPY** | 0.65 | 0.62 | 0.33 | 4% | −12% | 23% | 0.04 | 0.94 | 0.77 |
| 26 | **TSMOM 12-1, 9 ETFs** | 0.88 | 0.50 | 0.47 | 3% | −15% | 99% | 0.22 | −0.32 | 0.69 |
| 27 | Faber SMA10, SPY (offset 0) | 0.79 | 0.50 | 0.50 | 6% | −35% | 84% | 0.19 | −1.34 | 0.63 |

Bold rows are new this round. SPY buy-and-hold over the same holdout had Sharpe 0.87, CAGR about 15% and max drawdown −34%.

## New rules in detail (holdout 2016 to Oct 2026 unless noted)

### Regime, breadth and cross-asset overlays on SPY

These are mostly drawdown control: Sharpe is about the same as SPY, with smaller drawdowns.

| Rule | Holdout Sharpe | At 10 bp | CAGR | Max DD | Notes |
|---|---|---|---|---|---|
| VIX/VIX3M backwardation (flat after 3 days above 1) | 0.95 | 0.94 | 14% | −24% | Best raw result, but its data start in 2007, so the haircut is 0 and it fails that gate. Flat only 4% of days since 2016. StepM survivor vs cash. |
| SPY vol-targeted to 10% | 0.95 | 0.89 | 10% | −14% | Passes. The simplest overlay is as good as any. |
| DAA G12 (EEM/AGG canary, 13612W, top 6) | 0.95 | 0.84 | 9% | −19% | Passes. Sits on average 38% in the protective assets. |
| Breadth (≥60% of 9 sector SPDRs above SMA200) | 0.79 | 0.77 | 9% | −21% | Development Sharpe only 0.21, and the haircut is 0. |
| Jump model (round-1 code, ^GSPC signal, traded the day after) | 0.78 | 0.77 | 9% | −21% | Passes. Matches the paper's claim of lower drawdowns, not higher Sharpe. |
| Faber SMA10 + vol target | 0.70 | 0.64 | 7% | −19% | Passes. |
| Credit (HYG/IEF above its SMA200) | 0.54 | 0.47 | 6% | −35% | Did not reduce the 2020 or 2022 drawdowns. |
| GEM dual momentum | 0.48 | 0.46 | 7% | −37% | Lags. Consistent with the post-publication decay in the research notes. |
| TSMOM 12-1, long/flat, 9 ETFs | 0.50 | 0.47 | 3% | −15% | Passes, but alpha is negative. |
| Halloween (hold Nov–Apr) | 0.49 | 0.48 | 6% | −34% | Fails: development Sharpe 0.60 but holdout CI includes 0 and haircut 0. |

### Calendar rules

| Rule | Holdout Sharpe | At 10 bp | Exposure | Verdict |
|---|---|---|---|---|
| Turnaround Tuesday, SPY | 0.76 | 0.24 | 15% | Gross edge (55% wins, 698 trades); costs take most of it, and the haircut is 0 |
| Turnaround Tuesday, QQQ | 0.75 | 0.31 | 14% | Same, and the development Sharpe is only 0.16 |
| Wide turn of month (±3 days) | 0.55 | 0.34 | 33% | Fails the haircut |
| Narrow turn of month (L−1 to +3) | 0.39 | — | 20% | Weak, consistent with the decay in the research notes |
| Pre-FOMC drift | 0.03 | −0.39 | 6% | **Gone after 2015**: development Sharpe 0.66, holdout 0.03 |
| TOM ∪ FOMC | 0.40 | 0.03 | 29% | Fails |
| Overnight hold (close to open), SPY and QQQ | −0.04 / 0.15 | −2.8 | 100% | Two trades a day: costs consume any drift |

### New swing entries (SPY, QQQ, IWM, DIA)

| Rule | SPY | QQQ | IWM | DIA | Verdict |
|---|---|---|---|---|---|
| Double 7s | 0.69 | 0.70 | 0.12 | 0.57 | Passes on SPY. Correlated with RSI(2), so adds little diversification. |
| Double 7s, SMA5 exit | 0.62 | 0.53 | 0.20 | 0.25 | Passes on SPY, weaker elsewhere |
| Cumulative RSI(2) | 0.55 | 0.39 | 0.16 | 0.66 | Passes on SPY |
| %b three days | 0.34 | 0.18 | 0.29 | 0.36 | Weak |
| RSI(2) + high-volume day (Llorente hypothesis) | 0.74 | 0.61 | 0.10 | 0.37 | About the same as plain RSI(2) (0.76 on SPY), so volume adds nothing |
| RSI(2) gated by jump model instead of SMA200 | 0.30 | 0.42 | 0.06 | 0.11 | **Worse** than the SMA200 gate |
| VIX stretch (Connors) | 0.09 | 0.26 | 0.36 | −0.03 | Fails |
| Larry Williams breakout (open + 0.25 × range) | −0.84 | −0.02 | −0.85 | −0.90 | Fails badly |

### Intraday hybrids (holdout 2023 to Oct 2026, $0.001 slippage)

| Rule | QQQ | SPY | IWM | DIA |
|---|---|---|---|---|
| Noise Area, base exit | 1.29 | 0.62 | −0.85 | −0.19 |
| Noise Area + VWAP stop | **1.57** | 0.60 | −0.69 | −0.21 |
| Noise Area + VWAP + vol target | **1.63** | 0.78 | −0.38 | −0.12 |
| + trade only when VIX above its expanding median | 1.04 | 0.35 | −0.68 | −0.13 |
| + trade only after an NR4 day | 1.35 | 0.47 | −0.11 | −0.77 |
| VWAP trend (long above / short below VWAP, every minute) | 0.12 | −0.47 | −1.16 | −0.87 |

On the paper's own out-of-sample window (Mar 2024 onward), Noise Area + VWAP on SPY has Sharpe 0.00 (see
`intraday2_all.csv`).

- The authors' gates (VIX at the open, NR4) cut Sharpe on QQQ and SPY. On IWM and DIA the gated versions still lose money.
- VWAP trend, reported at Sharpe 2.1 for 2018–23, makes 0.44 net on QQQ over 2016–26, with about 8 round trips a day.

## Robustness and multiple-testing diagnostics

| Family | Candidates | PBO (CSCV) | Mean OOS Sharpe of in-sample best | SPA p vs cash | SPA p vs SPY | StepM survivors vs cash | StepM survivors vs SPY |
|---|---|---|---|---|---|---|---|
| Swing (round 5) | 165 | 0.23 | 0.63 | 0.000 | 0.50 | 10 (mostly IBS and SMH/XLK) | 0 |
| Hybrid (new) | 53 | 0.45 | 0.48 | 0.002 | 0.93 | 6 (DAA, vol target, jump model, breadth, VIX TS, Double 7s QQQ) | 0 |
| Positional (round 5) | 54 | 0.47 | 0.35 | 0.02 | 0.95 | 3 | 0 |
| Intraday | 46 | 0.02 | 0.94 | 0.006 | 0.54 | 2 (Noise Area QQQ variants) | 0 |

- **Deflated Sharpe** over all 318 candidates: the best full-sample Sharpe is 0.85 (IBS on XLP), and the DSR probability is 0.88. That is below the usual 0.95 bar, so no single daily rule is significant after accounting for the search.
- **PBO**: hybrid and positional selections are a coin flip (about 0.45). Swing PBO is 0.23. Intraday PBO is low (0.02) because the QQQ Noise Area variants are best in nearly every split. That shows the QQQ result is consistent over time, not that it carries over to other tickers.
- **Fill stress**: moving from a close fill to the next open roughly preserves the mean-reversion results (RSI(2) SPY 0.76 → 0.55; IBS QQQ 1.23 → 0.94).
- **Cost stress**: the high-turnover rules lose 40–70% of their Sharpe at 10 bp. These are IBS, Tuesday and the ensemble, which trades several books. The overlays (vol target, DAA, jump model) lose under 0.1.
- **Ensemble**: equal-risk mean reversion, jump model, DAA and seasonal books at 10% vol. It has the lowest drawdown of the full-exposure rules (−13%) and passes the gates. Its holdout Sharpe is 0.71, below its best single book, and it drops to 0.34 at 10 bp. A bug was fixed before these numbers: a book that sat flat for 63 days used to send the whole ensemble to cash.

## Verdict

- **Best intraday:** Noise Area + VWAP stop on QQQ. It is the only strategy with significant alpha out of sample, stable over time (PBO 0.02), and cost-robust (still Sharpe 1.46 at 1¢ slippage). Treat it as one bet on one market: the identical rule loses on IWM and DIA and fades on SPY, and the authors' gates hurt.
- **Best daily trading rules:** the short-term mean-reversion family (IBS, RSI(3)+IBS, RSI(2), 3 down days), on large-cap equity and tech ETFs. Their edge over cash is robust: it shows up across ETFs, survives next-open fills, and passes SPA and StepM against cash. The new Double 7s and cumulative RSI rules belong to the same family. Run them as one combined book, not as separate signals.
- **Best overlays:** volatility targeting, DAA and the jump model. They give SPY-like Sharpe with roughly half the drawdown. Volatility targeting is the simplest and the hardest to beat.
- **Dropped:** pre-FOMC drift (gone after 2015), Larry Williams breakout, VIX stretch, VWAP trend, overnight hold, GEM, the credit filter, and the VIX/NR4 gates on Noise Area.
- **What these tests cannot rule out:** ETF universes are hand-picked, not survivorship-free. The holdout covers one long bull market. Intraday covers only about 3.8 years of holdout. The scorecard weights are the report's proposal, not a standard.
