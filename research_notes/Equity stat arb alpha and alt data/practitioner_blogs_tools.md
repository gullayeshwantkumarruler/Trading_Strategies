# Practitioner blogs, competitions and open-source tooling for equity stat arb, alpha research and alt data (2023–2026)

Research date: 2026-10-21. About 20 search and fetch calls. Kaggle discussion pages and several practitioner sites rendered empty or sat behind paywalls (Robot Wealth RW Pro, CXO Advisory), so some competition details come from secondary write-ups. Each such case is flagged where it appears. Items marked "background knowledge, not re-verified" were NOT confirmed this session. Treat them as leads, not citations.

## Q1. What concrete stat-arb / alpha / alt-data recipes do credible practitioners publish (2023–2026), with enough detail to code?

### Takeaway
Free, dated practitioner material from 2023–2026 that is detailed enough to code is thinner than the blogs' reputations suggest. Hudson & Thames' pairs content dates mostly from 2020–21, with one 2023 post on combining momentum and mean reversion. Robot Wealth's 2025 "pairs to modern stat arb" series is paywalled. Rob Carver's 2026 posts cover forecast-weight fitting (pooling, shrinkage), not equity stat arb. The most code-ready equity recipe with recent practitioner backing is residual (factor- and industry-adjusted) short-term reversal (Robeco, 2023).

### Cited Findings
- **Residual / industry-adjusted short-term reversal (Robeco; Blitz, van der Grient & Honarvar, Sept 2023, "Reversing the Trend of Short-Term Reversal").** Stocks are sorted three ways: generic, industry-adjusted and residual STR. The residual version uses 3-factor alphas over rolling 36-month windows, scaled by volatility. The enhanced versions roughly double risk-adjusted return and stay effective over time. Source: [CXO Advisory summary](https://www.cxoadvisory.com/technical-trading/reviving-short-term-reversal/); [insuranceaum / Robeco](https://insuranceaum.com/reversing-the-trend-of-short-term-reversal)
- **Earlier evidence on residual reversal.** Residual reversal beat conventional reversal in US data from 1926 to 2008: 1.34% vs 0.97% monthly gross return (Blitz, Huij, Lansdorp & Verbeek 2011). Source: [CXO Advisory](https://www.cxoadvisory.com/technical-trading/purified-short-term-stock-reversal/)
- **Decomposing reversal profits (Da, Liu & Schaumburg).** Reversal profits split into industry-momentum, within-industry and residual parts. Only the residual part is significant, and a residual-based strategy earns about 3x the risk-adjusted return of standard reversal. Source: [NY Fed SR 513](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr513.html)
- **Robot Wealth webinar series (Sept–Oct 2025).** "From pairs trading to modern stat arb" (parts 1–3) is gated to RW Pro members, so the content could not be read. Source: [RW Pro webinar Sept 18 2025](https://robotwealth.com/rw-pro-webinar-from-pairs-trading-to-modern-stat-arb); [Part 3, Oct 30 2025](https://robotwealth.com/rw-pro-webinar-pairs-trading-to-modern-stat-arb-part-3); [weekly update](https://robotwealth.com/rw-pro-weekly-update-from-pairs-to-modern-stat‑arb-more-juice-with-less-waste)
- **Robot Wealth's stated philosophy (IBKR interview, Feb 2024).** Flexibility, opportunism, and "edges" with statistical support. Source: [IBKR Campus](https://www.interactivebrokers.com/campus/wp-json/wp/v2/posts/202446)
- **Hudson & Thames pairs-trading articles.** These cover OU optimal stopping (Sep 2020), ML pair selection (Jan 2021), copula and vine-copula stat arb (Jan–May 2021), the PMFG portfolio, and "Dynamically combining mean reversion and momentum investment strategies" (Oct 10 2023). They also have a "cold-start problem" post (Jun 2023) and an ML trading essentials post (Apr 2023). Source: [H&T pairs-trading category](https://hudsonthames.org/category/pairs-trading/); [mean-reversion + momentum, 2023](https://hudsonthames.org/dynamically-combining-mean-reversion-and-momentum-investment-strategies/); [ML pair selection](https://hudsonthames.org/employing-machine-learning-for-trading-pairs-selection/); [OU optimal stopping](https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/); [C-vine copula strategy](https://hudsonthames.org/copula-for-statistical-arbitrage-a-c-vine-copula-trading-strategy/)
- **Rob Carver, qoppac blog (2026).**
  - 29 Jun 2026: EWM vs all-data Sharpe estimates for optimisation, with spans of 5 to 40 years. EWM gave little or no benefit. Slow spans of 20 to 40 years were occasionally slightly better, and the differences were mostly not significant.
  - 3 Jul 2026: pooling forecast weights by asset class vs all-pooled vs clustered. Asset-class pooling was best in most in-sample/out-of-sample splits. Settings: SR shrinkage 0.5, correlation shrinkage 0.75, only positive-SR rules, about 6 hierarchical clusters, a 40-year EWM for SR, and 36 "sector stocks" in the universe. Costs are not yet included.
  - 4 Sep 2026: a fifth book announced.
  - Source: [qoppac.blogspot.com](https://qoppac.blogspot.com/)
- **Academic survey (Univ. Warsaw WP 19/2025, Yufei Sun).** It reviews more than 100 non-ML pairs papers from 2016 to 2023, grouped into distance, cointegration, time-series, stochastic control and other. Simple distance methods still hold up after costs. Source: [RePEc](https://ideas.repec.org/p/war/wpaper/2025-19.html)
- **Master's thesis on S&P 500 pairs, 2005–2024 (Univ. Gothenburg, Spring 2025).** High-volume pairs outperform. Performance was stronger in 2015–2024 than in 2005–2014. Commissions mattered more than borrow costs. Source: [GUPEA](https://gupea.ub.gu.se/items/dc1a29d8-4290-42c7-bf97-ee82eb7251d9)
- **Multi-asset stat arb via convex-concave optimisation (Johansson, Schmelzer, Boyd, arXiv Feb 2024).** It extends stat arb beyond 2–3-asset pairs and comes from the cvxportfolio/Stanford group. Source: [arXiv 2402.08108](https://arxiv.org/html/2402.08108v1)
- **Man Group.** The visible insight text says alt data and data science make emerging markets fertile ground for quant. A Feb 2025 podcast with Man's CTO describes in-house signal and execution platforms and an internal LLM tool used by more than half the firm, including on unstructured data in systematic strategies. Source: [Man insights](https://www.man.com/insights/why-now-for-quantitative-investing); [podcast summary](https://techblogwriter.libsyn.com/man-group)
- **Stat-arb fund returns.** One secondary Substack (unverified) says stat-arb funds returned 7.79% YTD through April 2025. Source: [Substack](https://navnoorbawa.substack.com/p/statistical-arbitrage-the-quant-strategy)

### Inferences
- **Most code-ready daily US-equity recipe from this pass.**
  1. Compute residual returns: regress daily or weekly returns on market, size, value and industry factors, or on PCA factors, over a rolling window of about 36 months (monthly) or 60–252 days (daily).
  2. Take the last 1–5 days of residual return, divided by residual volatility, as the signal.
  3. Go long losers and short winners, dollar- and industry-neutral.
  4. Filter for liquidity, since the thesis finds high-volume pairs and names work better.
  - This combines the Robeco 2023, Da-Liu-Schaumburg and Avellaneda-Lee-style approaches. The PCA/OU s-score variant (Avellaneda & Lee 2010) is background knowledge, not re-verified this session.
- Carver's results argue for heavy shrinkage of estimated Sharpe ratios and correlations, and for pooling across similar instruments, when combining many weak alpha signals. That applies directly to combining equity alphas.
- Practitioner pairs content is mature (2020–21 vintage). The 2023–2026 frontier has moved to residual/factor-neutral stat arb, multi-asset portfolio stat arb, and ML ensembles rather than new pair-selection tricks.

### Gaps
- **Not fetched or not found:** QuantStart, Quantocracy, Alpha Architect, Quantpedia strategy pages (stat-arb or alt-data), AQR, Two Sigma, Cubist, WorldQuant, Ernest Chan, Quant Seeker, Corey Hoffstein/Return Stacked. Searches for these returned no dated 2023–2026 posts within the call budget, so no recipes from them are cited.
- Robot Wealth's 2025 stat-arb series content is paywalled.
- **Background knowledge, not re-verified this session:**
  - WorldQuant's "101 Formulaic Alphas" (Kakushadze 2016) and the WorldQuant BRAIN platform.
  - Ernest Chan's work on PredictNow "conditional parameter optimisation" (meta-labelling style).
  - Quantpedia's alt-data strategy pages (e.g., sentiment, ESG, web traffic).

## Q2. What did top solutions in equity-forecasting competitions do, and what transfers to a daily cross-sectional stat-arb book?

### Takeaway
The two recent intraday equity competitions (Optiver 2023, Jane Street 2024–25) were won by the same recipe:
- a small ensemble of a GBDT (CatBoost) and/or sequence neural nets (GRU, with attention across assets);
- one shared, importance-selected feature set;
- seed ensembles;
- online learning, i.e. refitting or gradient-stepping on newly revealed labels during the test period;
- cross-sectional post-processing, i.e. re-centring predictions to zero mean across stocks.

For Numerai, the lessons are about orthogonality. FNC neutralises predictions to features, and since 2024 payouts reward MMC, the contribution to the meta-model, rather than raw correlation.

### Cited Findings
**Optiver Trading at the Close (2023; Nasdaq closing auction; about 4,000 teams; MAE in bps; $100k prize)**

1st place (hyd) blended CatBoost, GRU and Transformer with weights 0.5 / 0.3 / 0.2, chosen on validation:

| Model | CV MAE | Private LB MAE |
|---|---|---|
| CatBoost | 5.8240 | 5.4165 |
| GRU | 5.8481 | 5.4259 |
| Transformer | 5.8619 | 5.4296 |
| Blend | about 5.81 | about 5.40 |

- **Features:** all three models used the same 300 features, selected by CatBoost importance. Part of the reason was memory, so as to allow more online-retraining rounds.
- **Architecture:** the GRU took 55-step sequences, and the Transformer attended across the 200 stocks per timestep.
- **Post-processing:** each output was re-centred to zero mean.
- **Online learning:** retraining during the test period improved the private score.
- **Sourcing caveat:** these figures come from Chinese and Japanese summaries of Kaggle discussion 487446, because the Kaggle page did not render.
- Sources: [Zhihu 1st-place notes](https://zhuanlan.zhihu.com/p/689864294); [Zhihu code notes](https://zhuanlan.zhihu.com/p/699910063); [Docswell study-group slides](https://www.docswell.com/s/8980249862/K6YQ3E-2024-05-23-200638); [Kaggle discussion 487446](https://www.kaggle.com/competitions/optiver-trading-at-the-close/discussion/487446); [CSDN recap](https://blog.csdn.net/qq_51175703/article/details/137109118)

Other Optiver findings:
- 5th place used LightGBM plus CatBoost with refitting and a zero weighted-mean adjustment. Source: [CSDN recap](https://blog.csdn.net/qq_51175703/article/details/137109118)
- Competition facts (prize pool, team count, metric). Source: [Optiver](https://optiver.com/kaggle-and-optiver-predicting-nasdaqs-closing-cross-auction-movements/); [ESANN 2024 paper](https://www.esann.org/sites/default/files/proceedings/2024/ES2024-159.pdf)
- The ESANN 2024 paper reports that deep learning and SVR were common approaches. Source: [ESANN 2024](https://www.esann.org/sites/default/files/proceedings/2024/ES2024-159.pdf)

**Jane Street Real-Time Market Data Forecasting (Kaggle 2024–25; ended about July 2025; target responder_6; weighted R²; top scores about 0.01)**

- **Placing is unconfirmed.** A CLIST snapshot shows "ms capital" 1st and Patrick Yam's team 2nd. A Kaggle "Winners Walkthrough" video calls Patrick Yam's team the winning approach. Source: [CLIST standings](https://clist.by/standings/jane-street-real-time-market-data-forecasting-finance-tabular-regression-custom-metric-54687226/); [YouTube walkthrough](https://www.youtube.com/watch?v=lfzzPZZyzjE)
- **Patrick Yam team approach (third-party reproduction):**
  - training-only preprocessing;
  - asset attention combined with temporal GRUs;
  - delayed online updates that use only the previous day's labels once the API releases them;
  - seed ensembles;
  - a baseline of 5 offline epochs with online learning rate 1e-4.
  - Source: [cweill/jane-street-causal-forecasting](https://github.com/cweill/jane-street-causal-forecasting)
- **8th place (Evgeniia Grigoreva):**
  - GRU with a sequence length of one day, in two variants: a 3-layer GRU, and a 1-layer GRU plus 2 linear layers.
  - Online learning: one gradient step per new labelled batch at learning rate 3e-4, worth about +0.008 on CV.
  - Ensemble of 2 GRU variants x 3 seeds, CV about 0.0222.
  - MLP, time-series transformers, cross-symbol attention and embeddings did not help her.
  - Source: [Kaggle writeup](https://www.kaggle.com/c/jane-street-real-time-market-data-forecasting/writeups/evgeniia-grigoreva-private-lb-8th-solution); [code repo issue](https://github.com/evgeniavolkova/kagglejanestreet/issues/2)
- Jane Street describes the competition's challenges as fat tails, non-stationarity and sudden regime shifts. The organiser was the winner of their previous Kaggle competition. Source: [Jane Street ML page](https://janestreet.com/machine-learning)
- Another reproducible repo emphasises leak-free features, purged time-series validation, and timestep-by-timestep inference. Source: [Wy66wy repo](https://github.com/Wy66wy/Jane-Street-Real-Time-Market-Data-Forecasting)

**Numerai**

- **FNC (feature-neutral correlation, v3).**
  1. Rank predictions, keeping ties.
  2. Project the predictions onto the per-era feature matrix and subtract the projection.
  3. Rescale the residual to unit standard deviation.
  4. Score with Spearman correlation against the target.
  - Rationale: features are "inconsistent on their own", so linear feature exposure is risky.
  - Source: [Numerai docs: FNC](https://docs.numer.ai/numerai-tournament/scoring/feature-neutral-correlation)
- **Move to MMC-only payouts.** Numerai announced MMC-only payouts on a new target (Teager), with no payouts on CORR or TC. MMC staking started 2 Jan 2024. TC was dropped because it is a black box, unstable, and dependent on optimiser settings. Source: [Forum: MMC only](https://forum.numer.ai/t/changing-scoring-payouts-again-to-mmc-only/6794); [MMC staking starts Jan 2 2024](https://forum.numer.ai/t/mmc-staking-starts-jan-2-2024/6827?page=2)
- **TC persistence.** A backtest found TC in one round has practically no correlation with future TC, while MMC and FNC predict future TC better. Source: [Forum: true contribution backtest](https://forum.numer.ai/t/a-true-contribution-backtest)
- **Numerai Crypto payout cut.** Multipliers changed to 0xCORR + 1xMMC from rounds starting on or after 24 Jan 2025. Source: [Forum](https://forum.numer.ai/t/reducing-numerai-crypto-payouts/7914)

### Inferences
These lessons transfer to a daily cross-sectional US-equity book:
1. **Cross-sectional demeaning.** Re-centre or rank predictions per date, as in Optiver 1st place and the Numerai rank/neutralise step. This is equivalent to building a dollar-neutral book.
2. **Online or frequent refits.** Use only labels that are actually available, with a delay of 1 day or more, as in the Jane Street reproductions. For daily data, that means walk-forward retraining, e.g. weekly or monthly, plus a small learning-rate fine-tune on recent data for neural nets.
3. **Small heterogeneous ensembles with seed averaging.** For example, CatBoost or LightGBM plus a GRU, blended with weights fitted on validation.
4. **Feature neutralisation.** Partially neutralise to known risk factors and features, as in FNC, to make the alpha robust to factor-regime shifts. Score the alpha's residual contribution (MMC-like) against your existing book, not its raw IC.
5. **Scale caveat.** The competition targets are intraday and anonymised, and R² of about 0.01 counts as a win. The model architecture transfers less than the validation and online-update discipline does.

### Gaps
- Original Kaggle 1st-place write-ups for both competitions did not render (JS-rendered pages), so exact Jane Street 1st place details are unconfirmed.
- **Two Sigma and Ubiquant competitions not researched (budget).**
  - Background knowledge, not re-verified: Ubiquant Market Prediction (2022) was won mainly with LightGBM and DNN ensembles on 300 anonymised features with per-time-id normalisation. That competition falls outside 2023–2026.
- **Numerai Signals specifics not fetched.** Background knowledge: Signals scores are neutralised to Barra-style risk factors and country/sector exposures.
- The current Numerai Classic payout multipliers for 2026 were not confirmed.

## Q3. Advanced techniques used in practice (meta-labelling, purged CV, neutralisation, ensembling, online learning, regime filters, costs)

### Takeaway
The evidence from competitions and practitioners points the same way:
- Leak-free, purged and time-ordered validation is non-negotiable.
- Online or delayed-label refitting adds measurable skill.
- Neutralising to features and factors trades a little in-sample correlation for robustness.
- Ensembles of seeds and model families are standard.

Costs matter more than model sophistication for pairs and reversal strategies.

### Cited Findings
- **Online learning.** In Jane Street 2024–25, one gradient step per newly labelled batch added about +0.008 to CV R² (8th place). The 2nd/1st team used delayed online updates at learning rate 1e-4. Source: [8th-place writeup](https://www.kaggle.com/c/jane-street-real-time-market-data-forecasting/writeups/evgeniia-grigoreva-private-lb-8th-solution); [reproduction repo](https://github.com/cweill/jane-street-causal-forecasting)
- **Refit during the test period** improved Optiver 1st place's private score. 5th place also refit. Source: [Zhihu](https://zhuanlan.zhihu.com/p/689864294); [CSDN](https://blog.csdn.net/qq_51175703/article/details/137109118)
- **Purged time-series validation and leak-free feature engineering** are emphasised in Jane Street reproductions. Source: [Wy66wy repo](https://github.com/Wy66wy/Jane-Street-Real-Time-Market-Data-Forecasting)
- **Feature neutralisation (FNC)** formula and rationale. Source: [Numerai docs](https://docs.numer.ai/numerai-tournament/scoring/feature-neutral-correlation)
- **Shrinkage and pooling** when fitting combination weights: SR shrinkage 0.5, correlation shrinkage 0.75; EWM estimates add little. Source: [Carver, qoppac](https://qoppac.blogspot.com/)
- **Costs.** Commissions mattered more than borrow costs in S&P 500 pairs (2005–2024), and distance methods survive costs. Source: [Gothenburg thesis](https://gupea.ub.gu.se/items/dc1a29d8-4290-42c7-bf97-ee82eb7251d9); [Warsaw WP 19/2025](https://ideas.repec.org/p/war/wpaper/2025-19.html)
- **Regime adaptation.** Hudson & Thames (Oct 2023) dynamically combines mean-reversion and momentum strategies. Source: [H&T](https://hudsonthames.org/dynamically-combining-mean-reversion-and-momentum-investment-strategies/)

### Inferences
- **Meta-labelling, triple-barrier labels and combinatorial purged CV (López de Prado).** No new 2023–2026 practitioner evidence was located this session. These remain the standard references, and arbitragelab and Hudson & Thames' ML essentials series point to them. For a daily book, use purged K-fold with an embargo of at least the label horizon, plus walk-forward testing.
- **Execution and cost modelling.** cvxportfolio (Boyd group) builds transaction-cost and holding-cost models into multi-period optimisation (see Q4). It is the most practical open-source way to put costs into portfolio construction rather than charging them only after the fact.

### Gaps
- No 2023–2026 practitioner write-ups on meta-labelling performance or CPCV in live use were found within the budget.
- No regime-filter recipes with specific parameters were found.

## Q4. Which open-source libraries are maintained, licence-compatible and work on Windows + Python 3.13 today?

### Takeaway
Status as of Oct 2026, from live PyPI metadata pulled this session.

**Maintained, with Windows and Python 3.13 support:**
- zipline-reloaded 3.2.0 (Apache-2.0; cp313 win wheel)
- alphalens-reloaded 0.5.0, pyfolio-reloaded 0.10.0, empyrical-reloaded 0.7.0 (Apache; Python 3.11–3.15)
- Riskfolio-Lib 7.4.0 (BSD-3; cp313 win wheel)
- skfolio 1.9.7 (BSD-3; 3.10–3.14)
- vectorbt 1.2.0 (3.11–3.14; Apache-2.0 + Commons Clause)
- nautilus_trader 1.231.0 (LGPL-3.0; cp313 win wheel)
- lightgbm 4.7.0
- numerapi 3.1.1

**Problematic:**
- Qlib (pyqlib 0.9.7, Aug 2025) has wheels only up to cp312. There is no Python 3.13 classifier or wheel.
- arbitragelab 1.0.0 (May 2024; BSD-3; classifiers to 3.12) is effectively frozen.
- backtrader was last released in 2023, is GPLv3, and has Python 3.7-era classifiers.
- mlfinlab could not be queried. The PyPI API returned 503, so its status is unverified.

### Cited Findings (PyPI JSON API, queried 2026-10-21)

| Package | Version | Last upload | Licence | Python | Windows / cp313 |
|---|---|---|---|---|---|
| pyqlib | 0.9.7 | 2025-08-15 | MIT (classifier) | >=3.8; classifiers 3.8–3.12 | win_amd64 wheels cp38–cp312 only; no cp313 |
| zipline-reloaded | 3.2.0 | 2026-10-18 | Apache-2.0 | >=3.11,<3.15; classifiers 3.11–3.14 | cp311–cp314 win_amd64 wheels, incl. cp313 |
| vectorbt | 1.2.0 | 2026-10-19 | licence field empty on PyPI | >=3.11,<3.15; 3.11–3.14 | no platform wheel listed (likely pure-Python) |
| backtrader | 1.9.78.123 | 2023-04-19 | GPLv3+ | classifiers 3.2–3.7 | — |
| nautilus_trader | 1.231.0 | 2026-08-02 | LGPL-3.0-or-later | >=3.12,<3.15 | cp312–cp314 win_amd64, incl. cp313 |
| cvxportfolio | 1.5.1 | 2025-07-06 | GPLv3 | no requires_python | no platform wheel (pure-Python) |
| arbitragelab | 1.0.0 | 2024-05-12 | BSD-3-Clause | >=3.8,<4.0; classifiers 3.8–3.12 | — |
| Riskfolio-Lib | 7.4.0 | 2026-10-04 | BSD-3 | >=3.10; 3.10–3.14 | cp310–cp314 win_amd64, incl. cp313 |
| skfolio | 1.9.7 | 2026-10-20 | BSD-3 | >=3.10; 3.10–3.14 | — |
| alphalens-reloaded | 0.5.0 | 2026-10-17 | Apache-2.0 | >=3.11,<3.16; 3.11–3.15 | — |
| pyfolio-reloaded | 0.10.0 | 2026-10-17 | Apache-2.0 | >=3.11,<3.16 | — |
| empyrical-reloaded | 0.7.0 | 2026-10-17 | Apache-2.0 | >=3.11; 3.11–3.15 | — |
| numerapi | 3.1.1 | 2026-08-12 | MIT | >=3.10; 3.10–3.14 | — |
| lightgbm | 4.7.0 | 2026-07-18 | — | >=3.10; 3.10–3.14 | py3-none-win_amd64 |
| quantstats | 0.0.86 | 2026-09-27 | Apache-2.0 | >=3.10; 3.10–3.13 | — |
| backtesting.py | 0.6.6 | 2026-07-22 | AGPL-3.0 | >=3.9 | — |
| mlfinlab | — | — | — | — | PyPI returned 503; not verified |
| vectorbtpro | — | — | — | — | PyPI returned 503 (PRO is distributed privately) |

Source: [PyPI JSON API](https://pypi.org/pypi/pyqlib/json) (same endpoint per package, e.g. [zipline-reloaded](https://pypi.org/pypi/zipline-reloaded/json)). "—" means the field was not reported or not checked.

**arbitragelab**
- BSD-3-Clause ("open-source, following the BSD 3 license").
- Covers the full Krauss taxonomy of pairs strategies, plus n-asset mean-reverting portfolios.
- Source: [arbitragelab docs](https://hudson-and-thames-arbitragelab.readthedocs-hosted.com/en/latest/); [H&T ArbitrageLab page](https://hudsonthames.org/arbitragelab/)
- GitHub: 1,397 commits, 701 stars, 231 forks, 4 open issues, 3 open PRs, no releases listed, not archived. Source: [GitHub repo](https://github.com/hudson-and-thames/arbitragelab)
- A third-party tracker says the last push was 19 May 2024. Source: [gittrend.io](https://gittrend.io/repo/hudson-and-thames/arbitragelab)

**vectorbt (open-source)**
- "Fair-code" under Apache 2.0 with Commons Clause: you may not sell products or services that are primarily this software. It is described as the community edition of VectorBT PRO.
- PRO, which is separate and paid, adds parallelisation, portfolio optimisation, limit orders, leverage and CV tutorials.
- Features: multi-asset broadcasting, parameter sweeps, signal ranking, Numba and an optional Rust engine.
- Source: [vectorbt GitHub](https://github.com/polakowo/vectorbt)

**cvxportfolio:** the authors' 2024 multi-asset stat-arb paper is a companion method. Source: [arXiv 2402.08108](https://arxiv.org/html/2402.08108v1)

### Inferences
**Recommended stack for a daily US-equity stat-arb plus alt-data research pipeline on Windows with Python 3.13:**
1. **Data and factor research:** pandas/polars plus alphalens-reloaded for IC, turnover and quantile analysis. Add empyrical-reloaded and pyfolio-reloaded, or quantstats, for performance tear sheets.
2. **Models:** lightgbm (and CatBoost/XGBoost, not checked here) plus PyTorch GRUs if needed. Neutralisation and FNC-style scoring can be hand-rolled in about 20 lines of numpy, following the Numerai docs formula. numerai-tools also exists but its status was not checked here.
3. **Backtesting:**
   - vectorbt for fast vectorised parameter sweeps. Its Commons Clause is fine for internal research but restricts commercial resale.
   - zipline-reloaded for event-driven daily equity backtests with Pipeline factors (Apache-2.0; cp313 Windows wheels).
   - nautilus_trader if execution realism or a path to live trading is needed. Its LGPL is usable as a library.
4. **Portfolio construction and costs:**
   - cvxportfolio for multi-period optimisation with transaction and holding costs. It is pure-Python, but GPLv3 matters if you redistribute.
   - skfolio (BSD-3, scikit-learn API, so it plugs into CV pipelines) or Riskfolio-Lib (BSD-3) for risk-model and optimisation work.
5. **Pairs and cointegration toolkit:** arbitragelab is useful as a reference implementation (BSD-3), but its 2024 freeze and 3.12 ceiling mean it may need pinned older dependencies on 3.13. Re-implementing the needed pieces (Engle-Granger/Johansen, OU fit, distance/SSD) with statsmodels is likely safer.
6. **Avoid as core dependencies:** backtrader (dormant since 2023; GPL; old classifiers) and Qlib under Python 3.13. For Qlib's Alpha158 features and model zoo, run it in a separate Python 3.12 environment.

### Gaps
- **mlfinlab status not verified (PyPI 503).** Background knowledge: Hudson & Thames moved mlfinlab to a paid/proprietary licence around 2021–22, and open forks or alternatives exist. Not confirmed this session.
- **ml4t libraries** (Stefan Jansen's "Machine Learning for Trading" ecosystem) were not checked. The "-reloaded" packages above (zipline, alphalens, pyfolio, empyrical) are maintained by Jansen's org per background knowledge, not verified this session.
- Qlib GitHub activity in 2026 beyond the Aug 2025 PyPI release, and whether a Python 3.13 build is planned, were not checked.
- **Unverified Windows wheels and transitive dependencies:**
  - Packages showing "—" in the Windows column above may be pure-Python wheels.
  - Their transitive dependencies (e.g., arch, cvxpy, bottleneck, ta-lib) on Windows + cp313 were not checked.
  - Riskfolio-Lib and skfolio depend on cvxpy, whose solver wheels on cp313 should be checked before committing.
- vectorbt's PyPI licence field is empty, so the licence is taken from the README (Apache 2.0 + Commons Clause).
