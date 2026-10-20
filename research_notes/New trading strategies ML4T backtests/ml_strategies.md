# Recent (2023–2026) ML / DL Trading Strategies Implementable on Daily Equity/ETF Data

Scope: catalogue of ML-based strategies from 2023–2026 academic work, focused on what can be coded on daily OHLCV for US, European, Japanese and Chinese equities/ETFs. Research date: 2026-10-19. Older seminal work is marked **[CONTEXT, pre-2023]**.

Local PDFs (downloaded from arxiv.org, plus one from afajof.org) are in `C:\Users\Acer\Pictures\research_papers\paper1\papers\ml_strategies\`:
- 2025_Rahimikia_revisiting_TSFM_finance.pdf (arXiv 2511.18578)
- 2024_Shu_Yu_Mulvey_jump_model_downside_risk.pdf (arXiv 2402.05272)
- 2025_Valeyre_Aboura_Chronos_stat_arb.pdf (arXiv 2412.09394)
- 2025_LopezLira_Tang_ChatGPT_stock_returns.pdf (arXiv 2304.07619, v. Oct 30 2025)
- 2024_Wood_XTrend_fewshot_trend_following.pdf (arXiv 2310.10500)
- 2026_Wood_Roberts_Zohren_DeePM.pdf (arXiv 2601.05975)
- 2026_pretrained_TSFM_financial_return_forecasting.pdf (arXiv 2606.27100)
- 2025_Azevedo_Hoegner_Velikov_expected_returns_ML_strategies.pdf (AFA/JF accepted-paper PDF)

---

## Which 2024–2026 ML strategy papers report out-of-sample results that survive transaction costs? (Catalogue + ranking)

### Takeaway
The evidence that clearly survives realistic costs is concentrated in (a) low-turnover, price-only **regime filters** on indices (statistical jump model, 10 bps costs, US/Germany/Japan), (b) **deep trend-following / Sharpe-optimised networks** on futures (X-Trend, DeePM, net of costs), and (c) **monthly ML over anomaly characteristics** (LSTM, net 1.42%/month post-2005), which needs fundamentals. Daily-rebalanced cross-sectional ML (CatBoost, Chronos/TimesFM, LLM-headline signals) shows very high *gross* Sharpe ratios that mostly do not survive costs or are decaying.

### Ranked catalogue (rank = reproducibility with free daily data × expected robustness; ranking is my judgement, see Inferences)

**#1. Statistical Jump Model (JM) regime filter — "Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach"**, Yizhan Shu, Chenyu Yu, John M. Mulvey (Princeton), arXiv 2402.05272, v2 July 2024 — [arXiv](https://arxiv.org/html/2402.05272v2)
- Data: daily total returns of S&P 500, DAX, Nikkei 225 (Bloomberg, local currency), 3-month T-bill; data 1970–2023, OOS 1990–2023; each index tested separately — [arXiv](https://arxiv.org/html/2402.05272v2)
- Features (exact): (1) EWM downside deviation, halflife 10d, defined as sqrt of EWM of R²·1{R<0}; (2) EWM Sortino ratio halflife 20d; (3) EWM Sortino ratio halflife 60d — [arXiv](https://arxiv.org/html/2402.05272v2)
- Model: 2-state statistical jump model (k-means-like clustering with a jump penalty on state switches); training window 3000 days (~12y); parameters refit every 6 months; online regime inference by dynamic programming over a 3000-day lookback; jump penalty chosen monthly by time-series CV on an 8-year validation window maximizing validation Sharpe. Benchmark: 2-state Gaussian HMM refit daily, smoothed by a CV-tuned rolling mean — [arXiv](https://arxiv.org/html/2402.05272v2)
- Portfolio: 0/1 — 100% index in bull regime, 100% T-bills in bear regime; 1-day trading delay (signal at close t executed at close t+1), robustness with 5 and 10-day delays; **10 bps per one-way trade** — [arXiv](https://arxiv.org/html/2402.05272v2)
- Results 1990–2023 (B&H / HMM / JM): US CAGR 10.2/8.5/11.2%, Sharpe 0.48/0.54/0.68, MaxDD −55.2/−28.9/−26.6%; Germany CAGR 6.8/6.4/8.6%, Sharpe 0.30/0.35/0.44, MaxDD −72.7/−40.5/−39.4%; Japan CAGR 0.8/2.5/4.7%, Sharpe 0.12/0.19/0.31, MaxDD −79.1/−48.6/−45.3% — [arXiv](https://arxiv.org/html/2402.05272v2)
- Follow-ups by same group: JM regimes for factor-index allocation via Black-Litterman (arXiv 2410.14841) and asset-specific regime forecasts (arXiv 2406.09578), which argues HMMs give unstable state sequences with frequent false alarms — [arXiv 2410.14841](https://arxiv.org/html/2410.14841v1); [arXiv 2406.09578](https://arxiv.org/pdf/2406.09578)
- Free-data reproducibility: **Very high.** Only daily index/ETF closes needed (^GSPC/SPY, ^GDAXI/EWG, ^N225/EWJ, plus CSI 300 / ASHR for China via yfinance). Note yfinance price indices exclude dividends (paper uses total return) — use adjusted ETF closes instead.

**#2. Gradient-boosted trees on past daily returns (cross-sectional, daily) — benchmark in "Re(Visiting) Time Series Foundation Models in Finance"**, Eghbal Rahimikia, Hao Ni, Weiguan Wang, arXiv 2511.18578, Nov 2025 — [arXiv](https://arxiv.org/html/2511.18578v1)
- Data: daily firm-level excess returns 1990–2023, 94 countries (CRSP US, Compustat Global); OOS 2001–2023 with yearly expanding-window refits; test markets US, Hong Kong, Taiwan, South Korea, Germany, UK, India, Australia; US filter price ≥ $5, ~10,000 securities, >18M test observations — [arXiv](https://arxiv.org/html/2511.18578v1)
- Features: univariate lagged excess returns with lookback windows of 5, 21, 252, 512 days, winsorized to [−1, 1]; an augmented variant adds 153 JKP monthly factors — [arXiv](https://arxiv.org/html/2511.18578v1)
- Label: next-day excess return (regression) and up/down (classification) — [arXiv](https://arxiv.org/html/2511.18578v1)
- Models: OLS/LASSO/Ridge/ENet with Huber loss, PCR, XGBoost, CatBoost, LightGBM, small/large NN; vs Chronos and TimesFM variants — [arXiv](https://arxiv.org/html/2511.18578v1)
- Portfolio: daily sort into deciles on predicted return, equal-weighted, long top / short bottom decile, daily rebalance, **no transaction costs** — [arXiv](https://arxiv.org/html/2511.18578v1) (paper text: "rebalanced on a daily basis, without accounting for transaction costs")
- Results (US): CatBoost window 252 → 46.50% annualized, Sharpe 6.79; CatBoost window 512 with global data → 47.25%, Sharpe 6.46; average OOS R² CatBoost −0.10%, linear −0.47%; small caps more predictable than large; long leg outperforms short leg; similar non-US results — [arXiv](https://arxiv.org/html/2511.18578v1)
- Free-data reproducibility: **High** for features (pure returns), but survivorship bias with yfinance (no delisted stocks) and the result is almost surely dominated by daily short-term reversal in small caps, which is not tradable after costs (see Valeyre & Aboura below: net Sharpe of residual-reversal strategies significant only before 2006). Expect most of the 6.8 gross Sharpe to vanish in a liquid, costed, weekly-rebalanced version.

**#3. Deep trend-following networks (Oxford-Man line): X-Trend (2024) and DeePM (2026)** — tested on futures, directly portable to ETF universes
- **"Few-Shot Learning Patterns in Financial Time-Series for Trend-Following Strategies" (X-Trend)**, Kieran Wood, Samuel Kessler, Stephen J. Roberts, Stefan Zohren, arXiv 2310.10500 (journal-published 2024) — [arXiv](https://arxiv.org/html/2310.10500v2); [Oxford ORA](https://ora.ox.ac.uk/objects/uuid:be6e1671-0bce-4466-9a81-6ce3157bc5b2)
  - Model: Cross Attentive Time-Series Trend Network; attends to a context set of past regimes and transfers trends to the target; trained by jointly optimizing a Sharpe loss (plus forecasting); volatility targeting; transaction cost term C(i) per asset — [arXiv](https://arxiv.org/html/2310.10500v2)
  - Data: futures across equities, FX, commodities, fixed income — [arXiv](https://arxiv.org/html/2310.10500v2)
  - Results 2018–2023: +18.9% Sharpe vs a neural forecaster, ~10x conventional TSMOM; zero-shot on unseen assets Sharpe 0.47 vs loss-making TSMOM baselines (~5x neural forecaster); COVID drawdown recovery ~2x faster — [arXiv](https://arxiv.org/html/2310.10500v2)
- **"DeePM: Regime-Robust Deep Learning for Systematic Macro Portfolio Management"**, Kieran Wood, Stephen J. Roberts, Stefan Zohren, arXiv 2601.05975, Jan 2026 — [arXiv](https://arxiv.org/abs/2601.05975)
  - Data: 50 futures, daily closes only; backtest 2010–2025 — [arXiv](https://arxiv.org/abs/2601.05975)
  - Model: end-to-end portfolio net; "Directed Delay (Causal Sieve)" for asynchronous closes, strictly lagged cross-sectional attention, Macro-Graph GNN prior, robust objective = pooled net Sharpe + SoftMin worst-window penalty (proxy for EVaR); path-dependent transaction costs in the loss — [arXiv](https://arxiv.org/abs/2601.05975) and PDF text
  - Results: net risk-adjusted returns ~2x classical trend-following and passive benchmarks, ~50% better than Momentum Transformer; normalized OOS net Sharpe 0.93 (ablations 0.66–0.87; a transfer variant 0.79, 0.97 with MACD features); training with cost scaler γ=0.5 (half the true cost) improves OOS net performance ~50% vs training with full costs — [arXiv PDF](https://arxiv.org/pdf/2601.05975)
- **[CONTEXT, pre-2023]** Deep Momentum Networks (Lim, Zohren, Roberts, arXiv 1904.04912): Sharpe-optimised LSTM keeps higher cost-adjusted Sharpe only up to 2–3 bps costs; Slow Momentum with Fast Reversion (arXiv 2105.13727): changepoint-detection module adds ~1/3 to Sharpe over 1995–2020; Momentum Transformer (arXiv 2112.08534) less affected by costs than LSTM — [arXiv 1904.04912](https://arxiv.org/pdf/1904.04912); [arXiv 2105.13727](https://arxiv.org/pdf/2105.13727); [arXiv 2112.08534](https://arxiv.org/pdf/2112.08534). Spatio-temporal momentum (Tan, Roberts, Zohren, arXiv 2302.10175, 2023) combines TS and cross-sectional signals — [arXiv](https://arxiv.org/pdf/2302.10175). Public code: [trading-momentum-transformer](https://github.com/kieranjwood/trading-momentum-transformer)
- Free-data reproducibility: **High** (daily closes only) if applied to a multi-asset ETF panel (country equity ETFs EWJ/EWG/FXI/ASHR/SPY, sector ETFs, bond/commodity ETFs). Robustness: published net of costs, but on futures; ETF histories are shorter (~2000+), so fewer training samples — the few-shot/X-Trend framing is designed for exactly this.

**#4. CNN on price-chart images — "(Re-)Imag(in)ing Price Trends"** **[CONTEXT: JF 2023, the central price-only DL paper]**, Jingwen Jiang, Bryan Kelly, Dacheng Xiu, Journal of Finance 78(6), 2023, 3193–3249 — [PDF](https://www.aidf.nus.edu.sg/wp-content/uploads/2022/02/Xiu-Re-Imagining-Price-Trends.pdf)
- Inputs: images of daily OHLC bars, volume and moving-average line over past 5, 20, 60 days; output: probability of positive subsequent return (5/20/60-day horizons) — [PDF](https://www.aidf.nus.edu.sg/wp-content/uploads/2022/02/Xiu-Re-Imagining-Price-Trends.pdf); [SSRN](https://papers.ssrn.com/sol3/Delivery.cfm?delivery_id=3756587&download=yes&frd=yes&anym=yes)
- Results: weekly decile long-short OOS gross Sharpe up to 7.2 (equal-weight) and 1.7 (value-weight); patterns learned on US transfer to international markets — [search summary of paper versions](https://papers.ssrn.com/sol3/Delivery.cfm?delivery_id=3756587&download=yes&frd=yes&anym=yes) (note: earlier working-paper versions reported lower figures, e.g., monthly EW Sharpe up to 2.4 — numbers vary by version)
- Replication code: US + China A-shares, 9 specs (5/20/60-day images × 5/20/60-day horizons), train/val 2007–2014, OOS from 2015 — [GitHub](https://github.com/George-hardworking/reimaging-price-trends-replication-and-extension); another replication — [GitHub](https://github.com/Reed2006/-Re-imaging-the-price-trend)
- Free-data reproducibility: **High** (OHLCV only); weakness = the EW gross Sharpe is small-cap/weekly-turnover driven; the VW Sharpe of 1.7 is the realistic ceiling before costs.

**#5. LightGBM / XGBoost cross-section on Chinese A-shares (monthly)**
- Jie Yang, "Application of LightGBM in the Chinese stock market" (preprint Jan 2025; ACM proceedings) — OOS monthly R² 2.13% vs 0.95% OLS; long-short 2.63%/month, Sharpe 1.77; liquidity and volatility characteristics most important — [Preprints.org](https://www.preprints.org/frontend/manuscript/f55ab343f8b582b58b2289bf1be97357/download_pub); [ACM](https://dl.acm.org/doi/10.1145/3727353.3727490)
- XGBoost on >4,900 A-shares 2001–2022: long-short 2.73%/month, Sharpe 1.76 vs OLS 2.01%/1.17 — [ACM](https://dl.acm.org/doi/10.1145/3724154.3724237)
- CS-LSTM factor model (J. Forecasting 2024): 16 characteristics; illiquidity and short-term momentum most important — [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/for.3096)
- Costs: not verified in these papers (gross results). Feature lists include non-price characteristics in at least some (not confirmed).
- Free-data reproducibility: **Medium.** Price/volume/liquidity features (reversal, momentum, Amihud illiquidity, turnover, idiosyncratic vol) can be built from daily OHLCV; yfinance coverage of A-shares (.SS/.SZ) is patchy — free alternatives AKShare/Baostock (not verified here). Short-selling A-shares is practically restricted, so only the long leg / long-minus-index is implementable.

**#6. Time-series foundation models (Chronos / TimesFM / Moirai) as return forecasters**
- Rahimikia, Ni, Wang (2025), arXiv 2511.18578 — [arXiv](https://arxiv.org/html/2511.18578v1)
  - Zero-shot: Chronos-large OOS R² −1.37%, TimesFM-500M −2.80% (window 512); zero-shot portfolios: Chronos-large 20.17% p.a., TimesFM-500M −1.47% p.a.; TimesFM-20M with 5 past returns −18.22% p.a.
  - Fine-tuning gives limited gains; pretraining from scratch on financial returns helps a lot (Chronos-small R² −77.07% → −3.18% at window 5); Chronos-small pre-trained from scratch: 36.84% p.a., Sharpe 5.42; with global data + factors + augmentation: 41.89%, Sharpe 6.78, directional accuracy 51.74% vs CatBoost 51.16% — all daily-rebalanced, gross
  - TSFM performance decays more slowly over time than benchmarks
- Valeyre & Aboura, "Large Language Models for Time Series: an Application for Single Stocks and Statistical Arbitrage", arXiv 2412.09394 (v2 Nov 2025) — [arXiv PDF](https://arxiv.org/pdf/2412.09394)
  - Data: daily residual returns (FF, PCA, IPCA residuals) of the ~550 largest US stocks from Guijarro-Ordonez et al. (2021) datasets; 100-day context; period 2002–2016; long stocks with positive predicted next residual, short negative, vol-scaled weights
  - Results: zero-shot Chronos gross Sharpe up to ~3.25 (PCA residuals, with EMA-smoothed inputs), but with α=0.3 smoothing it becomes highly correlated with, and fails to beat, plain short-term reversal (STR); fine-tuned Chronos (α=0) gross Sharpe 0.24; authors conclude AI does not yet find opportunities profitable after trading costs (3 bps/trade discussed); prior deep stat-arb net Sharpe significant only before 2006
- Noguer i Alonso & Pereira Franklin (AIFI), "Pretrained Time-Series Foundation Models for Financial Return Forecasting", arXiv 2606.27100, June 2026 — 5 US large caps (AAPL, AMZN, GOOG, JPM, META), context 512, rolling origin; TimesFM-2.5 and Moirai-2.0 rank best; only two cases significant in Diebold-Mariano; TSFMs are "useful practical priors… not universal engines for statistically reliable alpha" — [arXiv](https://arxiv.org/html/2606.27100)
- Free-data reproducibility: **Very high** (models are open weights, input = price series), but **robustness low** for zero-shot use. Best use: a feature in a GBDT ensemble or pre-train/fine-tune on large return panels.

**#7. LSTM / NN over anomaly characteristics (monthly, net of costs) — "The Expected Returns on Machine-Learning Strategies"**, Vitor Azevedo, Christopher Hoegner, Mihail Velikov (JF accepted-paper listing) — [AFA PDF](https://afajof.org/management/viewp.php?n=75544)
- Data: 137 Chen-Zimmermann anomalies, only used after their publication dates; sample March 1957–Dec 2021, ~3.4M stock-months; trading evaluated post-2005 net of high-frequency (TAQ) effective spread costs; rolling 6-year validation, 1-year test — [AFA PDF](https://afajof.org/management/viewp.php?n=75544)
- Results: OOS R² 0.05% (OLS-Huber) to 0.76% (LSTM1); gross Sharpe 0.32–1.11; costs ~20–25 bps/month; net returns 0.x% (ENET, t=2.43) to **1.42%/month (LSTM1, t=3.99)** despite one-sided turnover 60%+; LSTM six-factor generalized net alpha 1.20% (t=3.46); cost-mitigation (longer holding, buy/hold bands) reduces turnover but improves net performance only marginally (~5 bps) — [AFA PDF](https://afajof.org/management/viewp.php?n=75544)
- Free-data reproducibility: **Low–medium.** Needs CRSP/Compustat characteristics; the open-source Chen-Zimmermann signals are a partial free route (US only). A price-only subset (momentum, reversal, volatility, beta, illiquidity, max return, volume) can be built from yfinance.

**#8. Cost-aware ML portfolio learning — "Machine Learning and the Implementable Efficient Frontier"**, Theis Ingerslev Jensen, Bryan Kelly, Semyon Malamud, Lasse Heje Pedersen; SSRN 4187217 (2022/2024 versions), in press at Review of Financial Studies (SFI listing May 2026) — [SSRN](https://papers.ssrn.com/abstract=4187217); [SFI](https://www.sfi.ch/en/publications/machine-learning-and-the-implementable-efficient-frontier)
- Idea: learn portfolio weights directly from a net-of-trading-cost objective; ML return forecasts that ignore costs over-weight short-lived, small-scale signals — [SFI](https://www.sfi.ch/en/publications/machine-learning-and-the-implementable-efficient-frontier)
- Findings: quality and value characteristics matter most for the implementable frontier; short-term reversal has limited impact for a large investor; OOS 1981–2020 — [CBS slides](https://www.cbs.dk/files/cbs.dk/slides_lasse_heje_pedersen.pdf)
- Related: Jo, Kim, Shin (June 2025), "Stock Return Predictability and Machine Learning: Incorporating Transaction Costs" — conditional autoencoder (Gu-Kelly-Xiu style) with a transaction-cost penalty; in non-microcaps ~40% higher Sharpe and larger alpha than the unpenalised model — [PDF](https://iksa.or.kr/file/download/9320)
- Free-data reproducibility: **Medium** for the *method* (apply cost-penalised objective to price-based features); the paper's characteristic set needs fundamentals.

**#9. LLM headline sentiment — "Can ChatGPT Forecast Stock Price Movements? Return Predictability and Large Language Models"**, Alejandro Lopez-Lira, Yuehua Tang (Univ. of Florida), arXiv 2304.07619, this version Oct 30 2025 — [arXiv](https://arxiv.org/pdf/2304.07619)
- Data: news headlines after the LLM knowledge cutoff, Oct 2021–May 2024, US stocks, TAQ — [arXiv](https://arxiv.org/pdf/2304.07619)
- Signal: prompt GPT-4 to score each headline's implication (good/bad/unknown) for the firm; long positive / short negative, daily rebalance — [arXiv](https://arxiv.org/pdf/2304.07619)
- Results: ~90% portfolio-day hit rate for non-tradable initial reaction; drift strategy on overnight news 34 bps/day before costs; annualized Sharpe falls from 6.54 (2021Q4) to 3.68 (2022), 2.33 (2023), 1.22 (Jan–May 2024); OpenAI embeddings Sharpe 1.71 vs 2.53; earlier version: >400% cumulative Oct 2021–Dec 2022 gross, ~350% at 10 bps and ~50% at 25 bps per trade — [arXiv](https://arxiv.org/pdf/2304.07619); [earlier version via search](https://arxiv.org/pdf/2304.07619v6)
- Must use post-cutoff samples to avoid look-ahead/memorization (Sarkar & Vafa 2024; Lopez-Lira, Tang, Zhu 2025, cited in the paper) — [arXiv](https://arxiv.org/pdf/2304.07619)
- Free-data reproducibility: **Low.** Needs a timestamped headline feed (not in yfinance); and the alpha is visibly decaying with LLM adoption.

**#10. Graph neural networks for stock relations**
- Best 2025–2026 evidence found is weak: GNN realized-volatility forecasts for 465 S&P 500 stocks 2015–2025 — min-variance Sharpe ~0.98 (GNN-Sector+Macro) vs ~0.64 HAR, but **all long-short portfolios negative** (best ~−1.14) — [arXiv 2605.19278](https://arxiv.org/html/2605.19278v1); code [GitHub](https://github.com/waderylan/sp500-gnn)
- LSTM + Graph Attention trained on Sharpe loss (arXiv 2509.24144, 2025) — numbers not verified — [arXiv](https://arxiv.org/pdf/2509.24144)
- Free-data reproducibility: Medium (graphs from return correlations / sectors are free); robustness: low/unproven.

**#11. Deep reinforcement learning portfolio allocation**
- 2025 risk-aware DRL paper: stabilized risk but "failed to preserve profitability", attributed to overfitting — [arXiv 2511.11481](https://arxiv.org/html/2511.11481v1)
- 2026 global-equity DRL paper: difficulty outperforming passive/classical benchmarks across markets, consistent with DeMiguel et al. (2009) 1/N result — [arXiv 2605.17307](https://arxiv.org/html/2605.17307v1)
- RSRRL (2025): OOS favours RSRRL over RRL but robustness concerns remain under transaction costs — [arXiv 2501.17992](https://arxiv.org/html/2501.17992v1)
- Free-data reproducibility: High; robustness: **lowest** of the families surveyed.

**#12. (Negative example) "Deep Learning in Long-Short Stock Portfolio Allocation: An Empirical Study"**, Junjie Guo (Rutgers), arXiv 2411.13555, Nov 2024 — MLP/CNN/LSTM/Transformer on randomly selected S&P 500 / NASDAQ stocks, features past returns, RSI, volume, volatility; long positive / short negative predicted daily returns, equal weights; 2-year test only — [arXiv PDF](https://arxiv.org/pdf/2411.13555). Easy to code but a 2-year test on random stock subsets is not credible evidence.

### Inferences
- Ranking logic: price-only + low turnover + costs in the paper + multi-market OOS (JM regime filter) > price-only + costed but non-equity (deep trend on futures) > price-only but gross/daily/small-cap (CatBoost returns, CNN images, TSFM) > needs fundamentals (LSTM anomalies, JKMP) > needs news (LLM) > unproven (GNN, DRL).
- The common pattern: daily-rebalanced cross-sectional ML on returns rediscovers short-term reversal in small caps (Valeyre & Aboura explicitly find Chronos ≈ STR). Any free-data replication should (i) restrict to liquid names (e.g., top 500 by dollar volume), (ii) rebalance weekly/monthly or use turnover penalties, (iii) charge ≥10 bps one-way (more for Japan/China small caps).
- DeePM's finding that training with half the true cost (γ=0.5) beats full-cost training is a cheap, generalisable trick for any end-to-end net-Sharpe model.
- For Chinese A-shares, short-sale constraints mean long-only top-quantile vs CSI 300/500 benchmark is the realistic implementation.

### Gaps
- Rahimikia et al. transaction-cost section (5.2.4) not read; only the explicit "without accounting for transaction costs" statement was confirmed.
- DeePM's exact cost model parameters and absolute (non-normalized) Sharpe were not extracted.
- Did not find a 2024–2026 paper applying Momentum Transformer/X-Trend specifically to equity ETFs; equity-ETF performance is an extrapolation.
- No verified 2024–2026 CSI 300 GNN result with net Sharpe found.

---

## What are the exact feature sets and labels (so they can be coded)?

### Takeaway
Three papers give fully codeable, price-only specifications: JM regime features (EWM downside deviation hl=10; EWM Sortino hl=20, 60), Rahimikia's lagged daily excess-return vectors (5/21/252/512) → next-day return with daily decile sorts, and JKX image inputs (5/20/60-day OHLC+MA+volume) → sign of 5/20/60-day forward return.

### Cited Findings
- JM features: EWM downside deviation (hl 10d), EWM Sortino (hl 20d), EWM Sortino (hl 60d); 2 states; 3000-day train; 6-month refit; jump penalty by 8-year rolling CV; 1-day execution lag; 10 bps — [arXiv 2402.05272](https://arxiv.org/html/2402.05272v2)
- Rahimikia et al.: inputs = past excess returns with windows {5, 21, 252, 512}, winsorized [−1,1]; label = next-day excess return or direction; yearly expanding-window refit; daily EW decile long-short — [arXiv 2511.18578](https://arxiv.org/html/2511.18578v1)
- JKX CNN: inputs = images of OHLC, volume, moving average over 5/20/60 days; label = probability of positive subsequent return; replication grid 5/20/60 × 5/20/60 — [PDF](https://www.aidf.nus.edu.sg/wp-content/uploads/2022/02/Xiu-Re-Imagining-Price-Trends.pdf); [GitHub](https://github.com/George-hardworking/reimaging-price-trends-replication-and-extension)
- Valeyre & Aboura: input = last 100 daily residual returns (or their EMA with α), Chronos mean forecast of next residual; long positive/short negative with vol-scaled weights — [arXiv 2412.09394](https://arxiv.org/pdf/2412.09394)
- Lopez-Lira & Tang: input = headline text + prompt; label = GPT-4 score (+1/0/−1); next-day long-short — [arXiv](https://arxiv.org/pdf/2304.07619)
- Azevedo et al.: input = 137 published anomaly characteristics (Chen-Zimmermann); label = next-month return; models OLS-Huber, ENET, NN, LSTM1/2, ensemble; rolling 6y validation, 1y test — [AFA PDF](https://afajof.org/management/viewp.php?n=75544)
- Guo (2024): past returns, RSI, volume, volatility → next-day return — [arXiv](https://arxiv.org/pdf/2411.13555)
- DeePM: daily closing prices only; ablation mentions MACD features (net Sharpe 0.97 with MACD in a transfer variant) — [arXiv PDF](https://arxiv.org/pdf/2601.05975)

### Inferences
- A practical label for a free-data cross-sectional model: cross-sectional rank (or demeaned) of 5-day or 21-day forward return, rebalanced weekly/monthly, using as features: returns over 1, 5, 21, 63, 126, 252 days (skip-month momentum 252−21), realized vol (21/63d), downside deviation, max daily return (21d), Amihud illiquidity, dollar volume, turnover proxy (volume/avg volume), distance from 52-week high, and the JM/EWM-Sortino features. This combines the cited specs; the specific list is my synthesis, not taken from one paper.
- Deep Momentum Network inputs in the Oxford-Man papers are (from my prior knowledge, NOT verified in this session) vol-normalised returns over 1, 21, 63, 126, 252 days plus MACD indicators at (8,24), (16,48), (32,96) — verify in arXiv 1904.04912 before coding.

### Gaps
- Exact JKX image pixel construction (heights, OHLC bar width) not extracted here; see replication repos.
- Yang (2025) A-share LightGBM feature list not confirmed.

---

## Which require only price/volume data vs. fundamentals/news?

### Takeaway
Price/volume-only: JM regime filter, Rahimikia GBDT/TSFM, JKX CNN images, X-Trend/DeePM/Momentum Transformer, Chronos stat-arb, Guo DL, GNN on correlation graphs, most DRL. Need fundamentals: Azevedo et al. LSTM anomalies, Jensen-Kelly-Malamud-Pedersen, Jo-Kim-Shin CAE, augmented Rahimikia (JKP factors), likely Yang A-share LightGBM. Need news: Lopez-Lira & Tang.

### Cited Findings
- JM: index daily returns only — [arXiv](https://arxiv.org/html/2402.05272v2)
- Rahimikia: univariate past returns (base); JKP 153 factors optional augmentation — [arXiv](https://arxiv.org/html/2511.18578v1)
- JKX: OHLCV images — [PDF](https://www.aidf.nus.edu.sg/wp-content/uploads/2022/02/Xiu-Re-Imagining-Price-Trends.pdf)
- DeePM: "solely using daily closing prices" — [arXiv](https://arxiv.org/abs/2601.05975)
- Valeyre & Aboura: residual returns (need factor model — PCA residuals computable from prices) — [arXiv](https://arxiv.org/pdf/2412.09394)
- Azevedo et al.: 137 anomalies incl. accounting-based — [AFA PDF](https://afajof.org/management/viewp.php?n=75544)
- Lopez-Lira & Tang: news headlines — [arXiv](https://arxiv.org/pdf/2304.07619)

### Inferences
- With yfinance, the main data threats are survivorship bias (no delisted tickers), unadjusted index levels (no dividends), patchy A-share/Japanese small-cap coverage, and occasional bad prints — mitigate by using current index constituents only as a *lower bound* of difficulty (survivorship inflates long-short results) and preferring ETF panels for TS/regime strategies.

### Gaps
- Did not verify free A-share data sources (AKShare/Baostock) in this session.

---

## Any replication studies or critiques showing these fail out of sample?

### Takeaway
Yes, in several forms: (1) zero-shot TSFMs lose to CatBoost and often have negative R²; (2) LLM-headline alpha decays from Sharpe 6.5 to 1.2 within ~2.5 years; (3) deep stat-arb on residuals is net-profitable only before 2006; (4) ML performance concentrates in small stocks and weakens among large ones in real-time tests; (5) DRL portfolios struggle to beat 1/N. Counter-evidence: Azevedo et al. find LSTM anomaly-combination strategies remain profitable net of realistic costs post-2005.

### Cited Findings
- Zero-shot Chronos/TimesFM worse than CatBoost with markedly negative OOS R²; generic pretraining does not transfer — [arXiv 2511.18578](https://arxiv.org/html/2511.18578v1)
- TSFMs are "not universal engines for statistically reliable alpha"; only two DM-significant cases — [arXiv 2606.27100](https://arxiv.org/html/2606.27100)
- Chronos with smoothing ≈ short-term reversal and fails to beat it; AI currently cannot find opportunities that remain profitable after trading costs; prior DL stat-arb net Sharpe significant only before 2006 — [arXiv 2412.09394](https://arxiv.org/pdf/2412.09394)
- LLM strategy Sharpe 6.54 (2021Q4) → 1.22 (Jan–May 2024); returns decline as LLM adoption rises — [arXiv 2304.07619](https://arxiv.org/pdf/2304.07619)
- Real-time ML (Bin Li): OOS performance significant among small stocks, only marginal/insignificant among large stocks — [Frankfurt School PDF](https://cfet.frankfurt-school.de/wp-content/uploads/2024/09/Real_Time_ML.pdf)
- Avramov et al. (2022), cited by Azevedo et al., argue ML profits shrink under economic restrictions (excluding microcaps, distressed firms) due to high turnover; Azevedo et al. counter that sophisticated ML (LSTM) earns up to 1.42%/month net post-2005 — [AFA PDF](https://afajof.org/management/viewp.php?n=75544)
- Bagnara (2024, J. Economic Surveys) critical review: ML methods need special care; OOS R² can be low or negative — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/joes.12532)
- Gu-Kelly-Xiu (2020) replication exists (Tidy Finance blog) — [Tidy Finance](https://www.tidy-finance.org/blog/gu-kelly-xiu-replication/) (content not read)
- GNN vol-forecast long-short portfolios all negative 2015–2025 — [arXiv 2605.19278](https://arxiv.org/html/2605.19278v1)
- DRL: risk stabilised but profitability lost (overfitting) — [arXiv 2511.11481](https://arxiv.org/html/2511.11481v1); difficulty beating passive/1/N — [arXiv 2605.17307](https://arxiv.org/html/2605.17307v1)
- HMMs produce unstable regimes with frequent false alarms (motivating jump models) — [arXiv 2406.09578](https://arxiv.org/pdf/2406.09578); HMM 0/1 strategy *lowered* US CAGR vs buy-and-hold (8.5% vs 10.2%) though it raised Sharpe — [arXiv 2402.05272](https://arxiv.org/html/2402.05272v2)
- Kelly, Malamud, Zhou "Virtue of Complexity" (JF 2024) is the main pro-complexity counter-argument — [Yale PDF](https://economics.yale.edu/sites/default/files/2024-01/The%20Journal%20of%20Finance%20-%202023%20-%20KELLY%20-%20The%20Virtue%20of%20Complexity%20in%20Return%20Prediction%20(1).pdf)

### Inferences
- Reported gross Sharpe ratios above ~3 on daily stock cross-sections should be treated as reversal/microstructure artefacts until shown net of costs in liquid universes.
- The most robust candidates for a free-data ML4T backtest suite are: (1) JM regime overlay on SPY/EWG/EWJ/ASHR, (2) Sharpe-loss deep trend model on a multi-asset ETF panel, (3) LightGBM on price-only features with weekly/monthly rebalance in top-liquidity universes, with Chronos/TimesFM forecasts as an extra feature rather than a standalone signal.

### Gaps
- No independent replication of X-Trend/DeePM by third parties found.
- Jensen-Kelly-Pedersen "Is there a replication crisis in finance?" (JF 2023) not read in this session.
- Contents of 2306.10950 (DRL robustness benchmark) not read.
