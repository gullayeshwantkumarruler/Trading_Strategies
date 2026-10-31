# Intraday price-action strategies for US stocks and ETFs (1–5 min and hourly bars)

Scope: US equities and ETFs only. Evidence from 2023–2026 is prioritised, and older seminal work is labelled as context. Every number below comes from the cited source. Practitioner replications that are not peer-reviewed are labelled as such.

PDFs downloaded to `C:\Users\Acer\Pictures\research_papers\paper1\papers\price_action\` (none were executed; text was extracted for reading only):
- `2024_Zarattini_Aziz_Barbon_Beat_the_Market_SPY_intraday_momentum.pdf`, from the Concretum/SFI working paper 24-97 (Concretum-hosted copy).
- `2021_Baltussen_Da_Lammers_Martens_Hedging_demand_market_intraday_momentum.pdf` (JFE 142, 2021; copy hosted on Zhi Da's Notre Dame page).
- `2021_Barbon_Beckmeyer_Buraschi_Moerke_LETF_option_imbalances_end_of_day.pdf` (St. Gallen WP 2021/14).
- `2022_Li_Sakkas_Urquhart_Intraday_time_series_momentum_global.pdf` (accepted version, Univ. of Reading repository).
- I could not get an open PDF of Gao-Han-Li-Zhou (JFE 2018). The super.so link returned XML rather than a PDF, and the only other copy found was an unofficial mql5 mirror, so I did not save it. SSRN-only papers (Stocks-in-Play ORB SSRN 4729284, QQQ ORB SSRN 4416622, VWAP "Holy Grail") were not downloaded because SSRN blocks direct download.
- Note: `2013_Pagonidis_IBS_effect_mean_reversion_ETFs.pdf` was already in that folder. Another process put it there, not this research.

---

## Q1. Strategy catalogue: exact rules, bar size, universe, holding time, costs, reported stats, sample, cost/post-publication survival

### Takeaway
The best-specified, codeable intraday strategies all come from the Concretum Group / Zarattini-Aziz-Barbon papers (5-min ORB on QQQ, 5-min ORB on "Stocks in Play", the SPY "Noise Area" momentum, and the VWAP trend). The academic anchors are market intraday momentum (Gao et al. 2018; Baltussen et al. 2021) and end-of-day hedging-flow effects (Barbon et al.). Each Concretum headline result relies heavily on cost assumptions and leverage (4x cap). Independent replications of the QQQ ORB show the gross result reproduces but most or all of the edge disappears at about 2 cents/share of slippage.

### Cited Findings

**S1. 5-minute ORB on QQQ/TQQQ ("Can Day Trading Really Be Profitable?", Zarattini & Aziz, SSRN 4416622)**
- Rules: 5-min bars. If the first 09:30–09:35 candle is bullish, go long at the open of the second candle (09:35). If bearish, go short. Doji means no trade. Stop at the opposite extreme of the first candle. Target 10R, otherwise exit at the close. Risk 1% of equity per trade, leverage capped at 4x. $25k start. Commission $0.0005/share, **no slippage modelled**. Sample Jan 2016–Feb 2023. This is a directional entry at 9:35, not a range breakout. — [danfin.net summary](https://danfin.net/opening-range-breakout-research); [SSRN 4416622](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622)
- Reported results: QQQ 676% total, 33% annualised, vol 29%, Sharpe 1.13, MDD 22%, win rate 24%, +0.13R/trade, about 1,795 trades. TQQQ 1,484% total, 48% annualised, Sharpe 1.19, MDD 28%, +0.18R/trade. Buy-and-hold QQQ: Sharpe 0.73, MDD 36%. A parameter-searched TQQQ variant (5% ATR stop, no target) reports 9,350%, which carries high overfitting risk. — [danfin.net](https://danfin.net/opening-range-breakout-research)
- Independent replication (GitHub, not peer-reviewed), same rules on QQQ 5-min bars 2016–Feb 2023:
  - Gross: Sharpe 1.06, CAGR 30.4%, MDD 22.4%, t = 1.79.
  - With $0.02/share entry slippage (stops pay an extra $0.04): Sharpe 0.23, CAGR 2.7%, MDD 43.9%.
  - Break-even at about 2.2¢/share slippage. The +10R target is hit on only about 2–3% of trades.
  - An NQ 09:25 confirmation filter gives net Sharpe 0.77 (t = 2.05), but 76% of its PnL comes from 2022 alone.
  - Placebo/bootstrap CIs overlap with buy-and-hold (Sharpe 0.72).
  - Source: [giovannibrusco/zarattini-2023-orb-qqq](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Second replication (MQL5 blog, Sept 2026, CFDs on NQ/SPX/Dow/DAX/FTSE, 2015–Jun 2026):
  - Gross reproduces (NQ about +0.13R/trade, hit rate about 23%; SPX +0.119R).
  - Net of CFD spread/slippage, no market is distinguishable from zero and 4 of 5 are negative. NQ is about +0.002R.
  - The rule was negative in every market in 2015–2017. The 2021–2026 out-of-sample period gives at most +0.06R on NQ.
  - Against a random-direction bracket, the first candle still carries about 0.10–0.13R of direction information (|t| ≥ 2), which is roughly the cost of a trade.
  - Source: [MQL5 blog](https://www.mql5.com/en/blogs/post/776235)

**S2. 5-minute ORB on "Stocks in Play" ("A Profitable Day Trading Strategy for the U.S. Equity Market", Zarattini, Barbon & Aziz 2024, SSRN 4729284 / SFI 24-98)**
- Universe (daily screen, all US listings, >7,000 stocks, 2016–2023):
  - Open > $5.
  - 14-day average volume ≥ 1M shares.
  - 14-day ATR > $0.50.
  - Relative Volume ≥ 100%, defined as the first-5-minute volume divided by the 14-day average of first-5-minute volume.
  - Trade only the top 20 names by Relative Volume.
  - Source: [CXO Advisory](https://www.cxoadvisory.com/individual-investing/intraday-trading-of-overactive-stocks-via-opening-range-breakout/); [QuantConnect replication](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- Entry: direction comes from the first 5-min candle. A bullish candle puts a buy-stop at the OR high, a bearish one a sell-stop at the OR low, and a doji means no trade. Stop is 10% of 14-day ATR from the entry. Exit at the close if not stopped. Size so a stop-out loses 1% of capital, with a 4x leverage cap. $25k start, commission $0.0035/share (IBKR Pro Tiered). — [CXO](https://www.cxoadvisory.com/individual-investing/intraday-trading-of-overactive-stocks-via-opening-range-breakout/); [danfin.net](https://danfin.net/opening-range-breakout-research)
- Results:
  - Top-20 Stocks in Play: 1,637% total, CAGR 41.6%, vol 14.8%, **Sharpe 2.81**, hit ratio 48.4%, MDD 12%, alpha 35.8%, beta about 0.
  - Same ORB on the unfiltered universe: 29% total, CAGR 3.2%, Sharpe 0.48.
  - Per-trade edge by Relative Volume: about −0.02R below 100%, +0.08R above 100%, +0.38R above 3,000%.
  - Source: [danfin.net](https://danfin.net/opening-range-breakout-research); headline Sharpe 2.81 / >1,600% / 36% alpha also on [EconPapers abstract](https://econpapers.repec.org/RePEc:chf:rpseri:rp2498)
- OR length sensitivity (Stocks in Play):

  | OR length | Sharpe | CAGR | MDD |
  |---|---|---|---|
  | 5 min | 2.81 | 41.6% | n/a here |
  | 15 min | 1.43 | 17.4% | 11% |
  | 30 min | 0.21 | 2.3% | 35% |
  | 60 min | 0.40 | 4.1% | 21% |
  | Equal-weight combo | 1.99 | n/a here | 7% |

  Source: [danfin.net](https://danfin.net/opening-range-breakout-research)
- Caveats noted by a secondary reviewer: no separate out-of-sample period. Spreads, slippage, short availability and stop fills are not fully modelled. — [danfin.net](https://danfin.net/opening-range-breakout-research)
- Sources disagree on the stop: CXO/danfin give 10% of ATR, while QuantConnect describes the stop only as "a function of entry price and 14-day ATR". — [QuantConnect](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)

**S3. SPY "Noise Area" intraday momentum ("Beat the Market", Zarattini, Aziz & Barbon 2024, SFI 24-97, SSRN 4824172). Rules read directly from the downloaded PDF.**
- Noise Area: for each time-of-day HH:MM, σ(HH:MM) is the 14-day average of |Close(HH:MM)/Open(9:30) − 1|.
  - UpperBound = max(Open_t, Close_{t−1}) × (1 + σ)
  - LowerBound = min(Open_t, Close_{t−1}) × (1 − σ)
  - The max/min term is the gap adjustment. An optional volatility multiplier VM scales σ.
  - Source: [Beat the Market PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Entry: check only at HH:00 and HH:30, so the first possible trade is at 10:00. Go long if price is above UB and short if below LB. Use 1-min data and market orders. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Exit:
  - Base model: reverse on a cross of the opposite band.
  - Improved model: trailing stop at max(UB, VWAP) for longs and min(LB, VWAP) for shorts. VWAP uses regular-hours data only. Stops are checked only on the half-hour.
  - All positions are flat at 16:00.
  - Source: [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Sizing: shares = AUM_{t−1} × min(4, 2% / σ_SPY,14d) / Open_t, where σ_SPY,14d is the 14-day std of daily returns. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Costs: $0.0035/share commission (IBKR entry level; about 20% of days qualify for $0.002) plus $0.001/share slippage. The slippage figure was measured in a live IBKR experiment in April 2024: more than 1,000 random-side $100k SPY market orders, mean slippage about $0.001 and median $0.0005 versus the minute open. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Results 2007–early 2024:

  | Variant | Total return | IRR | Vol | Sharpe | Hit ratio | MDD | Other |
  |---|---|---|---|---|---|---|---|
  | Base (opposite-band stop, 1x) | 178% | 6.2% | 10.9% | 0.61 | 54% | 21% | worst day −10.3% |
  | Current band + VWAP stop, 1x | 380% | 9.7% | 7.7% | 1.24 | 43% | 12% | skew +1.29; trades rose from 5,494 to 7,668 |
  | + vol-targeted sizing | 1,985% | 19.6% | 14.3% | 1.33 | 43% | 25% | alpha 19.6%, beta −0.07 |
  | SPY buy-and-hold | 227% | 7.2% | 20.2% | 0.45 | n/a | 56% | n/a |

  Source: [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Regime notes from the paper: Sharpe rises with VIX at the open (about 1.5 when VIX > 6, about 3.5 when VIX > 40, then falls at extreme VIX). The authors link profitability to dealer gamma, where negative gamma means more trending. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- I found no independent out-of-sample replication. The search summary notes that Concretum runs a live experiment of its own. — [Concretum page](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)

**S4. VWAP trend-following ("VWAP: The Holy Grail for Day Trading Systems", Zarattini & Aziz 2023)**
- Reported: QQQ VWAP trend strategy grew $25,000 to $192,656 net of commissions (671%). The TQQQ version grew $25,000 to $2,085,417. One summary cites QQQ MDD of 9.4%. — [search summary of ResearchGate/Scribd copies](https://www.researchgate.net/publication/376217460_Volume_Weighted_Average_Price_VWAP_The_Holy_Grail_for_Day_Trading_Systems); full text not accessible (403)
- Exact rules could not be verified from the primary source. In Beat the Market, the authors use VWAP (regular-hours only) as an intraday supply/demand regime line and as a trailing stop (long exits when price crosses below VWAP). — [Beat the Market PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)

**S5. Market intraday momentum: first half-hour → last half-hour (Gao, Han, Li & Zhou, JFE 2018). Seminal context.**
- SPY, 1993–2013. The first half-hour return (previous close to 10:00) predicts the last half-hour return (15:30–16:00). Trading rule: at 15:30 take the sign of the first half-hour return and hold to the close. — [working-paper copy](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf); [summary](https://tapescript.io/blog/intraday-momentum-strategy)
- In-sample R² of 1.6%, as reported by Li-Sakkas-Urquhart. — [Li, Sakkas & Urquhart accepted version](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf)
- A search snippet reports out-of-sample R² of 1.2% and says predictability was lower after 2001 decimalization. I could not confirm this beyond the snippet. — [unofficial mirror](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)

**S6. Market intraday momentum generalised (Baltussen, Da, Lammers & Martens, JFE 2021)**
- More than 60 futures, 1974–May 2020. The return over the "rest of day" (previous close to 15:30) positively predicts the last-30-minute return everywhere. The authors tie this to hedging of short gamma (options dealers, leveraged ETFs). The effect reverts over the next days. — [JFE PDF](https://www3.nd.edu/~zda/intramom.pdf)
- Subsamples 1974–1999 vs 2000–2020 are "similar". The strategy results exclude transaction costs. The authors state that in S&P 500 futures the net Sharpe stays positive at a 1-tick cost, but frequent rebalancing may make the strategy unexploitable for many investors. — [JFE PDF](https://www3.nd.edu/~zda/intramom.pdf)

**S7. End-of-day effects from LETF rebalancing and option gamma (Barbon, Beckmeyer, Buraschi & Moerke 2021)**
- Large negative aggregate gamma imbalance relative to dollar volume produces end-of-day momentum, and large positive imbalance produces reversal. The LETF rebalancing effect is economically larger than the options channel. Both effects revert at the next day's open (temporary price pressure). — [WP PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/5a99db31-0d37-4f86-9502-8cb0f3bff4fe/content)

**S8. Cross-sectional end-of-day reversal in single stocks (Soebhag, Baltussen & Da, Nov 2024, SSRN)**
- Tests whether stocks that fell during the day rebound in the last 30 minutes. Predictors are overnight, the first half-hour, and mid-day to one hour before the close; the next-to-last half-hour is skipped to avoid bounce. Universe excludes stocks below the NYSE 10th size percentile and those under $5. US stocks 1993–2019. Results are behind a paywall in the summary I accessed. — [CXO summary](https://www.cxoadvisory.com/?p=46335)

**S9. Overnight vs intraday decomposition and the overnight drift (Boyarchenko, Larsen & Whelan, RFS 2023; NY Fed 2026 update)**
- E-mini S&P 500, 1998–2018: close-to-close about 4.5%/yr, close-to-open about 3.1%, open-to-close about 1.4% (gross). The 2–3 a.m. ET hour earned about 3.6%/yr gross but turns negative after spreads. 8:30–10:00 ET averaged about −3.9%/yr, an opening reversal. — [CXO summary](https://www.cxoadvisory.com/?p=33743); [RFS listing](https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html)
- July 2026 update: the 2–3 a.m. drift, previously about 3.7%/yr and more than 60% of the E-mini's 5.9% close-to-close return, averaged about zero in 2021–2025 (1,245 days). The same holds for NQ and YM. The main cause is that dispersion of end-of-day signed volume fell from 6.5% to 2.9%. NightShares overnight ETFs (NSPY, NIWM) launched in June 2022 and closed about 14 months later. — [Liberty Street Economics, "The Disappearing Overnight Drift"](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- A 2025/26 SSRN paper (Iwanaga & Sakemoto) finds that a high overnight return negatively predicts the first half-hour return for US indices, i.e. an opening reversal. — [SSRN 5807282](https://papers.ssrn.com/sol3/Delivery.cfm/5807282.pdf?abstractid=5807282)

**S10. Gap-and-go vs gap-fade at the open**
- Only descriptive or practitioner evidence was found.
- One base-rate table for US stocks reports that 1%+ up-gaps fill the same day only about a quarter of the time, with positive average open-to-close returns after them. That points to continuation, not fade, for large gaps. — [thetrading.tools gap analysis](https://www.thetrading.tools/gap-analysis)
- Older post: SPY gapped up on 54.8% of days since 1993, and those gaps filled the same day 68.9% of the time. This is not conditioned on gap size. — [Global Macro Monitor 2011](https://global-macro-monitor.com/2011/05/30/fading-the-open/)
- CXO studied SPY gaps vs open-to-close returns for 1993–Mar 2025, but the result is paywalled. — [CXO](https://www.cxoadvisory.com/?p=46627)
- Related evidence: the ORB "Stocks in Play" filter (S2) behaves like a gap-and-go filter on news stocks, and its edge rises sharply with opening relative volume. — [danfin.net](https://danfin.net/opening-range-breakout-research)

**S11. Intraday reversal after large moves (SPY microstructure)**
- arXiv 2025, SPY NBBO quotes 2018–2023: short-horizon responses switch between momentum and reversal depending on lag and push size. Large negative pushes are followed by stronger rebounds than equally large positive pushes, which the authors attribute to asymmetric liquidity replenishment. — [arXiv 2511.06177](https://arxiv.org/pdf/2511.06177v1)
- Older context: intraday reversals follow large opening price changes in S&P 500 futures. — [HKBU repository](https://scholars.hkbu.edu.hk/en/publications/intraday-price-reversals-for-index-futures-in-the-us-and-hong-kon/)

### Inferences
- Codeable priority list for a 1–5-min backtest:
  1. S3 Noise Area SPY/QQQ: fully specified from the PDF, liquid ETF, cheap execution, half-hour decisions are tolerant to latency.
  2. S2 Stocks-in-Play ORB: highest reported Sharpe but the most sensitive to execution and data. It needs survivorship-free all-stock 1-min data, borrow availability and stop-fill modelling.
  3. S5/S6 last-half-hour momentum on SPY or ES as a 15:30→16:00 overlay.
  4. S1 QQQ ORB, only as a benchmark, because two independent replications put it at about zero net.
- Templates I propose for the less-specified effects. These are my constructions and have not been tested in any source:
  - **VWAP mean reversion (S4 inverse):** fade a k×ATR deviation from session VWAP and exit at VWAP. Expect it to work on positive-gamma or low-VIX days and fail on negative-gamma days, given S3/S7 (Barbon et al.: positive gamma means reversal).
  - **Gap-fade:** fade only small gaps (<0.5%) and trade large/news gaps with ORB continuation, per S10.
  - **First-hour reversal:** go against the overnight return during 9:30–10:00, motivated by the −3.9%/yr 8:30–10:00 window (S9) and Iwanaga & Sakemoto. Test it after 2021 because the overnight-drift regime changed.
- Most effects share one mechanism: dealer gamma and LETF rebalancing flows. Adding a gamma-sign or VIX-regime filter is a natural way to switch between momentum (S3/S5/S6) and reversal (VWAP-MR, S7 positive-gamma case).

### Gaps
- **Not verified from primary text:**
  - VWAP "Holy Grail" exact rules (paper not accessible).
  - Stocks-in-Play profit factor and full cost-sensitivity table (CXO paywall; SSRN PDF not downloaded).
- **No rigorous US-equity paper found:**
  - Gap-and-go vs gap-fade with costs.
  - VWAP mean reversion.
  - "First-hour reversal" as a standalone strategy.
  - Closing-auction (MOC imbalance) trading strategies for retail.
- **Not reached within the tool budget:**
  - Soebhag-Baltussen-Da end-of-day reversal results (paywalled summary).
  - Quantpedia, Alpha Architect, QuantSeeker and Robot Wealth posts. They were not fetched, so their specific backtests are not included.

---

## Q2. Which effects have the strongest recent (2023–2026) out-of-sample evidence, and which have decayed?

### Takeaway
No strategy here has independent, peer-reviewed post-2023 out-of-sample confirmation. The strongest evidence is cross-asset, multi-decade intraday momentum (Baltussen et al., stable 1974–1999 vs 2000–2020; 12 of 16 international markets in Li et al.) and its documented gamma/LETF mechanism. Decay is documented for the overnight drift (about zero in 2021–2025) and, per independent replications, for the 5-min QQQ/index ORB net of costs. The Concretum Noise Area and Stocks-in-Play results are recent but in-sample and author-reported only.

### Cited Findings
- Intraday momentum is similar in 1974–1999 and 2000–2020 subsamples across asset classes. — [Baltussen et al. JFE 2021](https://www3.nd.edu/~zda/intramom.pdf)
- International evidence, 2005–2017: the first half-hour predicts the last half-hour in 12 of 16 markets. 11 of 18 timing portfolios have Sharpe > 1 (before costs). — [Li, Sakkas & Urquhart (J. Financial Markets 2022)](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf)
- The effect is weaker in Asia-Pacific markets than in the US. — [Limkriangkrai, Chai & Zheng 2023, via search summary](https://hull-repository.worktribe.com/output/3679202)
- I found no 2024–2026 study that specifically re-tests Gao et al. on SPY after 2013. The practitioner write-ups found restate the original result without new tests. — [TapeScript](https://tapescript.io/blog/intraday-momentum-strategy); [QuantifiedStrategies note](https://substack.com/@quantifiedstrategies/note/c-151224359)
- ORB decay and cost fragility:
  - QQQ ORB net Sharpe falls from 1.06 to 0.23 at 2¢ slippage. No 2024–2026 out-of-sample result exists in the repo. An external ES futures run for Mar–Sep 2026 found no edge even gross. — [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
  - Index-CFD ORB: 2021–2026 out-of-sample gives at most +0.06R gross on NQ, and the rule is net-negative or zero across 5 indices. — [MQL5 replication](https://www.mql5.com/en/blogs/post/776235)
- Overnight drift decayed to about zero in 2021–2025. The authors attribute this to lower dispersion of closing order imbalances. — [NY Fed Liberty Street, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- Noise Area SPY: the sample runs to early 2024 and the paper reports no holdout. The authors note that the VWAP-stop improvement was chosen after observing base-model failures. — [Beat the Market PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)

### Inferences
- Ranking by robustness of evidence:
  1. Last-half-hour momentum (index level; mechanism-backed, multi-asset, multi-decade).
  2. Noise Area SPY momentum (a recent, more aggressive variant of the same mechanism; author-only).
  3. Stocks-in-Play ORB (very high reported Sharpe but in-sample with simplified fills).
  4. QQQ/index 5-min ORB (replications say about zero net).
  5. Overnight drift (decayed).
- A 2024-2026 holdout test of S3 and S2 should be the first thing a backtest checks. Neither paper's sample extends past early 2024.

### Gaps
- No independent out-of-sample replication was found for the Stocks-in-Play ORB or the Noise Area SPY strategy. A QuantConnect community replication of SiP exists, but its numeric results were not retrieved.
- No post-2013 SPY-specific test of Gao et al. was found.

---

## Q3. Which execution assumptions matter most?

### Takeaway
Slippage per share matters far more than the commission tier. The ORB family dies at about 2¢/share. Noise Area SPY assumes 0.1¢/share slippage plus 0.35¢ commission, and makes decisions only at half-hour marks. Fill convention (signal on bar close, fill at next bar open) and stop-fill modelling are the other big drivers, along with the 4x leverage cap, which binds on about 60% of QQQ ORB trades.

### Cited Findings
- Commission assumptions vary across Concretum papers:
  - $0.0005/share in the QQQ ORB, with no slippage. — [danfin.net](https://danfin.net/opening-range-breakout-research)
  - $0.0035/share in the Stocks-in-Play ORB (IBKR Pro Tiered, Dec 2023). — [CXO](https://www.cxoadvisory.com/individual-investing/intraday-trading-of-overactive-stocks-via-opening-range-breakout/)
  - $0.0035/share (falling to $0.002 above 300k shares/month) plus $0.001 slippage in Noise Area SPY. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Measured live SPY market-order slippage versus the minute's open price: mean about $0.001, median about $0.0005 (1,000+ orders, $50M notional, April 2024, $100k clips). The authors caution that it rises with size. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- QQQ ORB break-even is about 2.2¢/share of entry slippage with stops at 2x. The QQQ spread is about 1¢. — [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- ORB on CFDs: costs consume 6–12% of initial risk per trade, which wipes out the edge. The author adds a minimum risk floor of 2x round-trip cost. — [MQL5](https://www.mql5.com/en/blogs/post/776235)
- About 60% of QQQ ORB trades are capped by the 4x leverage limit. Removing the cap lifts the reported total from 676% to about 1,630%, so the reported results depend heavily on margin rules. — [danfin.net](https://danfin.net/opening-range-breakout-research)
- Tighter stops cut drawdown but raise turnover. Noise Area trades rose from 5,494 to 7,668 with the VWAP stop, so cost sensitivity rises too. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Restricting decisions to HH:00/HH:30 is a deliberate guard against noise and overtrading. Trades fire at the half-hour even if the band was breached minutes earlier. — [PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Beat-the-Market.pdf)
- Baltussen et al. report gross results only. The S&P 500 futures last-30-minute strategy stays positive at a 1-tick cost. — [JFE PDF](https://www3.nd.edu/~zda/intramom.pdf)

### Inferences
- Backtest conventions I recommend, derived from the sources above:
  - Signal on the bar close, fill at the next bar's open (the Concretum slippage study measures against the next minute's open).
  - Stops fill at the stop price plus at least 1–2 ticks, and gap-through stops fill at the bar open.
  - Model short-borrow and halts for SiP names.
  - Run a slippage sweep from 0 to 5¢/share, and report the break-even slippage alongside Sharpe.
- At zero-commission brokers, payment-for-order-flow routing usually means worse price improvement on market orders. Model slippage rather than assuming $0. (This is my reasoning; I found no source quantifying it for these strategies.)
- For S2, $0.0035/share commission matters more on low-priced stocks: the screen allows stocks down to $5, so commission is a larger share of the R per trade than on SPY. (My reasoning.)

### Gaps
- No source quantified slippage for small and mid-cap Stocks-in-Play at the 9:35 breakout, where spreads are widest.
- No source compared zero-commission PFOF fills with IBKR-tiered fills for these strategies.
