# Rules-based / regime strategy backtests (ML4T stack): results

Run date: 2026-10-19. Data runs to 2026-10-19 (^N225 to 2026-10-16).
Code: `strategies\rules\` (entry point `run_all.py`). Outputs: `strategies\rules\results\`.
Rerun: `.venv\Scripts\python strategies\rules\run_all.py` (about 65 s with cached data and cached jump-model signals). Add `--refresh` to re-download prices and refit the jump models; the refit takes about 20 min on 4 processes.

**Bottom line.** None of the five strategies shows a statistically reliable edge over its own buy & hold benchmark after costs and after correcting for the number of variants tried. Three strategies do deliver what they are usually sold for: lower drawdowns at similar or better Sharpe.
- Jump-model regime filter
  - US: works as a drawdown reducer. Max drawdown falls from -55% to -23% and Sharpe edges up from 0.51 to 0.56 on SPY. It does not beat the plain 200-day-MA filter or the HMM baseline, and it does not reproduce the paper's Sharpe gap (paper: 0.68 vs 0.48).
  - Europe: fails out of sample. 2018+ Sharpe is -0.15 on the DAX index and -0.30 on EWG.
  - China: fails out of sample (FXI and ASHR both negative 2018+).
- Trend following and momentum
  - Vol-targeted ETF trend (Sepp-Lucic proxy): Sharpe 0.56 at best, below 60/40 (0.68) and SPY (0.58).
  - TSMOM long-short: about zero.
  - Cross-asset momentum (Quantpedia 13 ETFs): the best absolute result, Sharpe 0.73-0.77 with max drawdown -29% to -34%. Its active return vs SPY is not significant after deflation.
- Turn-of-month
  - The [-3:+3] window has statistically significant in-window excess returns in most US, Europe and China instruments.
  - It is absent in the Nikkei 225 (t = 0.8; OOS in-window returns are *below* out-of-window returns), as the literature says for Japan.
  - USD-denominated EWJ does show it (t = 2.4).
- Sector momentum with the trend-gated short: small improvement in drawdown and Sharpe vs EW sectors (0.53 vs 0.46), consistent in-sample and OOS. Active DSR is only 0.42.

---

## 1. What was built

| File | Content |
|---|---|
| `strategies\rules\common.py` | yfinance cache (per-ticker parquet in `strategies\rules\data\`); akshare fallback for CSI 300; daily drift-aware portfolio simulator; metrics; IS/OOS split; deflated Sharpe wrapper; plots |
| `jump_model.py` | Strategy 1: statistical jump model (JM), HMM baseline, SMA200 baseline; 4 regions; local index and US-listed ETF versions |
| `trend.py` | Strategy 2: Sepp-Lucic EWMA crossover and TSMOM, vol-targeted, 16 multi-region ETFs |
| `momentum.py` | Strategy 3: Quantpedia cross-asset momentum (13 ETFs) and country-ETF momentum |
| `tom.py` | Strategy 4: turn-of-month on 14 US-listed country ETFs and 5 local indices |
| `sector.py` | Strategy 5: SPDR sector momentum with market-trend-gated short |
| `ml4t_engine.py` | Strategies 5 and 1 (SPY) run end to end through the **ml4t-backtest `Engine`**, with a parity check against the vectorised simulator, plus ml4t-diagnostic `portfolio_analysis_from_result` |
| `run_all.py` | Runs everything and writes `metrics_rules.csv`, `dsr_rules.csv`, `tom_stats.csv`, `trend_region_contrib.csv`, `notes_rules.json` and 21 PNGs |

**Package added to the venv:** `jumpmodels==0.1.1` (pure Python; Shu/Yu/Mulvey group's implementation). Nothing else was installed, and zipline was not touched.

### Common conventions (all strategies)
- Prices: yfinance `auto_adjust=True`, so ETFs are total-return in USD. Index tickers (^GSPC, ^N225, 000300.SS, ^STOXX50E) are **price** indices without dividends. ^GDAXI is a performance (total-return) index. CSI 300 comes from akshare (Sina `sh000300`, 2002+) because Yahoo's `000300.SS` returned a single row.
- Timing: signal at close *t*, trade at close *t+1*. The first return earned is *r(t+2)*: `simulate(..., lag=2)`. The exception is TOM, whose calendar window is known in advance, so positions are placed directly on the holding days (enter at close of day -4).
- Costs: 5 bp per unit of one-way turnover (10 bp for the jump model, as in the paper). Shorts pay an extra 25 bp/yr borrow fee.
- Cash: uninvested cash earns the 3-month T-bill (^IRX) for USD instruments. For DAX, Nikkei and CSI 300 local-currency tests, cash earns 0%. That is conservative for the JM/HMM/MA filters in pre-2012 Germany.
- Weights drift between rebalances, and turnover is measured on the drifted book.
- Metrics:
  - Sharpe and Sortino are computed on returns in excess of the T-bill, annualised at 252 days.
  - Turnover = sum of |Δw| per year, so a full in-and-out round trip counts as 2.0.
  - IS = before 2018-01-01; OOS = 2018-01-01 to 2026-10-19.
- Multi-region ETF portfolios use the NYSE (SPY) calendar. Single-index tests use each index's own calendar.

## 2. Exact parameters

**1. Statistical jump model (Shu, Yu & Mulvey 2024)**
- Features: computed on daily excess returns *r*.
  - EWM downside deviation, halflife 10: sqrt(EWM(r²·1{r<0})).
  - EWM Sortino at halflives 20 and 60: EWM_h(r) / downside deviation_h.
- Preprocessing: features are clipped at ±3 sd and standardised using training-window moments.
- Model: 2-state discrete `jumpmodels.jump.JumpModel` with `n_init=5`; the library default is 10, reduced for speed.
- Training and refit schedule:
  - Training window is the trailing 3000 days; it starts expanding once 1500 days are available.
  - Refits happen at end-June and end-December, starting from 1981.
  - Online state inference uses `JumpModel.predict_online` over a 3000-day lookback.
  - Bull state = the state with the higher mean training return.
- Jump penalty λ:
  - The grid is {5, 15, 30, 50, 100}.
  - At each month end, the λ with the best trailing-8-year Sharpe of its own walk-forward 0/1 strategy is chosen; at least 3 years of history are required. The chosen λ's state is used for the next month.
  - This deviates from the paper. Its CV refits inside the validation window; this implementation reuses out-of-sample online labels, which is cheaper and equally look-ahead-free.
- Position: 100% index when bull, cash when bear. 10 bp per trade.
- HMM baseline:
  - statsmodels `MarkovRegression`, 2 regimes, switching mean and variance.
  - Same 6-month refit and 3000-day window.
  - Filtered probabilities with a causal 10-day smoothing; risk-off when P(high-variance state) > 0.5.
- MA baseline: risk-on when price > its 200-day SMA.
- Markets:
  - US: ^GSPC traded as ^GSPC and as SPY.
  - Europe: ^GDAXI traded as ^GDAXI, EWG and EZU.
  - Japan: ^N225 traded as ^N225 and EWJ.
  - China: CSI 300 traded as CSI 300, ASHR and FXI.
  - ETF versions use the *local-index* signal, carried as-of to the US calendar. Asian and European closes precede the US close, so there is no look-ahead.
- Evaluation starts in 1990, or as soon as the CV-λ signal exists (CSI 300: 2011-09).

**2. Vol-targeted trend (Sepp & Lucic 2026), ETF proxy**
- Universe:
  - US equity: SPY, QQQ, IWM.
  - Europe: EZU, VGK, EWG, EWU.
  - Japan: EWJ, DXJ.
  - China: FXI, MCHI, ASHR, KWEB.
  - Diversifiers: TLT, IEF, GLD.
  - Each ETF is traded after 260 days of history.
- σ: EWMA volatility, span 33. z = r / σ(t-1), clipped at ±5.
- EWMA system: x = cumsum(z). S = [EWMA20(x) − EWMA250(x)] / theoretical sd, clipped to ±2.
- TSMOM: S = Σ of the last 100 z / √100 (L = 10, M = 10, equal-weighted blocks), clipped to ±2.
- Sizing:
  - Per asset: w = S · (10% / √N) / σ_ann.
  - Portfolio: scaled to 10% by EWMA-63 realised vol of the pro-forma book; scale in [0.25, 3].
  - Gross exposure capped at 2×.
- Variants: long-short / long-only × daily / weekly rebalance, 8 in total.
- Benchmarks: monthly-rebalanced equal-weight universe, SPY, and 60/40 SPY/IEF.

**3. Cross-asset / country momentum (Quantpedia Jan 2025)**
- Score = mean of the 63/126/189/252-day returns, computed at month end. Assets need 252 days of history to be ranked.
- Variants:
  - QP13 (SPY IWM EFA EEM IYR QQQ LQD IEF TIP GLD USO DBC FXE), top-4 long-only.
  - QP13 top-4 + 30% short of the bottom ETF when the average pairwise 20-day correlation > the 250-day correlation.
  - QP13 top-4 + always-on short.
  - Country (SPY QQQ IWM EZU VGK EWG EWU EWQ EWJ DXJ FXI MCHI ASHR KWEB EWH), top-3.
  - Country top-3 with an absolute-momentum switch to IEF.
  - Country + TLT/IEF/GLD, top-4.
- Monthly rebalance, 5 bp.

**4. Turn-of-month**
- Day 0 = the last trading day of the month on the instrument's own calendar.
- [-3:+3]: long from the close of day -4 to the close of day +3 (7 sessions).
- [0:+3]: long from the close of day -1 to the close of day +3.
- 5 bp per side.
- Instruments: 14 US-listed ETFs, ^GSPC, ^GDAXI, ^STOXX50E, ^N225 and CSI 300, plus an equal-weight 14-ETF TOM portfolio. Sample starts in 2000 or at inception.

**5. Sector momentum with trend-gated short (Quantpedia Oct 2024)**
- Universe: XLB XLE XLF XLI XLK XLP XLU XLV XLY. The 11-sector variant adds XLRE and XLC.
- Signal: 12-month (252-day) return at month end.
- Positions: long the top 5 at 20% each. Short the bottom sector at 25% only when the monthly EW-sector index is below its 12-month SMA of month-end values. The gate was on 22% of months.
- Variants: top-5 long-only, gated, always-on short, top-4/top-6 gated, and 11-sector gated.

## 3. Results (net of costs)

CAGR, Vol and MaxDD are in %. "Turn" = annual turnover (Σ|Δw|/yr). The full table, including Sortino, Calmar, IS/OOS CAGR and MaxDD and the per-λ JM variants, is in `results\metrics_rules.csv`.

### 3.1 Jump-model regime filter vs baselines

| Market / instrument | Strategy | Start | CAGR | Vol | Sharpe | MaxDD | Calmar | Turn | IS Sharpe | OOS Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|
| US ^GSPC | Buy & hold | 1990 | 8.7 | 18.0 | 0.41 | -56.8 | 0.15 | – | 0.34 | 0.59 |
| | **JM (CV-λ)** | 1990 | 7.1 | 10.9 | 0.43 | -24.7 | 0.29 | 1.5 | 0.41 | 0.49 |
| | HMM 2-state | 1990 | 7.3 | 11.4 | 0.43 | -25.9 | 0.28 | 3.5 | 0.45 | 0.36 |
| | SMA200 | 1990 | 7.1 | 11.5 | 0.42 | -22.9 | 0.31 | 6.7 | 0.39 | 0.50 |
| US SPY | Buy & hold | 1993 | 10.8 | 18.5 | 0.51 | -55.2 | 0.20 | – | 0.45 | 0.67 |
| | **JM (CV-λ)** | 1993 | 8.5 | 11.3 | 0.56 | -23.1 | 0.37 | 1.2 | 0.56 | 0.57 |
| | HMM | 1993 | 8.5 | 11.5 | 0.55 | -23.8 | 0.36 | 3.7 | 0.58 | 0.45 |
| | SMA200 | 1993 | 8.6 | 11.8 | 0.54 | -23.1 | 0.37 | 6.7 | 0.52 | 0.60 |
| Europe ^GDAXI | Buy & hold | 1997 | 7.3 | 22.7 | 0.42 | -72.7 | 0.10 | – | 0.40 | 0.50 |
| | **JM (CV-λ)** | 1997 | 3.2 | 13.7 | 0.30 | -55.0 | 0.06 | 2.0 | 0.50 | **-0.15** |
| | HMM | 1997 | 4.5 | 14.1 | 0.38 | -43.3 | 0.10 | 3.5 | 0.47 | 0.17 |
| | SMA200 | 1997 | 5.9 | 14.5 | 0.47 | -46.2 | 0.13 | 5.8 | 0.51 | 0.37 |
| Europe EWG | Buy & hold | 1997 | 6.0 | 25.5 | 0.27 | -67.6 | 0.09 | – | 0.29 | 0.22 |
| | **JM (CV-λ)** | 1997 | 4.2 | 15.8 | 0.20 | -53.1 | 0.08 | 2.0 | 0.42 | **-0.30** |
| | SMA200 | 1997 | 6.2 | 16.4 | 0.32 | -41.2 | 0.15 | 5.9 | 0.37 | 0.17 |
| Europe EZU | Buy & hold / JM / SMA200 | 2000 | 4.7 / 2.6 / 5.7 | | 0.24 / 0.12 / 0.32 | -65 / -49 / -44 | | | | 0.33 / -0.23 / 0.25 |
| Japan ^N225 | Buy & hold | 1990 | 1.5 | 23.7 | 0.18 | -81.8 | 0.02 | – | 0.04 | 0.67 |
| | **JM (CV-λ)** | 1990 | 1.5 | 12.8 | 0.18 | -43.0 | 0.04 | 1.9 | 0.20 | 0.13 |
| | HMM | 1990 | 1.9 | 16.3 | 0.20 | -64.5 | 0.03 | 5.8 | 0.12 | 0.44 |
| | SMA200 | 1990 | 1.7 | 14.4 | 0.19 | -42.5 | 0.04 | 7.8 | 0.20 | 0.17 |
| Japan EWJ | Buy & hold | 1996 | 3.0 | 22.6 | 0.14 | -58.9 | 0.05 | – | 0.08 | 0.34 |
| | **JM (CV-λ)** | 1996 | 4.1 | 12.4 | 0.20 | -34.9 | 0.12 | 1.8 | 0.29 | -0.08 |
| China CSI 300 | Buy & hold | 2011-09 | 2.8 | 21.3 | 0.24 | -46.7 | 0.06 | – | 0.37 | 0.12 |
| | **JM (CV-λ)** | 2011-09 | 3.1 | 11.8 | 0.32 | -31.4 | 0.10 | 2.1 | 0.97 | **-0.24** |
| | HMM | 2011-09 | 4.3 | 17.8 | 0.33 | -44.1 | 0.10 | 3.7 | 0.49 | 0.21 |
| China ASHR | Buy & hold / JM / HMM | 2013-11 | 5.1 / 5.8 / 7.2 | 27.9 / 14.7 / 22.1 | 0.25 / 0.33 / 0.34 | -51 / -31 / -49 | | | 0.54 / 0.97 / 0.80 | 0.08 / -0.11 / 0.15 |
| China FXI | Buy & hold / JM / SMA200 | 2011-09 | 1.8 / 0.4 / -4.1 | | 0.14 / -0.05 / -0.25 | -61 / -29 / -54 | | | | 0.00 / -0.29 / -0.27 |

The CV-chosen λ by month was as follows (share of months; `notes_rules.json`):

| Market | λ = 5 | λ = 15 | λ = 30 | λ = 50 | λ = 100 |
|---|---|---|---|---|---|
| US | 13% | 11% | 13% | 6% | 57% |
| Europe | 38% | 5% | 13% | 8% | 36% |
| Japan | 10% | 22% | 34% | 24% | 9% |
| China | 73% | 0% | 1% | 15% | 11% |

Selection is unstable outside the US. The best *fixed* λ ex post differs by market: 30 for the US, 100 for Europe, 50 for Japan and 30 for China. That is the multiple-testing trap the DSR row below accounts for (K = 11-14 per market).

### 3.2 Trend, momentum, sector

| Strategy | Start | CAGR | Vol | Sharpe | MaxDD | Calmar | Turn | IS Sharpe | OOS Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| Trend EWMA 20/250, long-short, daily | 2003 | 5.8 | 10.7 | 0.42 | -21.0 | 0.28 | 13.3 | 0.57 | 0.17 |
| Trend EWMA 20/250, long-only, daily | 2003 | 7.3 | 10.4 | 0.56 | -18.1 | 0.40 | 12.3 | 0.72 | 0.28 |
| Trend EWMA 20/250, long-only, weekly | 2003 | 7.4 | 10.7 | 0.56 | -18.8 | 0.40 | 8.0 | 0.73 | 0.27 |
| Trend TSMOM 10×10, long-short, daily | 2003 | 1.7 | 10.6 | 0.05 | -26.4 | 0.06 | 36.0 | 0.17 | -0.16 |
| Trend TSMOM 10×10, long-only, weekly | 2003 | 5.9 | 10.4 | 0.44 | -19.2 | 0.31 | 13.7 | 0.69 | -0.00 |
| *EW 16-ETF universe B&H* | 2003 | 9.0 | 15.9 | 0.51 | -46.0 | 0.20 | 0.4 | 0.61 | 0.34 |
| *60/40 SPY/IEF* | 2003 | 8.6 | 10.4 | 0.68 | -32.2 | 0.27 | 0.3 | 0.74 | 0.60 |
| *SPY* | 2003 | 11.3 | 18.5 | 0.58 | -55.2 | 0.21 | – | 0.53 | 0.67 |
| Mom QP13 top-4 long-only | 2002-10 | 12.1 | 14.8 | 0.73 | -34.3 | 0.35 | 4.6 | 0.81 | 0.60 |
| Mom QP13 top-4 + 30% short (corr filter) | 2002-10 | 13.2 | 15.5 | 0.77 | -28.8 | 0.46 | 6.6 | 0.87 | 0.59 |
| Mom QP13 top-4 + 30% short (always) | 2002-10 | 11.5 | 15.6 | 0.67 | -27.3 | 0.42 | 7.4 | 0.81 | 0.43 |
| Mom Country top-3 | 2001 | 6.7 | 22.5 | 0.32 | -63.0 | 0.11 | 6.3 | 0.26 | 0.45 |
| Mom Country top-3 + abs-mom → IEF | 2001 | 7.7 | 19.2 | 0.39 | -42.8 | 0.18 | 6.9 | 0.36 | 0.43 |
| Mom Country + TLT/IEF/GLD top-4 | 2001 | 7.3 | 17.7 | 0.39 | -46.7 | 0.16 | 6.1 | 0.38 | 0.40 |
| *EW QP13* | 2002-10 | 8.1 | 12.2 | 0.56 | -40.6 | 0.20 | 0.4 | 0.57 | 0.55 |
| *EW Country* | 2001 | 6.3 | 20.9 | 0.31 | -58.9 | 0.11 | 0.3 | 0.32 | 0.31 |
| Sector 9S top-5 long-only | 2000 | 9.2 | 17.6 | 0.48 | -47.7 | 0.19 | 3.1 | 0.38 | 0.67 |
| **Sector 9S top-5 + 25% gated short** | 2000 | 9.3 | 15.5 | 0.53 | -33.0 | 0.28 | 3.7 | 0.47 | 0.66 |
| Sector 9S top-5 + 25% always short | 2000 | 8.4 | 14.0 | 0.51 | -30.2 | 0.28 | 5.1 | 0.44 | 0.65 |
| Sector 11S top-5 + gated short | 2000 | 9.9 | 15.5 | 0.57 | -33.0 | 0.30 | 3.8 | 0.47 | 0.76 |
| *EW 9 sectors* | 2000 | 9.0 | 18.1 | 0.46 | -53.6 | 0.17 | – | 0.39 | 0.60 |
| *SPY* | 2000 | 8.3 | 19.2 | 0.41 | -55.2 | 0.15 | – | 0.29 | 0.67 |

**Trend P&L contribution by region** (gross, % per year; `trend_region_contrib.csv`). EWMA long-short, daily:

| US | Europe | Bonds | China | Commodity | Japan |
|---|---|---|---|---|---|
| 1.5 | 1.6 | 0.9 | 0.8 | 0.9 | 0.8 |

Every region contributes positively.

### 3.3 Turn-of-month, per region

Daily return in basis points, inside vs outside the window. Welch t-stat on the full sample. Full table in `tom_stats.csv`.

| Instrument | Region | [-3:+3] in (bp/d) | out (bp/d) | t | OOS (2018+) in / out | TOM Sharpe | B&H Sharpe | TOM OOS Sharpe |
|---|---|---|---|---|---|---|---|---|
| SPY | US | 8.9 | 1.4 | 2.46 | 9.2 / 4.6 | 0.53 | 0.41 | 0.54 |
| ^GSPC | US | 8.3 | 0.6 | 2.50 | 8.9 / 3.8 | 0.48 | 0.32 | 0.52 |
| EZU | Europe | 9.3 | -0.2 | 2.37 | 4.7 / 3.3 | 0.43 | 0.23 | 0.17 |
| EWG | Europe | 10.4 | -0.9 | 2.74 | 4.6 / 2.1 | 0.47 | 0.21 | 0.15 |
| EWU | Europe | 10.2 | -1.2 | 3.15 | 5.3 / 2.6 | 0.52 | 0.21 | 0.23 |
| ^GDAXI | Europe | 9.5 | -0.4 | 2.74 | 5.3 / 2.9 | 0.53 | 0.33 | 0.31 |
| ^STOXX50E | Europe | 5.0 | 0.1 | 1.23 | 4.7 / 2.5 | 0.25 | 0.20 | 0.26 |
| **^N225** | **Japan** | 5.1 | 1.9 | **0.84** | **1.1 / 8.4** | 0.23 | 0.32 | **-0.02** |
| EWJ (USD) | Japan | 7.7 | -0.7 | 2.41 | 4.7 / 3.0 | 0.38 | 0.16 | 0.18 |
| DXJ (hedged) | Japan | 6.7 | 3.5 | 0.77 | 5.7 / 7.5 | 0.31 | 0.45 | 0.23 |
| FXI | China | 12.3 | -0.1 | 2.15 | 6.9 / -1.8 | 0.47 | 0.26 | 0.23 |
| MCHI | China | 8.9 | -1.2 | 1.84 | 9.0 / -2.9 | 0.39 | 0.14 | 0.35 |
| ASHR | China | 12.5 | -1.1 | 2.14 | 12.5 / -3.6 | 0.57 | 0.25 | 0.60 |
| CSI 300 | China | 8.9 | 0.0 | 2.11 | 6.2 / -1.9 | 0.45 | 0.32 | 0.34 |
| EW 14-ETF TOM portfolio | Multi | – | – | – | – | 0.57 (CAGR 8.2, MDD -18) | 0.29 (CAGR 6.0, MDD -58) | 0.37 |

- [0:+3] is much weaker than [-3:+3] everywhere except China, where it is the best window: CSI 300 Sharpe 0.75 (t = 4.0) and ASHR 0.77.
- TOM turnover is 24×/yr. With 5 bp per side, that costs about 12 bp/yr.

### 3.4 Deflated Sharpe ratios (ml4t-diagnostic)

`dsr_prob` is P(true Sharpe of the best variant > 0) after deflating for K trials. `dsr_active_prob` is the same test applied to active returns (variant − benchmark), i.e. "is there skill vs the benchmark?". Absolute DSRs are high only because 20-30 years of mostly positive equity returns make "Sharpe > 0" an easy bar. **The active DSRs are the informative ones.**

| Family | K | Best variant | SR (ann.) | DSR (SR > 0) | Benchmark | Best active IR | DSR active |
|---|---|---|---|---|---|---|---|
| JM US ^GSPC | 11 | HMM | 0.43 | 1.00 | B&H | -0.17 | 0.00 |
| JM US SPY | 11 | JM (CV-λ) | 0.56 | 1.00 | B&H | -0.21 | 0.01 |
| JM Europe ^GDAXI | 14 | SMA200 | 0.47 | 1.00 | B&H | -0.16 | 0.01 |
| JM Europe EWG / EZU | 14 | SMA200 | 0.32 | 0.98 / 0.87 | B&H | -0.09 / -0.05 | 0.03 / 0.02 |
| JM Japan ^N225 | 11 | JM λ=50 | 0.30 | 0.97 | B&H | -0.03 | 0.13 |
| JM Japan EWJ | 11 | JM (CV-λ) | 0.20 | 0.85 | B&H | -0.04 | 0.15 |
| JM China CSI 300 / ASHR | 14 | JM λ=30 / HMM | 0.37 / 0.34 | 0.93 / 0.98 | B&H | 0.07 / 0.04 | 0.33 / 0.30 |
| JM China FXI | 14 | HMM | 0.15 | 0.08 | B&H | 0.00 | 0.00 |
| Trend | 8 | EWMA long-only | 0.56 | 0.995 | 60/40 | -0.10 | 0.01 |
| Cross-asset momentum | 6 | QP13 + corr-short | 0.77 | 1.00 | SPY | 0.05 | 0.40 |
| TOM (NYSE ETFs, common sample 2013-11+) | 29 | ASHR [0:+3] | 0.77 | 0.95 | – | – | – |
| Sector momentum | 6 | 11S gated | 0.57 | 1.00 | EW-9 | 0.04 | 0.42 |

Active returns of 0/1 timing filters vs buy & hold include the cost of lower average exposure, so a negative IR is expected even when risk-adjusted performance improves. Read it as "does not beat B&H in return terms", not "useless as a risk overlay".

## 4. Out-of-sample (2018 → 2026-10) findings

- **Jump model.**
  - US OOS Sharpe 0.57 vs 0.67 for SPY buy & hold, with OOS max drawdown -22% vs -34%.
  - Europe, Japan and China OOS Sharpe ranges from -0.30 to 0.13. The JM *lost* to buy & hold in every non-US market OOS, often badly: DAX CAGR -3.2%/yr vs +7.9%. In choppy post-2018 markets it repeatedly switched out at lows and back in late.
  - The SMA200 filter was the more robust baseline in Europe. The HMM was more robust in Japan (OOS 0.44) and China.
  - The paper's 1990-2023 superiority of JM over HMM is not reproduced with free data and this λ-selection scheme.
- **Trend.** Sharpe roughly halves OOS for all variants (EWMA long-only 0.73 → 0.28; TSMOM ≈ 0). This matches the documented post-2009 decay of naive TSMOM, and it is worse than the futures results in Sepp & Lucic (net Sharpe ~0.5).
- **Cross-asset momentum.** The most stable: QP13 OOS Sharpe 0.60 vs IS 0.81-0.87, still above EW-QP13 (0.55) but below SPY (0.67). The correlation-filtered short adds about 0.04-0.06 Sharpe IS and nothing OOS. Country momentum (0.40-0.45 OOS) beat EW-Country (0.31) but not SPY; US dominance explains most of its return.
- **TOM.**
  - Persists OOS in the US: SPY in-window 9.2 vs 4.6 bp/day.
  - Persists in China, where the effect is larger: ASHR 12.5 vs -3.6 bp/day.
  - Fades in Europe: in-window advantage falls from ~10 bp to ~2-3 bp/day.
  - Gone in Japan's local index: N225 OOS in-window 1.1 vs out 8.4 bp/day.
  - Because the strategy is invested only ~1/3 of the time, OOS CAGR is below buy & hold everywhere except China.
- **Sector momentum + gated short.** OOS Sharpe 0.66 vs EW-sector 0.60 and SPY 0.67; OOS max drawdown -20% vs -34% for SPY. This is the cleanest IS→OOS consistency in the set, but the edge over SPY is nil in Sharpe terms.

## 5. Caveats, data issues and failures (be careful with these numbers)

- **Survivorship and selection.**
  - All universes are ETFs that exist *today*, chosen with hindsight: China ETFs, KWEB, DXJ.
  - There are no delisted ETFs.
  - Short-history ETFs (ASHR 2013, MCHI 2011, KWEB 2013, XLRE 2015, XLC 2018) enter when they have data, so early-period portfolios are smaller.
- **Index data.**
  - ^GSPC, ^N225, ^STOXX50E and CSI 300 are price indices (no dividends), which understates buy & hold and the filters equally by about 1.5-2.5%/yr.
  - Yahoo's `000300.SS` is broken (1 row), so CSI 300 comes from akshare/Sina. Values before its 2005 launch are back-calculated.
  - The local-currency index tests assume 0% cash. This disadvantages the risk-off state in Germany pre-2012 and in China, where rates are positive.
- **Jump model deviations from the paper.**
  - `n_init` is 5, not 10.
  - λ is selected from walk-forward online labels, not by re-fitting within the 8-year validation window.
  - The λ grid is coarse (5 values).
  - The feature scaler uses training moments with ±3 sd clipping.
  - The paper uses Bloomberg total-return indices from 1970 and US T-bills for all markets.
  - Any of these could explain part of the gap to the paper's Sharpe of 0.68 (US) / 0.44 (Germany) / 0.31 (Japan).
- **Trend ETF proxy.**
  - 16 ETFs vs 84 futures.
  - Equity-heavy, with no commodities beyond GLD and no FX or rates futures.
  - Shorting ETFs is not the same as shorting futures (borrow costs, no roll).
  - TSMOM 10×10 is approximated as a 100-day normalised sum.
  - Turnover (8-36×/yr in weight units) is high because both asset-level and portfolio-level vol scaling run daily. Weekly rebalancing helps without hurting Sharpe.
- **Quantpedia correlation filter.** The exact threshold is unpublished; a simple "20d > 250d" rule was used, untuned. QP13 trading starts 2002-10 with fewer than 13 ETFs (USO/DBC/FXE arrive in 2006); the paper starts in 2006.
- **TOM.** The window uses the realised trading calendar, which assumes holidays are known in advance (they are). The TOM DSR inner-joins variants on their common sample (2013-11+, because of ASHR), so it covers fewer years than the per-instrument stats.
- **Costs.** A flat 5-10 bp per side. There is no market impact, and no FX or settlement costs for China (ASHR/FXI expense ratios are inside the adjusted prices). Japan and China local-index tests ignore real implementability: T+1 and price limits do not bind for index exposure via ETFs.
- **Multiple testing.** This report covers about 100 variants across 5 families. Reported best-variant numbers (λ choice, 11 sectors, the [0:+3] window in China) are selected ex post. Use the DSR table, not the best row.
- **Failures and underperformers (explicit list).**
  - JM in Europe and China OOS.
  - FXI SMA200 (Sharpe -0.25).
  - TSMOM long-short (Sharpe 0.05).
  - All trend variants vs 60/40.
  - All timing filters on CAGR vs buy & hold.
  - TOM on ^N225 and DXJ.
  - The always-on short in QP13 (worse than long-only).
  - Nothing failed to run: `run_all.py` completed with exit code 0 and `failures: {}`.
- **Bug fixed during development.** The first EWMA trend version applied the 20/250 EWMAs to z (returns) rather than to cumulative z, which gave about 100×/yr turnover and a negative Sharpe. The corrected crossover is in the code. This is noted because it is an easy mistake to repeat.

## 6. ML4T APIs that actually worked (verified against installed sources)

Versions: ml4t-backtest 0.1.12, ml4t-diagnostic 0.1.9, plus jumpmodels 0.1.1.

**ml4t-backtest.** The imports below match the docs, except for the module paths of the enums.
```python
from ml4t.backtest import Engine, DataFeed, BacktestConfig, Strategy   # all exported at top level
from ml4t.backtest.config import CommissionType, SlippageType, ShareType, ExecutionPrice
from ml4t.backtest.types import ExecutionMode                         # SAME_BAR / NEXT_BAR

cfg = BacktestConfig(initial_cash=1e6,
        commission_type=CommissionType.PERCENTAGE, commission_rate=0.0003,
        slippage_type=SlippageType.PERCENTAGE,  slippage_rate=0.0002,
        share_type=ShareType.FRACTIONAL, allow_short_selling=True, allow_leverage=True,
        execution_mode=ExecutionMode.NEXT_BAR)
feed = DataFeed(prices_df=pl_df)          # long polars frame: timestamp, asset, close
class S(Strategy):
    def on_data(self, timestamp, data, context, broker):   # data: _AssetsData, data[asset] -> dict
        broker.rebalance_to_weights({"XLK": 0.2, "XLU": -0.25})
res = Engine(feed, S(), cfg).run()        # BacktestResult (single-use engine)
res.to_equity_dataframe()                 # timestamp, equity, return, cumulative_return, drawdown, high_water_mark
res.metrics["sharpe"|"cagr"|"total_commission"|"total_slippage"|"num_fills"|"num_rejected_orders"|...]
res.to_fills_dataframe(); res.to_rejected_orders_dataframe(); res.to_portfolio_state_dataframe()
```
- **Fill timing.** `data[asset]` is a dict with keys `price, open, high, low, close, volume, signals`. With a close-only feed, `open` is filled with `close`, so NEXT_BAR fills happen at the *next bar's close*. That is exactly signal close *t* → trade close *t+1*.
- **Gotcha: margin flag.** With the default cash account (`allow_leverage=False`), 100% long + 25% short produced 226 `insufficient_cash` rejections, and the engine diverged from the vectorised result (MaxDD -43% vs -33%). Setting `allow_leverage=True` fixed it.
- **Parity.** Engine vs vectorised simulator (rf = 0) gave daily return correlation 0.9999 and tracking error 0.2%/yr.

| Run | CAGR engine / vectorised | Sharpe engine / vectorised |
|---|---|---|
| Sector momentum top-5 + gated short | 9.3% / 9.3% | 0.53 / 0.53 |
| JM on SPY (10 bp/side) | 6.9% / 6.9% | 0.48 / 0.48 |

- **Interest gap.** The engine pays no interest on idle cash, unless `funding_df` is used, which was not tried. Engine-reported `metrics["sharpe"]` (0.64) is on raw returns, not excess of T-bill.

**ml4t-diagnostic**
```python
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio, deflated_sharpe_ratio_from_statistics
r = deflated_sharpe_ratio([ret1, ret2, ...], frequency="daily", effective_trials=K)   # .probability, .sharpe_ratio_annualized
from ml4t.diagnostic.integration import portfolio_analysis_from_result
pa = portfolio_analysis_from_result(engine_result); pa.compute_summary_stats()   # pyfolio-style perf stats
```
- Both imports work.
- `correlation_method="effective_rank"` also runs. Its estimated K_eff is not exposed as `effective_trials` on the result object.
- Not used: `analyze_signal`, `generate_tearsheet_from_result` (needs the `viz` extra), ml4t-engineer, ml4t-data (yfinance was used directly), and alphalens/pyfolio.

**jumpmodels**
```python
from jumpmodels.jump import JumpModel
jm = JumpModel(n_components=2, jump_penalty=lam, cont=False, n_init=5, random_state=0)
jm.fit(X_std, ret_ser=returns, sort_by="cumret"); jm.ret_; jm.predict_online(X_lookback)
```
Each fit takes about 1-2 s (3000 × 3 features). The full walk-forward with 5 λ values over 4 markets takes about 20 min on 4 processes, so signals are cached as `data\signals_jm_<market>.parquet`.

## 7. Output files
- `strategies\rules\results\metrics_rules.csv` (150 rows), `dsr_rules.csv`, `tom_stats.csv`, `trend_region_contrib.csv`, `notes_rules.json`.
- Equity curve and drawdown PNGs:
  - Jump model: `jm_{US,Europe,Japan,China}_index.png`, `jm_US_SPY.png`, `jm_Europe_{EWG,EZU}.png`, `jm_Japan_EWJ.png`, `jm_China_{ASHR,FXI}.png`.
  - Other strategies: `trend.png`, `xasset_momentum.png`, `tom.png`, `tom_ew.png`, `sector_momentum.png`.
  - Engine runs: `engine_sector.png`, `engine_jm_spy.png`.
- Cached data in `strategies\rules\data\`: 43 ticker parquets and 4 JM signal parquets.
