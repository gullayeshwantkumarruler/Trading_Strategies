# AI alpha-research pipeline — results (round 4)

Code: `strategies/alpha_research/` (`fields.py` data grid incl. new alt data, `dsl.py` formula language + frozen referee,
`agent_alphas.py` frozen agent proposals, `gp.py` genetic-programming miner, `run_research.py` mining + one-shot sealed
test). Results: `strategies/alpha_research/results/`. Survey of AI pipelines: `ai_alpha_pipelines.md` (this folder).

Universe and costs as round 3: 337 current S&P 500 large caps (survivorship bias), month-end rank IC vs next-21-day
excess return; books net of 5 bp per unit turnover + 1 bp/day on shorts.

## Pipeline

1. **Fields (25)** on one daily grid: price/volume (close, ret, volume, dollar volume, FF5 residual, beta);
   point-in-time SEC XBRL fundamentals (gross profitability, asset growth, accruals, issuance, earnings yield, B/M, ROE,
   CFO/assets, SUE); round-3 alt data (opportunistic insider buys, FINRA short-volume ratio from 2018, Lazy Prices
   similarity); **new alt data**: Wikipedia daily page views (310 of 337 stocks, from 2015-07; Wikimedia API) and SEC
   8-K events from the EDGAR submissions index (8-K intensity, items 5.02 executive change / 2.02 results / 1.01 material
   agreement, 10-K/10-Q filing delay vs the firm's own history). Coverage: `results/field_coverage.csv`.
2. **DSL**: Qlib/Alpha101-style operators (rank, zscore, ts_mean/std/sum/delta/delay/max/min/rank/zscore, decay,
   ts_corr/cov, arithmetic), depth ≤ 4.
3. **Two proposers** (no LLM API key is configured, so the agent role is played by Claude in-session):
   - *agent*: 40 hypothesis-driven formulas with rationales, written and frozen before evaluation
     (`agent_alphas.py`; contamination note: ~9 base signals had been seen in round 3);
   - *GP*: population 200 × 30 generations, fitness on TRAIN months only, top 5 per generation sent to the referee.
4. **Frozen referee**: TRAIN 2010–2017 |IC t| ≥ 3; VALID 2018–2021 same sign, t ≥ 1.5; redundancy |ρ| < 0.6;
   validity safeguards (≥ 10 distinct values and no value > 90% of names per month; |mean IC| ≥ 0.005).
   Mining data are truncated at 2021-12-31 so the test cannot leak.
5. **Sealed test 2022-01 → 2026-08**: per-alpha IC; composites (EW, ridge, LightGBM trained on ≤ 2021 months, frozen);
   monthly quintile L/S and the round-3 cost-aware optimiser (γ chosen on 2018–2021).

**Process note (reported for honesty).** The first full run admitted 62 degenerate GP expressions (constants such as
`sub(close, close)` and ultra-sparse event factors like `ts_min(k8_101, 10)`) whose "IC" was floating-point tie noise with a
near-zero standard deviation and therefore a huge t-stat — the "unsafe generation" failure Hubble (arXiv 2604.09601)
warns about. Its test numbers were discarded (log kept as `results/research_log_buggy_referee_run1.txt`), the validity
safeguards above were added, and everything was re-mined. The 2022–2026 window had therefore been opened once before the
final run; the agent library (Amihud only) was unaffected by the fix and its test result is identical in both runs.

## Referee outcomes

| Proposer | Judged | Admitted | Failed TRAIN | Failed VALID | Degenerate | Redundant |
|---|---|---|---|---|---|---|
| Agent (Claude) | 40 | **1** (Amihud illiquidity) | 29 | 1 (Lazy Prices: train t 3.11, valid 0.31) | 9 | 0 |
| GP | 150 | **5** | 0 | 144 | 0 | 1 |
| Union (agent first, then GP) | 6 | **5** | | | | 1 |

Every alt-data proposal failed: Wikipedia attention had only 25–29 TRAIN months and |t| ≤ 0.83; 8-K executive-change
counts are too sparse to rank; 8-K intensity t −1.52; filing delay t 1.30; insider buys t 0.93; FINRA starts in 2018
(no TRAIN months). The GP found nothing in the alt-data fields either — its admitted alphas are price/volume/accrual
combinations. GP's VALID failure rate (144/150 TRAIN-strong candidates) is the overfitting the 2026 literature warns about.

## Admitted alphas and their decay

| Alpha | Source | IC train | IC valid | IC test | t test |
|---|---|---|---|---|---|
| `div(ts_mean(abs(ret),21), ts_mean(dvol,21))` (Amihud) | agent | 0.039 | 0.041 | 0.004 | 0.23 |
| `−rank(resid)` (1-day residual reversal) | GP | 0.035 | 0.023 | 0.008 | 0.55 |
| `accruals − ts_rank(ret,126)·close` | GP | 0.055 | 0.041 | **0.030** | **1.76** |
| `−(ret + accruals)` | GP | 0.036 | 0.026 | −0.000 | −0.01 |
| `ts_rank(ret,126)·(close − dvol)` | GP | 0.054 | 0.032 | 0.011 | 0.62 |
| `−(k8 − close·dvol / decay(accruals,252))` | GP | 0.037 | 0.032 | 0.019 | 1.39 |

Average IC roughly halves from TRAIN to VALID and halves again in TEST; none is individually significant out of sample.
Several GP alphas multiply by the raw share price or dollar volume (scale-dependent terms) — they behave like size/price-level
tilts and are hard to justify economically.

## Sealed-test books (2022-01 → 2026-08, net)

| Library / combiner | Monthly L/S net SR (gross) | Optimiser net SR (γ, val SR 2018–21) |
|---|---|---|
| agent EW | −0.06 (0.23) | −0.12 (γ 1.0, 0.84) |
| agent LightGBM | −0.32 (0.19) | 0.34 (γ 0.2, 1.37) |
| GP EW / ridge | 0.17 / 0.20 | 0.07 (γ 0.5) |
| GP LightGBM | 0.42 (0.84) | 0.12 (γ 0.2, 3.63) |
| union EW / ridge | 0.19 / 0.23 | −0.10 (γ 1.0) |
| **union LightGBM** | **0.54 (0.93)** | 0.12 (γ 0.2, 3.37) |
| *round 3 slow optimiser (same window)* | *0.80* | |
| *round 3 Attention Factors lite (same window)* | *0.38* | |

Deflated Sharpe over the 15 test variants (ml4t.diagnostic): best = union LightGBM monthly L/S, SR 0.54,
**P(true SR > 0) = 0.73** — not significant. The optimiser versions underperform because γ was selected on 2018–2021
where the LightGBM combiner is in-sample (validation SR 3.4–3.6 is inflated), a selection flaw worth fixing next time
(select γ on a combiner trained only through 2017).

## Conclusions

- The AI-pipeline pattern (generate → frozen referee → sealed test) works as a *filter*: it rejected 184 of 190
  candidates and exposed a referee bug that would otherwise have produced 64 fake alphas.
- It did not produce a better book than round 3: the best new composite (0.54 net) trails the round-3 slow optimiser
  (0.80) on the same window and is not significant after deflation.
- The free alt data tried (Wikipedia attention, 8-K events, filing delays, insider buys, Lazy Prices, FINRA) adds no
  measurable alpha in US large caps under a t ≥ 3 hurdle; Wikipedia's short history (2015 →) leaves too few TRAIN months.
- Next steps if continued: plug a real LLM (AlphaAgent / RD-Agent need an API key) into the same frozen referee,
  move the TRAIN/VALID split so short-history alt data can qualify, add a point-in-time universe, and fix γ selection.
