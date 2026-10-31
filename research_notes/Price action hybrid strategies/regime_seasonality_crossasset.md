# Hybrid Price-Action Strategies: Regime, Breadth, Seasonality, Cross-Asset and Ensembles (US stocks/ETFs)

Scope note: research round of ~17 tool calls (Oct 2026). Many headline numbers in this area sit in table images or paywalled PDFs and could not be extracted. Where that happened it is listed under Gaps. Rule specifications marked "UNVERIFIED (from prior knowledge)" were not confirmed by a source fetched in this round and need checking against the primary paper before coding.

## Q1. Regime/trend filters: does conditioning on trend (SMA200, 10-month SMA, dual SMA), market-state models (HMM, jump models) or drawdown state improve risk-adjusted returns?

### Takeaway
The best-documented out-of-sample result is the statistical jump model (JM) regime filter on the S&P 500 (1990-2023, with 10 bps costs and a one-day delay). It raised Sharpe from 0.48 to 0.68 and cut max drawdown from -55% to -27%, beating an HMM filter. Trend-filtered RSI mean reversion (EMA50 > EMA200) has a >80% win rate with about 30% exposure, but its exact CAR/DD numbers sit in images. No source fetched this round gives a clean head-to-head of "MR with vs. without a regime filter" on 2020-2026 data, so that test has to be run.

### Cited Findings
- **Statistical Jump Model (Shu, Yu, Mulvey; arXiv 2402.05272, published in Journal of Asset Management, DOI 10.1057/s41260-024-00376-x).** Exact spec — [arXiv HTML v3](https://arxiv.org/html/2402.05272v3):
  - Features, all computed only from the index's own returns: EWM downside deviation (halflife 10 days), and EWM Sortino ratio (halflives 20 and 60 days).
  - Two-state JM with a jump penalty λ. λ is re-chosen monthly by time-series CV: pick the λ whose 0/1 strategy has the best Sharpe over a trailing 8-year validation window. λ=50 is used for illustration, and Table 3 tests 0, 5, 15, 35, 70 and 150.
  - Training window 3,000 days (about 12 years). JM is refit every 6 months; the HMM benchmark is refit daily.
  - The regime signal updates daily. The signal at the close of day t is applied from day t+2 (one-day delay). Costs are 10 bps one-way.
  - Strategy "0/1": 100% in the index in the bull regime, 0% (risk-free) in the bear regime.
  - S&P 500 out-of-sample results, 1990-2023 (data from 1970):

    | | B&H | HMM 0/1 | JM 0/1 |
    |---|---|---|---|
    | CAGR | 10.2% | 8.5% | 11.2% |
    | Vol | 18.2% | 11.3% | 13.1% |
    | Sharpe | 0.48 | 0.54 | 0.68 |
    | MaxDD | -55.2% | -28.9% | -26.6% |

    Source: [arXiv HTML v3](https://arxiv.org/html/2402.05272v3). The paper also covers DAX and Nikkei, with the same qualitative result: lower vol and DD and a higher Sharpe than both HMM and B&H — [arXiv abs](https://arxiv.org/abs/2402.05272v3).
  - The authors say the same method could be applied to strategy return series such as trend following — [search summary of arXiv 2402.05272](https://arxiv.org/abs/2402.05272v3).
- **Follow-on JM work:**
  - Shu & Mulvey (arXiv 2410.14841, Oct 2024) use a sparse jump model to identify bull/bear regimes per factor, feeding Black-Litterman factor allocation — [arXiv 2410.14841](https://web3.arxiv.org/pdf/2410.14841).
  - Aydinhan, Kolm, Mulvey & Shu ("continuous" JM, Annals of OR, DOI 10.1007/s10479-024-06035-z) replace the discrete state with a probability vector to get smoother transitions — [SSRN 4556048](https://papers.ssrn.com/abstract=4556048).
- **Trend-filtered RSI mean reversion on SPY (Arthur Hill, StockCharts, Oct 2016, tested in Amibroker with Cesar Alvarez):**
  - Rules: long only. Trade only when EMA(50) > EMA(200). Buy when RSI(5) or RSI(10) drops below 30; sell when RSI rises above 70. No stop; trailing stops were tested and lowered returns while raising DD.
  - Results: CAR "over 7%", about 30% exposure, risk-adjusted return about 25.5%, win rate >80%. MaxDD was much lower for RSI(5). The exact CAR, DD, trade counts and test dates are in an image and not extractable.
  - Source: [StockCharts / Arthur Hill](https://articles.stockcharts.com/article/articles-arthurhill-2016-10-using-breadth-for-trading-bias-and-overboughtoversold-setups---a-mean-reversion-system-for-spy-/)
- A TradingView breadth script argues that naive breadth mean-reversion loses money in bull markets and adds a regime filter, so that long signals fire only in "Bear/Oversold" regimes. This is a community script with no verified stats — [TradingView script](https://www.tradingview.com/script/vYcHWuTY/).

### Inferences
- The JM's gain over B&H (Sharpe +0.20, DD halved) comes mostly from sidestepping crash regimes. Its CAGR is only 1 pt higher. That points to the JM as the best overlay on a long-biased MR or trend book: gate MR entries, or scale exposure, by JM state. It is the most promising "market-state" candidate here because it is out-of-sample, cost-inclusive, delay-inclusive and code-able with yfinance SPY data alone. Open-source `jumpmodels` Python implementations exist from the same authors, but that was not verified this round.
- The JM's validation-window λ selection is itself a tuning step. Keep it walk-forward exactly as specified, or results become in-sample.
- In the Hill/Alvarez system, a long-term trend filter on short-term MR mainly cuts DD and exposure, not CAR. That matches the prior round's finding that "trend filters cut drawdowns."

### Gaps
- No source fetched gives a direct A/B of RSI(2)/IBS with vs. without an SMA200, 10-month SMA or dual-SMA filter on 2020-2026 SPY/QQQ data.
  - The canonical Connors rule (RSI(2) < 10 with close > SMA200, exit when close > SMA5) is UNVERIFIED (from prior knowledge) for this round. Run that test locally.
- No source found for drawdown-state conditioning, e.g. "MR only when SPY is more than X% below its 52-week high". This needs an original test.
- HMM results beyond the JM paper's benchmark (e.g. 2- or 3-state Gaussian HMM on SPY returns) were not found with numbers.

## Q2. Breadth filters: % of sectors/stocks above 200-day MA, advance-decline, new highs-new lows

### Takeaway
Breadth thresholds in common use are >60% bullish and <40% bearish for % of stocks above the 200-day average, and <30% for % above the 20-day as short-term oversold. However, no fetched source reports a rigorous backtest with numbers for breadth as a filter on SPY mean reversion. Breadth filters built from 11 sector SPDRs are therefore an original-research item.

### Cited Findings
- Hill/Alvarez breadth framework (discretionary context only, not part of the backtest):
  - % of stocks above EMA(200) above 60% = bullish bias; below 40% = bearish bias.
  - % above EMA(20) below 30 = short-term oversold, with a move back above 40 as a possible upturn signal.
  - % above EMA(50) is a medium-term check.
  - Source: [StockCharts / Arthur Hill](https://articles.stockcharts.com/article/articles-arthurhill-2016-10-using-breadth-for-trading-bias-and-overboughtoversold-setups---a-mean-reversion-system-for-spy-/)
- Generic thresholds: >75% of stocks above an MA = overbought, <25% = oversold. LuxAlgo notes there is no universal line for the 200-day — [LuxAlgo](https://www.luxalgo.com/library/concept/percent-stocks-above-20-50-200-day-ma/).
- DAA's canary rule is itself a cross-asset breadth filter: it counts how many canary assets have negative momentum (see Q4) — [CXO Advisory](https://www.cxoadvisory.com/strategic-allocation/multi-class-momentum-portfolio-with-canary-crash-protection/).

### Inferences
- A sector-ETF breadth proxy is implementable with yfinance: `breadth_t = (# of 11 sector SPDRs with close > SMA200) / 11`. Note that XLC starts in 2018 and XLRE in 2015, so use 9 sectors (XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY) for history from Dec 1998.
- A Hill-style "trade only when breadth ≥ 60%" rule is a bias filter, analogous to SMA200, and likely correlated with it. Its incremental value over SPY > SMA200 is the thing to test.
- With only 9-11 sector names, breadth is coarse (steps of 9-11%). Stock-level breadth from a current S&P 500 list is survivorship-biased.

### Gaps
- No quantitative backtest found for:
  - an advance-decline line or new highs-new lows filter on SPY MR or trend;
  - Zweig breadth thrust;
  - % of sectors above SMA200 as a filter.
- Free A/D and NH-NL history is not on yfinance. FRED does not carry it either (not verified).

## Q3. Seasonality: TOM, pre-holiday, FOMC drift, Halloween, OpEx, end-of-quarter, and combinations with price action

### Takeaway
Pre-FOMC drift survives in recent data (SPY 1993-2024 Sharpe of about 0.5-0.6 with only about 5% of days invested), but it is weaker and contested after 2015. The TOM effect has decayed sharply:
- the narrow [0:+3] window is largely gone in US ETFs;
- the [-3:+3] window still shows about 5-12 bps/day of excess return but has a downtrend.

Halloween/sell-in-May held out-of-sample through 2011. Standalone seasonal books reduce DD but lower CAGR versus B&H, so they are best used as filters or overlays (e.g. RSI(2) only in the TOM window), not as standalone books. No published test of such a combo with numbers was found.

### Cited Findings
- **Pre-FOMC drift (Quantseeker replication):**
  - Rules: buy SPY at the close the day before a scheduled FOMC announcement day (for 2-day meetings, the day before the first meeting day) and sell at the close of the final meeting day. Hold T-bills otherwise (FRED DTB3). Costs 5 bps one-way. Only scheduled meetings count.
  - Sample: SPY Jan 1993-Dec 2024.
  - Results:
    - SPY: CAGR about 4%, Sharpe about 0.5-0.6, invested about 5% of days.
    - SPXL/TQQQ: CAGR 8-9%, after-cost Sharpe about 0.6, MaxDD about 18%.
  - Robustness: flat 2016-2019, recovered later. The effect looks stronger when VIX is high (chart only). The results are in-sample.
  - Source: [Quantseeker](https://www.quantseeker.com/p/trading-the-fed-the-pre-fomc-drift)
- **Post-2015 decay:**
  - Kurov, Wolfe & Gilbert find the pre-FOMC drift "essentially disappeared" after 2015 for both press-conference and non-press-conference meetings — [Kurov et al.](https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf); [IDEAS (Finance Research Letters 2021)](https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html).
  - Contradicting this, Ben Dor & Rosa (2019) find no change after 2015 (as cited by Kurov et al.).
  - Lucca & Moench (2018 note, second-hand) say the drift is now concentrated in press-conference meetings — [Quantseeker](https://www.quantseeker.com/p/trading-the-fed-the-pre-fomc-drift).
  - Since 2019 every FOMC meeting has a press conference, which partly reconciles the two views (inference).
- **Turn of the month (Quantseeker, ETF data via EODHD):**
  - Windows in the literature:
    - Ariel (1987): 9 days, from the last trading day of the month through eight days later;
    - Lakonishok-Smidt (1988): [0:+3];
    - Etula et al. (2020): [-3:+3].
  - Chen et al. (2015): TOM-window daily returns averaged 15-20 bps vs. about 0 otherwise (iShares country ETFs, 1996-2012).
  - Blog results:
    - [0:+3] is not significant for US ETFs (SPY, QQQ, IWM, sectors); QQQ's strong early-2000s effect has faded to about zero.
    - [-3:+3] still shows significant excess returns of about 5-12 bps/day for most equity ETFs. Among non-equities only HYG shows it.
  - Strategy test: long from the close of day 0-4 to the close of day 0+3, with 5 bps costs.
    - US: lower CAGR than B&H, comparable or lower Sharpe, reduced drawdowns, better skew.
    - Decay: the [-3:+3] effect "declined substantially" over the past decade.
  - Source: [Quantseeker TOM](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)
- CXO Advisory tested a TOM window of -5 to +4 trading days on dividend-adjusted SPY (Jan 1993-Jan 2024) against B&H and against a 200-day SMA filter. The results were not extractable — [CXO calendar effects](https://cxoadvisory.com/calendar-effects/page/3).
- **Halloween / sell in May:**
  - Bouman & Jacobsen (2002): Nov-Apr returns are significantly higher than May-Oct in 36 of 37 countries.
  - Jacobsen & Zhang ("everywhere and all the time", 108 markets): the effect held out-of-sample in all 37 original countries over Sep 1998-Apr 2011.
  - Andrade, Chhaochharia & Fuerst (FAJ 2013): about 14 more years of data, and the effect held.
  - Doeswijk & van Vliet (2011): the sell-in-May sector rotation kept working after publication, while valuation and monetary signals did not.
  - Sources: [Jacobsen & Zhang PDF](https://www.bnains.org/backtest/periode/The_Halloween_Indicator_everywhere_and_all_the_time_-_Ben_Jacobsen_%26_Cherry_Y._Zhang.pdf); [search summary incl. Andrade et al.](https://blogs.cfainstitute.org/?p=7086); [Quantpedia on decay](https://quantpedia.com/in-sample-vs-out-of-sample-analysis-of-trading-strategies/)
- **TOM + RSI(2) combo ("Turn of the Month Strategy on Steroids", TradingView):** buy when the day of the month is ≥ 25 (default); exit when RSI(2) > 65. This is a community script with unvalidated stats — [TradingView](https://jp.tradingview.com/script/fknZA6qS-Turn-of-the-Month-Strategy-on-Steroids).

### Inferences
- Seasonal books are low-exposure (FOMC about 5%, TOM [-3:+3] about 33%), so they combine well with other books. The FOMC book is nearly uncorrelated with other books by construction. As a standalone book with about 4% CAGR its value is in a combined portfolio or with leverage (the 3x ETF result).
- The most promising seasonal+price-action hybrids to test:
  - (a) RSI(2)/IBS entries allowed only in TOM [-3:+3] or pre-FOMC windows, or given double size there;
  - (b) seasonal windows gated by SPY > SMA200;
  - (c) Halloween: hold equities Nov-Apr and, in May-Oct, only when trend and JM are bullish.
- The day-of-week, pre-holiday, OpEx-week and end-of-quarter effects were not evaluated with 2015-2026 evidence this round. Treat them as weak priors until tested.

### Gaps
- No numeric pre-holiday, OpEx-week, end-of-quarter or day-of-week results for 2015-2026 were retrieved.
- No published, numerically reported backtest of RSI(2)-in-TOM-window was found.
- The exact CXO TOM-plus-SMA200 numbers were not extractable.
- Lucca & Moench's 2018 Liberty Street note was not opened directly.

## Q4. Cross-asset/macro: canary assets (DAA, BAA), credit spread, dollar, gold/copper, curve, TSMOM

### Takeaway
Keller & Keuning's canary approach is the most-replicated cross-asset risk-on/off signal for ETFs, but the exact reported CAGR/DD figures were not extractable in this round.
- DAA: a VWO/BND canary with breadth B=2.
- BAA: introduced mid-2022 with an SPY/EEM/EFA/AGG canary.

Independent replications flag lower performance than the paper (BAA) and a sensitivity to total-return data and the choice of cash asset. Credit-spread, gold/copper and curve filters had no quantitative evidence retrieved.

### Cited Findings
- **Defensive Asset Allocation (Keller & Keuning, July 2018, "Breadth Momentum and the Canary Universe"):**
  - Canary = VWO and BND, breadth threshold B = 2.
  - Let b = number of canary assets with negative momentum. If b ≥ B, hold 100% in the cash universe; otherwise the cash fraction is b/B, rounded to 1/T.
  - The cash universe holds the best of SHY, IEF or LQD.
  - Risky universes tested: G12, G4 (SPY, VEA, VWO, BND), U6 and U15.
  - VAA's momentum score is the average annualized return over 1, 3, 6 and 12 months.
  - Periods: canary chosen on 1926-1970, optimization 1971-1993, OOS 1994-Mar 2018.
  - Results: DAA beat VAA on CAGR in 3 of 4 universes but had worse MaxDD in all 4. CXO cautions that parameters were optimized in-sample and the period is short.
  - Source: [CXO Advisory](https://www.cxoadvisory.com/strategic-allocation/multi-class-momentum-portfolio-with-canary-crash-protection/)
  - A secondary source cites DAA MaxDD of about -16.6% vs. -50.8% for the S&P 500 and -29.5% for 60/40 (period unverified) — [Substack (ES)](https://yagogarcia.substack.com/p/estrategia-daa-la-proteccion-efectiva).
- **Bold Asset Allocation (Keller, SSRN 4166845, mid-2022):**
  - Structure: offensive universe of 12 ETFs (G12) or 4 (G4); a defensive universe of bonds and commodities; a canary universe that switches between the two; monthly rebalance; up to 9 ETFs held — [TuringTrader](https://turingtrader-com.web.app/portfolios/keller-bold-asset-allocation).
  - TuringTrader: higher returns than 60/40 with reduced DD, but it trailed its benchmark in most years — [TuringTrader](https://turingtrader-com.web.app/portfolios/keller-bold-asset-allocation).
  - QuantConnect replications:
    - results were worse than the paper's, attributed partly to fill timing (next-day open vs. month-end close);
    - momentum must use total-return (dividend-adjusted) prices;
    - adding IEF to the safe universe, not BIL only, mattered (e.g. COVID 2020).
    - One unverified user backtest: CAGR about 32.8%, DD 36.5%.
    - Source: [QuantConnect forum](https://www.quantconnect.com/forum/discussion/14190/bold-asset-allocation-baa-keller/)
  - Hybrid Asset Allocation is a further Keller variant — [QuantConnect HAA thread](https://www.quantconnect.com/forum/discussion/14842/hybrid-asset-allocation/).
- An Allocate Smartly-attributed Feb 2026 TAA attribution piece says recent TAA outperformance came mostly from greater exposure to international equities, commodities and gold — [pulse.bot summary](https://www.pulse.bot/stock-trading/news/why-taa-is-performing-well-now-outperformance-attribution-e6a9a396-10e3-4333-a41c-9ee43923f9cb/).

### Inferences
- Exact BAA rules are UNVERIFIED (from prior knowledge) and must be confirmed in SSRN 4166845:
  - Canary: SPY, EEM, EFA, AGG. Go defensive if any canary has 13612W momentum ≤ 0.
  - 13612W = (12·r1m + 4·r3m + 2·r6m + r12m) / 4.
  - Offensive assets are ranked by relative momentum = price / SMA(13 month-end closes) − 1. The top 6 are held in G12; in the "aggressive" G4 variant (QQQ, EEM, EFA, AGG) the top 1 is held.
  - Defensive: top 3 of TIP, DBC, BIL, IEF, TLT, LQD, AGG by the same relative momentum; any asset ranking below BIL is replaced by BIL.
- All canary-based assets (VWO, EEM, EFA, AGG, BND, TIP, DBC, IEF, LQD, SHY, BIL) are on yfinance. Pre-2007 history needs index proxies. With ETF-only data, the backtest starts about 2007-2008, so most of the sample is post-GFC.
- Canary rules are binary, monthly and trigger-happy (VWO/EEM go negative often). Their documented trade-off is lower DD at the cost of whipsaw and trailing in bull years, which matches the TuringTrader comment.

### Gaps
- No numeric evidence retrieved for:
  - HYG/LQD or HYG/IEF credit-ratio filters;
  - UUP dollar filters;
  - gold/copper ratio;
  - yield-curve (^TNX − ^IRX, or FRED T10Y3M) filters;
  - VIX term structure (VIX/VIX3M);
  - intermarket divergence.
- TSMOM-across-ETFs numbers (Moskowitz-Ooi-Pedersen, AQR "Century of Evidence") were not fetched this round.
- Exact DAA/BAA paper CAGR, MaxDD and Sharpe tables were not extracted (paper PDFs not fetched).

## Q5. Multi-strategy ensembles: MR + trend + seasonality books, risk parity, vol targeting

### Takeaway
The evidence consistently shows that combining low-correlation trend and mean-reversion streams raises Sharpe, mainly by cutting volatility. One example: a 50/50 trend + SPY-MR blend had a Sharpe of 0.91 vs. 0.65 for each alone. Evidence quality is mostly blog and backtest level, not peer-reviewed for ETF price-action books.

### Cited Findings
- **Price Action Lab:** a 50/50 blend of a futures trend-following system and a long-only SPY mean-reversion system. Sharpe 0.91 vs. 0.65 for each alone; vol 12.4% vs. 19.2% (trend) and 15.2% (MR). The gain is attributed to low correlation. It is a single backtest — [Price Action Lab](https://priceactionlab.com/Blog/?p=67828).
- **Choi, Jeong & Park (2017), via CXO:** trend following combined with covered calls (a short-vol/reversion-type stream) across asset classes gave a Sharpe of 0.86 vs. 0.66 for equal risk contribution (2007-2016). Costs were omitted — [CXO](https://cxoadvisory.com/momentum-investing/trend-following-and-covered-calls-in-combination).
- **Baltas (2015), via CXO:** risk-parity-weighted long/short trend across 35 futures, gross Sharpe 1.48 (1987-2013) — [CXO](https://www.cxoadvisory.com/volatility-effects/combining-trend-following-and-risk-parity-across-asset-classes).
- **Substack (synthetic SPY/TLT/GLD core):** adding a trend program lifted a 1.1-Sharpe core to about 1.5, with the benefit thinning in recent years — [Beyond Passive](https://beyondpassive.substack.com/p/what-trend-following-actually-adds).
- **"The Science and Practice of Trend-Following Systems"** (arXiv 2607.19497, 2026) is a recent survey; its content was not reviewed — [arXiv](https://arxiv.org/pdf/2607.19497).

### Inferences
- Suggested portfolio construction for the user's books, built on these sources plus standard practice:
  1. **Books:**
     - (A) SPY/QQQ RSI(2)/IBS MR gated by SMA200 or JM;
     - (B) JM or 10-month-SMA trend on SPY/QQQ;
     - (C) DAA/BAA canary cross-asset rotation (monthly);
     - (D) seasonal book: pre-FOMC plus TOM [-3:+3], with T-bills otherwise.
  2. **Weighting:** size each book to equal ex-ante vol (inverse 60-day realized vol of the book's own returns, or equal risk contribution using a 1-year covariance).
  3. **Vol targeting:** scale the combined book to a 10-12% vol target, capped at 1.0-1.5x gross.
  4. **Netting:** net overlapping SPY positions across books before trading to save costs.
- MR and seasonal books have low exposure, so they need an explicit cash yield (T-bills) in backtests. Otherwise their Sharpe and CAGR are misstated.

### Gaps
- No peer-reviewed study was found that combines specifically ETF RSI(2)-MR + trend + seasonality books with reported out-of-sample numbers.
- No evidence was retrieved on how much vol targeting adds on top of the ensemble for these books.

## Q6. Robustness post publication (Allocate Smartly tracking) vs. overfit

### Takeaway
On general evidence, expect a one-third to one-half Sharpe haircut out-of-sample.
- Sell-in-May and momentum signals survived publication.
- TOM [0:3] and the post-2015 pre-FOMC drift weakened.
- Dual momentum deteriorated after publication.
- BAA replications underperform the paper.

Allocate Smartly's own post-publication tracking numbers were not accessible.

### Cited Findings
- Quantpedia, 671 replicated strategies: out-of-sample Sharpe is about 33% lower on average and 44% lower at the median — [Quantpedia](https://quantpedia.com/in-sample-vs-out-of-sample-analysis-of-trading-strategies/).
- McLean & Pontiff (as summarized): returns are 26% lower out-of-sample and 58% lower in the five years after publication — [Quantpedia](https://quantpedia.com/in-sample-vs-out-of-sample-analysis-of-trading-strategies/).
- Falck, Rej & Thesmar (2021): publication date is the main predictor of decay, driven by crowding and multiple testing — [arXiv 2105.01380](https://arxiv.org/pdf/2105.01380).
- Price Action Lab: a 2013-published dual-momentum-type TAA deteriorated significantly after publication (selection bias plus regime change) — [Price Action Lab](https://priceactionlab.com/Blog/?p=68274).
- Doeswijk & van Vliet (2011): momentum and sell-in-May sector signals survived out-of-sample, while valuation and monetary-policy signals did not. Average decay was about one-third — [search summary](https://quantpedia.com/in-sample-vs-out-of-sample-analysis-of-trading-strategies/).
- TOM [0:3] has largely decayed in US ETFs, and pre-FOMC was flat 2016-2019 — [Quantseeker TOM](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they); [Quantseeker FOMC](https://www.quantseeker.com/p/trading-the-fed-the-pre-fomc-drift).
- JM regime filter: genuinely out-of-sample (rolling refit, CV-chosen λ), costs and delay included, 1990-2023 — [arXiv HTML](https://arxiv.org/html/2402.05272v3).

### Inferences
- Robustness ranking (judgement based on the cited evidence):
  - **Most robust:** simple trend/regime filters (JM; SMA-type), Halloween, and canary-style crash protection. They reduce DD more reliably than they add return.
  - **Medium:** pre-FOMC (alive but episodic) and TOM [-3:+3] (decaying).
  - **Most fragile:** narrow TOM [0:3], plus heavily parameterized TAA variants (BAA top-N and universe choices; DAA B and T choices were optimized in-sample).
- For any rule from the catalogue, the backtest should report:
  - pre-2015 vs. 2015-2026 split;
  - next-open fills vs. same-close fills;
  - total-return data;
  - 5-10 bps costs.

### Gaps
- Allocate Smartly's per-strategy post-publication tracking (BAA, DAA, VAA, GEM) could not be retrieved, since the site is subscription-based and no public excerpt was found.
- No 2020-2026 live or out-of-sample statistics were found for DAA or BAA.
