# Swing-trading (daily-bar) price-action strategies for US stocks and ETFs

Scope: daily OHLC bars, holding periods from 1 day to about 2 weeks, US equities and ETFs. Evidence from 2010 to 2026 is preferred; older seminal work is marked [CONTEXT].

Source-quality legend used below: [PEER] peer-reviewed journal; [WP] working paper or preprint; [PRAC] practitioner blog or newsletter with a disclosed method; [VENDOR] marketing or paywalled product page whose numbers cannot be checked.

PDFs saved to `C:\Users\Acer\Pictures\research_papers\paper1\papers\price_action\`:
- `2013_Pagonidis_IBS_effect_mean_reversion_ETFs.pdf`: the IBS paper (NAAIM, data to May 2013)
- `2019_LouPolkSkouras_tug_of_war_overnight_intraday.pdf`: JFE 2019, overnight vs intraday return decomposition
- `2023_Pandey_IBS_country_ETFs.pdf`: 2-page arXiv note, IBS on country ETFs, 2009–2019. It is weak evidence, kept only as a recent replication.

(The folder already held other researchers' PDFs: George-Hwang 52-week high, Zarattini et al. papers and others. I did not add those.)

---

## Q1. Strategy catalogue: exact rules, universe, holding period, reported stats, sample and costs

### Takeaway
The best-documented daily swing edges for US equities are **short-horizon mean reversion on index ETFs**: RSI(2) or RSI(3) oversold above a 200-day MA, IBS (close near the low), and N-day-low or consecutive-down-day pullbacks. These have audited-style backtests with ~70–80% win rates, average trades of +0.5–0.9%, and low exposure (~10–30%), and they deliver lower CAGR than buy and hold but with much smaller drawdowns. Breakout, volatility-contraction and candlestick rules have much thinner or negative evidence. Most published numbers for NR7, inside bars and Bollinger squeezes sit behind paywalls and cannot be verified.

### Cited Findings

**S1. Connors RSI(2) pullback in an uptrend (SPY). This is the best-documented case.**
- Rules as rebuilt: buy SPY **at the close** when RSI(2) < 10 and close > 200-day SMA. Sell at the close when close > 5-day SMA. No stop. Fully invested or fully in cash, and cash earns 0. Signal and fill both use the same close, so a live trader must estimate RSI a few minutes before the bell. — [EmpiricaLab Substack, "Connors' RSI(2) had a Sharpe of 0.97 before the book. Since then: 0.68"](https://empiricalab.substack.com/p/connors-rsi2-spy) [PRAC]
- Sample: SPY daily, dividend-adjusted, 29 Jan 1993 to 30 Sep 2026, with 2 bp per side costs. 265 trades, 77% winners, average trade +0.63%, average hold just over 3 days. CAGR 5.0% vs 10.8% buy and hold. Sharpe 0.81 vs 0.65. Max drawdown 14.8% vs 55.2%. Exposure ~11% of days (893 of 8,475). 26 of 34 calendar years positive. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- Cost sensitivity: CAGR is 5.3%, 4.4% and 3.7% at 0, 6 and 10 bp per side. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- Robustness: 15 parameter variants (RSI length 2–4, threshold 5–25) are all positive, with Sharpe 0.13–0.92, and the published pair ranks 3rd. In 2,000 random-entry simulations the median return was ~+32% vs +168% for the rule, and no random run matched it. Bootstrap 95% CI: win rate 72–82%, Sharpe 0.53–1.11. Deflated Sharpe 99%, probability of backtest overfitting 4%. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- Origin [CONTEXT]: Connors & Alvarez, *Short Term Trading Strategies That Work* (2008/2009). A practitioner summary of the standard rules (RSI(2) < 5 or < 10, above 200-day MA, exit on close > 5-day MA or RSI(2) > 70) is at [QuantifiedStrategies RSI-2 guide](https://www.quantifiedstrategies.com/rsi-2-strategy/) [PRAC]. That guide claims an out-of-sample check over 2015–2025 shows "slight performance decay" but a retained edge. Its method is not disclosed.

**S2. RSI(3) plus IBS filter (QQQ and other US ETFs). Pagonidis variant.**
- Rules: go long at the close if Cutler's RSI(3) < 10. Hold while RSI(3) ≤ 40. Filter: enter or keep the position only if IBS ≤ 0.5. Over the paper's ETF sample, the IBS filter removed ~43% of days in market and raised total returns by ~9.6 percentage points on average. Illustrated on QQQ. — [Pagonidis, "The IBS Effect: Mean Reversion in Equity ETFs" (NAAIM, 2013)](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf) [WP], PDF saved locally

**S3. Internal Bar Strength (IBS), close near low, on SPY/QQQ.**
- Definition: IBS = (Close − Low) / (High − Low), ranging 0 to 1. — [Pagonidis 2013](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf); also implemented as a TA-Lib function ([TA-Lib IBS](https://ta-lib.org/functions/ibs.html))
- Pagonidis evidence (ETF inception to 12 May 2013, CSI data): next-day close-to-close return averages +0.35% when IBS < 0.20 and −0.13% when IBS > 0.80. Across ETFs the bottom bucket averages +38 bp and the top bucket −14 bp. The relationship is non-linear, with thresholds near 0.4 and 0.9. The up-day probability differs by 11.2 percentage points between the top and bottom buckets. — [Pagonidis 2013](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Conditioning, all from the same paper:
  - The effect is stronger in high 20-day realized volatility and after high-range days.
  - It is slightly stronger in bear markets (negative 200-day return).
  - For US ETFs it **disappears on low-volume days**.
  - It is strongest on Mondays (the "Turnaround Tuesday" next-day return) and weakest on Fridays.
  - It is largely **absent in locally listed non-US index ETFs** (DAX ETF inverted), so it is a US-session phenomenon.
  - Next-day returns after low IBS are positively skewed (skew 0.65).
  - IBS alone is "difficult" after commissions. Pagonidis suggests trading at the closing auction to avoid the spread.
- QuantifiedStrategies QQQ rule: buy at the close when IBS < 0.1, sell at the close when IBS > 0.9. Reported average gain +0.9% per trade, 70% win rate, ~14% annual return over ~30 years. — [QuantifiedStrategies IBS article (Substack)](https://quantifiedstrategies.substack.com/p/the-ibs-indicator-the-powerful-indicator) [PRAC/VENDOR]. The period split, costs and drawdown were not visible.
- 2009–2019 replication on 15 country ETFs: IBS < 0.2 long / > 0.8 short. Single-ETF Sharpe ranges from −0.45 (EWC) to 2.17 (PIN). **IVV (S&P 500) Sharpe only 0.20.** Probability of an up day after IBS < 0.2 for IVV is 56.6%. — [Pandey & Joshi, arXiv 2306.12434 (2023)](https://arxiv.org/pdf/2306.12434) [WP, 2 pages, no costs stated, low quality]
- A dissenting practitioner test (StockViz, 2016) concluded IBS mean reversion "as the author intended" was a losing proposition. — [StockViz](https://stockviz.biz/2016/06/22/internal-bar-strength/) [PRAC], whose market and sample were not checked.

**S4. Cumulative RSI (Connors).**
- Canonical rules [CONTEXT, Connors & Alvarez book]: the sum of RSI(2) over the last 2 days < 35, close > 200-day SMA. Buy at the close and exit when RSI(2) > 65. A practitioner write-up of this rule on the S&P 500 is at [StatOasis, "Cumulative RSI Strategy"](https://statoasis.com/overfit/research/cumulative-rsi-strategy-a-smarter-twist-on-rsi(2)-for-s-p-500) [PRAC]. I did not fetch the page, so its statistics are not reported here.

**S5. Consecutive down days, N-day lows and large short-term declines (ETF pullbacks).**
- In 6,000 backtests across 75 ETFs, 20 entry families were tested: RSI oversold, consecutive lower closes, % declines, distance below MA, Williams %R, Stochastic, N-day lows, Bollinger weakness, ATR pullbacks, gap-downs and pullbacks in an uptrend. Entry was at the **next session's open**, with 10 bp round-trip costs tested and a ~70/30 in-sample/holdout split.
  - The best entry family was a "large 5-day decline", with median PF ~1.55.
  - The best exit was "close above prior day's high", with median PF ~1.35. Other exits tested: close above a short MA, RSI recovery, and a fixed 5 bars.
  - Median profit factor by ETF: MTUM 2.68 (2.41 after costs), SMH 2.36, QQQ 2.31, SPY 1.83. Commodity, volatility and bond ETFs were below 1 (UNG 0.89, VIXY 0.86, USO 0.83, BKLN 0.49, MUB 0.30).
  - From 2016 the top five were SMH, MTUM, XLK, IGV and QQQ.
  - Rankings were unstable in the holdout. USO went from the bottom to near the top. MTUM's holdout PF of 6.37 rests on only ~37 trades.
  - Exact thresholds were not disclosed.
  - Source: [QuantifiedStrategies, "Best ETF for Mean Reversion Strategies? 6,000 Backtests Across 75 ETFs"](https://quantifiedstrategies.substack.com/p/best-etf-for-mean-reversion-strategies) [PRAC]
- Canonical Connors rules [CONTEXT, not independently verified here]: "3 or more consecutive lower closes, above 200-day MA, buy at the close, exit on close > 5-day MA"; and "close at a 7-day low above 200-day MA, exit at a 7-day high close". Treat these as specifications to test, not as evidence.

**S6. Volatility-contraction breakouts (NR4/NR7, inside bars, Bollinger squeeze).**
- NR7 (today's range is the narrowest of the last 7 bars) has been backtested on SPY since 1993 by QuantifiedStrategies. The author says it "works reasonably well" and is improved by "one simple parameter", but the rules and all statistics are **paywalled**. — [QuantifiedStrategies NR7 (Substack, May 2024)](https://quantifiedstrategies.substack.com/p/nr7-trading-strategy-the-narrow-range-b35) [VENDOR]
- SentimenTrader found a narrow-range / selling-pressure-drying-up setup on SPY "did tend to lead to a rebound in the very short-term". No PF was given. — [SentimenTrader](https://sentimentrader.com/blog/selling-pressure-drying-up) [PRAC]
- An inside-bar continuation test (MQL5 blog) gave PF 1.43 on XAUUSD H1 and found no reliable edge on EURUSD. It is not a US equity daily-bar test. — [MQL5 blog](https://www.mql5.com/en/blogs/post/771362) [PRAC]
- Note: on equity index ETFs the practitioner use of NR7 and inside days is often *mean-reverting* (buy the narrow day in an uptrend and exit within days), not breakout-following. This is consistent with S3's finding that IBS effects are weaker after small-range days. That is an inference, not a direct test.

**S7. N-day high/low (Donchian) breakouts.**
- QuantifiedStrategies states that Donchian channels "work well as a trend following indicator for commodities and currencies, but not for stocks", and tests an *inverted* mean-reversion version for stocks. — [QuantifiedStrategies Donchian (Substack)](https://quantifiedstrategies.substack.com/p/donchian-channels-trading-strategy) [PRAC]
- A Dow 30 Donchian test (TrendSpider-based) gave 65% losing trades and a 2.4:1 reward-to-risk ratio. — [Liberated Stock Trader](https://www.liberatedstocktrader.com/donchian-channels-indicator/) [VENDOR]
- A 20-bar Donchian on NQ futures over 2015–2024 had PF 1.56 and max drawdown ~40%. That is futures, not ETFs. — [Anup Shinde](https://anupshindedotcom.pages.dev/breakout-continuation-backtested/) [PRAC]
- On short swing horizons, index-ETF N-day *highs* have historically been better *exit* triggers for mean-reversion longs than entry triggers. Longer-horizon breakout/trend evidence on stocks (e.g., George-Hwang 52-week high; Zarattini 2025 trend following on stocks) is held in the same PDF folder by the other horizon researchers.

**S8. Overnight vs intraday returns as a daily strategy.**
- Rules: buy SPY at the close and sell at the next open (the "night" strategy), or the reverse (the "day" strategy).
- SPY 1993–2017: overnight returns averaged higher than intraday, but the difference "is not stable across arbitrarily set subperiods". — [CXO Advisory, "SPY by Day of the Week and Overnight"](https://www.cxoadvisory.com/calendar-effects/spy-by-day-of-week-and-overnight/) [PRAC]
- Alpha Architect's summary reports cumulative price returns of 717% for overnight, 627% for buy and hold and 12% for intraday before costs, and concludes that **trading costs wipe out** the overnight anomaly as a stand-alone strategy. — [Alpha Architect](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/) [PRAC]. The page returned 403 to my fetch, so these figures come from the search snippet.
- Academic grounding: across 14 cross-sectional strategies, profits are earned "entirely overnight (for reversal and a variety of momentum strategies) or entirely intraday", typically with opposite signs. — [Lou, Polk & Skouras, JFE 134 (2019) 192–213](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf) [PEER], PDF saved locally
- Contrary evidence: an ES futures analysis for 1997–2025 reports overnight −1.22%/yr and intraday +6.10%/yr, the opposite of the SPY ETF finding. This shows the result depends on the instrument and session definition (futures trade overnight on Globex). — [TradingView post, EdgeTools](https://www.tradingview.com/chart/SPY/5fk9yQhZ-The-Overnight-Wealth-Machine/) [PRAC]
- Robot Wealth reports SPY's intraday total return since 2000 is negative, and that the night-minus-day spread mean-reverts over shorter windows. — [Robot Wealth](https://robotwealth.com/overnight-and-intraday-spx-returns/) [PRAC]

**S9. Candlestick patterns (engulfing, hammer, doji, three white soldiers etc.).**
- [CONTEXT] Marshall, Young & Rose tested 28 candlestick signals on DJIA stocks over 1992–2002 with a 10-day hold. Bootstrap tests found "no evidence that any candlestick signals predict stock price movements". — [CXO Advisory summary](https://www.cxoadvisory.com/technical-trading/candlesticks-fiddlesticks/); [Marshall PhD thesis, Massey](https://mro.massey.ac.nz/items/edc6c1cf-63d9-4c94-a13d-92ffe1a53481/full) [PEER, J. Financial Transformation 2007]
- Lu, Chen & Hsu (J. Banking & Finance, 2015) studied DJIA components. Eight 3-day reversal patterns **are profitable at 0.5% transaction cost after data-snooping correction** when using the Caginalp-Laurent holding rule, but **not** with the Marshall-Young-Rose holding rule. The evidence is stronger in volatile markets. The exit or holding rule, not the pattern, decides the result. — [ScienceDirect abstract](https://www.sciencedirect.com/science/article/abs/pii/S0378426615002678); [Academia Sinica WP](https://ideas.repec.org/p/sin/wpaper/14-a010.html) [PEER]
- [CONTEXT] Caginalp & Laurent (1998) tested all S&P 500 stocks over 1992–1996 and found statistically significant results, almost 1% return over a 2-day horizon. — summarised in [Lund University thesis](https://lup.lub.lu.se/luur/download?func=downloadFile&recordOId=8877738&fileOId=8877838) [WP]
- [CONTEXT] Horton studied 3-day patterns on 349 stocks and found no trading value. — referenced in [Tharavanij et al., SAGE Open 2017](https://journals.sagepub.com/doi/10.1177/2158244017736799) [PEER, Thai market]
- Price-definition sensitivity: over six decades of S&P 500 data, Hammer and Shooting Star had little reliability on closes but were reportedly "highly reliable" when defined using lows and highs. — search-snippet attribution only; primary source not fetched, so treat as unverified.
- I found **no peer-reviewed 2020–2026 study of candlesticks on US stocks or ETFs**. 2020s work is mostly ML on non-US or crypto data, e.g. Bullish Harami and Hikkake significant after an SPA test in crypto ([ScienceDirect 2026](https://sciencedirect.com/science/article/pii/S1059056026002716)). Cohen (2020) reported a custom "stairs" pattern profitable on 20 stocks ([ResearchGate](https://www.researchgate.net/publication/339935171_BEST_CANDLESTICKS_PATTERN_TO_TRADE_STOCKS)), which is a small sample.

**S10. Day-of-week interplay (price-based only).**
- The IBS edge is largest when the signal is formed on Monday's close (Turnaround Tuesday) and weakest on Friday. — [Pagonidis 2013](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- A study of SPY Tuesdays reports a significant negative correlation between Tuesday intraday and overnight returns. — referenced via [CXO Advisory](https://www.cxoadvisory.com/calendar-effects/spy-by-day-of-week-and-overnight/), unverified detail

**S11. Gap behaviour on daily bars.**
- Gap-down entries were one of the 20 entry families in the 75-ETF study, with next-open entry. It was **not** among the best families. Large 5-day declines were best. — [QuantifiedStrategies 75 ETF study](https://quantifiedstrategies.substack.com/p/best-etf-for-mean-reversion-strategies)
- I found no recent, rule-level, verifiable US ETF gap-fade or gap-and-go daily study. See Gaps.

### Inferences
- A codeable core set with credible evidence would be: (a) RSI(2) < 10 above 200-day SMA, exit close > SMA(5); (b) IBS < 0.2 (or ≤ 0.5 as a filter) combined with RSI(3) < 10; (c) a "large N-day decline / N-day low above 200-day SMA" pullback with exit on close > prior high. All are long-only, on SPY/QQQ (and tech-heavy ETFs such as SMH/XLK), with ~3–5 day holds.
- Typical profile of these systems: win rate 70–80%, average trade 0.5–0.9%, exposure 10–30%, PF ~1.8–2.4 on SPY/QQQ, CAGR 4–14% depending on ETF and leverage, max drawdown ~15% (much less than buy and hold). They rarely beat buy and hold on CAGR unless levered or stacked.
- Stops tend to hurt these mean-reversion rules. EmpiricaLab and the Connors originals use no price stop and rely on a time or MA exit. A time stop (e.g., 5–10 bars) is the usual safety valve.
- Volatility-contraction, breakout and candlestick rules should be treated as unproven on US equity ETFs at daily/swing horizon until tested in-house. Lu-Chen-Hsu suggests that if candlesticks are used at all, the exit rule should be what gets optimised and tested.

### Gaps
- Verified statistics for NR4/NR7, inside-bar and Bollinger squeeze (e.g., the Connors/Raschke "%b" or the TTM squeeze) on SPY/QQQ: the QuantifiedStrategies pages are paywalled. I found no peer-reviewed US-equity test.
- Exact published statistics for Connors' cumulative RSI, "3 down days" and "7-day low" rules after 2010. I relied on book specifications, not fetched numbers.
- Three white soldiers, doji, engulfing and hammer: I found no pattern-by-pattern US evidence for 2015–2026 with costs.
- A gap fade/continuation study on US ETFs with daily bars and costs.
- Alpha Architect's overnight-cost article could not be fetched (403), so its exact cost assumptions are unknown.

---

## Q2. Which swing strategies have robust recent (2015–2026) evidence, and which have decayed?

### Takeaway
RSI(2) on SPY has measurably decayed since publication (2008/2009). Its Sharpe fell from 0.97 to 0.68, below buy and hold's 0.87 post-2009, though it is still positive with PF ~2.4 and a 74% win rate. The decay may be partly regime-driven: there was a weak 2010s and a recovery in 2020–2024. IBS and pullback mean reversion still show positive results in recent windows, mainly on QQQ, SMH and momentum or tech ETFs, but there is no clean, peer-reviewed post-2015 replication. Candlesticks never had robust US evidence. The overnight premium persists in the ETF data but does not survive costs as a stand-alone trade.

### Cited Findings
- RSI(2) SPY, before vs after 1 Jan 2009: trades 116 → 149; win rate 81% → 74%; average trade 0.79% → 0.51%; Sharpe 0.97 → 0.68 (buy and hold 0.42 → 0.87); max drawdown 7.0% → 14.8%; post-2009 PF 2.4. Since 2009 SPY returned 14.9%/yr and the rule 4.3%/yr. Over the last three years, 8.8%/yr vs 22.3% for SPY. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- The same source cites McLean & Pontiff (2016): predictor returns were 58% lower after publication. It calls the comparison loose. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- A decade-level replication found edge per trade shrank in 2010–2019 and recovered in 2020–2024. A 2020+ holdout of 58 trades averaged +0.50% net and stayed positive after an extra 0.20% round-trip cost. It is labelled "report-only". — [GitHub research card, golden_boy_peanuts #262](https://github.com/jeisenback/golden_boy_peanuts/issues/262) [PRAC, low weight]
- Another test said RSI(2) "seems to have lost some of its edge in recent years" but performance "did come back strongly in 2015". — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/) [PRAC]
- 26-year SPY RSI(2) test: 181 trades, 82% win rate. — [GuruFinance Substack](https://gurufinanceinsights.substack.com/p/i-backtested-the-classic-rsi2-mean) [PRAC], details not fetched
- In the 75-ETF study, mean reversion remained profitable from 2016 and in the 30% holdout, with SMH, MTUM, XLK, IGV and QQQ on top. Rankings shifted between regimes. — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/best-etf-for-mean-reversion-strategies)
- IBS on IVV over 2009–2019 had only Sharpe 0.20 as a stand-alone long/short threshold strategy, vs 1–2 for several EM/Asian country ETFs. — [Pandey & Joshi 2023](https://arxiv.org/pdf/2306.12434). This suggests the pure S&P 500 IBS long/short edge is weak post-2009 without the RSI/trend filters.
- Pagonidis described the IBS effect as "highly consistent through time" from the early 1990s to 2013, a pre-2013 sample. — [Pagonidis 2013](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Micaletti (SSRN, Jan 2023) compared short-term mean-reversion indicators for global equities and found modified oscillators dominate performance rankings on both the long and short side. — [SSRN 4339128](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4339128) [WP], details not fetched
- Overnight vs intraday: the overnight dominance in SPY is not stable across subperiods ([CXO](https://www.cxoadvisory.com/calendar-effects/spy-by-day-of-week-and-overnight/)) and is erased by costs ([Alpha Architect](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/)). Futures data shows the opposite sign ([TradingView/EdgeTools](https://www.tradingview.com/chart/SPY/5fk9yQhZ-The-Overnight-Wealth-Machine/)).

### Inferences
- "Decay" in RSI(2) is mostly **relative**: absolute per-trade edge fell ~35% (0.79% → 0.51%), but the main reason it now lags is that 2009–2026 buy-and-hold Sharpe was exceptionally high. With 11% exposure, the strategy is better used as an overlay (cash earning T-bills, or stacked with other signals) than as a replacement for beta.
- Recent evidence favours mean reversion on **high-beta, tech or momentum-heavy ETFs** (QQQ, SMH, XLK, MTUM) over SPY and especially over small caps or non-equity ETFs.
- The 2010s weakness and 2020s recovery fit a volatility-regime explanation: Pagonidis found IBS stronger in high volatility. The 2020–2022 and 2025 volatility spikes would favour these rules. This is an inference, not tested here.

### Gaps
- No peer-reviewed post-2015 out-of-sample study of RSI(2), IBS or cumulative RSI on US ETFs was found.
- No IBS-only SPY/QQQ results split by 2015–2026 were found. QuantifiedStrategies figures are full-period and partly paywalled.
- I found no Allocate Smartly or Robot Wealth post with verified post-2015 decay numbers within the search budget.

---

## Q3. ETFs vs single stocks, and sensitivity to entry convention (close vs next open)

### Takeaway
Daily mean-reversion edges are documented mainly on **US index ETFs**. Evidence on single stocks is weaker and noisier, with gap risk on earnings. Non-US-session ETFs and non-equity ETFs (commodities, volatility, bonds) do poorly. Entry convention matters because IBS and RSI(2) are defined on the close and most of their edge is in the next close-to-close return. Same-close execution, via a MOC or closing-auction order using a pre-close estimate, is the published standard. Next-open fills still yield positive PFs in the 75-ETF study, but I found no direct head-to-head quantification.

### Cited Findings
- RSI(2) on five other equity ETFs: win rates 70–73%, returns 2.1–4.3%/yr, Sharpe 0.38–0.53 vs 0.81 on SPY. On 4 of 5 the rule's Sharpe was below buy and hold. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- Median mean-reversion PF: QQQ 2.31 > SPY 1.83. Commodity, volatility and bond ETFs were below 1. — [QuantifiedStrategies 75 ETFs](https://quantifiedstrategies.substack.com/p/best-etf-for-mean-reversion-strategies)
- IBS is US-centric. Locally listed foreign index ETFs show little or inverse effect. After 2008, international ETF IBS signals depend on SPY's own IBS. The effect is concentrated at the end of the US session. — [Pagonidis 2013](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Pagonidis recommends trading at the closing auction to avoid the bid-ask spread, and notes that the need to execute in a small window near the close constrains scale. — [Pagonidis 2013](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- EmpiricaLab tests only the same-close fill and flags that live orders use a pre-close RSI estimate. It does not report next-open results. — [EmpiricaLab](https://empiricalab.substack.com/p/connors-rsi2-spy)
- The 75-ETF study uses next-open entry throughout and still finds PF 1.8–2.7 on top equity ETFs, but does not compare it with close entry. — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/best-etf-for-mean-reversion-strategies)
- Single stocks: a TrendSpider-style Donchian test on the Dow 30 had 65% losing trades ([Liberated Stock Trader](https://www.liberatedstocktrader.com/donchian-channels-indicator/)). Candlestick tests on DJIA stocks show no value under MYR exits ([CXO](https://www.cxoadvisory.com/technical-trading/candlesticks-fiddlesticks/)) and conditional value under Caginalp-Laurent exits ([Lu, Chen & Hsu 2015](https://www.sciencedirect.com/science/article/abs/pii/S0378426615002678)).
- Cross-sectional context: short-term reversal and momentum profits accrue overnight, while intraday components carry the opposite sign. — [Lou, Polk & Skouras 2019](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf). This implies that close-vs-open conventions shift which component of the edge you capture.

### Inferences
- **Entry convention**: oversold signals formed on the close (low IBS, RSI(2) < 10) are followed by positive *next close-to-close* returns. Part of that return arrives in the overnight gap, which is consistent with Lou-Polk-Skouras's finding that reversal profits are earned overnight. A next-open entry therefore gives up the overnight piece. Expect lower average trade and PF with next-open fills. The practical answer is MOC or closing-auction orders with signals computed 5–15 minutes before the close. This is an inference; quantify it in-house.
- **ETFs vs stocks**: ETFs diversify away idiosyncratic jump risk (earnings, news) that turns "oversold" stocks into losers with no stop. This is consistent with the stronger and more stable ETF results above. For stocks, practitioners add liquidity, price and above-200-day-MA filters and exclude earnings windows. No verified recent stock-universe statistics were found here.
- A robust in-house test grid would cover {SPY, QQQ, IWM, DIA, sector SPDRs, SMH, MTUM} × {close-to-close, close-to-open, open-to-close fills} × {2 bp, 5 bp, 10 bp per side}, with splits for pre-2009, 2009–2019 and 2020–2026.

### Gaps
- No source directly quantifies RSI(2) or IBS performance with a next-open entry vs a same-close entry on SPY/QQQ.
- No 2015–2026 single-stock (e.g., S&P 500 constituents, survivorship-free) RSI(2), IBS or N-day-low results with costs were verified in this pass.
- The source of the IBS volume dependence (it disappears on low-volume days) and its recent stability are untested post-2013.
