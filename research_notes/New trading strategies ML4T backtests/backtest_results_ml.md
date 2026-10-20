# ML cross-sectional strategies on US, Europe, Japan and China: ML4T backtest results

Run date: 2026-10-19. Code: `strategies/ml/` (entry point `run_all.py`). Outputs: `strategies/ml/results/`.
Data are cached in `strategies/ml/data/` (prices and out-of-sample predictions as parquet).

## Bottom line

- **Long-short top-minus-bottom quintile ML portfolios do not survive realistic costs in any region.** Gross Sharpe ratios (0 bp) are 0.4 to 0.8. At 10 bp per side they fall to between −0.2 and +0.24, and at 20 bp every one is negative. Annual one-way turnover is about 45–55x NAV, which is what kills them.
- **Long-only top quintile looks good in absolute terms (Sharpe 0.6–1.0), but that is almost all market beta plus survivorship.** Measured against an equal-weight benchmark of the same universe with the same costs and weekly rebalance:
  - US: LightGBM-5d adds +4.5%/yr (information ratio 0.40, t = 1.3).
  - Japan: +2.4%/yr (IR 0.24).
  - Europe: about 0.
  - China: about 0 for LightGBM, +1.4%/yr for Ridge (IR 0.13).
  - None of these is statistically significant.
- **The out-of-sample IC is real but small.** Mean daily rank IC versus the 5-day forward return is 0.016–0.029 for ML signals, with Newey-West t of 2.3–3.5 in every region. That signal is too weak, and too fast, to monetise after costs in 40–50 large caps.
- **Deflated Sharpe ratio.** On active returns (LS raw, LO minus EW), no region's best strategy passes once the CPCV grid is counted (DSR probabilities 0.001–0.43). The global best over all 28 backtested configs plus 24 grid trials has DSR probability 0.04. The raw long-only DSRs (0.86–0.997) are not evidence of skill, because they reward beta.
- **Is the ML just reversal?** Partly. The LightGBM 5d prediction has an average cross-sectional rank correlation of 0.20 (EU) to 0.47 (CN) with −r_5, and LS return correlations with the pure-reversal LS are 0.28–0.52. Pure weekly reversal itself loses money net of costs in every region. Its gross OOS IC is ≈0 in EU and CN and 0.011 in US, and only Japan has a meaningful reversal IC (0.019). After regressing on reversal (and EW for LO), the ML alphas are positive but insignificant (t ≤ 1.6). The trees also lean heavily on beta, Amihud, volume z-scores and volatility, so the model is a "liquidity/vol/beta + some reversal" mix, not a pure reversal clone.
- **The predictive power is decaying.** In the US, LightGBM-5d IC was 0.029 in 2017–21 and 0.010 in 2022–26, and LS Sharpe went 0.62 → −0.05. Japan and US lgbm_21 show the same pattern. China's EW benchmark Sharpe fell from 1.28 to 0.22 between the two halves.

## What was built

### Universes (survivorship bias)
All four universes are **current** index constituents, hand-picked large caps as of 2026, applied back to 2012. Firms that were delisted, acquired or dropped from the indices are missing, and today's winners are over-represented. This biases long-only and EW returns upward. Long-short results are less affected, but not clean. The universes are small (40–50 names), so quintiles hold 8–10 stocks.

| Region | N | Source | Notes |
|---|---|---|---|
| US | 50 | yfinance `auto_adjust=True` | S&P 100 names (AAPL…LLY) |
| EU | 40 | yfinance | Euro Stoxx 50/STOXX names in EUR on .DE/.PA/.AS/.MI/.MC; mixed exchange holiday calendars |
| JP | 40 | yfinance | Nikkei 225 large caps (.T) |
| CN | 40 | **akshare `stock_zh_a_daily` (Sina), adjust='hfq'** | CSI 300 large caps (.SS/.SZ). Eastmoney `stock_zh_a_hist` failed from this machine (`RemoteDisconnected`). The Sina call worked for all 40 names, and the yfinance fallback was not needed. Sina provides the RMB traded amount and true turnover (volume/float). |

Daily data run from 2012-01 to 2026-10-16 (cut-off `END = 2026-10-17` to drop partial bars). Later listings: META 2012-05, ABBV 2013, 6098.T 2014, 000333.SZ 2013-09, 300750.SZ 2018-06.

### Features (24, price/volume only; `features.py`)
All features at date t use data up to the **close of t**. Each is then ranked cross-sectionally within the region per date, mapped to [−0.5, 0.5], with NaN → 0.

- Lagged returns r_1, r_5, r_10, r_21, r_63, r_126, r_252, and mom_12_1 (t−252 → t−21).
- Residual (market-adjusted) returns resid_5/21/63: the daily return minus lagged rolling 252d beta × the equal-weight regional market return, then summed. Also beta_252.
- Volatility and range:
  - **vol_21 (ml4t-engineer `realized_volatility`)**, vol_63;
  - **dvol_63 (ml4t-engineer `downside_deviation`, window 63)**;
  - max_21 (MAX) and min_21 daily return.
- Liquidity and volume:
  - amihud_21 = log(1 + mean |r|/traded value). Computed in pandas, because ml4t's `amihud_illiquidity` uses close × volume, which is wrong for China hfq prices.
  - volz_21 and volz_5: z-scores of log-volume against a 252d window.
  - turn_21: true turnover, **China only**; constant 0 elsewhere because shares outstanding are not free on yfinance.
- dist_52w_high, **rsi_14 (ml4t-engineer `rsi`)**, and gap_1 (open_t / close_{t−1} − 1).

### Labels
Forward return from **open of t+1 to open of t+1+h**, for h = 5 and h = 21, clipped and cross-sectionally ranked. This is exactly the return a close-t signal can capture when executed at the next open.

### Models and CV (`model.py`)
- **LightGBM** regressor: lr 0.03, num_leaves 15, min_child_samples 400, subsample 0.7, colsample 0.7, λ=5. `n_estimators` comes from a grid {100, 300, 600}, chosen once per region and horizon by **ml4t CombinatorialCV** (6 groups, 2 test groups = 15 paths, label_horizon = h+1, embargo 5 days). The selection used **only 2013–2016 data** and the criterion was mean daily rank IC.
  - Chosen values: US 100/100; EU 300 (5d) and 600 (21d); JP 100/100; CN 100 (5d) and 600 (21d).
  - EU 21d IS CPCV IC was negative (−0.016 to −0.021) and the 21d model was still run. It is an honest negative IS result.
- **Ridge** (α=10) linear baseline on the same ranked features.
- **Outer walk-forward: ml4t `WalkForwardCV`**, run on the region's array of trading **dates** and then mapped to panel rows:
  - settings: `n_splits=10`, `train_size` = number of dates before 2017-01-01, `test_size` ≈ 1 year, `label_horizon=h+1`, `embargo_size=5`, `expanding=True`, `consecutive=True`;
  - this gives an expanding window from 2013 (after a 252d warm-up) with **annual retraining** and 10 consecutive OOS folds covering 2017-01 to 2026-10;
  - a code assertion checks `max(train_date)+h+1 <= min(test_date)` (e.g., US fold 1 trains 2013-01-04→2016-12-23 and tests 2017-01-05→2017-12-26);
  - fold boundaries are in `results/walk_forward_folds.csv`.
- **Reversal baseline:** rev_5 = −r_5 (raw, unranked).

### Backtests (`backtest.py`)
- **ml4t-backtest `Engine`** with a custom `Strategy` that calls `broker.rebalance_to_weights()` on the **last trading day of each week**.
  - Config: `ExecutionMode.NEXT_BAR` + `ExecutionPrice.OPEN`, so orders are filled at the **open of t+1**.
  - Fractional shares, `MissingPricePolicy.USE_LAST`, `rebalance_headroom_pct=0.98`, initial cash 10M.
  - Costs: `CommissionType.PERCENTAGE` + `SlippageType.PERCENTAGE`, each set to half of the stated bp/side.
- Portfolio types:
  - **LS:** +1/q top quintile, −1/q bottom quintile (100% long / 100% short, gross 2). Uses `allow_short_selling=True, allow_leverage=True`.
  - **LO:** top quintile, equal weight.
  - **EW benchmark:** all names, weekly rebalanced, same costs.
- **China:** long-only only, 15 bp/side in the engine (2.5 bp commission + 2.5 bp amortised stamp duty + 10 bp slippage).
  - **Price-limit rule:** do not buy a name that closed at its upper limit on the signal day, and do not sell a held name at its lower limit. Limits are ±10%, or ±20% for 300xxx from 2020-08-24 and for 688xxx. They are detected from the hfq return ≥ limit − 0.3%.
  - In practice the rule found only 328 limit stock-days and blocked 1–3 trades per strategy. It is immaterial for these mega caps.
  - **T+1** holds automatically: positions are bought at the open of t+1 and held at least to the next weekly rebalance.
  - The engine's commission model only sees unsigned fill quantity, so it cannot charge a sell-only tax. A **vectorized replica** therefore applies the exact sell-side stamp duty: buy 12.5 bp; sell 22.5 bp before 2023-08-28 and 17.5 bp after. It gives Sharpe 0.68 (lgbm_5) and 0.71 (ridge_5), versus 0.71/0.79 in the engine.
- The vectorized open-to-open replica is also a parity check on the engine. For long-only, the Sharpe ratios agree within about 0.07. For high-turnover LS books they agree within about 0.13 (largest gaps: EU rev_5 and the EU and JP ridge LS). The replica ignores intra-week weight drift and holiday mismatches, so it is only a rough check.

## Results

### Signal quality: OOS daily rank IC versus forward 5d return (own computation, `ic_summary.csv`)
NW t uses Newey-West with h lags, to correct for overlapping labels.

| Region | lgbm_5 IC (NW t) | ridge_5 | lgbm_21 | rev_5 (pure reversal) | lgbm_5 IC 2017–21 → 2022–26 |
|---|---|---|---|---|---|
| US | 0.020 (2.41) | 0.014 (1.44) | 0.015 (1.79) | 0.011 (1.37) | 0.029 → 0.010 |
| EU | 0.016 (2.34) | 0.022 (2.95) | 0.014 (2.16) | 0.003 (0.36) | 0.016 → 0.015 |
| JP | 0.018 (2.59) | 0.023 (3.02) | 0.010 (1.42) | 0.019 (2.63) | 0.019 → 0.016 |
| CN | 0.025 (3.32) | 0.029 (3.47) | 0.005 (0.70) | 0.002 (0.28) | 0.026 → 0.024 |

Versus the 21d forward return, the lgbm_5 IC is 0.025–0.039, but the NW t is only 1.5–2.8 and the non-overlapping t only 0.7–2.4.

**In-sample vs OOS:** the CPCV (2013–16) ICs for the 5d model were US 0.026, EU 0.027, JP 0.023 and CN 0.062. OOS ICs are about 25–60% lower, and China shows the biggest drop (0.062 → 0.025).

**ml4t `analyze_signal`, 5D period** (`analyze_signal_summary.csv`). Prices were fed as open_{t+1}, so forward returns are tradable. The library's IC t-stats use overlapping daily observations and are inflated by about √5; the NW figures above are the honest ones.

| Region | Signal | IC | Q5−Q1 5d spread | monotonicity | 5D quantile turnover |
|---|---|---|---|---|---|
| US | lgbm_5 | 0.020 | 0.24% | 1.0 | 0.58 |
| US | rev_5 | 0.011 | 0.13% | 0.9 | 0.79 |
| EU | lgbm_5 | 0.016 | 0.15% | 0.6 | 0.63 |
| EU | rev_5 | 0.003 | 0.02% | 0.3 | 0.79 |
| JP | lgbm_5 | 0.018 | 0.15% | 0.7 | 0.58 |
| JP | rev_5 | 0.019 | 0.17% | 1.0 | 0.79 |
| CN | lgbm_5 | 0.025 | 0.27% | 0.7 | 0.64 |
| CN | ridge_5 | 0.029 | 0.21% | 1.0 | 0.68 |

A 5-day Q5−Q1 spread of 0.15–0.27% against roughly 0.6 turnover per week × 2 legs × 10–15 bp is break-even at best.

### Backtests at base cost (10 bp/side developed, 15 bp China), OOS 2017-01 → 2026-10 (`backtest_metrics.csv`)

| Region | Strategy | Ann. ret | Vol | Sharpe | MaxDD | Ann. one-way turnover (×NAV) | Active vs EW (IR, NW t) |
|---|---|---|---|---|---|---|---|
| US | lgbm_5 LS | 2.7% | 18.3% | 0.24 | −40% | 44 | – |
| US | ridge_5 LS | 0.3% | 20.8% | 0.12 | −48% | 47 | – |
| US | lgbm_21 LS | 1.2% | 18.1% | 0.16 | −43% | 30 | – |
| US | rev_5 LS | −6.7% | 19.4% | −0.26 | −63% | 80 | – |
| US | lgbm_5 LO | 21.2% | 23.7% | 0.93 | −32% | 22 | +4.5% (0.40, 1.30) |
| US | ridge_5 LO | 18.7% | 24.8% | 0.81 | −35% | 23 | +2.7% (0.23, 0.74) |
| US | rev_5 LO | 12.9% | 22.2% | 0.66 | −39% | 40 | −3.0% (−0.28) |
| US | EW benchmark | 17.5% | 17.0% | 1.03 | −31% | – | – |
| EU | lgbm_5 LS | −0.9% | 12.6% | −0.01 | −35% | 53 | – |
| EU | ridge_5 LS | −3.8% | 14.9% | −0.19 | −56% | 55 | – |
| EU | rev_5 LS | −13.5% | 17.1% | −0.76 | −77% | 81 | – |
| EU | lgbm_5 LO | 12.5% | 19.4% | 0.70 | −41% | 26 | +0.4% (0.05, 0.18) |
| EU | EW benchmark | 12.3% | 18.2% | 0.73 | −40% | – | – |
| JP | lgbm_5 LS | 1.3% | 15.2% | 0.16 | −40% | 46 | – |
| JP | ridge_5 LS | −2.8% | 16.1% | −0.10 | −53% | 46 | – |
| JP | rev_5 LS | −7.0% | 17.8% | −0.32 | −58% | 80 | – |
| JP | lgbm_5 LO | 21.0% | 22.2% | 0.97 | −28% | 22 | +2.4% (0.24, 0.75) |
| JP | ridge_5 LO | 21.0% | 21.5% | 0.99 | −29% | 23 | +2.2% (0.23, 0.69) |
| JP | EW benchmark | 19.2% | 18.2% | 1.06 | −27% | – | – |
| CN | lgbm_5 LO | 13.2% | 20.5% | 0.71 | −29% | 27 | 0.0% (0.00, 0.01) |
| CN | ridge_5 LO | 14.8% | 20.0% | 0.79 | −29% | 30 | +1.4% (0.13, 0.42) |
| CN | lgbm_21 LO | 10.4% | 20.6% | 0.58 | −35% | 20 | −2.4% (−0.26) |
| CN | rev_5 LO | 6.7% | 22.5% | 0.40 | −42% | 39 | −5.4% (−0.46, −1.47) |
| CN | EW benchmark | 13.6% | 18.1% | 0.80 | −29% | – | – |

Turnover = mean (|buys|+|sells|)/2 per rebalance × 52. For LS this is relative to 1x NAV with gross exposure of 2. Full rows, including the lgbm_21 variants, are in the CSV.

### Cost sensitivity: Sharpe at 0 / 10 / 20 bp per side (`cost_sensitivity.csv`, `cost_sensitivity.png`)

| Region | lgbm_5 LS | ridge_5 LS | rev_5 LS | lgbm_5 LO | rev_5 LO | EW |
|---|---|---|---|---|---|---|
| US | 0.73 / 0.24 / −0.25 | 0.57 / 0.12 / −0.34 | 0.56 / −0.26 / −1.07 | 1.13 / 0.93 / 0.75 | 1.04 / 0.66 / 0.34 | 1.04 / 1.03 / 1.03 |
| EU | 0.82 / −0.01 / −0.85 | 0.53 / −0.19 / −0.89 | 0.20 / −0.76 / −1.64 | 0.99 / 0.70 / 0.43 | 0.64 / 0.27 / −0.04 | 0.74 / 0.73 / 0.72 |
| JP | 0.77 / 0.16 / −0.45 | 0.53 / −0.10 / −0.67 | 0.57 / −0.32 / −1.20 | 1.16 / 0.97 / 0.73 | 1.04 / 0.68 / 0.32 | 1.06 / 1.05 / 1.05 |
| CN (LO) | – | – | – | 1.09 / 0.90 / 0.59 (15 bp: 0.71) | 0.94 / 0.60 / 0.18 | 0.81 / 0.80 / 0.79 |

At **zero cost**, the ML long-only portfolios beat EW in every region (by 0.1–0.3 Sharpe), and LS gross Sharpe is 0.5–0.8. Costs consume all of it. The gross reversal LS is positive (0.2–0.6) but goes negative at 10 bp.

### Sub-periods: Sharpe 2017–2021 / 2022–2026 (`subperiod_metrics.csv`)
- US: lgbm_5 LS 0.62 / −0.05; LO 1.23 / 0.62 (EW 1.18 / 0.86).
- EU: lgbm_5 LS 0.27 / −0.25; LO 0.73 / 0.67 (EW 0.66 / 0.82).
- JP: lgbm_5 LS 0.13 / 0.18; LO 1.05 / 0.93 (EW 0.95 / 1.16).
- CN: lgbm_5 LO 1.08 / 0.27; ridge_5 LO 1.33 / 0.16 (EW 1.28 / 0.22).

### ML vs reversal (`ml_vs_reversal.csv`)
Regression of daily net ML returns on the rev_5 strategy returns (plus EW returns for LO), with HAC standard errors.

| Region | LS lgbm_5: corr with rev LS / β_rev (t) / alpha p.a. (t) | LO lgbm_5: alpha p.a. (t) after rev + EW | avg CS rank-corr(lgbm_5, −r_5) |
|---|---|---|---|
| US | 0.39 / 0.37 (9.5) / +6.2% (1.17) | +2.1% (0.67) | 0.29 |
| EU | 0.28 / 0.21 (8.4) / +2.5% (0.65) | +2.3% (1.04) | 0.20 |
| JP | 0.52 / 0.45 (16.1) / +5.0% (1.17) | +2.9% (1.02) | 0.35 |
| CN | – | +2.5% (0.84); ridge +4.6% (1.58) | 0.47 (ridge 0.52) |

The ML signal loads significantly on reversal, most heavily in China and Japan. What remains after reversal is positive everywhere but never significant. LightGBM gain shares (5d model, `feature_importance.png`) put the most weight on beta_252, amihud_21, volz_21, vol_63/dvol_63, mom_12_1 and max/min_21. In China, r_5 and true turnover (turn_21) rank highly, which fits the A-share "trading-anomaly" literature. Raw r_1 and resid_5 carry little weight.

### Deflated Sharpe ratio (ml4t `deflated_sharpe_ratio`, `deflated_sharpe.csv`)
Trials counted: the backtested configs per region (8 developed, 4 China) plus 6 CPCV grid evaluations (3 n_estimators × 2 horizons). Globally that is 28 + 24 = 52. Cost variants are not counted as separate trials.

| Scope | Returns | Best | SR (ann.) | DSR prob, K=backtested | DSR prob, K incl. grid | DSR prob, K_eff (effective rank) |
|---|---|---|---|---|---|---|
| US | raw | lgbm_5 LO | 0.93 | 0.95 | 0.86 (K=14) | 1.00 (K_eff 2.7) |
| EU | raw | lgbm_5 LO | 0.70 | 0.41 | 0.14 | 0.76 |
| JP | raw | ridge_5 LO | 0.99 | 0.87 | 0.64 | 0.98 |
| CN | raw | ridge_5 LO | 0.79 | 1.00 | 1.00 (K=10) | 0.99 |
| ALL | raw | JP ridge_5 LO | 0.96 | 0.57 | 0.27 (K=52) | 0.90 |
| US | active (LO − EW; LS raw) | lgbm_5 LO | 0.40 | 0.58 | 0.43 | 0.79 |
| EU | active | lgbm_5 LO | 0.05 | 0.01 | 0.001 | 0.06 |
| JP | active | lgbm_5 LO | 0.24 | 0.31 | 0.19 | 0.50 |
| CN | active | ridge_5 LO | 0.13 | 0.26 | 0.06 | 0.32 |
| ALL | active | US lgbm_5 LO | 0.40 | 0.11 | 0.04 (K=52) | 0.28 |

The raw long-only "passes" mostly reflect the equity premium on a survivorship-biased universe; the EW benchmark alone has Sharpe 0.8–1.05. On active returns nothing passes at 95%. Per-strategy PSRs for the LS books range from 0.01 to 0.77.

## Caveats
1. **Survivorship bias** (current constituents only) inflates long-only and EW levels. It probably also helps the momentum and 52w-high features, which favour today's winners.
2. **Small universes.** With 40–50 names, a quintile holds 8–10 stocks, so the backtests are noisy. The research results these replicate (e.g., Rahimikia et al. gross Sharpe ~6.8) come from about 10,000 small-cap stocks with daily rebalancing and no costs. These are different experiments: this run is intentionally liquid, weekly and costed.
3. **Costs are flat bp per side.** There is no market impact or borrow fee for shorts. Short borrow in Europe and Japan, and especially China (excluded here), would make LS worse. UK stamp duty and French/Italian FTT were not modelled; EU names are continental, so the FTT on .PA/.MI names (0.3%/0.1% on buys of large caps) is missing. That makes the EU numbers optimistic.
4. **yfinance adjusted OHLC.** Dividend adjustment scales open and close alike, which is fine for returns. Amihud and volume features for US/EU/JP use adjusted close × volume as a value proxy, and turnover is unavailable outside China.
5. **China data:** Sina hfq prices. The limit detection uses hfq returns, which can misclassify on ex-dividend days. Lot size (100 shares) and minimum commission (RMB 5) were ignored. Engine costs are symmetric (stamp amortised); the vectorized exact-stamp check gives Sharpe about 0.05 lower.
6. **EU calendar.** The panel mixes Xetra, Euronext, Borsa and BME calendars; on local holidays the engine marks with the last price.
7. **One hyper-parameter pass.** No tuning beyond the 3-point n_estimators grid, so the DSR trial count is small but honest. The feature list was fixed in advance from the research notes.
8. **Not tested:** CatBoost, sequence/foundation models (Chronos), triple-barrier labels, and turnover-penalised portfolio construction (e.g., holding bands). The last is the most promising next step given the cost results.

## ml4t APIs actually used (installed versions: ml4t-engineer 0.1.6, ml4t-diagnostic 0.1.9, ml4t-backtest 0.1.12)

| Use | Real import / call | Notes |
|---|---|---|
| Features | `from ml4t.engineer import compute_features`; `compute_features(pl_df, [{"name":"rsi","params":{"period":14}}, {"name":"realized_volatility","params":{"period":21,"annualize":False}}, {"name":"downside_deviation","params":{"window":63}}], group_col="asset", timestamp_col="timestamp")` | Worked. `downside_deviation` takes `window`, not `period`, and needs a `returns` column. `amihud_illiquidity` uses `returns`/`volume`/close. The catalog is `feature_catalog.describe(name)`; the notes' `.get()` does not exist. Output column names equal the feature name. |
| Walk-forward CV | `from ml4t.diagnostic.splitters import WalkForwardCV`; `WalkForwardCV(n_splits, train_size=int, test_size=int, label_horizon=h+1, embargo_size=5, expanding=True, consecutive=True).split(np.arange(n_dates).reshape(-1,1))` | Worked on an integer date axis. A pandas DatetimeIndex switches to calendar mode, which **requires tz-aware timestamps** (naive ones raise `ValueError`) and aligns folds from the start of the data. The int mode places the first test at `train_size`. |
| CPCV | `from ml4t.diagnostic.splitters import CombinatorialCV`; `CombinatorialCV(n_groups=6, n_test_groups=2, label_horizon=h+1, embargo_size=5, isolate_groups=False)` | Worked; purging and embargo were verified. The default `isolate_groups=True` is for asset groups. |
| Signal eval | `from ml4t.diagnostic import analyze_signal`; `analyze_signal(factor_pl[date,asset,factor], prices_pl[date,asset,price], periods=(1,5,21), quantiles=5, filter_zscore=None)` | Worked, about 35–40 s per signal on about 120k rows. Returns a `SignalResult`; `.to_dict()` has keys ic, ic_t_stat, ic_ir, spread, quantile_returns, monotonicity, turnover, autocorrelation…, and `.summary()` gives text. The IC t-stat treats overlapping horizons as independent. |
| DSR | `from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio`; `deflated_sharpe_ratio(list_of_arrays, frequency="daily", effective_trials=K \| correlation_method="effective_rank")` | Worked. Returns `DSRResult` with fields `.probability`, `.sharpe_ratio_annualized`, `.n_trials_raw`, `.n_trials_effective`, `.expected_max_sharpe`. A single array gives a PSR. |
| Backtest | `from ml4t.backtest import Engine, DataFeed, BacktestConfig, CommissionType, Strategy`; `from ml4t.backtest.config import ExecutionPrice, ShareType, SlippageType, MissingPricePolicy`; `from ml4t.backtest.types import ExecutionMode` | Worked; 2–4 s per 10-year weekly run. Usage details are below. |

Backtest usage details:
- `Strategy.on_data(self, timestamp, data, context, broker)`, where `data` is `{asset: {"close":…, "signals":{…}}}`.
- `broker.rebalance_to_weights({asset: w})` closes positions that are absent from the dict. Negative weights need `allow_short_selling=True, allow_leverage=True`.
- `result.to_equity_dataframe()` (timestamp, equity, return, …) and `result.metrics[...]` (sharpe, num_trades, total_commission, total_slippage).
- The commission model receives an unsigned quantity, so a sell-only tax cannot be modelled through `BacktestConfig`.

Not used: zipline (not installed). alphalens/pyfolio were also not needed, since `analyze_signal` covered IC and quantiles.

## Reproduce
```
.venv\Scripts\python strategies\ml\run_all.py              # cached data and predictions: ~11 min
.venv\Scripts\python strategies\ml\run_all.py --retrain    # retrain all models (CPCV + walk-forward): ~20 min
.venv\Scripts\python strategies\ml\run_all.py --refresh    # also re-download (akshare China ~4 min)
.venv\Scripts\python strategies\ml\run_all.py --regions US --no-analyze   # quick single-region run
```
Files: `data_loader.py` (universes, download, cache), `features.py`, `model.py`, `backtest.py`, `run_all.py`.

Results:
- CSVs: `backtest_metrics`, `cost_sensitivity`, `subperiod_metrics`, `ic_summary`, `analyze_signal_summary`, `ml_vs_reversal`, `deflated_sharpe`, `feature_importance`, `walk_forward_folds`, `cpcv_model_selection`.
- PNGs: `cumulative_returns`, `ic_timeseries`, `feature_importance`, `cost_sensitivity`.
- Log: `run_log.txt`.

No extra packages were installed.
