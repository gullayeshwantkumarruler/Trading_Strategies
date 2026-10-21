# Equity Statistical Arbitrage Methods 2023–2026: Implementation Catalogue

Scope note: about 17 search and fetch calls. Primary sources are arXiv abstract and HTML pages; full-text details come from arXiv HTML or ar5iv renderings where noted. PDFs downloaded (not executed) to `C:\Users\Acer\Pictures\research_papers\paper1\papers\stat_arb_alt_data\`:
- `2021_GuijarroOrdonez_Pelger_Zanotti_deep_learning_stat_arb.pdf` (arXiv 2106.04028; seminal baseline, revised 2022)
- `2025_Epstein_Pelger_attention_factors_stat_arb.pdf` (arXiv 2510.11616)
- `2024_Korniejczuk_Slepaczuk_graph_clustering_multipair.pdf` (arXiv 2406.10695)
- `2024_Krause_Calliess_endtoend_stat_arb_autoencoder.pdf` (arXiv 2402.08233)
- `2025_Valeyre_Aboura_LLMs_time_series_stat_arb.pdf` (arXiv 2412.09394)
- `2024_Mousavi_Michailidis_sparse_mean_reverting_portfolios.pdf` (arXiv 2305.00203)

The folder also holds files from other researchers (alpha mining, LLM sentiment). I did not create those.

---

## Q1. Which 2023–2026 equity stat-arb methods report out-of-sample performance that survives realistic costs, and on which universes?

### Takeaway
The only strong and well-specified net-of-cost evidence in US large caps comes from Pelger's group. The CNN+Transformer on IPCA residuals (DLSA) reaches a net Sharpe of about 1.0–1.24 at 5 bp, against 3–4 gross. Attention Factors (2025) trained end-to-end on net Sharpe reaches 2.28 net (3.97 gross), on the 500 largest US stocks, OOS 1998–2021. Classic parametric OU-threshold rules on PCA residuals have strongly negative net Sharpe at the same 5 bp cost (−2.72), which matches the user's own negative net FF5 result. Graph-clustering and Korean, Polish and Chinese evidence is weaker or less robust.

### Cited Findings

**Catalogue (latest first). Seminal context is marked [CONTEXT].**

**1. Amortized Neural Filtering for Calibrated Posteriors in Statistical Arbitrage (NFE). Minkey Chang (Seoul National Univ.), arXiv 2610.25802, Oct 2026, ICAIF 2026.** [Link](https://arxiv.org/html/2610.25802)
- Universe: 120 Korea Exchange stocks (from the top 200 by median traded value), 2010–2026. — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- Residuals: PCA K=3 on a 252-day window; FF3 residuals; Attention Factor Model residuals (K=5, annual refit). — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- Regime model: two-state OU. The "converging" state has a 10-day half-life and the "diverging" state has 120 days, split at τ*=60 days. A GRU encoder with a 5-component mixture-density head gives the posterior over half-life; position size scales with the posterior. — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- Rules:
  - Base rule: position ∝ −z (standardized deviation), clipped at ±3.
  - Avellaneda–Lee threshold rule: tuned entry level.
  - Lookback L=60 days, holding period H=20 days (non-overlapping).
  - Dollar-neutral, unit gross.
  - Source: [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- Costs: 5 bp per unit turnover plus 1 bp/day on short notional. — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- Net Sharpe, OOS 2018-04 to 2026-07: — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
  - FF3: −0.12
  - PCA: 0.57 (PCA with threshold rule 0.75, PCA with posterior sizing 0.68)
  - AFM: 1.45
  - NFE: 1.49
  - AFM's own trading network: 0.25
  - Random benchmark: −0.23
  - Gross Sharpe is not reported.
- Code: https://github.com/minkeymouse/nfe — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)

**2. Statistical Arbitrage in Polish Equities Market Using Deep Learning Techniques. Adamczyk & Dąbrowski (Univ. Wrocław), arXiv 2512.02037, Nov 2025.** [Link](https://arxiv.org/abs/2512.02037)
- Universe: WIG20 + mWIG40, with Polish sector indices as factors. — [arXiv 2512.02037](https://arxiv.org/html/2512.02037v1)
- Signal: factor replication by PCA, by ETFs, or by LSTM (the paper's own contribution), with OU residuals and s-score. Avellaneda–Lee reference thresholds: open at ±1.25, close long at −0.5, close short at +0.75. The thresholds are re-optimized per method on an extra training period. — [arXiv 2512.02037](https://arxiv.org/html/2512.02037v1)
- Results:
  - 2017–2019: all strategies profitable; PCA about 20% combined return, annualized Sharpe up to 2.63 (in 2017).
  - 2020: only the ETF variant is profitable (~5%); PCA and LSTM are not.
  - Source: [arXiv 2512.02037](https://arxiv.org/html/2512.02037v1)
- Cost assumptions: adjusted from Avellaneda–Lee to local conditions; exact bp not visible in the text I read. — [arXiv 2512.02037](https://arxiv.org/abs/2512.02037)
- Code: none found.

**3. Attention Factors for Statistical Arbitrage. Epstein, Wang, Choi, Pelger, arXiv 2510.11616, Oct 2025, ICAIF 2025.** [Link](https://arxiv.org/abs/2510.11616)
- Universe: CRSP daily, the 500 largest stocks by prior-month market cap. Data 1990–2021; OOS Jan 1998 to Dec 2021 (24 years). — [arXiv HTML](https://arxiv.org/html/2510.11616)
- Inputs:
  - 39 characteristics from Chen et al., plus previous-day and previous-week return and volatility, cross-sectional medians, and the risk-free rate.
  - 79 inputs in total, rank-normalized; missing values filled with the last observation or the cross-sectional median.
  - Source: [arXiv HTML](https://arxiv.org/html/2510.11616)
- Factors: characteristic embeddings, with factor weights from a softmax over scaled dot products with K learned factor queries. K ∈ {1, 3, 5, 8, 15, 30, 100}. — [arXiv HTML](https://arxiv.org/html/2510.11616)
- Signal model: LongConv sequence model (1 layer, hidden 32) on a 30-day window of residual returns. — [arXiv HTML](https://arxiv.org/html/2510.11616)
- Objective and training:
  - Net-of-cost Sharpe + λ_Var·(explained variance), λ_Var=100, with ‖w‖₁=1.
  - Adam, learning rate 0.003, 30 epochs, weight decay 0.05, dropout 0.1.
  - Rolling 8-year training window, retrained yearly.
  - Source: [arXiv HTML](https://arxiv.org/html/2510.11616)
- Costs: 5 bp × ‖w_t − w_{t−1}‖₁ plus 1 bp × short gross. — [arXiv HTML](https://arxiv.org/html/2510.11616)
- OOS results (Table 2): — [arXiv HTML](https://arxiv.org/html/2510.11616)
  - Attention Factors, K=30: gross SR 3.97, net SR 2.28, net mean 9.52%/yr, beta 0.05.
  - Attention Factors, K=100: gross 4.52, net 2.19.
  - PCA + LongConv (two-step), K=3 or 30: gross ~2.8, net 1.57.
  - PCA + OU threshold, K=3: gross 1.26, net −2.72 (net mean −9.04%/yr).
- Ablation: removing past-return characteristics cuts net SR from 2.28 to 0.59. Most of the edge therefore runs through short-horizon return features. — [arXiv HTML](https://arxiv.org/html/2510.11616)
- Turnover: not reported numerically; it is controlled only by the cost term in the training loss. — [arXiv HTML](https://arxiv.org/html/2510.11616)
- Code: no repository linked. — [arXiv abs](https://arxiv.org/abs/2510.11616)

**4. LLMs for Time Series: an Application for Single Stocks and Statistical Arbitrage. Valeyre & Aboura, arXiv 2412.09394, v1 Dec 2024, v2 Nov 2025.** [Link](https://arxiv.org/abs/2412.09394)
- Method: the Chronos time-series foundation model, pretrained and fine-tuned, forecasts single-stock returns; a long/short portfolio is built from the forecasts. Data is the largest US stocks, from the Guijarro-Ordonez et al. dataset. — [arXiv 2412.09394](https://arxiv.org/abs/2412.09394)
- The abstract claims the forecasts "generate alpha"; costs, Sharpe and OOS period are not on the abstract page (the PDF is downloaded). No code. — [arXiv 2412.09394](https://arxiv.org/abs/2412.09394)

**5. Statistical arbitrage in multi-pair trading strategy based on graph clustering algorithms in US equities market. Korniejczuk & Ślepaczuk, arXiv 2406.10695, Jun 2024 (also a WNE Warsaw WP 2024-09).** [Link](https://arxiv.org/abs/2406.10695)
- Universe: historical S&P 500 constituents, Yahoo Finance adjusted closes; OOS Mar 2006 to Dec 2022. — [arXiv HTML](https://arxiv.org/html/2406.10695)
- Clustering:
  - SPONGEsym signed-graph clustering on a residual-return correlation graph (following Cartea et al. 2023).
  - Number of clusters = the smallest number of eigenvectors explaining 90% of variance.
  - 30-day lookback; rebalance every 10 days.
  - Source: [arXiv HTML](https://arxiv.org/html/2406.10695)
- Signal: long or short each stock by its recent return deviation from its cluster mean. — [arXiv HTML](https://arxiv.org/html/2406.10695)
- Filter: soft-voting ensemble (MLP, AdaBoost, HistGB×2, SGD, logistic regression); trade only if probability > 0.6. — [arXiv HTML](https://arxiv.org/html/2406.10695)
- Exits: take-profit 8% and stop-loss 5%, both decaying linearly over a ≤10-day hold. — [arXiv HTML](https://arxiv.org/html/2406.10695)
- Costs: 5 bp per side (sensitivity at 0, 7.5, 10 bp). — [arXiv HTML](https://arxiv.org/html/2406.10695)
- Results: — [arXiv HTML](https://arxiv.org/html/2406.10695)
  - Strategy: ARC 49.3%, IR* 1.30, max drawdown 32%.
  - Cartea et al. benchmark: 1.13% at 5 bp vs 9.01% gross.
  - SPY: IR* 0.45.
- Caveats: results are highly sensitive to two volatile stocks (EP, CPWR); no slippage modeled. — [arXiv HTML](https://arxiv.org/html/2406.10695)

**6. End-to-End Policy Learning of a Statistical Arbitrage Autoencoder Architecture. Krause & Calliess, arXiv 2402.08233, Feb 2024.** [Link](https://arxiv.org/abs/2402.08233)
- Method: an autoencoder builds factor residuals and OU s-score strategies, then is embedded in a policy network trained end-to-end on risk-adjusted returns. US stocks. The abstract claims superior gross returns. Costs and net Sharpe are not on the abstract page. No code linked. — [arXiv 2402.08233](https://arxiv.org/abs/2402.08233)

**7. Correlation Matrix Clustering for Statistical Arbitrage Portfolios. Jin, Cucuringu, Cartea, ICAIF 2023 (ACM, DOI 10.1145/3604237.3626894).** [Link](https://ora.ox.ac.uk/objects/uuid:c60358c0-24f0-4c66-b973-f84776f66f8a)
- Method: cluster the correlation matrix of market-residual returns with five graph-clustering algorithms, then build mean-reverting portfolios within each cluster. — [ORA](https://ora.ox.ac.uk/objects/uuid:c60358c0-24f0-4c66-b973-f84776f66f8a)
- Results: over 10% annualized returns and Sharpe above 1 (cost treatment not stated in the abstract). — [ORA](https://ora.ox.ac.uk/objects/uuid:c60358c0-24f0-4c66-b973-f84776f66f8a)
- Independent replication: the same benchmark replicated by Korniejczuk & Ślepaczuk falls to 1.13%/yr at 5 bp per side (2006–2022). — [arXiv 2406.10695](https://arxiv.org/html/2406.10695)
- Follow-ups from the same group:
  - Gaussian Boson Sampling clustering of S&P 500 residual correlations, benchmarked against Spectral and SPONGE. — [arXiv 2607.19279](https://arxiv.org/abs/2607.19279v1)
  - A Transformer-GNN that forecasts correlations, motivated by the critique that clustering on past correlations is backward-looking. — [arXiv 2601.04602](https://arxiv.org/pdf/2601.04602)

**8. Statistical Proxy based Mean-Reverting Portfolios with Sparsity and Volatility Constraints. Mousavi & Michailidis, arXiv 2305.00203 (v2 Jan 2024).** [Link](https://arxiv.org/abs/2305.00203v2)
- Method: maximize mean-reversion proxies (predictability, portmanteau, crossing statistic) under cardinality (sparsity) and volatility constraints. Solved by penalty decomposition with block coordinate descent. Experiments on S&P 500 data. — [search summary of arXiv 2305.00203](https://arxiv.org/pdf/2305.00203)
- [CONTEXT] Builds on d'Aspremont (2007), who frames sparse mean-reverting portfolio selection as a sparse generalized eigenvalue problem. Dense cointegration portfolios raise trading costs. — [arXiv 0708.3048](https://arxiv.org/pdf/0708.3048)
- Net trading performance: not verified.

**9. [CONTEXT, 2021/2022; published version cited as 2025] Deep Learning Statistical Arbitrage (DLSA). Guijarro-Ordonez, Pelger, Zanotti, arXiv 2106.04028.** [Link](https://arxiv.org/abs/2106.04028)
- Universe: CRSP stocks with market cap > 0.01% of total (~550 largest). OOS Jan 2002 to Dec 2016. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2106.04028)
- Characteristics: 46 (Chen et al.), rank-transformed. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2106.04028)
- Residual models: — [ar5iv](https://ar5iv.labs.arxiv.org/html/2106.04028)
  - FF K ∈ {1, 3, 5, 8}: 60-day rolling time-series regressions.
  - PCA: 252-day correlation matrix, 60-day loadings.
  - IPCA: re-estimated yearly on the last 240 months.
- Signal model: — [ar5iv](https://ar5iv.labs.arxiv.org/html/2106.04028)
  - L=30-day window of cumulative residuals.
  - CNN (2 layers, 8 filters, kernel 2), then a Transformer (1 layer, 4 heads), then an FFN that outputs weights.
  - Retrained on a rolling 1,000-day window every 125 days.
  - Daily trading at the close; ‖w‖₁ = 1.
- Gross OOS Sharpe 2002–2016: — [ar5iv](https://ar5iv.labs.arxiv.org/html/2106.04028)
  - CNN+Trans: IPCA5 4.16, PCA5 3.36, FF5 3.21.
  - Fourier+FFN on IPCA5: 1.90.
  - OU+threshold on IPCA5: 0.97.
  - K=0 (raw returns): 1.64.
- Net results with a cost-aware objective (5 bp turnover, 1 bp shorts), IPCA residuals: — [ar5iv](https://ar5iv.labs.arxiv.org/html/2106.04028)
  - K=3: net SR 1.24 (μ 6.6%, σ 5.4%).
  - K=5: 1.11.
  - K=10: 0.98.
  - K=15: 0.94.
  - K=0: 0.52.
  - FF is excluded from the friction analysis.
- Code: https://github.com/gregzanotti/dlsa-public — [search result](https://github.com/gregzanotti/dlsa-public). README not inspected.

**10. [CONTEXT] Avellaneda & Lee (2010), "Statistical Arbitrage in the U.S. Equities Market".** [Link](https://www.researchgate.net/publication/227623962_Statistical_Arbitrage_in_the_US_Equities_Market)
- Method: PCA or sector-ETF residuals; cumulative residual fitted as an OU (AR(1)) process; trade on the s-score.
- Thresholds: open at |s| > 1.25; close long at s > −0.5; close short at s < 0.75. — [as restated in arXiv 2512.02037](https://arxiv.org/html/2512.02037v1)
- Later replications of the parametric OU rule in the 2020s show it does not survive 5 bp costs in US large caps (net SR −2.72). — [arXiv 2510.11616](https://arxiv.org/html/2510.11616)

**11. LLM / news-conditioned stat arb.**
- I found no paper that conditions residual or pairs stat arb on LLM news signals with a full net-of-cost US backtest. — searches summarized in [arXiv 2412.19245](https://arxiv.org/abs/2412.19245) and [arXiv 2605.01954](https://arxiv.org/pdf/2605.01954)
- Moira (arXiv 2605.01954) is a language-driven hierarchical RL pair-trading method; only its references were visible, so details are unverified. — [arXiv 2605.01954](https://arxiv.org/pdf/2605.01954)
- Kirtac & Germano (arXiv 2412.19245) score 965k US news articles from 2010–2023 with LLMs for sentiment long-short. This is directional sentiment, not stat arb. — [arXiv 2412.19245](https://arxiv.org/abs/2412.19245)
- Adversarial headlines can cut returns of LLM-driven trading systems by up to 17.7 percentage points per year. — [arXiv 2601.13082](https://arxiv.org/html/2601.13082)

### Inferences
- Under a common 5 bp cost model, the ranking is consistent across two Pelger-group papers and one Korean replication:
  - Parametric OU-threshold on PCA residuals: net negative or barely positive.
  - Two-step (residual, then a neural signal): net ~1–1.6.
  - Joint factor-plus-policy learning with a cost-aware loss: net ~1.5–2.3.
- The user's FF5-residual result (gross ~1.3, net negative) is in line with the published OU/threshold benchmarks (gross 0.97–1.26 and net negative).
- The Korean NFE paper suggests that FF-style residuals are the weakest residual choice (net −0.12). Characteristic-conditioned (AFM/IPCA) residuals are much better net.
- Korniejczuk & Ślepaczuk's 49% ARC rests on a few volatile names and an ML filter fitted on early data. Treat it as fragile.

### Gaps
- No OPTICS-based or copula-based equity pairs paper from 2023–2026 with verified net results was found in this pass.
- No verified net Sharpe for Krause & Calliess, Valeyre & Aboura, Mousavi & Michailidis, or Jin–Cucuringu–Cartea (their PDFs are downloaded for checking).
- No Japanese or Chinese 2023–2026 stat-arb paper was verified. Non-US evidence covered here is Korean (NFE) and Polish only.
- I could not confirm the venue or year of the published DLSA version (Attention Factors cites "Guijarro-Ordonez et al. (2025)").

---

## Q2. What are the exact recipes, so they can be reproduced?

### Takeaway
The DLSA and Attention Factors papers fully specify their windows, costs and normalization. A reproducible daily-data ladder is:
1. FF5 or PCA residuals with an OU threshold.
2. The same residuals with a learned cost-aware signal.
3. IPCA or attention residuals trained end-to-end.

All of them use 5 bp turnover cost and 1 bp short cost, with ‖w‖₁ = 1.

### Cited Findings
- **Residual estimation:** — [ar5iv DLSA](https://ar5iv.labs.arxiv.org/html/2106.04028)
  - FF: 60-day rolling OLS of each stock on the factors.
  - PCA: eigenvectors of the 252-day correlation matrix, with loadings estimated on the last 60 days.
  - IPCA: loadings linear in rank-normalized characteristics, refit yearly on 240 months.
- **Signal window:** last L=30 days of cumulative residuals (L=60 comparable). — [ar5iv DLSA](https://ar5iv.labs.arxiv.org/html/2106.04028). The 2025 paper uses a 30-day residual window with LongConv. — [arXiv 2510.11616](https://arxiv.org/html/2510.11616)
- **OU benchmark:** fit OU (AR(1)) parameters plus R² on the window; trade on s-score thresholds of ±1.25 to open, −0.5 to close longs, +0.75 to close shorts. — [arXiv 2512.02037](https://arxiv.org/html/2512.02037v1)
- **No-tuning baseline from NFE:** w ∝ −z clipped at ±3; L=60, H=20-day non-overlapping holds; dollar-neutral, unit gross. — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- **Allocation normalization and objective:** — [ar5iv DLSA](https://ar5iv.labs.arxiv.org/html/2106.04028); [arXiv 2510.11616](https://arxiv.org/html/2510.11616)
  - Weights are mapped back from residual portfolios to stocks, then scaled so ‖w‖₁ = 1.
  - Objective: maximize the Sharpe ratio, or mean − γ·std, net of 0.0005·‖Δw‖₁ + 0.0001·‖w⁻‖₁.
- **Training:**
  - DLSA: rolling 1,000-day window, re-fit every 125 days. — [ar5iv DLSA](https://ar5iv.labs.arxiv.org/html/2106.04028)
  - Attention Factors: rolling 8-year window, yearly refit, Adam lr 3e-3, 30 epochs. — [arXiv 2510.11616](https://arxiv.org/html/2510.11616)
- **Graph clustering recipe:** — [arXiv 2406.10695](https://arxiv.org/html/2406.10695)
  - 30-day residual correlation matrix, then SPONGEsym clustering.
  - k = number of eigenvectors explaining 90% of variance.
  - Trade deviation from the cluster mean; 10-day rebalance.
  - TP 8% / SL 5%, decaying linearly; 5 bp per side.

### Inferences
- With yfinance prices and Ken French factors, the FF and PCA variants, the OU benchmark and a cost-aware neural signal can all be reproduced exactly.
- IPCA or attention residuals need characteristics (Chen–Zimmermann Open Source Asset Pricing data is free). Since past-return features drive most of the Attention Factors edge, a reduced characteristic set built from prices only (short-term reversal, momentum, volatility) is a reasonable first approximation. This is an inference from their ablation.

### Gaps
- The Attention Factors universe uses point-in-time CRSP top-500 membership. yfinance has survivorship bias, which matters for reversal strategies.

---

## Q3. What is known about decay and capacity of residual reversal / stat arb in US large caps since ~2015, and how do the best papers control turnover?

### Takeaway
There is little direct post-2015 decay evidence. The DLSA authors report "non-declining profitability" through 2016, and the Attention Factors OOS ends in 2021. Older literature shows residual reversal surviving costs in large caps up to 2010, while raw reversal profits decline over time with liquidity. The best papers control turnover by putting the cost term inside the training objective rather than with ad-hoc thresholds. Capacity is not quantified in any paper found.

### Cited Findings
- DLSA concludes "non-declining profitability of arbitrage trading over time" for the 2002–2016 OOS period. The cost-penalized model lowers daily turnover in calm periods (2011–2015) and raises it in volatile ones (2007–2009). The Sharpe half-life is about 7 trading days, and about half the Sharpe persists with a one-week holding period. — [ar5iv DLSA](https://ar5iv.labs.arxiv.org/html/2106.04028)
- Attention Factors controls turnover only through the 5 bp cost term in its net-Sharpe loss. No turnover figures are reported. Net SR falls from 3.97 to 2.28, so costs consume about 43% of gross Sharpe. — [arXiv 2510.11616](https://arxiv.org/html/2510.11616)
- For the PCA + OU threshold rule, costs flip SR from 1.26 gross to −2.72 net. Turnover is the binding constraint for parametric rules. — [arXiv 2510.11616](https://arxiv.org/html/2510.11616)
- [CONTEXT] Blitz, Huij, Lansdorp & Verbeek: residual reversal roughly doubles the risk-adjusted returns of conventional reversal and stays significant net of costs in large caps post-1990. Conventional reversal net of costs is about zero or negative. Sample is 1929–2010. — [EFMA paper](https://www.efmaefm.org/0EFMSYMPOSIUM/2012/papers/017_update.pdf)
- [CONTEXT] Huij (Nomura slides, 2010): reversal profits shrink in the 1,500 largest US stocks after costs. This is not peer-reviewed. — [Nomura](https://www.nomura.com/events/global-quantitative-equity-conference/resources/upload/joop_huij.pdf)
- [CONTEXT] Reversal profits decline over time, consistent with improved liquidity and price efficiency. — [NY Fed SR513](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr513.pdf)
- Turnover-control mechanisms used in the papers: — [arXiv 2610.25802](https://arxiv.org/html/2610.25802); [arXiv 2406.10695](https://arxiv.org/html/2406.10695)
  - Cost-in-loss training (DLSA, Attention Factors).
  - Non-overlapping 20-day holds (NFE).
  - 10-day rebalance plus an ML trade filter (Korniejczuk & Ślepaczuk).
  - Sparsity constraints are offered as a cost-reducing design for cointegration portfolios. — [arXiv 0708.3048](https://arxiv.org/pdf/0708.3048)

### Inferences
- The user's 70–80% daily turnover with an FF5 residual and a daily signal is the regime where every published parametric benchmark goes net negative at 5 bp.
- The most evidence-backed fixes are:
  - (a) Cost-aware objectives or no-trade bands.
  - (b) Longer holds (5–20 days), given the ~7-day signal half-life.
  - (c) Characteristic-conditioned or PCA residuals instead of FF5.
- Post-2016 evidence for US large caps is limited to the Attention Factors sample (to 2021). Performance in 2022–2026 is unverified.

### Gaps
- No paper found reports capacity (AUM at which the alpha vanishes) or explicit turnover numbers for these strategies.
- No 2023–2026 paper found isolates residual-reversal decay in US large caps after 2015.

---

## Q4. Which methods have public code?

### Takeaway
Only two of the papers here have verified public code: DLSA (gregzanotti/dlsa-public) and NFE (minkeymouse/nfe). The NFE repository also implements PCA, FF3 and AFM residual baselines with a 5 bp cost model, though on Korean data. No repository was found for Attention Factors, Krause & Calliess, Korniejczuk & Ślepaczuk, Valeyre & Aboura, or Jin–Cucuringu–Cartea.

### Cited Findings
- DLSA code: https://github.com/gregzanotti/dlsa-public — [GitHub](https://github.com/gregzanotti/dlsa-public); listed as "code available" on [SOTAVerified](https://sotaverified.org/papers/deep-learning-statistical-arbitrage)
- NFE code: https://github.com/minkeymouse/nfe — [arXiv 2610.25802](https://arxiv.org/html/2610.25802)
- The arXiv pages for 2510.11616, 2402.08233, 2406.10695 and 2412.09394 link no repository. — [2510.11616](https://arxiv.org/abs/2510.11616); [2402.08233](https://arxiv.org/abs/2402.08233); [2406.10695](https://arxiv.org/abs/2406.10695); [2412.09394](https://arxiv.org/abs/2412.09394)

### Inferences
- SPONGE and signed-Laplacian clustering, used by Cartea et al. and Korniejczuk & Ślepaczuk, can be reproduced with the open-source `signet` Python package. This was not verified in this pass.

### Gaps
- I did not inspect the README, license or completeness of dlsa-public or nfe. In particular, I did not check whether the IPCA and cost-aware training code is included.
