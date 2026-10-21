# Alternative Data for Equity Alpha and Stat Arb (2023-2026): what an individual researcher can access and build

Scope note: research budget was about 15 tool calls, so coverage is uneven. Items marked **[unverified this session]** come from the researcher's background knowledge and were NOT re-checked against a source in this session; the report writer should treat them as leads, not citable facts. Everything else carries an inline source.

PDFs saved (arXiv, open access) to `C:\Users\Acer\Pictures\research_papers\paper1\papers\stat_arb_alt_data\`:
- `2025_LopezLira_Can_ChatGPT_Forecast_Stock_Prices.pdf` (arXiv 2304.07619 v6, Oct 2025)
- `2024_Kirtac_Sentiment_Trading_LLMs.pdf` (arXiv 2412.19245)
- `2026_Yilki_Supply_Chain_LLM_Embeddings.pdf` (arXiv 2606.29290)
- `2025_Reddit_ChatGPT_Annotated_Sentiment.pdf` (arXiv 2507.22922)
- `2025_LLM_Enhanced_News_Momentum.pdf` (arXiv 2510.26228)
(Other PDFs in that folder were already there from other researchers.)

## Q1. Which alt-data signals have the strongest recent out-of-sample evidence that persists after publication and after costs?

### Takeaway
LLM-scored news sentiment has the most 2023-2026 out-of-sample evidence. Its edge sits mainly in the first day, in small stocks and in negative news, and the authors of the lead paper (Lopez-Lira & Tang) report that it is shrinking as LLM adoption spreads. Older "slow" signals hold up as multi-week to multi-month predictors but have little fresh replication from 2023-2026: filing-text changes (Lazy Prices), short-selling flows, option skew and opportunistic insider buys. Each has a known mechanism-based weakening: borrow fees for skew, small-cap concentration, and costs for daily short-volume trading.

### Cited Findings

**News/LLM sentiment (headlines)**
- Lopez-Lira & Tang, "Can ChatGPT Forecast Stock Price Movements?", v6 (30 Oct 2025). On headlines published after the model's knowledge cutoff, GPT-4 gets about 90% portfolio-day hit rates on the initial reaction, which cannot be traded. Its scores also significantly predict the later drift, especially in small stocks and after negative news. Predictive ability rises with model size. — [arXiv 2304.07619](https://arxiv.org/abs/2304.07619v5); [v6 PDF](https://arxiv.org/pdf/2304.07619v6)
- The same paper reports that strategy returns fall as LLM adoption rises, consistent with better price efficiency. This is direct evidence of decay. — [arXiv 2304.07619](https://arxiv.org/abs/2304.07619v5)
- Earlier drafts found that GPT-1, GPT-2 and BERT cannot forecast returns, and that ChatGPT scores subsume traditional sentiment methods. — [arXiv 2304.07619v1](https://arxiv.org/abs/2304.07619v1)
- Kirtac & Germano, "Sentiment trading with large language models" (Finance Research Letters 2024, DOI 10.1016/j.frl.2024.105227). The sample is 965,375 US news articles from 2010-2023. OPT, BERT and FinBERT are compared with the Loughran-McDonald dictionary. An OPT-based long-short strategy has a Sharpe ratio of 3.05 after 10 bp costs (trading period Aug 2021-Jul 2023). — [arXiv 2412.19245](https://arxiv.org/pdf/2412.19245); [LSE record](https://researchonline.lse.ac.uk/id/eprint/122592)
- Kirtac (single author), arXiv 2609.23703 (Sep 2026, R&R at *Engineering Applications of AI*). Data are Refinitiv news linked to CRSP, plus a public-data replication arm. The test is net of 5 bp costs with a 10% daily dollar-volume participation cap. Decoder-only LLMs (LLaMA-3 best) beat encoder and dictionary models on a net basis. The dictionary baseline loses money after turnover costs. The out-of-sample evaluation is restricted to news released after each model's training-data cutoff. — [arXiv 2609.23703](https://arxiv.org/abs/2609.23703)
- S&P Global Market Intelligence (Sep 2025): when the LLM flags performance-related events as high importance, earnings-call sentiment earns 6.4% per year in long-short excess returns. The LLM strategy kept working in recent years while the lexicon benchmark weakened. This is a vendor report. — [S&P Global](https://www.spglobal.com/market-intelligence/en/news-insights/research/2025/09/familiar-signal-new-context-from-lexicon-to-llm-the-evolution-of-earnings-call-nlp)
- Chen, Kelly & Xiu, "Expected Returns and Large Language Models" (presented 2024). They build contextual embeddings of news from ChatGPT/LLaMA across 16 international markets and 13 languages. Prices respond slowly to news, and embedding-based predictions beat technical signals and simpler NLP. — [Sydney seminar listing](https://business.sydney.edu.au/events/research/2024/finance/dacheng-xiu); [Tsinghua PBCSF listing](https://www.pbcsf.tsinghua.edu.cn/info/1504/7668.htm); [Kelly slides, Wharton JLC](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2024/09/Kelly-WhartonJL.pdf)
- LLM-enhanced momentum (arXiv 2510.26228): LLM-read news conditions momentum stock selection and weights in the S&P 500. It reports higher Sharpe and Sortino ratios than long-only momentum, both in-sample and in a truly out-of-sample period, robust to costs, prompt design and constraints. — [arXiv 2510.26228](https://arxiv.org/html/2510.26228v1)
- A student thesis (Imperial) combining GPT-4o news sentiment with macro and technical signals reports long-short Sharpe ratios of 3.64 (2022) and 5.10 (2023) at a 1-day holding period. Low credibility: student work, not peer-reviewed. — [Imperial thesis](https://imperial.ac.uk/media/imperial-college/faculty-of-natural-sciences/department-of-mathematics/math-finance/Kargarzadeh_Alireza_02092220.pdf)

**Filing text changes (Lazy Prices)**
- Cohen, Malloy & Nguyen (JF 2020): a portfolio that is short "changers" and long "non-changers" in 10-K/10-Q language earns up to 188 bp per month in alpha (over 22% per year). There is no announcement-day reaction, which points to investor inattention. — [EconBiz record](https://econbiz.de/Record/lazy-prices-cohen-lauren/10012910642); [SUFE summary](https://academicnewsletter.sufe.edu.cn/info/359228)
- An embedding-based extension ("Lazy Network", Complexity 2022) reports up to 95 bp per month in five-factor alpha. — [air.unipr.it](https://air.unipr.it/handle/11381/2922088)
- QuantConnect practitioner note (UCSD Triton): a long-only 10-K/10-Q language-stability filter beat SPY on a risk-adjusted basis from Jan 2020 to Jun 2026. This is post-publication, but practitioner-grade evidence. — [QuantConnect](https://www.quantconnect.com/research/20966/filing-language-stability-as-a-selection-signal/)

**Short selling (FINRA daily short volume)**
- Using FINRA 2010-2015 data, shorting flows significantly predict negative future returns. The predictability decays slowly over a year, and long-term flows are more informative than short-term ones. — [Lehigh paper](https://www.lehigh.edu/~xuy219/research/Short_Final_Version.pdf)
- HKUST thesis, 2010-2018: the short volume ratio still predicts negative returns, and the abnormal short volume ratio anticipates earnings news. — [HKUST](https://lbezone.hkust.edu.hk/rse/?p=51474)
- Goyal, Reed, Smajlbegovic & Soebhag, "Stealthy Shorts: Informed Liquidity Supply": they split daily short volume into liquidity-supplying (LSS) and liquidity-demanding parts. Only LSS predicts returns, negatively. — [Quantpedia summary](https://quantpedia.com/short-sellers-informed-liquidity-suppliers/)
- Stanford GSB working paper: short-sellers who supply liquidity against price-destabilizing mutual-fund trades explain most of short-sale volume's long-horizon predictability. — [Stanford GSB](https://www.gsb.stanford.edu/faculty-research/working-papers/mutual-funds-short-sellers-why-does-short-sale-volume-predict-stock)
- Older context: Diether, Lee & Werner find that rising short sales predict negative returns, but trading costs eliminate the profit of a daily strategy. — [NBER conf. draft](https://users.nber.org/~confer/2005/mmf05/werner.pdf)

**Options-implied signals**
- Xing, Zhang & Zhao (JFQA 2010): stocks with the steepest smirk underperform those with the flattest by 10.9% per year on a risk-adjusted basis. — [Cambridge/JFQA](https://resolve.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/what-does-the-individual-option-volatility-smirk-tell-us-about-future-equity-returns/ECFD16BA9ACBDC8D577D1BD866FBEA72)
- Muravyev, Pearson & Pollet: predictability from the IV spread and skew falls by at least two-thirds when high-borrow-fee stocks are excluded. The signal is largely a proxy for short-sale constraints. — [Replication package](https://data.mendeley.com/datasets/n73cyx89gs)
- Goncalves-Pinto et al. (Management Science): the predictability is mechanically tied to mispricing of the stock, not to informed option trading. — [MS supplement](https://pubsonline.informs.org/doi/suppl/10.1287/mnsc.2019.3398/suppl_file/mnsc.2019.3398.sm1.pdf)
- Fu, Arisoy, Shackleton & Umutlu (2016): IV skew has the strongest predictive power across horizons, both before and after the GFC. — [Yasar repository](https://gcris.yasar.edu.tr/entities/publication/bfc57b8a-49bd-4726-96a7-a5e3eca8a5cb/full)

**Insider trades (Form 4)**
- Cohen, Malloy & Pomorski (secondary summary): routine insider trades have zero predictive power, while opportunistic trades earn about 82 bp per month. — [Gotrade summary](https://heygotrade.com/en/blog/insider-buying-signals-should-you-follow-the-c-suite/)
- Trades reported in late Form 4 filings earn significantly higher abnormal returns and appear to conceal trading ahead of material events. — [Wharton faculty page](https://faculty.wharton.upenn.edu/?p=32560)
- Avci, Schipani, Seyhun & Verstein (2024): insiders using concealment strategies beat the market by up to 20% on average. — [Wharton faculty page](https://faculty.wharton.upenn.edu/?p=32560)
- Recent free-data replication (QuantInsti, C-suite purchases from 2022 to mid-2026, filing-date event study): SPY-adjusted mean CAR is +0.53% the next session and +1.01% over 5 sessions. Longer-horizon confidence intervals include zero, and costs are not modelled. The edge is modest and short-lived. — [QuantInsti](https://blog.quantinsti.com/sec-form-4-insider-trading-python-event-study/)

**Supply chain / customer-supplier links**
- Yılkı (arXiv 2606.29290, Jun 2026): FinBERT embeddings of 10-K MD&A for 255 S&P 500 firms (2011-2025) are propagated over a supply-chain knowledge graph. The network factor `net_pc_5` has a Fama-MacBeth NW t-stat of -2.64 after controls. Long-short Sharpe is 0.86 and FF5 alpha is 7.27% per year (t = 2.30). It survives out-of-sample, placebo and sector-neutral tests. The abstract mentions no cost analysis. — [arXiv 2606.29290](https://arxiv.org/abs/2606.29290)

**Alpha decay / crowding (general)**
- BlackRock assesses alt-data signals on live information ratios rather than backtests. — [BlackRock whitepaper](https://blackrock.com/us/individual/literature/whitepaper/alpha-innovation-via-alt-data.pdf)
- Neudata reviews a 2024 INSEAD working paper on crowding and alpha decay in widely adopted datasets. Specific findings could not be extracted. — [Neudata](https://www.neudata.co/literature-reviews/do-well-adopted-datasets-suffer-from-alpha-decay)

### Inferences
- Ranking by strength and persistence of recent out-of-sample evidence, for an individual:
  1. LLM news sentiment, but with daily or faster holding periods, small-cap and negative-news concentration, and documented erosion.
  2. Text-change signals from filings (slow, low-turnover, cheap to trade, and EDGAR is free). This is the most cost-robust choice for an individual.
  3. Short-volume and short-interest signals at weekly-to-monthly horizons.
  4. Option skew, mostly a borrow-fee proxy, and in any case lacking free historical data.
  5. Opportunistic insider buying (small, fast edge).
- Sharpe ratios above 3 in news-sentiment papers (Kirtac & Germano 3.05; the Imperial thesis 3.6-5.1) come from short samples (2021-2023) and daily rebalancing. Kirtac's own 2026 follow-up adds participation caps, which signals that those headline numbers were optimistic. Expect material haircuts.
- The cleanest "after costs" evidence is the pattern that dictionary-based sentiment dies once costs are applied while LLM signals survive (Kirtac 2026). In other words, signal quality has to clear turnover costs.

### Gaps
- No 2023-2026 out-of-sample replication of Lazy Prices on post-2020 samples was found in a peer-reviewed venue.
- No specific post-publication decay estimates were found for Google Trends or Wikipedia attention signals. Background context [unverified this session]: Da, Engelberg & Gao (JF 2011) found that the Google SVI predicts higher prices over 2 weeks followed by reversal within a year. McLean & Pontiff (JF 2016) found that anomaly returns fall about 26% out-of-sample and about 58% after publication.
- The net Sharpe ratios and sample dates in Kirtac 2026 could not be extracted from the abstract.
- No ETF-flow, web-traffic, app-download, job-posting, patent, satellite or credit-card evidence was gathered this session (budget). Background [unverified this session]: these are mostly paid vendor data (YipitData, Similarweb, Thinknum, Placer.ai, Orbital Insight, card panels such as Bloomberg Second Measure/Consumer Edge). Pricing is typically five to six figures per year and not realistic for individuals. Free proxies include USPTO PatentsView (patents) and ETF shares-outstanding changes (flows) from issuer sites or yfinance.

## Q2. Which signals can be built with free data today, and how much history is available?

### Takeaway
SEC EDGAR is the best free alt-data source: full filing text, Form 4, 13F, 13D/G, and XBRL facts via JSON APIs with no key. FINRA daily short-sale volume is free, but its public catalog only goes back to Aug 2018. Free options data is effectively current-only, so you must build your own history by collecting snapshots going forward.

### Cited Findings
- SEC EDGAR APIs need no authentication or API key. The endpoints are:
  - `data.sec.gov/submissions/CIK##########.json`: filing history, names, tickers.
  - `data.sec.gov/api/xbrl/companyfacts/CIK##########.json`
  - `companyconcept`
  - `frames`, e.g. `.../frames/us-gaap/AccountsPayableCurrent/USD/CY2019Q1I.json`: one fact per filer per period.
  - Nightly bulk `companyfacts.zip` and `submissions.zip`.
  - Full-text search at sec.gov/edgar/search.

  — [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- Access must follow SEC's Privacy & Security Policy; the Developer FAQ has the details. — [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). [unverified this session: the fair-access limit is 10 requests per second and a declared User-Agent with a contact email is required; EDGAR full-text search covers 2001 onward; the raw EDGAR archive and quarterly form index go back to 1993-94; insider and 13F structured datasets are published as quarterly "Financial Statement and Notes" / "Insider Transactions" / "Form 13F" data sets.]
- FINRA daily short sale volume files are free. Separate files exist for each TRF (Nasdaq Chicago, Nasdaq Carteret, NYSE), the ADF and the ORF, plus a consolidated NMS file. They are posted by 6:00 pm ET on the trade date, and corrections are marked "Updated". The public catalog's consolidated files start 1 Aug 2018 (TRF Chicago from 10 Sep 2018). Older data ties back to an Information Notice of 29 Sep 2009; monthly short-sale transaction files exist per year (e.g. 2012, 2013). — [FINRA Daily Short Sale Volume](https://www.finra.org/finra-data/browse-catalog/reg-sho-daily); [FINRA TRF Reg SHO 2013](https://www.finra.org/filing-reporting/trf/trf-regulation-sho-2013)
- A free Python EDGAR Form 4 event-study pipeline (purchases, filing-date alignment) is documented by QuantInsti. — [QuantInsti](https://blog.quantinsti.com/sec-form-4-insider-trading-python-event-study/)
- Google Trends samples change between pulls. One practitioner guide recommends re-pulling several times and averaging, and notes that attention signals decay quickly. Secondary source. — [LuxAlgo](https://www.luxalgo.com/library/concept/alternative-sentiment-data.md)
- In the Reddit/GME/AMC study, comment volume and Google search trends predicted better than ChatGPT-annotated sentiment, and sentiment showed only weak correlation with prices. — [arXiv 2507.22922](https://arxiv.org/pdf/2507.22922)

**Free-data build table.** Access details marked [u] are unverified this session.

| Signal family | Free source / Python | History | Notes / pitfalls |
|---|---|---|---|
| 10-K/10-Q text change (Lazy Prices) | EDGAR archives + full-text search; `requests`, `sec-edgar-downloader` [u], `edgartools` [u] | 1993+ archives [u] | Use the filing *acceptance* timestamp, not the period end. Strip boilerplate and tables. Compare each filing with the same form type a year earlier (10-K vs prior 10-K, Q vs same Q). |
| 8-K events | EDGAR submissions JSON | 2001+ full-text [u] | Item codes give event types. Check timestamps for after-hours filings. |
| Form 4 insiders | EDGAR (XML since 2003 [u]); SEC insider data sets [u] | 2003+ [u] | Classify trades as opportunistic or routine, and use only open-market purchases (code P). Late filings carry more information (Wharton). |
| 13F holdings | EDGAR 13F; SEC 13F data sets [u] | 1999+ text, 2013+ XML [u] | 45-day reporting lag, so lag the data to the filing date. Confidential-treatment amendments arrive late. |
| 13D activism | EDGAR full-text search | 2001+ [u] | Filing deadline was cut from 10 to 5 business days in 2024 [u]. |
| XBRL fundamentals | `companyfacts`/`frames` | 2009+ [u] | `frames` gives the latest restated value, which is a look-ahead risk. Use the `filed` field to rebuild point-in-time values. |
| Short-sale volume ratio | FINRA daily files | Aug 2018+ in catalog | Covers off-exchange (TRF/ADF/ORF) volume only, not total market volume. Market-maker hedging inflates "short" volume. Split it into liquidity-supplying vs demanding parts where possible (Stealthy Shorts). |
| Short interest (bi-monthly) | FINRA equity short interest [u] | Varies [u] | About a 1-week publication lag. Align to the publication date, not the settlement date. |
| News sentiment | GDELT 2.0 (15-min updates, 2015+ [u]); free RSS; LLM/FinBERT via `transformers` | GDELT 2015+ [u] | GDELT has poor ticker mapping. RSS has no history, so start archiving now. Use post-cutoff-only evaluation to avoid LLM look-ahead (Lopez-Lira; Kirtac 2026). |
| Attention | `pytrends` (unofficial, rate-limited) [u]; Wikimedia Pageviews REST API (Jul 2015+) [u] | 2004+ Trends, 2015+ pageviews [u] | Trends values are rescaled per request and resampled. Page titles change. Article views include bots, so use the `user` agent filter [u]. |
| Reddit | Official API (free tier with rate limits since 2023 pricing change) [u]; Pushshift no longer publicly available [u] | Limited historical [u] | Signal concentrated in meme stocks (Oxford; arXiv 2507.22922). |
| Options (IV skew, P/C, IV spread) | `yfinance` option chains, current snapshot only [u]; CBOE daily aggregate P/C [u] | None free historically [u] | Build your own panel by snapshotting daily. Historical data (OptionMetrics, ORATS, CBOE DataShop) is paid [u]. |

### Inferences
- With only free data, the most credible project is a monthly or quarterly EDGAR-text strategy: Lazy Prices similarity, optionally with LLM embeddings, combined with insider purchases and short-volume ratios. These need no paid data and trade slowly.
- Signals from news, social media and options require forward data collection: archive RSS, Reddit and yfinance chains daily now, to get 1-3 years of your own history later.

### Gaps
- Exact current SEC rate limits, Reddit API tiers, and Wikimedia/GDELT history start dates were not re-verified (budget); check the official docs.
- Whether FINRA still serves pre-2018 daily files publicly was not confirmed. The catalog page points to FINRA Support.

## Q3. How are LLMs used to turn text into signals in 2024-2026 papers, and how big is the alpha after costs?

### Takeaway
There are three patterns.
- **Prompt scoring:** ask GPT-class models whether a headline is good, bad or unknown for the stock. This is Lopez-Lira & Tang.
- **Embeddings plus a supervised return head:** OPT, LLaMA or FinBERT embeddings feed a regression or classifier for next-day return. This is Kirtac & Germano and Chen-Kelly-Xiu.
- **LLM as a conditioner on classical factors:** news-filtered momentum, or embeddings propagated over a supply-chain graph.

Reported net Sharpe ratios run from about 0.9 (monthly embedding factor) to 3+ (daily news long-short with 5-10 bp costs). Daily news alpha is decaying with adoption.

### Cited Findings
- **Prompt scoring.** Headline score is +1 for good, -1 for bad, 0 for unknown. The signal is the daily mean per firm, used for next-day long-short. It predicts the drift beyond the initial move, mainly in small caps and negative news, and returns decline with adoption. — [Lopez-Lira & Tang v5/v6](https://arxiv.org/abs/2304.07619v5)
- **Embeddings plus a classifier.** OPT, BERT and FinBERT embeddings are trained on returns. OPT long-short Sharpe is 3.05 after 10 bp costs over Aug 2021-Jul 2023, and the LM dictionary does far worse. — [Kirtac & Germano](https://arxiv.org/pdf/2412.19245)
- **Decoder versus encoder.** Decoder LLMs (LLaMA-3) beat encoders and dictionaries net of 5 bp costs with a 10% ADV cap. The design evaluates only news after each model's data-freshness date, to avoid memorisation look-ahead, and checks probability calibration. — [Kirtac 2026](https://arxiv.org/abs/2609.23703)
- **Multilingual embeddings.** Contextual embeddings in 16 markets and 13 languages beat technical signals and simpler NLP. — [Kelly slides](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2024/09/Kelly-WhartonJL.pdf); [Sydney listing](https://business.sydney.edu.au/events/research/2024/finance/dacheng-xiu)
- **China evidence.** "Large Language Models and Return Prediction in China" was discussed at ABFER 2024. — [ABFER discussion slides](https://abfer.org/media/abfer-events-2024/cmd/Large-Language-Models-and-Return-Prediction-in-China_slides_discuss_YinanSu.pdf)
- **Graph-propagated embeddings.** FinBERT MD&A embeddings over a supply-chain graph give Sharpe 0.86 and FF5 alpha of 7.27% per year. — [arXiv 2606.29290](https://arxiv.org/abs/2606.29290)
- **LLM-conditioned momentum.** It beats plain momentum in true out-of-sample tests and is robust to costs. — [arXiv 2510.26228](https://arxiv.org/html/2510.26228v1)
- **Earnings calls.** LLM importance-weighted sentiment earns 6.4% per year long-short; lexicon signals are weakening. — [S&P Global 2025](https://www.spglobal.com/market-intelligence/en/news-insights/research/2025/09/familiar-signal-new-context-from-lexicon-to-llm-the-evolution-of-earnings-call-nlp)
- **Earnings-call agents.** MarketSenseAI 2.0 (an LLM agent over filings, call transcripts and numbers) reports 8.0-18.9% alpha on S&P 100/500. This is an agent backtest, so treat it with caution. — [alphaxiv 2502.00415](https://alphaxiv.org/overview/2502.00415v2)
- **Transcript models.** ECC Analyzer (arXiv 2404.18470) uses LLMs on earnings calls for volatility, VaR and returns. STRUX uses 11,950 Motley Fool transcripts (2017-2024) for 30-day decisions. — [arXiv 2404.18470](https://arxiv.org/html/2404.18470v1); [arXiv 2410.12583](https://arxiv.org/pdf/2410.12583)
- **Reddit.** Sentiment from GPT-annotated r/WSB data is weakly related to GME/AMC prices, and volume and attention metrics work better. — [arXiv 2507.22922](https://arxiv.org/pdf/2507.22922)
- **WSB more generally.** The forum gives little to no signal outside meme stocks (Oxford study). — [ORA Oxford](https://ora.ox.ac.uk/objects/uuid:6f3c53d3-f0d6-4232-b3cf-bf1696b200f9/files/dsf268587w)

### Inferences
- For an individual, a FinBERT or open-weight LLM (LLaMA-class) running locally on free text (EDGAR, RSS archives, GDELT) is feasible. Paid GPT-4-class APIs on millions of headlines can cost hundreds to thousands of dollars [unverified estimate].
- **Look-ahead bias:** an LLM may have memorised post-event outcomes. Valid tests use only text dated after the model's training cutoff, which limits backtest length to roughly 1-2 years for current models.
- **Point-in-time timestamps:** news must be aligned to its publication timestamp versus the market close. A headline after 16:00 trades at the next open.

### Gaps
- No standardised net-of-cost alpha comparison across LLM papers. Cost assumptions vary (5-10 bp) and several report gross figures only.
- Japan and Europe LLM-text evidence was not gathered, beyond the multi-market Chen-Kelly-Xiu work.

## Q4. Any evidence for alt-data-conditioned statistical arbitrage (news-driven pairs, attention-based residual reversal)?

### Takeaway
Direct evidence is thin. No 2023-2026 paper turned up that explicitly builds news-conditioned pairs or attention-conditioned residual reversal with published net results. The closest are LLM or time-series-foundation-model long-short books and network propagation (supply chain) of text signals.

### Cited Findings
- Valeyre & Aboura (arXiv 2412.09394): the Chronos time-series foundation model is used for a US single-stock long/short stat-arb portfolio. It runs on price series, not text. — [RePEc](https://ideas.repec.org/p/arx/papers/2412.09394.html)
- A Swiss bachelor's thesis uses LLMs for anomaly detection on pair spreads. Student work, used here only as a lead. — [OST](https://orix.ost.ch/bitstreams/63969afe-2069-4369-aa34-adff19b1f23b/download)
- arXiv 2603.19286 (Mar 2026) encodes news with a pre-trained LLM and filters it by stock relevance for prediction. Not framed as pairs trading. — [EconPapers](https://econpapers.repec.org/paper/arxpapers/2603.19286.htm)
- Supply-chain propagation of text signals (customer to supplier) is a lead-lag cross-asset mechanism related to pairs logic. — [arXiv 2606.29290](https://arxiv.org/abs/2606.29290)
- An IAQF seminar covered newswire information being priced in with a delay, which is relevant to news-triggered spread trades. — [IAQF](https://iaqf.org/event-5627652)

### Inferences
- A plausible research design for an individual, untested here:
  1. Use residual reversal: either PCA/ETF-residual stat arb (Avellaneda-Lee style [unverified this session]) or the attention-factor stat-arb models already in the folder (Epstein-Pelger 2025).
  2. Condition entries on whether a residual move came with firm-specific news, using GDELT or RSS plus FinBERT.
  3. Fade no-news moves (liquidity shocks, which tend to revert). Avoid fading, or follow, news-driven moves (information, which tends to drift; consistent with the Lopez-Lira drift findings).
  4. Pageviews or Trends spikes can serve as a "noise-attention" flag that strengthens reversal.

  This is an inference from combining sources and is not documented here.

### Gaps
- No peer-reviewed 2023-2026 study of news-conditioned pairs or attention-conditioned residual reversal with net-of-cost results was found. Classic background [unverified this session]: Chan (2003) found news-driven drift versus no-news reversal, and Da-Engelberg-Gao found attention-induced reversal.
