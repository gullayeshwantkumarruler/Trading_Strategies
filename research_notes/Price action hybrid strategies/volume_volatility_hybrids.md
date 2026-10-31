# Hybrid Price-Action + Volume + Volatility Strategies for US Stocks/ETFs (intraday, daily swing, weekly)

Scope note: about 20 tool calls (searches, fetches, plus a local text extraction of the Zarattini-Aziz-Barbon 2024 PDF). Primary-source figures are marked [PRIMARY]. Figures from blogs and vendors are marked [SECONDARY/UNAUDITED]. Many vendor pages (CXO, Concretum Substack, QuantifiedStrategies) are paywalled, so their exact rules and stats could not be checked. These items are listed under Gaps rather than guessed.

---

## Q1. Does volume (RVOL, spikes, OBV, CMF, VWAP distance, up/down volume, price-volume divergence) improve breakouts or mean-reversion entries?

### Takeaway
The strongest evidence that volume helps is **intraday and cross-sectional**. The "Stocks in Play" filter (opening-5-min relative volume) turns a near-useless 5-min ORB on all stocks into a high-Sharpe strategy. VWAP used as a **trailing stop**, not as an entry signal, roughly doubles the Sharpe of the SPY Noise Area momentum strategy. For **daily ETF mean reversion**, no source showed that a volume filter helps. Academic theory (Llorente et al. 2002) predicts that high-volume days in large, liquid names are followed by *reversal*, not continuation. No public test was found for OBV, CMF or up/down-volume as add-ons to daily ETF rules.

### Cited Findings

**A. Stocks-in-Play ORB (Zarattini, Barbon & Aziz 2024, "A Profitable Day Trading Strategy for the U.S. Equity Market", SFI rp2498)**
- Exact rules as summarised by CXO [SECONDARY, rules match paper]. Universe: all US-listed stocks (>7,000), Jan 2016 to Dec 2023. Daily screen: open > $5; 14-day average daily volume >= 1,000,000 shares; 14-day ATR > $0.50; **Relative Volume = volume in the first 5-min opening-range bar / average volume of the same 5-min bar over the prior 14 days, >= 100%**; keep the **top 20 by RVOL**. Entry: if the first 5-min bar closed up, place a buy-stop at the 5-min high; if down, a sell-stop at the low. Stop: **10% of the 14-day ATR** from the fill. Exit at the close if not stopped. Size so that a stop-out loses 1% of capital; leverage cap 4x. Starting capital $25k; commission $0.0035/share — [CXO Advisory](https://www.cxoadvisory.com/?p=45379)
- Performance [SECONDARY, attributed to the paper]: top-20 Stocks-in-Play portfolio >1,600% total net return, **Sharpe 2.81**, annual alpha 36%. Unfiltered 5-min ORB on all eligible stocks: 29% total return, **Sharpe 0.48**. This is the clearest published "volume filter versus pure price rule" comparison — [Let's Data Science summary](https://www.letsdatascience.com/news/traders-adopt-orb-strategy-for-stocks-in-play-19394da2); paper listing [IDEAS/RePEc rp2498](https://ideas.repec.org/p/chf/rpseri/rp2498.html)
- Independent replication: a QuantConnect recreation reports **Sharpe 2.396, beta -0.042**, against 0.836 for SPY buy-and-hold — [QuantConnect forum 18444](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- Counter-evidence: an MQL5 replication of the ORB on five *indices* (no stock-in-play filter) found that "gross reproduced, net zero" — [MQL5 blog](https://www.mql5.com/en/blogs/post/776235). This fits the view that the edge comes from the RVOL selection, not from the ORB on index instruments.

**B. VWAP as a stop in intraday momentum (Zarattini, Aziz & Barbon 2024, "Beat the Market", SFI rp2497) [PRIMARY, paper text extracted]**
- Ablation on SPY, May 2007 to Apr 2024, commission $0.0035/share plus slippage $0.001/share:
  - (a) Noise Area breakout, stop at the opposite band: total return 178%, 6.2% per year, vol 10.9%, **Sharpe 0.61**, worst day -10.33%, skew -1.24, 5,494 trades.
  - (b) Stop = current band **or VWAP** (long stop = max(UpperBand, VWAP); short stop = min(LowerBand, VWAP)): 9.7% per year, vol 7.7%, **Sharpe 1.24**, hit ratio 43%, skew +1.29, worst day -4.8%, 7,668 trades.
  - (c) (b) plus volatility-targeted sizing: total return 1,985%, **19.6% per year, vol 14.3%, Sharpe 1.33, MaxDD 25%**, daily hit ratio about 43%, best trade +9.1%, worst trade -2.9% — [paper PDF (Univ. St. Gallen repository)](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content); [Concretum summary](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
- The VWAP is computed from regular-session data only — same paper.

**C. VWAP trend rule on QQQ (Zarattini & Aziz 2023, "VWAP: the Holy Grail for Day Trading Systems")**
- Authors report on QQQ, Jan 2018 to Sep 2023: $25k grew to $192,656 (671%), **Sharpe 2.1, MaxDD 9.4%**, against QQQ buy-and-hold at 126%, Sharpe 0.7, MaxDD 37% — [Concretum page](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/); [Bear Bull Traders](https://bearbulltraders.com/?p=2606339)
- Replications are weak. One QuantConnect "VWAP_trend" report shows **Sharpe -0.6, DD 49%** — [QC report](https://www.quantconnect.com/reports/2dd44a5c1394e0ba3de9c7f4d7dc0716). A forum thread titled "not so fast" reports very poor raw results, partly improved by a **2% deadband around VWAP**, but still far below the paper — [QuantConnect forum 16706](https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/)

**D. Academic volume-return evidence**
- High-volume return premium: stocks with abnormally high volume over a day or week earn higher subsequent returns. Return autocorrelation, announcements, market risk and liquidity do not explain it; the authors link it to investor recognition (Merton 1987). Gervais, Kaniel & Mingelgrin, JF 2001, 56(3) 877-919 — [RePEc](https://econpapers.repec.org/RePEc:bla:jfinan:v:56:y:2001:i:3:p:877-919); [working paper PDF](https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/9901.pdf)
- Kaniel, Li & Starks find the premium in almost all developed and emerging markets — [NYU archive SSRN-id1122463](https://archive.nyu.edu/bitstream/2451/27578/2/SSRN-id1122463.pdf)
- Llorente, Michaely, Saar & Wang (RFS 2002, 15(4) 1005-1047): hedging/risk-sharing volume implies **return reversal**, speculative/informed volume implies **continuation**. Larger firms and tighter-spread stocks show almost no continuation and mostly **reversal after high-volume days** — [NYU archive](https://archive.nyu.edu/jspui/bitstream/2451/26698/1/FIN-00-032.pdf); [RePEc](https://econpapers.repec.org/RePEc:oup:rfinst:v:15:y:2002:i:4:p:1005-1047)
- Campbell, Grossman & Wang (QJE 1993, 108, 905-939) is the earlier aggregate result: the search surfaced only the citation — [NCCU thesis ref](https://thesis.lib.nccu.edu.tw/thesis/detail/8032c8bc014f30620a23b0facbbbb0ac)
- Market intraday momentum (Gao, Han, Li & Zhou, JFE 2018, 129(2) 394-414): the first half-hour SPY return (prior close to 10:00) predicts the last half-hour return. Predictability is **stronger on higher-volume and more-volatile days**, recession days and macro-news days. It also holds for 10 other liquid ETFs — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414); [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/). A QuantConnect replication found lower returns over its own test window (about 6.67% per year reported for the original SPY strategy) — [QuantConnect](https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum)

**E. Volume on daily mean reversion**
- No published Alvarez or Connors test of a volume filter on RSI(2) was found. A Quantopian thread that sorted by 5-day volume over longer-run average volume could not improve simple short-term mean reversion — [Quantopian archive](https://quantopian-archive.netlify.app/forum/threads/enhancing-short-term-mean-reversion-strategies-1)

### Inferences
- Volume helps most when it is used to **select which instrument or day to trade** (cross-sectional RVOL, high-volume days for intraday momentum) or as a **path-dependent stop** (VWAP). It helps little as a confirmation gate on a single index ETF's daily signal. On a single liquid ETF, daily volume mostly tracks volatility, so it repeats what a VIX or ATR filter already captures.
- Llorente et al. imply that for SPY/QQQ (large, tight spreads), a **high-volume down day should strengthen RSI(2)/IBS mean-reversion entries** rather than weaken them. This is a testable hypothesis, not a published rule.
- The previous round found Noise Area working only on QQQ. The paper's own ablation shows **most of the Sharpe gain comes from the VWAP stop (0.61 to 1.24), and only about 0.09 from volatility sizing (1.24 to 1.33)**. Retesting on SPY should therefore isolate the VWAP stop first.

### Gaps
- No published tests were found of OBV, Chaikin Money Flow, up/down-volume ratio, or price-volume divergence as add-on filters to daily ETF breakouts or RSI(2) with full statistics. Treat any such rule as unpublished, with all parameters free.
- The exact Stocks-in-Play stats (max DD, win rate, profit factor, trade count) were not seen in primary text. The CXO stats are paywalled.
- The Campbell-Grossman-Wang finding (high aggregate volume implies weaker index reversal) is not confirmed from source text here.

---

## Q2. Volatility filters: VIX level and term structure, VIX stretches, realized-vol regimes, vol targeting, ATR sizing, squeeze/NR7/Keltner breakouts

### Takeaway
VIX-spike filters for **long-only index mean reversion** are popular but thinly documented publicly. The canonical rule is Connors' "VIX Stretches". Published results are mostly anecdotal or paywalled, with small samples. Same-day **VIX/VIX3M backwardation** has **not** reproduced as a standalone bearish signal in 2016-2025 tests. Persistence-based variants are untested. **Volatility targeting** reliably reduces tail risk and modestly raises Sharpe for equity exposure (Harvey et al. 2018). The stronger "alpha" claims (Moreira-Muir) fail out of sample in direct comparisons (Cederburg et al. 2020). **Squeeze/NR7** breakout claims have no rigorous ETF backtest. The one primary result is that **NR4 days condition SPY intraday momentum** strongly (t = 5.14).

### Cited Findings

**A. Connors VIX Stretches (Connors & Alvarez, *Short Term Trading Strategies That Work*, 2008)**
- Rules: SPY close > 200-day SMA; VIX close >= 5% above its 10-day SMA for **3 or more consecutive days**; buy SPY at the close; exit when **SPY RSI(2) closes above 65** — [NexusFi thread](https://nexusfi.com/emini-emicro-index/18571-using-vix-time-markets.html); [book PDF](https://thechartist.com.au/wp-content/uploads/2024/12/504/ShortTermTradingStrategiesThatWork.pdf)
- A NexusFi user's EasyLanguage test (1997 to Mar 2011, $20 round-trip cost) "did rather well", but no numbers were visible. Another commenter notes the code has no stops — [NexusFi](https://nexusfi.com/emini-emicro-index/18571-using-vix-time-markets.html)
- Related: buying SPY when VIX closes >20% above its 10-day SMA and holding until VIX closes back below that SMA gave an average return of 0.13%, median 0.57%, 11 wins out of 18 trades (Schaeffer's, 2014). The sample is tiny — [Schaeffer's](https://www.schaeffersresearch.com/content/news/2014/12/12/how-to-trade-a-surging-vix-by-the-numbers)
- QuantifiedStrategies "VIX strategy for the S&P 500" [paywalled rules]: 328 trades, average gain 0.5%, **win rate 75%, PF 2, CAGR 5.2%** — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/vix-trading-strategy-for-the-s-and). Another QS variant buys SPY when VIX makes a new 20-day high **and** VIX RSI(5) > 70 — [QS VIX backtest](https://quantifiedstrategies.substack.com/p/vix-futures-trading-strategy-backtest-4a9)
- Concretum (2026) "A Profitable Strategy for Short-Term…": VIX "volatility burst" signal plus sizing for prolonged weakness plus a rebound exit, executed MOC on SPY. Jan 2007 to Jun 2026, **10.8% CAGR net, active 14% of days**. The rules are paywalled — [Concretum Substack](https://concretumgroup.substack.com/p/a-profitable-strategy-for-short-term)

**B. VIX term structure**
- A GitHub reference strategy holds SPY only when the prior day's VIX3M/VIX > 1.0 (contango) and scales by realized vol. It shows **information ratio -0.554 and active return -6.69% per year** versus SPY — [GitHub Filip303](https://github.com/Filip303/Simple-Strategy)
- An independent 2016-2025 check: VIX > VIX3M on about 7.6% of days, and the signal "does not reproduce" as a bearish trigger — [McMillan VX3-VX1 monitor doc](https://agent-jay-ser5.tail14ee01.ts.net/docs/vix-monitors/vx3-vx1-mcmillan.html). The information was in the *duration* of backwardation (2011, 2018, 2020 episodes); brief spikes resolved quickly — [thetrading.tools](https://www.thetrading.tools/vix-term-structure). Common thresholds: ratio > 1.0 = backwardation, < 0.90 = strong contango, with a risk-on/off switch at 0.95/1.00 (no backtest given) — same source.

**C. Volatility targeting and scaling**
- Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert, "The Impact of Volatility Targeting", JPM Fall 2018, 60+ assets from 1926. Vol scaling **raises Sharpe for equities and credit** (leverage effect) and has a negligible effect for bonds, FX and commodities. It **reduces the left tail and vol-of-vol in all asset classes** and reduces max DD for 60/40 and risk parity — [Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf); [Quantpedia](https://quantpedia.com/the-impact-of-volatility-targeting-on-equities-bonds-commodities-and-currencies). US equities Sharpe rises from about 0.40 to 0.48-0.51 [SECONDARY] — [Alpha Architect](https://alphaarchitect.com/volatility-targeting-improves-risk-adjusted-returns/)
- Cederburg, O'Doherty, Wang & Yan, JFE 2020, 138(1) 95-117, 103 strategies: vol-managed portfolios **do not systematically beat** unmanaged ones in direct comparison. Spanning-regression alphas are not achievable in real time because the parameters are unstable — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117); [Alpha Architect](https://alphaarchitect.com/?p=59058). DeMiguel, Martín-Utrera & Uppal (JF 2024) find a multifactor vol-managed version does beat out of sample, net of costs — [LBS](https://lbsresearch.london.edu/id/eprint/3716)
- In Beat the Market, vol-targeting the intraday strategy (target 2% daily, 14-day realized SPY vol, cap 4x) took Sharpe from 1.24 to 1.33 — [paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)

**D. Volatility contraction and squeeze**
- No rigorous ETF backtest of the TTM Squeeze was found. Vendor claims ("75%+ win rate") have no sample or PF — [Simpler Trading](https://www.simplertrading.com/?p=811028). QuantConnect squeeze-on-stock-universe tests show a 52-55% win rate with profit/loss ratio 1.06-1.14. Another shows a 73% win rate, but the average loss is twice the average win — [QC backtest 1](https://quantconnect.com/terminal/cache/embedded_backtest_defe22ea8f146d5740a1e68277c7affe.html); [QC 2](https://quantconnect.com/terminal/cache/embedded_backtest_5bd4ce268540b69b5bff8356c98ce254.html); [QC 3](https://quantconnect.com/terminal/cache/embedded_backtest_84dd3907db265a3ef4e7ced003177c92.html)
- NR7 on NDX since 1986: buying at the close of an NR7 day that follows a wide-range down day and holding several days was positive. NR7 direction mattered little — [Quantifiable Edges 2008](https://quantifiableedges.blogspot.com/2008/04/what-happens-when-range-rapidly.html). No SPY/ETF NR7 breakout backtest was found.
- **[PRIMARY] NR4 as a day filter for SPY intraday momentum**: on days after an NR4 pattern, the Noise Area strategy averaged **+22 bp/day, t = 5.14, hit ratio 45%**, the best of the patterns tested (Big Tail, Strong/Weak Closure and others were weaker) — [Beat the Market PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)

**E. Volatility and daily mean reversion**
- No direct test of RSI(2) returns bucketed by VIX was found. A volatility-filter test on RSI(2) showed only a "small, non-significant" improvement — [R-bloggers "Mean reverting strategies and volatility"](https://www.r-bloggers.com/2010/09/mean-reverting-strategies-and-volatility/). RSI(2) < 15 on SPY with exit above the prior high: about 9% CAGR, about 28% time invested, MaxDD about 34% [SECONDARY] — [QuantifiedStrategies](https://quantifiedstrategies.substack.com/p/spy-trading-strategy-using-rsi-insights-4d4)

### Inferences
- For mean reversion, **inverse-vol sizing works against the edge**: bounce magnitude scales with volatility, so ATR/vol-targeted sizing shrinks exactly the trades that pay most. Fixed-fraction or VIX-*increasing* sizing (with a hard cap) is the logical hybrid. A Connors-style VIX stretch is effectively a "trade only when vol is elevated" gate. This is inference and must be tested on the ETF/VIX data.
- For trend/breakout and intraday momentum, vol targeting is supported (Harvey et al.; the paper's 1.24 to 1.33). The gain is mainly lower tail risk, not higher alpha (Cederburg et al.).
- VIX/VIX3M: a same-day > 1.0 switch looks curve-fit or useless. A **persistence rule** (for example, 3 or more consecutive days > 1.0 means flat for trend rules or "enable" for mean reversion) is the only variant with any support, and it is anecdotal.

### Gaps
- Published Sharpe/MaxDD/PF for VIX Stretches, Connors' "VIX RSI" or "VIX 10-day MA" rules from the original book were not retrieved; exact book tables were not visible.
- No rigorous study of ATR-risk sizing versus fixed-notional sizing for price-action systems on ETFs was found.
- No ETF Bollinger/Keltner squeeze (BB inside KC) backtest with out-of-sample results was found.

---

## Q3. Intraday: volatility-scaled sizing, VIX-conditional intraday momentum, opening-volume conditioning

### Takeaway
This is the best-documented area. The Noise Area plus VWAP stop plus vol-target design is fully specified in the primary text. Its Sharpe rises with VIX at the open (about 1.5 overall, about 3.5 when VIX > 40). Opening-bar relative volume is the key filter for single-stock ORB. Gao et al. show intraday momentum is stronger on high-volume, high-volatility days.

### Cited Findings (all [PRIMARY] from the paper text unless noted)
- **Noise Area definition**: move_{i,HH:MM} = |Close_{i,HH:MM} / Open_{i,9:30} - 1|; sigma_{t,HH:MM} = mean over the last 14 days. UpperBound = max(Open_{t,9:30}, Close_{t-1,16:00}) × (1 + VM·sigma); LowerBound = min(Open_t, Close_{t-1}) × (1 - VM·sigma), with base VM = 1. Signals are checked only at **HH:00 and HH:30**. Long if price > UB, short if < LB. Flatten at the close. Reverse on a cross of the opposite band. Stop (final version): long exits if price < max(UB, VWAP), short exits if price > min(LB, VWAP), checked on semi-hourly marks. **Shares_t = floor(AUM_{t-1} × min(4, 0.02/sigma_SPY,t) / Open_t)**, where sigma_SPY is the standard deviation of the last 14 daily returns — [paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- **VIX conditioning**: using VIX at the open, Sharpe is about 1.50 for all days (VIX > 6) and rises to about **3.50 when VIX > 40**, then declines at extreme levels because of few observations — same PDF; also [QuantifiedStrategies summary](https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following)
- **Lookback robustness**: Sharpe is "largely unaffected" by the sigma lookback; the best total return and Sharpe come with long windows (for example 90 days) — same PDF (FAQ)
- **Volatility multiplier**: total return falls as VM rises; the risk-adjusted optimum is near the base (figure only) — same PDF
- **Multi-asset**: across 33 futures (2007 to Sep 2024) the average Sharpe is 0.60, with only 2 negative; a diversified portfolio reaches Sharpe 1.65. Liquid ETFs and stocks, 2018 to Aug 2024, diversified: Sharpe > 2 (authors' FAQ, not peer-reviewed) — same PDF
- **Costs**: slippage measured in live trading at about $0.001/share on average (median lower) — same PDF
- Opening volume: the Stocks-in-Play RVOL (first 5 min / 14-day same-bar average >= 1, top 20) — [CXO](https://www.cxoadvisory.com/?p=45379). Gao et al. found intraday momentum stronger on high-volume and high-volatility days — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)

### Inferences
- Concrete hybrid to test with the Alpaca 1-minute data: Noise Area on SPY/QQQ, trading only when (VIX_open > its 20-day median) **or** (the prior day was NR4), with SPY/QQQ opening-30-minute RVOL > 1. Each gate is supported by a separate primary or academic result. Combining all three is unpublished and risks overfitting, so use walk-forward.
- Previous-round finding (works on QQQ only): the paper's SPY results include 2007-2015. If SPY weakness is concentrated after 2016, VIX/NR4 conditioning is the natural repair to try.

### Gaps
- No published equity curve was found for "VIX-gated" versus ungated Noise Area out of sample. The Figure 8 VIX buckets are in-sample.
- RVOL conditioning of the *index-ETF* Noise Area (as opposed to single stocks) is untested publicly.

---

## Q4. Catalogue of implementable hybrid rules and robustness verdict

### Takeaway
Robust or likely robust: (1) RVOL-selected single-stock ORB with independent replications, though cost-sensitive; (2) VWAP trailing stop on intraday momentum, a large in-paper ablation gain; (3) volatility targeting of trend/momentum systems, for tail reduction. Plausible but weakly evidenced: VIX-stretch gating of RSI(2) mean reversion; NR4 conditioning; Gao et al. volume/volatility conditioning. Likely curve-fit or unsupported: TTM/Bollinger squeeze breakouts on ETFs, same-day VIX/VIX3M switches, OBV/CMF confirmations, the 2.1-Sharpe VWAP-only QQQ rule (fails replication).

### Cited Findings: rule catalogue

| # | Rule (horizon) | Exact definition | Reported performance | OOS / replication status |
|---|---|---|---|---|
| H1 | Stocks-in-Play 5-min ORB (intraday, single stocks) | Screen: open > $5, ADV14 >= 1M, ATR14 > $0.50, RVOL(5-min) >= 1, top 20. Stop-entry at the 5-min high/low in the direction of the first bar; stop 0.1×ATR14; exit at close; risk 1% per trade; 4x cap; $0.0035/share | Sharpe 2.81, >1,600% net 2016-23, versus 0.48 unfiltered — [summary](https://www.letsdatascience.com/news/traders-adopt-orb-strategy-for-stocks-in-play-19394da2) | QC replication Sharpe 2.40 — [QC](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/). Index ORB net zero — [MQL5](https://www.mql5.com/en/blogs/post/776235) |
| H2 | Noise Area + VWAP stop + vol target (intraday, SPY) | See Q3 formulas | Sharpe 1.33, 19.6% per year, vol 14.3%, MaxDD 25%, hit 43%, 2007-2024, net — [PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content) | Ablation 0.61 → 1.24 → 1.33; futures average Sharpe 0.60 — same PDF. Earlier internal round: QQQ only |
| H3 | H2 gated by VIX_open | Trade only when VIX_open > threshold (unpublished; paper shows buckets) | Sharpe ≈ 3.5 at VIX > 40 (in-sample bucket) — same PDF | Not tested OOS |
| H4 | H2 on post-NR4 days | NR4: today's range is the smallest of the last 4 days; trade H2 the next day | +22 bp/day, t = 5.14, hit 45% — same PDF | In-sample only |
| H5 | VWAP trend (intraday, QQQ) | Long above VWAP, short below (1-min, per authors) | Sharpe 2.1, MaxDD 9.4%, 2018-23 — [Concretum](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/) | Replications negative or weak; a 2% deadband helps — [QC](https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/) |
| H6 | First-half-hour momentum, volume/vol conditioned (intraday, SPY) | Sign of the return from prior close to 10:00 → hold 15:30-16:00; strengthen on high volume or high vol days | About 6.67% per year (base), stronger on high-volume and high-vol days — [QC](https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum); [JFE](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414) | 10 other ETFs confirm in the paper; the QC replication is weaker |
| H7 | Connors VIX Stretches (daily swing, SPY) | SPY > SMA200; VIX >= 1.05×SMA10(VIX) for 3 or more days; buy at close; exit when RSI(2) > 65 | "Did rather well" 1997-2011 (no numbers) — [NexusFi](https://nexusfi.com/emini-emicro-index/18571-using-vix-time-markets.html) | No public OOS stats |
| H8 | VIX spike + SPY (daily) | VIX > 1.20×SMA10(VIX) → buy; exit when VIX < SMA10 | Average +0.13%, 11/18 wins — [Schaeffer's](https://www.schaeffersresearch.com/content/news/2014/12/12/how-to-trade-a-surging-vix-by-the-numbers) | Too few trades |
| H9 | QS VIX strategy (daily) | Rules paywalled; a variant: VIX new 20-day high and VIX RSI(5) > 70 → buy SPY | 328 trades, win rate 75%, PF 2, CAGR 5.2% — [QS](https://quantifiedstrategies.substack.com/p/vix-trading-strategy-for-the-s-and) | Unknown |
| H10 | Concretum VIX-burst MOC (daily) | Rules paywalled | 10.8% CAGR net, 14% exposure, 2007 to Jun 2026 — [Concretum](https://concretumgroup.substack.com/p/a-profitable-strategy-for-short-term) | Unknown |
| H11 | Vol-targeted trend/Faber (weekly/monthly) | w_t = min(cap, σ_target/σ̂_t) on the trend position (σ̂ = 20-60d realized) | US equities Sharpe 0.40 → about 0.50, thinner left tail — [Harvey et al.](https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf) | Cederburg 2020: no systematic OOS gain in head-to-head — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117) |
| H12 | VIX/VIX3M contango gate (daily) | Hold SPY if VIX3M/VIX(t-1) > 1.0 | IR -0.55, -6.7% per year active — [GitHub](https://github.com/Filip303/Simple-Strategy) | Fails |
| H13 | TTM/BB squeeze breakout (daily) | BB(20,2) inside KC(20,1.5×ATR) then momentum breakout | Win rate 52-55%, P/L ratio 1.06-1.14 (stock universes) — [QC](https://quantconnect.com/terminal/cache/embedded_backtest_defe22ea8f146d5740a1e68277c7affe.html) | No credible edge |
| H14 | NR7 after wide-range down day (swing, index) | Buy at close of the NR7 day following a wide-range down day; hold several days | Positive on NDX since 1986 (no full stats) — [Quantifiable Edges](https://quantifiableedges.blogspot.com/2008/04/what-happens-when-range-rapidly.html) | Single blog test |

### Inferences
- Priority test list given available data (yfinance ETF + ^VIX/^VIX3M/^VIX9D; Alpaca 1-min 2016-2026):
  1. H2 ablation on SPY/QQQ/IWM/DIA: VWAP stop on/off, vol sizing on/off, then H3/H4 gates with walk-forward thresholds.
  2. H1 on Alpaca stock 1-min data, including realistic spread and slippage. RVOL needs a point-in-time universe to avoid survivorship bias.
  3. Prior-round RSI(2)/IBS × {VIX/SMA10(VIX) > 1.05 for 1/2/3 days; VIX9D/VIX > 1; high-relative-volume down day (Llorente)} with **fixed or vol-increasing sizing**, compared against the same rule with inverse-ATR sizing.
  4. H11 on the Faber SMA / ATH-ATR rule (weekly).
- Curve-fit warning signs: thresholds chosen from in-sample buckets (VIX > 40 Sharpe 3.5), trade counts below about 100 (Schaeffer's, Reddit BB tests), and replication gaps (VWAP-only QQQ).
- Unpublished parameters to flag: H3 VIX threshold, H6 volume cutoffs, VIX9D/VIX ratio gates, persistence counts for VIX/VIX3M, and all OBV/CMF settings.

### Gaps
- Full statistics (MaxDD, PF, trade count) for H1, H7, H9 and H10 are not in accessible sources (paywalled or not retrieved).
- No 2020-2026 out-of-sample re-test of Connors VIX rules was found.
- No study directly comparing ATR-based sizing with fixed sizing on mean-reversion ETF systems was found.
