# Alpha (Return-Predictive) Signal Research Methods for Equities, 2023–2026

Scope note: these notes cover equities only and focus on 2023–2026. Older seminal work is marked "(context)". Downloaded PDFs (not executed) are in `C:\Users\Acer\Pictures\research_papers\paper1\papers\stat_arb_alt_data\`:
- `2026_Qu_propose_dont_judge_anytime_valid_referee.pdf` (arXiv 2609.27051)
- `2025_Tang_AlphaAgent_regularized_alpha_mining.pdf` (arXiv 2502.16789)
- `2025_Shi_AlphaForge_mine_combine_formulaic_alphas.pdf` (arXiv 2406.18394, AAAI 2025)
- `2026_Chen_Welch_what_useful_alphas.pdf` (arXiv 2607.06502)
- `2026_FactorMiner_self_evolving_alpha_agent.pdf` (arXiv 2602.14670)

## Q1. Which signal families show the most robust 2023–2026 out-of-sample evidence net of costs?

### Takeaway
Recent evidence is sobering. Published characteristic anomalies largely replicate in-sample and globally (JKP 2023). Net of trading costs and post-publication decay, though, the average anomaly earns close to zero: about 4 bp/month (Chen-Velikov 2023), and a median of 7 bp/month gross for non-microcaps after 2005 (Chen-Welch 2026). Combinations do better than single signals. So do ML/composite strategies built with cost-aware construction (Azevedo-Hoegner-Velikov; Jensen-Kelly-Malamud-Pedersen). The families that ML models consistently rank highest are momentum, liquidity and volatility variants. Short-horizon reversal-type signals look strong on gross IC but tend not to survive costs.

### Cited Findings
- Jensen, Kelly & Pedersen, "Is There a Replication Crisis in Finance?" (JF 2023, 78(5):2465–2518), replicate 153 equity factors in 93 countries with a Bayesian model that handles multiple testing and publication bias. Most factors replicate, cluster into 13 themes, and work out of sample. The evidence gets stronger as more factors are observed. — [NBER w28432](https://nber.org/system/files/working_papers/w28432/w28432.pdf); [CBS publisher version](https://research-api.cbs.dk/ws/portalfiles/portal/95651880/theis_ingerslev_jensen_et_al_is_there_a_replication_crisis_in_finance_publishersversion.pdf)
- A secondary summary puts JKP's replicable share at about 82%, against a 35% rate claimed by more pessimistic studies. This figure is secondary and should be checked against the paper. — [Alpha Architect](https://alphaarchitect.com/is-there-a-replication-crisis-in-finance/)
- Chen & Zimmermann's Open Source Asset Pricing reproduces nearly all of 319 published predictors. Reproduced t-stats regress on the originals with slope 0.88 and R² 82% (Critical Finance Review). — [SSRN 3604626](https://papers.ssrn.com/abstract=3604626); [CFR PDF](https://cfr.ivo-welch.info/published/papers/chen2021open.pdf)
- Chen & Zimmermann, "Publication Bias in Asset Pricing Research": bias-adjusted returns are only about 12.3% smaller than in-sample returns, so publication bias is much smaller than post-publication decay. — [arXiv 2209.13623](https://arxiv.org/pdf/2209.13623)
- Chen & Velikov, "Zeroing in on the Expected Returns of Anomalies" (JFQA 2023, 58(3)), cover 204 anomalies. After effective bid-ask spreads, post-publication decay and modern trading technology, the average anomaly's expected return is about 4 bp/month. The strongest anomalies net about 10 bp after data-mining controls, and combined-anomaly strategies about 20 bp/month. These figures exclude price impact. — [Cambridge/JFQA](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/zeroing-in-on-the-expected-returns-of-anomalies/945133D5A3ECEEAF466AEE91551FD225); [FEDS page](https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm)
- Chen & Welch, "What Useful Alphas?" (arXiv, July 2026), study about 200 Chen-Zimmermann long-short anomalies. The median zero-investment return across all stocks was 48 bp/month through 2005 and 19 bp after 2005. For non-microcaps (top 3,000 stocks, about 90% of market cap) it was 26 bp, and 7 bp after 2005. "Modest allowances for luck or transaction costs" would eliminate even the 7 bp. The authors conclude that published anomalies have been of little use to non-microcap PMs in the 21st century. — [arXiv 2607.06502](https://arxiv.org/abs/2607.06502)
- Azevedo, Hoegner & Velikov, "The Expected Returns on Machine-Learning Strategies" (working paper, AFA/AEA 2025). After transaction costs, post-publication decay and a post-decimalization restriction, ML-strategy performance falls by about 57% on average versus a typical backtest. The decline ranges from 23% (LSTM) to 92% (FFNN2), and trading costs alone account for 13–40%. The best strategies still earn net OOS returns up to 1.42%/month despite turnover above 50%. The LSTM's six-factor net alpha is 1.20%/month (t = 3.46). — [Quantpedia summary](https://quantpedia.com/the-expected-returns-of-machine-learning-strategies/); [AEA 2025 program](https://www.aeaweb.org/conference/2025/program/paper/TihddefB)
- Jensen, Kelly, Malamud & Pedersen, "Machine Learning and the Implementable Efficient Frontier" (RFS, in press 2026; SFI WP 22-63). ML return forecasts that ignore trading costs lean too heavily on short-lived, small-scale characteristics and deliver weak net returns. Learning portfolio weights directly against a cost-aware economic objective gives a superior net-of-cost frontier, and also yields an "economic feature importance" measure. — [SFI](https://www.sfi.ch/en/publications/machine-learning-and-the-implementable-efficient-frontier); [SSRN 4187217](https://papers.ssrn.com/abstract=4187217)
- (context) Gu, Kelly & Xiu (RFS 2020): trees and neural nets roughly double the performance of leading regression-based strategies. All methods agree that the dominant signals are variations on momentum, liquidity and volatility. — [NBER w25398](https://www.nber.org/papers/w25398.pdf)
- In the "Propose, Don't Judge" CSI 500 walk-forward (15 bp per side), the statistically certified factor book underperforms the ungated book (net Sharpe +0.33 to +0.50 versus +0.59 to +0.77). Its alpha is indistinguishable from zero, partly because the IC-based bar "favours short-horizon reversal, which does not pay after costs." — [arXiv 2609.27051](https://arxiv.org/html/2609.27051v1)
- Post-sample decay benchmarks: McLean-Pontiff (context) find post-publication returns about half of in-sample. Another study finds declines of about 25% three years post-sample and about 40% five years post-sample. A 2024 Cologne working paper matches 200 predictors to data-mined benchmarks and finds that risk-based predictors do not earn higher post-sample returns than data-mined ones. — [CFR Cologne WP 24-02](https://www.cfr-cologne.de/download/workingpaper/cfr-24-02.pdf)

### Inferences
- For a non-microcap, cost-aware US equity book, no single published anomaly should be expected to pay on its own. Value comes from (a) combining many weak signals, (b) cost-aware portfolio construction (turnover penalties, trading towards a target), and (c) restricting to liquid names, where the remaining premia are small but real.
- Momentum, volatility/low-risk and liquidity families are where ML and replication studies agree most. Short-term reversal and high-turnover microstructure signals show the largest gap between gross IC and net returns. Treat them as execution or timing overlays rather than standalone alphas unless costs are modelled explicitly.
- JKP's optimistic replication results and Chen-Welch's pessimistic net-of-cost results are compatible. JKP tests gross factor existence across markets; Chen-Welch and Chen-Velikov test usefulness to an investor after costs and after 2005.

### Gaps
- I found no 2023–2026 study that ranks families (price/volume vs fundamental vs analyst vs microstructure) head-to-head on a common net-of-cost basis. The JKP and Chen-Velikov full texts may contain theme-level tables, but I did not extract them.
- Analyst-based signals (revisions, recommendation changes) have no 2023–2026 net-of-cost evidence in my sources.
- I found no independent 2024–2025 net-of-cost replication of Gu-Kelly-Xiu. The SSRN versions were revised in Nov 2024 and Sep 2025, with unknown changes.
- Specific empirical numbers from Jensen-Kelly-Malamud-Pedersen were not extracted, because I did not read the full text.

## Q2. What does the evidence say about LLM/agentic alpha mining: do mined factors survive out of sample, and how is data-snooping controlled?

### Takeaway
The field is growing fast: about 25 agentic factor-mining systems appeared in the 18 months to mid-2026. Most report good held-out IC or IR, but they evaluate after a fixed search budget with at most a static batch deflation, so none controls the sequential optional-stopping and multiplicity error of the agent loop. The best 2026 evidence on proper control ("Propose, Don't Judge") shows that a frozen, anytime-valid referee cuts false admissions sharply. It also shows that certification is slow (about 500 trading days median) and that certified alpha was not distinguishable from zero after costs. LLM memorization or look-ahead (training data overlapping the backtest) is a central unresolved threat.

### Cited Findings
- **Propose, Don't Judge** (Qu, Chen, Wang; arXiv 2609.27051, Sep 2026). The LLM proposes factors and writes diagnostic probes. A frozen referee the agent cannot modify decides admission and retirement: each candidate's post-submission daily rank-IC is bet against a zero-edge null as an e-process, online e-BH controls FDR across all candidates ever submitted at any stopping time, and an e-detector retires factors whose edge falls below δ = 0.015. The data are a point-in-time CSI 500 walk-forward from 2015-01 to 2026-08 at 15 bp per side. On real data the frozen referee admits 11.7 false factors per campaign, against 86–196 for leaky referees (peeking, adaptive threshold, no gate) under round-robin, which is a 5–11× advantage. Under the LLM proposer the advantage is 2.6–4.9×. The LLM beats a script on yield and roughly ties a discounted-UCB bandit. Its clearest value is writing its own probes. The median wait to certify a true factor is about 500 trading days. Limitations: LLM real-data results are replays (the model may have seen the period), there is one market, there is no held-out period beyond the walk-forward, and false retirements reach 8.5% at autocorrelation 0.4. The paper also states that about 25 agentic factor-mining systems appeared in the 18 months to mid-2026, and that AlphaGen, RD-Agent and AlphaAgent each use held-out IC/ICIR/Sharpe after a fixed budget, at most with static deflation, so none controls the loop's sequential error. — [arXiv 2609.27051 HTML](https://arxiv.org/html/2609.27051v1); [summary issue](https://github.com/jjakimoto/research-issues/issues/1907)
- **AlphaAgent** (Tang et al., arXiv 2502.16789, 2025) is a closed-loop multi-agent system (hypothesis, factor construction, evaluation) built to counter alpha decay. It uses three regularizers: originality via AST similarity to existing alphas, LLM-checked hypothesis-factor alignment, and complexity limits on AST size and free parameters. Reported results for Jan 2021–Dec 2024 after costs: 11.0% annual excess return (IR 1.5) on CSI 500 and 8.74% (IR 1.05) on S&P 500. The authors also claim an 81% higher hit ratio and 30% fewer tokens than baselines. These are self-reported, and the test window overlaps the LLM's training period. — [arXiv 2502.16789](https://arxiv.org/html/2502.16789v1)
- **Alpha-GPT** (arXiv 2308.00016, 2023) is human-AI interactive alpha mining. It reports average top-20 out-of-sample IC before and after search enhancement, for example Momentum rising from 0.0095 to 0.0276. **Alpha-GPT 2.0** (arXiv 2402.09746, Feb 2024) extends this to human-in-the-loop modelling and analysis and is a draft. Its overfitting claims come from the authors. — [arXiv 2308.00016](https://arxiv.org/pdf/2308.00016); [arXiv 2402.09746](https://arxiv.org/abs/2402.09746v1)
- **FactorMiner** (arXiv 2602.14670, 2026) is a self-evolving agent with skills and experience memory. Its OOS protocol is strict: factors are selected once on 2024 CSI 500 data, then frozen and evaluated on 2025 data across several markets. — [arXiv 2602.14670](https://arxiv.org/abs/2602.14670)
- **EverMine** (Li et al., arXiv 2609.33524, Sep 2026) splits research state into history, the current factor portfolio, and reusable capabilities. Its main result is negative: across 18 long-horizon trajectories, evolving capabilities gives no consistent end-to-end gain. — [arXiv 2609.33524](https://arxiv.org/abs/2609.33524)
- **AgonAlpha** (arXiv 2608.11250, Aug 2026) pairs an adversarial proposer with an attacker and is evaluated on WorldQuant BRAIN as an external environment. It reports 60 submissions, 17 graded "SPECTACULAR", and best Fitness 9.50 and Sharpe 3.48. These are BRAIN platform in-sample-style metrics, not independent live OOS. — [arXiv 2608.11250](https://arxiv.org/html/2608.11250)
- **AlphaBench** (ICLR 2026) is described as the first systematic benchmark for LLMs in formulaic alpha mining, covering generation, evaluation and search. It finds that LLMs struggle with robustness and search efficiency. — [ICLR 2026 poster](https://iclr.cc/virtual/2026/poster/10008434)
- Memorization control: an LLM evolutionary factor-search paper (arXiv 2507.17211) uses data through 2025 so that most test periods fall after the training cutoffs of DeepSeek-V3 and GPT-4.1. A China futures LLM factor paper (arXiv 2509.23609) uses GPT-4's April 2023 cutoff for a genuine post-cutoff test and reports that factors held up. — [arXiv 2507.17211](https://arxiv.org/pdf/2507.17211); [arXiv 2509.23609](https://arxiv.org/html/2509.23609v1)
- Other 2025–2026 systems seen in search: AlphaSchema (arXiv 2607.26642; within a structured search, model identity matters little, a result Propose-Don't-Judge reproduces), AlphaDiverse (arXiv 2609.29014), AlphaMemo (arXiv 2606.20625), and an LLM-MCTS formulaic miner (arXiv 2505.11122). — [Pith AlphaSchema](https://pith.science/paper/2607.26642); [arXiv 2609.29014](https://arxiv.org/pdf/2609.29014); [arXiv 2606.20625](https://arxiv.org/pdf/2606.20625); [arXiv 2505.11122](https://arxiv.org/pdf/2505.11122)
- Non-LLM automated mining: **AlphaForge** (Shi et al., AAAI 2025, arXiv 2406.18394) argues that RL miners such as AlphaGen produce combined factors with fixed weights that perform inconsistently. It uses a generative-predictive network to build a diverse, low-correlation, IC-maximising "factor zoo", then a dynamic combiner that re-scores factors on recent data each day and re-weights them into a "Mega-Alpha". The authors report better results than GP/RL baselines and mention real-money results. — [arXiv 2406.18394](https://arxiv.org/html/2406.18394v5); [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/33365)

### Inferences
- Most published LLM-mining results are on Chinese A-shares (CSI 300/500), use test windows that overlap the LLM's training data, and evaluate after a fixed search budget. Treat reported IR/IC as upper bounds.
- A practical snooping-control recipe from this literature:
  1. Freeze the evaluator so the agent cannot edit it.
  2. Log every candidate ever tried, because the denominator matters for FDR.
  3. Deduplicate by AST and by factor-return correlation (AlphaAgent).
  4. Use a post-cutoff, post-submission holdout (FactorMiner; Propose-Don't-Judge).
  5. Use sequential, anytime-valid FDR (e-BH) if the agent loops; otherwise use BH or deflated Sharpe across the full trial count.
  6. Evaluate net of costs, because IC-based gates favour reversal-like signals that fail after costs.
- The negative result from EverMine and the null net alpha in Propose-Don't-Judge suggest that LLMs help mainly with throughput and diagnostics, not with discovering durable alpha.

### Gaps
- **FactorBench**: I could not find a paper with this name. AlphaBench (ICLR 2026) is the closest match. **AlphaRLM**: no results found. **QuantAgent** (2024, self-improving LLM trading agent): no OOS methodology details found.
- No AgonAlpha or EverMine results on live trading or independent OOS.
- AlphaGen (Yu et al., KDD 2023, RL with a PPO generator over a formula grammar, reward = combined-alpha IC) was not fetched directly. Its description here comes from the papers citing it.

## Q3. Exact formulas for a practical starter alpha library (20–40 signals), a sound evaluation/combination pipeline, and open-source implementations

### Takeaway
Use Qlib's Alpha158 operator vocabulary (exact expressions below) plus a handful of Kakushadze-style 101 alphas and a fundamental block from JKP/OSAP definitions. Evaluate with rank-IC/ICIR, decay by horizon, turnover, neutralisation and orthogonalisation, then FDR/deflated-Sharpe control. Combine with IC-weighting or ridge as a baseline and LightGBM (Qlib's standard baseline) as a challenger, using cost-aware construction. Tools: Qlib, alphalens-reloaded, OSAP code, JKP code.

### Cited Findings
- **Qlib Alpha158** (exact expressions from `qlib/contrib/data/loader.py`). The default config enables kbar, price (window 0) and rolling features over windows 5, 10, 20, 30, 60. — [Qlib loader.py](https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/data/loader.py)
  - KBAR: `KMID=($close-$open)/$open`, `KLEN=($high-$low)/$open`, `KMID2=($close-$open)/($high-$low+1e-12)`, `KUP=($high-Greater($open,$close))/$open`, `KLOW=(Less($open,$close)-$low)/$open`, `KSFT=(2*$close-$high-$low)/$open` (plus range-normalised KUP2/KLOW2/KSFT2)
  - ROLLING (d ∈ {5,10,20,30,60}):
    - Price level and trend: `ROC=Ref($close,d)/$close`, `MA=Mean($close,d)/$close`, `STD=Std($close,d)/$close`, `BETA=Slope($close,d)/$close`, `RSQR=Rsquare($close,d)`, `RESI=Resi($close,d)/$close`
    - Range and position: `MAX=Max($high,d)/$close`, `MIN=Min($low,d)/$close`, `QTLU/QTLD=Quantile($close,d,0.8/0.2)/$close`, `RANK=Rank($close,d)`, `RSV=($close-Min($low,d))/(Max($high,d)-Min($low,d)+1e-12)`, `IMAX=IdxMax($high,d)/d`, `IMIN=IdxMin($low,d)/d`, `IMXD=(IdxMax($high,d)-IdxMin($low,d))/d`
    - Price-volume correlation: `CORR=Corr($close,Log($volume+1),d)`, `CORD=Corr($close/Ref($close,1),Log($volume/Ref($volume,1)+1),d)`
    - Up/down counts and sums: `CNTP=Mean($close>Ref($close,1),d)`, `CNTN`, `CNTD`, `SUMP=Sum(Greater($close-Ref($close,1),0),d)/(Sum(Abs($close-Ref($close,1)),d)+1e-12)` (RSI-like), `SUMN`, `SUMD`
    - Volume: `VMA=Mean($volume,d)/($volume+1e-12)`, `VSTD=Std($volume,d)/($volume+1e-12)`, `WVMA=Std(Abs($close/Ref($close,1)-1)*$volume,d)/(Mean(Abs($close/Ref($close,1)-1)*$volume,d)+1e-12)`, `VSUMP/VSUMN/VSUMD` (volume analogues of SUMP/SUMN/SUMD)
- **Qlib Alpha360**: 60 days of lagged raw OHLC and VWAP, each divided by today's close, and volume divided by today's volume, giving 6×60 = 360 features meant for deep models. — [Qlib loader.py](https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/data/loader.py)
- (context) Kakushadze, "101 Formulaic Alphas" (Wilmott 2016), gives explicit formulas for 101 real-life short-horizon alphas (average holding period about 0.6–6.4 days), built from operators such as rank, delay, delta, correlation, ts_rank, decay_linear and indneutralize. Examples are Alpha#101 = `(close-open)/((high-low)+0.001)` and Alpha#12 = `sign(delta(volume,1)) * (-1*delta(close,1))`. — [arXiv 1601.00991](https://arxiv.org/abs/1601.00991)
- alphalens-reloaded (Stefan Jansen, PyPI 0.4.x) gives factor tear sheets: forward returns by quantile, IC analysis, turnover and grouped analysis. Note that NumPy ≥ 2.0 needs pandas ≥ 2.2.2. ml4t-diagnostic is listed on Jansen's PyPI as a diagnostics/evaluation framework for quant ML workflows, but I found no API documentation. factrix is a Polars-native alternative. — [alphalens docs](https://alphalens.ml4trading.io/); [PyPI ml4t](https://pypi.org/user/ml4t); [factrix](https://pypi.org/project/factrix/)
- OSAP provides public code and data reproducing 319 predictors, so it is the recipe source for fundamental and price-based anomaly definitions. JKP provides global factor data and code for 153 factors in 13 themes. — [SSRN 3604626](https://papers.ssrn.com/abstract=3604626); [JKP NBER](https://nber.org/system/files/working_papers/w28432/w28432.pdf)
- Dynamic combination (AlphaForge): re-score each factor in the zoo on a trailing window and keep and weight the recent winners. This beat fixed-weight RL combinations in the authors' tests. — [arXiv 2406.18394](https://arxiv.org/html/2406.18394v5)
- Cost-aware combination (JKMP): learn portfolio weights against a net-of-cost objective rather than ranking by predicted return. — [SFI](https://www.sfi.ch/en/publications/machine-learning-and-the-implementable-efficient-frontier)
- Retirement and decay monitoring: an e-detector retires a factor when the rank-IC edge drops below 0.015, and ordinary BH with a 500-day test admits about 4× more false factors on a large library. — [arXiv 2609.27051](https://arxiv.org/html/2609.27051v1)

### Inferences
- **Suggested starter library (about 30 signals).** These are standard definitions given as context. They follow OSAP/JKP conventions and should be checked against OSAP code before use.
  - *Price/volume only (about 18):*
    - 12-1 momentum, `P[t-21]/P[t-252]-1`
    - 1-month short-term reversal, `-r[t-21,t]`
    - industry-relative momentum
    - 52-week-high proximity, `P/max(P,252)`
    - realised volatility over 20/60 days, negated
    - CAPM beta over 252 days, negated (betting-against-beta direction)
    - idiosyncratic volatility, negated
    - max daily return over 21 days, negated
    - Amihud illiquidity, `mean(|r|/dollar_volume,21)`
    - turnover change, Qlib `VMA20`
    - `CORR20`/`CORD20` price-volume correlation
    - `RSV20`, `SUMD14` (RSI-like), `KSFT`, `RESI20`, `RSQR60` (trend quality)
    - skewness over 60 days
    - Alpha#101
  - *Fundamentals (about 12, need EDGAR/yfinance):*
    - value: book-to-market, earnings yield, cash-flow yield, EBITDA/EV
    - profitability: gross profits/assets (Novy-Marx), operating profitability, ROE
    - investment: asset growth, negated
    - accruals, negated
    - net share issuance, negated
    - SUE / earnings surprise from consecutive 10-Q EPS
    - Piotroski F-score
- **Evaluation pipeline:**
  1. Winsorise at 1%/99%, then cross-sectionally rank or z-score each day.
  2. Neutralise to industry and size (and beta).
  3. Compute daily Spearman rank-IC against 1/5/10/21-day forward returns, plus mean IC, ICIR (mean/sd), and a Newey-West t-stat. Use t > 3 as the discovery hurdle when many signals are tested (context: Harvey-Liu-Zhu 2016).
  4. Decay: plot IC by lag.
  5. Turnover: rank autocorrelation, and a quantile-portfolio turnover-to-cost estimate.
  6. Orthogonalise each new signal against the existing book (regress cross-sectionally on existing signals and keep the residual IC), and drop pairs with |corr| > 0.7.
  7. Control false discovery with BH-FDR across all tried signals, deflated Sharpe on the final strategy (context: Bailey-López de Prado 2014), or e-BH if search is sequential.
  8. Use purged, embargoed walk-forward CV.
  9. Report net of half-spread plus impact costs.
- **Combination ladder:**
  1. Equal-weight z-scores.
  2. IC-weighting with trailing ICIR weights, shrunk towards equal weight.
  3. Ridge or ElasticNet regression of forward residual returns on signals (cross-sectional, pooled).
  4. LightGBM regressor or LambdaRank on Alpha158 plus fundamentals (Qlib's standard benchmark model).
  5. Gu-Kelly-Xiu-style NN.
  
  Then feed the composite into a turnover-penalised optimiser.

### Gaps
- GTJA 191 alphas: I did not retrieve the original Guotai Junan report or a canonical code listing in this session. It is commonly implemented in Chinese open-source repos, but I have no verified source.
- Qlib's published Alpha158 benchmark numbers (IC/ICIR for LightGBM and others) were not fetched. See the Qlib `examples/benchmarks` README.
- ml4t-diagnostic API details are unknown.

## Q4. Free data sources for fundamentals and point-in-time issues

### Takeaway
SEC EDGAR's XBRL APIs (data.sec.gov) are free and keyless, and they cover US-GAAP facts since about 2009. Each fact carries filing metadata, so a careful user can build a point-in-time panel. yfinance statements are convenient but not point-in-time and cover only recent periods. Survivorship, restatements and filing lags are the main pitfalls.

### Cited Findings
- EDGAR APIs (JSON, no key):
  - `submissions/CIK##########.json`: filing history, updated in real time
  - `api/xbrl/companyconcept/CIK##########/us-gaap/{Tag}.json`: all facts for one tag
  - `api/xbrl/companyfacts/CIK##########.json`: all facts for one company
  - `api/xbrl/frames/us-gaap/{Tag}/USD/CY2019Q1I.json`: cross-section of one fact per entity per period, using each entity's latest filing that best fits the period
  
  Bulk `companyfacts.zip` and `submissions.zip` are rebuilt nightly at about 03:00 ET. Frames include only non-custom taxonomies, and fiscal calendars vary. — [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- Fair access: at most 10 requests per second, with a declared User-Agent naming the company and a contact email. — [SEC Accessing EDGAR Data](https://www.sec.gov/os/accessing-edgar-data)
- Point-in-time caveat: frames return each entity's *latest* filed value for a period, which embeds restatements and creates look-ahead if used naively. — [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

### Inferences
- For point-in-time use, build from `companyfacts` rather than `frames`. Each fact record has `filed`, `form`, `accn`, `fy/fp` and `frame` fields (from working knowledge of the JSON schema, not confirmed on the fetched page). For each (concept, period end), keep the first-filed value and make it available from `filed` + 1 trading day. Also apply the conventional OSAP/JKP lag (annual data available about 6 months after fiscal year-end; quarterly about 4 months, or the actual filing date).
- yfinance `financials`/`quarterly_financials`/`balance_sheet` give only about 4 annual and about 4–5 quarterly periods of latest-restated data, so they are unsuitable for backtests. Use them only for live signal snapshots. This is from working knowledge and was not verified with a source this session.
- Survivorship: EDGAR includes delisted filers by CIK, but free price data (yfinance) usually lacks delisted tickers. Map CIK to ticker history through the `submissions` former names and tickers.

### Gaps
- I did not verify the current yfinance statement coverage or how it is sourced.
- I did not check the free/paid status of JKP or OSAP data downloads in 2026. Both have historically been free (jkpfactors.com, openassetpricing.com).
