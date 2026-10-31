# Additional Pure Price-Action Strategies for US Stocks/ETFs (Round 2: intraday, swing, positional)

Scope note: about 16 search and fetch calls. Several primary PDFs (SSRN) were not fetched in full, so some numbers come from abstracts, author or firm pages, or aggregators, and each one is labelled that way. Rule specifications I could not verify from a source this round are in the Gaps sections and marked "unverified spec". Treat them as hypotheses to code and test, not as cited facts.

## Intraday (1-min/5-min): which other rules have evidence?

### Takeaway
The best-documented new intraday candidates are (1) the 5-minute ORB on "Stocks in Play" ranked by opening relative volume (Zarattini, Barbon & Aziz 2024; Sharpe 2.81 net, 2016-2023), (2) the VWAP trend rule on QQQ (Zarattini & Aziz 2023; Sharpe 2.1, max DD 9.4%, 2018-2023), and (3) the overnight-vs-intraday split (hold close to open), which persists in SPY through 2024 but has no cost-adjusted tradability evidence. All three come from the authors' own backtests or blog-level checks. Independent replications are mixed: the Stocks-in-Play ORB was reproduced on QuantConnect, while an index-level ORB replication found gross reproduced and net zero. Last-half-hour intraday momentum (already tested) shows evidence of decay.

### Cited Findings

**A. ORB on Stocks in Play (Zarattini, Barbon & Aziz, "A Profitable Day Trading Strategy For The U.S. Equity Market", SFI RP 24-98, SSRN 4729284, Feb 2024; earlier version Zarattini & Aziz, "Can Day Trading Really Be Profitable?", SSRN 4416622, Apr 2023)**
- Universe: more than 7,000 US stocks, 2016-2023. Trading is limited to "Stocks in Play", stocks with unusually high activity that day, usually because of company news — [IDEAS/RePEc abstract](https://ideas.repec.org/p/chf/rpseri/rp2498.html)
- Daily filters: open > $5, 14-day average daily volume >= 1,000,000 shares, 14-day ATR > $0.50. Relative Volume (volume in the opening-range interval divided by the 14-day average for the same interval) must be >= 100%, and only the top 20 stocks by Relative Volume are traded — [CXO Advisory summary](https://www.cxoadvisory.com/?p=45379)
- Entry: the opening range is the first 5 minutes. If the first 5-minute bar is up, place a buy-stop at the OR high. If it is down, place a sell-stop at the OR low (the direction follows the sign of the first 5-minute bar). The entry triggers when price trades through that level after minute 5 — [CXO Advisory](https://www.cxoadvisory.com/?p=45379)
- Stop: 10% of the 14-day ATR from the fill price. Exit at the close if the stop is not hit. Sizing: risk 1% of capital per trade at the stop, leverage capped at 4x. Starting capital $25k. Commissions $0.0035/share (IBKR Pro Tiered) — [CXO Advisory](https://www.cxoadvisory.com/?p=45379)
- Results (top-20 portfolio): total net return over 1,600%, Sharpe 2.81, annualized alpha 36%, against 198% for passive S&P 500 exposure over the same period. The paper also compares 15-, 30- and 60-minute ORBs — [IDEAS/RePEc](https://ideas.repec.org/p/chf/rpseri/rp2498.html)
- One summary reports the 15-minute ORB on Stocks in Play at 272% total return and Sharpe 1.43, so the 5-minute window is materially better (aggregator figure, not verified in the PDF) — [search summary of SSRN/Scribd 4416622](https://www.scribd.com/document/711773899/SSRN-id4416622)
- Independent replication: a QuantConnect/LEAN recreation reports Sharpe of about 2.40 and beta of -0.04, against SPY buy-and-hold Sharpe of about 0.84 — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/18444/Opening+Range+Breakout+for+Stocks+in+Play/p4/comment-50717)
- Contrary replication: an ORB replication on index CFDs (NQ, SPX, Dow, DAX, FTSE, Jan 2015 - Jun 2026) found "gross reproduced, net zero". This means the edge on broad indices is consumed by costs, which fits the paper's claim that the edge sits in Stocks in Play — [MQL5 blog](https://www.mql5.com/en/blogs/post/776235)

**B. VWAP trend (Zarattini & Aziz, "Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems", SSRN 4631351, Nov 2023)**
- Rule as published on the firm page: long when price is above VWAP, short when price is below VWAP. QQQ is the main instrument and TQQQ the extension. Sample: Jan 2, 2018 to Sep 28, 2023 — [Concretum Group](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/)
- QQQ: $25k grew to $192,656 (+671%) net of commissions, max DD 9.4%, Sharpe 2.1. QQQ buy-and-hold: +126%, DD 37%, Sharpe 0.7. TQQQ: about +8,242%, roughly 116% a year. The page does not give the bar size, trade count, win rate or commission level — [Concretum Group](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/)
- Skepticism: a QuantConnect thread titled "Bear Bull Traders' paper on 'the Holy Grail': not so fast" disputes the result — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/). A separate QuantConnect VWAP_trend strategy report shows a 49.0% drawdown and 2,108% turnover — [QuantConnect report](https://www.quantconnect.com/reports/2dd44a5c1394e0ba3de9c7f4d7dc0716). Note that this was a different implementation; its exact settings were not checked.

**C. Concretum intraday momentum on other ETFs (Zarattini, Aziz & Barbon, "Beat the Market", SSRN 4824172, May 2024; the Noise Area rule already tested on SPY)**
- New evidence on the already-tested rule: the same rules applied to QQQ, BITO and SOXX gave Sharpe 2.03 (QQQ), 1.72 (BITO) and 1.48 (SOXX), against 2.11 for SPY. Source is a conference slide deck, not peer-reviewed — [Bear Bull Traders / MoneyShow deck](https://bearbulltraders.com/wp-content/uploads/2024/08/Money_Show_Final.pdf)
- An aggregator notes that the "Beat the Market" tests do not account for slippage — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following)

**D. Overnight vs intraday ("night effect")**
- Haghani, Ragulin & Dewey, "Night Moves: Is the Overnight Drift the Grandmother of All Market Anomalies?", JOIM 22(2) 2024, pp. 68-80. A stock-level long-short (overnight vs intraday) earns about 38%/yr before costs, and borrow fees reduce that by about 1pp. A secondary summary of their chart reports S&P 500 overnight +1,750% vs intraday -13% over about 30 years (1991-2024) — [JOIM PDF](https://joim.com/wp-content/uploads/emember/downloads/P0753.pdf)
- Mamaysky, Krstovski, Glasserman & Laliberte (arXiv 2507.04481, Jul 2025): nearly all US equity gains over 30 years came overnight, with intraday returns flat or negative. News-based forecasts can pick stocks likely to rise overnight and fall intraday — [arXivLens summary](https://arxivlens.com/PaperView/Details/does-overnight-news-explain-overnight-returns-3036-75a58faf)
- RobotWealth, SPY 2000 to May 2024: overnight = Open/prevClose - 1, intraday = Close/Open - 1. "The effect has persisted" in a 2024 update of the May 2020 study, and it is stronger on adjusted prices. There is no cost analysis or sub-period statistic — [RobotWealth](https://robotwealth.com/revisiting-overnight-vs-intraday-equity-returns/)
- CXO Advisory, SPY 1993-2017: overnight beat intraday on every weekday, but the outperformance "is not stable over time" — [CXO Advisory](https://www.cxoadvisory.com/?p=27932)

**E. Leveraged-ETF / option-gamma rebalancing near the close**
- Barbon, Beckmeyer, Buraschi & Moerke, "Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows: Evidence from End-of-Day Stock Prices" (SSRN 3925725, 2021; SFI 22-40). LETF rebalancing and option delta-hedging cause end-of-day momentum or reversal depending on the direction of the imbalance, and the effect reverts within the next trading day. The flows are mechanical, not informational — [SSRN](https://papers.ssrn.com/abstract=3925725); [Alpha Architect summary](https://alphaarchitect.com/options-hedging-leveraged-etfs-in-market-swings/)
- LETF rebalancing demand is approximately proportional to L(L-1) x AUM x the day's return so far. That means it is computable from price data plus LETF AUM, and it is same-direction (momentum) into the close for both bull and bear LETFs — [SSRN abstract](https://papers.ssrn.com/abstract=3925725) (the exact formula was not checked in the PDF; see Gaps)

**F. First/last half-hour momentum (already tested, new evidence on decay)**
- Original: Gao, Han, Li & Zhou, JFE 2018, SPY 1993-2013 — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)
- CXO, SPY 2012-2014: R-squared about 0.014. Last-half-hour returns after the biggest first-half-hour moves are "too small in magnitude for most investors to exploit" — [CXO Advisory](https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked)
- A 2024 MDPI *Risks* paper states that overnight effects and intraday momentum "have diminished over time" — [MDPI Risks 12(11):180](https://mdpi.com/2227-9091/12/11/180)

### Inferences
- The SIP 1-min data (2016-2026) covers the Stocks-in-Play ORB, but the universe needs about 7,000 tickers of 1-min or 5-min bars plus 14-day opening-interval volume. That is a large Alpaca download, and survivorship-free listings matter. A cheaper first test is ORB with relative volume on a fixed list of high-beta liquid names, then scaling up.
- VWAP trend on QQQ can be coded directly from the 1-min bars already downloaded. The unpublished pieces (bar resolution, whether the signal is evaluated every bar or every N minutes, a flat-at-close rule) should be swept, and costs per crossing matter given 2,000%+ turnover.
- The overnight hold (buy SPY/QQQ at the close, sell at the next open) is testable on daily data (close to next open). Expect gross positive and net sensitive to spread and auction costs. Costs per round trip are the deciding variable.
- LETF close-flow momentum is codeable without order-book data if LETF AUM is approximated (shares outstanding x NAV). The signal is: if |SPY return from open to 15:30| is large, trade in the same direction 15:30 to 16:00. This is a partial overlap with the already-tested last-half-hour momentum and should be tested as a conditional enhancement.

### Gaps
- Not found this round: VWAP-reversion (fade) rules with published stats; mean reversion after large opening moves beyond the already-tested gap fade; MOC-imbalance rules (these need imbalance feeds, which are not available); "turn-of-day" patterns; 30-minute and 60-minute ORB stats from the Zarattini paper (they are in the PDF, not fetched).
- The VWAP paper's bar size, signal frequency, sizing (likely 1x notional) and commission level were not on the firm page. The SSRN PDF is needed.
- I could not verify the exact LETF rebalancing formula or the trading-rule magnitudes from the Barbon et al. PDF.
- I found no peer-reviewed 2025-2026 replication of the Stocks-in-Play ORB with real fills.

## Swing (daily bars): Connors variants, Williams, Bollinger, turnaround Tuesday, etc.

### Takeaway
Of the requested swing rules, only Double 7s has a solid independent replication this round. It survives on SPY through Sep 2026 (PF 2.35, Sharpe 0.85, 333 trades, about 28% exposure, zero costs), and a variant exiting on close > SMA5 is reported as more robust. Williams %R on SPY is reported to "work" by QuantifiedStrategies, but the details are paywalled. Larry Williams' open + k x range volatility breakout has only vendor evidence. For cumulative RSI, %b, TPS, turnaround Tuesday, key reversal and close-near-low streaks I found no fetched sources this round; the specs below are unverified.

### Cited Findings
- **Double 7s (Connors & Alvarez, *Short Term Trading Strategies That Work*, 2008):** buy when the close > SMA200 and the close is the lowest close of the last 7 days. Sell when the close is the highest close of the last 7 days. No stop; stops reduced returns in testing — [StrategyQuant](https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/)
- StrategyQuant on SPY daily, Jan 1993 to Sep 2026: 333 trades, net profit about $143k, PF 2.35, Sharpe 0.85, max DD about 12.5%, exposure about 28%, with zero commission, spread and slippage (vendor marketing) — [StrategyQuant](https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/)
- Connors and Penn, S&P 500 Jan 1995 to Apr 2008: +1,133 index points, nearly 80% winners. Penn's article uses the same rules — [Traders.com Jan 2009](https://traders.com/Documentation/FEEDbk_docs/2009/01/penn.html)
- Independent Python test, S&P 500 1990-2024: replacing the 7-day-high exit with close > SMA5 performed well and was consistent across lookbacks, unlike the original exit — [Ayrat Murtazin](https://ayratmurtazin.beehiiv.com/p/backtest-results-for-larry-connors-double-7-strategy)
- QuantifiedStrategies: Double 7s "still works", but other Connors strategies work better — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/larry-connors-double-seven-trading-bad)
- **Williams %R:** the QuantifiedStrategies SPY backtest concludes it "seems to work pretty well". Their "81% win rate" variant is paywalled, so the rules are not visible — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/larry-williams-r-trading-strategy); [81% post](https://quantifiedstrategies.substack.com/p/williams-r-trading-strategy-81-win)
- **Larry Williams volatility breakout:** the WHS version is stop-entry at open +/- 0.25 x (prior high - prior low), traded intraday on 5-min charts. One variant uses target = stop = 2x the breakout range. The vendor says the backtests were profitable but gives no figures — [WH SelfInvest](https://www.whselfinvest.com/en-be/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free)

### Inferences
- Double 7s overlaps heavily with the already-tested RSI(2)/SMA5 family (it is the same pullback-in-uptrend logic with a different trigger). Expect high trade correlation, so test it as a robustness check, not as a diversifier.
- The open + k x prior range breakout is easy to code on 1-min SIP data for SPY/QQQ (entry intraday, exit at close). k in {0.25, 0.5, 0.6} and a test for whether to filter by the prior day's NR or inside bar are natural sweeps. No published equity-ETF stats were found.

### Gaps (unverified specs from Connors and Alvarez books; not confirmed by a source fetched this round)
- **Cumulative RSI (Connors & Alvarez, *High Probability ETF Trading*, 2009), unverified spec:** close > SMA200, and the sum of RSI(2) over the last 2 days < 35. Exit when RSI(2) > 65.
- **%b strategy (same book), unverified spec:** close > SMA200, and Bollinger %b(5, 1 SD) < 0.2 for 3 consecutive days. Exit when %b > 0.8.
- **TPS, Time-Price-Scale (same book), unverified spec:** close > SMA200, and RSI(2) < 25 for 2 days. Buy 10% of the position, then add 20/30/40% on each lower close. Exit when RSI(2) > 70.
- **Turnaround Tuesday, unverified spec:** buy at Monday's close if Monday closed down (some variants require the close < prior close and IBS low), sell at Tuesday's close. No fetched stats this round.
- **Not found this round:** key reversal, lower-low/higher-high count, close-near-low streak, and consecutive-up-day index short rules. Published stats need a follow-up search (Alvarez Quant Trading, QuantifiedStrategies).

## Positional (weekly/monthly): TSMOM, dual momentum, channels, 52-week-high ETFs, ensembles

### Takeaway
TSMOM 12-1 (Moskowitz, Ooi & Pedersen 2012) is well established in-sample (positive for every contract, 1985-2009), but Huang, Li, Wang & Zhou (JFE 2020) find little asset-by-asset evidence in or out of sample. Dual momentum / GEM held up on Antonacci's own extended backtest (1950-1973 and 2012-2018 out-of-sample), but an independent replication found the original specification regressed to the median of its variants out of sample, and one analysis reports a related Antonacci portfolio trailing its benchmark since 2012. Treat both as decayed or weakened.

### Cited Findings
- MOP 2012: 12-month TSMOM profits are positive "for every asset contract we examine", 1985-2009 (futures, not ETFs) — [AQR](https://aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum?aqrPDF=1)
- Huang, Li, Wang & Zhou (JFE 2020, "Time series momentum: Is it there?"): asset-by-asset regressions show little TSMOM evidence in or out of sample. The TSMOM strategy performs about the same as a historical-sample-mean strategy that needs no predictability — [WUSTL profile](https://profiles.wustl.edu/en/publications/time-series-momentum-is-it-there/)
- A KAIST study argues the anomaly remains present in recent years, which conflicts with Huang et al. — [KAIST](https://koasas.kaist.ac.kr/handle/10203/268191)
- **GEM / dual momentum (Antonacci):** each month, if the S&P 500's 12-month return exceeds T-bills (absolute momentum), hold the better of US vs ex-US equities over 12 months (relative momentum); otherwise hold aggregate bonds. Formalized in 2012 and tested on 1974-2011. Later extension to 1950-2018 created out-of-sample windows (1950-73 and 2012-18) — [HedgeFundAlpha/Antonacci](https://hedgefundalpha.com/strategies/global-equity-momentum-a-craftsmans-perspective/)
- Independent replication (ReSolve): the original GEM specification's out-of-sample performance "regressed to the median" of alternative specifications — [AlgoEdge summary](https://algoedgeinsights.beehiiv.com/p/is-gary-antonacci-s-global-equity-momentum-strategy-robust); [HedgeFundAlpha](https://hedgefundalpha.com/strategies/global-equity-momentum-a-craftsmans-perspective/)
- TuringTrader: a related Antonacci dual momentum portfolio beat its benchmark until 2012 and has "continuously trailed its benchmark since" — [TuringTrader](https://turingtrader-com.web.app/portfolios/antonacci-dual-momentum)
- Price Action Lab reports "significant deterioration in performance after publication" for dual momentum, attributed to selection bias and regime change — [Price Action Lab](https://priceactionlab.com/Blog/?p=68274)

### Inferences
- With yfinance ETF data, a TSMOM 12-1 rule on a multi-asset ETF set (SPY, EFA, EEM, IEF, TLT, GLD, DBC, VNQ) is immediately testable. Signal = sign of the 12-month return excluding the latest month. Size each position at 40%/(annualized 60-day vol), as in MOP's volatility scaling. Given Huang et al., the key comparison is against a historical-mean benchmark and against Faber's 10-month SMA (already tested). The two will be highly correlated.
- GEM is implementable with SPY/VEU (or EFA)/AGG/BIL monthly. The post-2012 period is the honest out-of-sample period.

### Gaps
- Not found this round: published ETF-level stats for Keltner/ATR channel trend, 52-week-high proximity (George & Hwang 2004) applied to ETFs, monthly turtle variants, and multi-lookback trend ensembles. These need a follow-up (Allocate Smartly and Alpha Architect pages were not fetched).
- I did not obtain post-2014 live GEM performance from an audited tracker (Allocate Smartly did not surface).

## Which have survived out-of-sample/post-publication, and which decayed?

### Takeaway
Survivors with independent support: the Stocks-in-Play 5-min ORB (QuantConnect replication, Sharpe about 2.4), Double 7s on SPY (through Sep 2026, zero-cost), and the overnight drift (persists through 2024 in SPY and is documented across stocks in 2024-2025 papers). Weakened or decayed: first/last-half-hour intraday momentum, broad-index ORB (net zero after costs), dual momentum/GEM after 2012, and TSMOM at the single-asset level (contested). Unresolved: VWAP trend (author-only headline vs. skeptical replications).

### Cited Findings
- Stocks-in-Play ORB: independent QuantConnect Sharpe 2.396 vs. the paper's 2.81 — [QuantConnect](https://www.quantconnect.com/forum/discussion/18444/Opening+Range+Breakout+for+Stocks+in+Play/p4/comment-50717)
- Index ORB: "gross reproduced, net zero" on index CFDs 2015-2026 — [MQL5](https://www.mql5.com/en/blogs/post/776235)
- VWAP trend disputed — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/)
- Overnight drift persisted through 2024 — [RobotWealth](https://robotwealth.com/revisiting-overnight-vs-intraday-equity-returns/); unstable over time per [CXO](https://www.cxoadvisory.com/?p=27932)
- Intraday momentum diminished — [MDPI Risks 2024](https://mdpi.com/2227-9091/12/11/180); [CXO](https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked)
- Double 7s survives 1993-2026 on SPY (zero-cost) — [StrategyQuant](https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/)
- GEM regressed out of sample — [AlgoEdge/ReSolve](https://algoedgeinsights.beehiiv.com/p/is-gary-antonacci-s-global-equity-momentum-strategy-robust); [TuringTrader](https://turingtrader-com.web.app/portfolios/antonacci-dual-momentum)
- TSMOM contested — [Huang et al. JFE 2020](https://profiles.wustl.edu/en/publications/time-series-momentum-is-it-there/); [KAIST](https://koasas.kaist.ac.kr/handle/10203/268191)

### Inferences
- A common pattern: edges reported by strategy authors in 2023-2024 (Concretum) are post-2016 in-sample, and the out-of-sample period available to the user (2024-2026 SIP data) is the cleanest test. Lock the parameters from the papers and test only on Oct 2023 to Oct 2026 data as a sealed holdout.
- Costs dominate every intraday candidate. Cost modelling at $0.0035/share plus 1-2 bps slippage per side is the minimum.

### Gaps
- No 2025-2026 post-publication study was found for the Stocks-in-Play ORB or the VWAP trend.
- No out-of-sample decay study was found for Connors' %b, cumulative RSI or TPS, or for Williams %R.
