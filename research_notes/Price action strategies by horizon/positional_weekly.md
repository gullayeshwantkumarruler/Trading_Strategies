# Positional (weekly bars, weeks-to-months holding) price-action strategies for US stocks and ETFs

Scope note: these notes cover 8-12 codeable positional strategies, their reported evidence, which of them hold up after 2010 / out of sample, and how survivorship bias affects single-stock breakout and new-high systems. Older seminal work is marked **[CONTEXT, pre-2010]**. Items marked **[UNVERIFIED]** come from the researcher's background knowledge and were *not* confirmed against a fetched source this session. The report writer should either drop them or label them as such.

PDFs saved to `C:\Users\Acer\Pictures\research_papers\paper1\papers\price_action\` by this researcher:
- `2025_Zarattini_Does_Trend_Following_Still_Work_on_Stocks.pdf` (Zarattini, Pagani & Wilcox; all-time-high breakout plus ATR trailing stop on survivorship-free US stocks, 1950-2024)
- `2004_George_Hwang_52_Week_High_Momentum.pdf` (J. Finance 2004) **[CONTEXT]**
- `2024_Zhu_Zhu_Image_induced_importance_weights_price_trend.pdf` (arXiv 2408.08483; image/ResNet price-pattern follow-up to Jiang-Kelly-Xiu; Chinese A-shares)
- I could not retrieve a readable open-access PDF of Jiang-Kelly-Xiu (2023) or Lo-Mamaysky-Wang (2000). The NBER w7613 PDF is a JBIG2 scan with no extractable text.

---

## Q1. Strategy catalogue: exact rules, universe, holding period and reported stats

### Takeaway
The best-documented and most codeable positional systems are the following. (a) All-time-high or 52-week-high breakout entries with a wide ATR trailing stop on single stocks (Wilcox-Crittenden 2005; Zarattini-Pagani-Wilcox 2025). (b) Faber's 10-month SMA filter on indices and ETFs. (c) 52-week-high-proximity cross-sectional ranking (George-Hwang). Chart-pattern evidence (LMW 2000; CNN image models) is statistically interesting but mostly tested at short horizons. The image-based edge is weakest at weekly and monthly horizons.

### Cited Findings

**S1. All-time-high (ATH) breakout + 10x ATR trailing stop, single US stocks (Wilcox-Crittenden lineage)**
- Rules: a stock qualifies at close of day t if its close is above $10 (unadjusted) and its 42-day average dollar volume is above $1M (CPI-adjusted back through time, about $80k in 1951, $300k in 1980 and $600k in 2005). Entry: close >= highest adjusted close in its history, buy at next open. — [Zarattini, Pagani & Wilcox 2025 PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Exit: trailing stop = ATH_t x (1 - 10 x ATR42_t / Close_t), ratcheted up and never lowered. Sell at next open if the close is below the stop. This stop is about 10 ATRs wide by design, to avoid exits on pullbacks. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Costs: 0.50% per round turn in the trade-level study. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Trade stats: about 66,000 trades, 1950-2024. Win rate 43.9%. Average win +1.90R, average loss -0.70R. Average winning trade held about 370 days. 8% of trades lost more than 1R, mainly from gap-downs, and 22% gained more than 1R. Fewer than 7% of trades produced most of the cumulative profits. The core statistics hold out of sample for 2005-2024. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf); [Concretum summary](https://concretumgroup.com/does-trend-following-still-work-on-stocks/)
- Portfolio version: the universe is Russell 3000 members passing the $10 and $1M filters, buying every new ATH. Weight per stock = 30% / σ_i(42-day annualized) x 1/max(200, N_holdings). Gross leverage is capped at 200%. Weights are rebalanced daily. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Portfolio results 1991-2024 (theoretical, no costs): CAGR 15.02%, vol 14.93%, Sharpe 0.85, Sortino 1.11, max drawdown 31.75%, alpha 6.19%/yr (p = 0.05%), beta 0.66. The market returned CAGR 11.18%, Sharpe 0.54, max drawdown 54.68%. — [Zarattini et al. 2025, Table 2](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- With realistic costs (IBKR commissions, I-Star slippage, borrow cost, no fractional shares; AUM reset each year):

  | AUM | CAGR | Sharpe | Max drawdown | Alpha |
  |---|---|---|---|---|
  | $100k | 2.45% | 0.06 | 39.8% | -4.63% |
  | $1M | 9.01% | 0.49 | 36.5% | +0.91% |
  | $10M | 12.53% | 0.70 | 34.3% | +4.13% |
  | $100M | 10.97% | 0.65 | 36.2% | +2.72% |

  At $10M, cost drag is about 2.5%/yr. At $100k, drag is above 10%/yr, almost all commissions. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- A "turnover control" layer (skip small rebalances, spread trades over days, skip trades where commission is too large relative to size) cut commission drag at $100k from about 10% to under 1%. It cut slippage at $100M from 3% to 1.3%/yr. The exact thresholds are proprietary ("contact us"). — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Original 2005 study **[CONTEXT]**: 24,000+ securities over 22 years, all-time-high entry, 10-ATR stop, 0.5% round-turn costs, 18,000+ trades. ATR multiples of 8-12 were tested. Tighter stops gave slightly lower win rates and slightly higher win/loss ratios. Sources differ on whether the entry used daily or weekly closes. — [UPenn copy of Wilcox & Crittenden](https://www.cis.upenn.edu/~mkearns/finread/trend.pdf); [Quantpedia](https://quantpedia.com/strategies/trend-following-effect-in-stocks); [review blog](https://adiscountedview.blogspot.com/2016/04/research-review-does-trend-following.html)
- Critique: the skew means small accounts holding few names can easily miss the few outliers that drive profits. — [Harbourfront Quant](https://harbourfrontquant.substack.com/p/does-trend-following-work-on-single)

**S2. 52-week-high proximity (George & Hwang 2004) [CONTEXT, pre-2010]**
- Rules: monthly, rank all CRSP stocks by PTH = P_t / max(P over the past 12 months). Long the equal-weighted top 30% and short the bottom 30%. Hold 6 months as overlapping (6,6) portfolios, following JT/MG methodology. Sample July 1963-Dec 2001. — [George & Hwang 2004, Table I](https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf)
- Monthly winner-minus-loser returns in Table I: 52-week high 0.45% (t = 2.00), JT individual momentum 0.48% (t = 2.35), MG industry momentum 0.45% (t = 3.43). This is the all-months table. The paper's headline result is that 52-week-high nearness dominates past returns in head-to-head comparisons, and its profits do not reverse in the long run. — [George & Hwang 2004](https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf)
- Post-publication: Lobão & Fernandes (2017), 1980-2014, found an insignificant overall return. Results were significantly positive in 1980-2000 and significantly negative in 2001-2014, partly due to the 2009 momentum crash. — [EconPapers / Lobão 2017](https://econpapers.repec.org/RePEc:cuf:journl:y:2017:v:18:i:2:lobao)
- A later SSRN working paper reports return decay over time in both JT momentum and 52-week-high strategies, with less decay for the 52-week high. — [Scribd copy, SSRN 4587697](https://www.scribd.com/document/694152012/SSRN-id4587697) (secondary; not independently verified)
- Internationally, 52-week-high profits are positive in 17 of 18 markets (12 significant) and survive controls for JT momentum. — [UCP repository thesis](https://repositorio.ucp.pt/entities/publication/c22f4883-b81e-46bd-a090-7bba2ffeb72c/full)

**S3. Faber 10-month SMA timing (index/ETF trend filter)**
- Rules: at each month-end, hold the asset if its close is above its 10-month SMA; otherwise hold 90-day T-bills. In GTAA-5 this is applied separately to S&P 500, 10-yr Treasuries, MSCI EAFE, GSCI and NAREIT, equal-weighted and rebalanced monthly. Results are gross of costs and taxes. — [CXO Advisory summary of Faber 2013 update](https://www.cxoadvisory.com/?p=1115)
- S&P 500, 1901-2012: SMA10 timing returned 10.2%/yr (vol 12.0%, Sharpe 0.55, max drawdown -50.3%). Buy-and-hold returned 9.3%/yr (vol 17.9%, Sharpe 0.32, max drawdown -83.5%). — [CXO](https://www.cxoadvisory.com/?p=1115)
- Five-asset portfolio, 1973-2012: timing returned 10.5%/yr (vol 7.0%, Sharpe 0.73, max drawdown -9.5%). Buy-and-hold returned 9.9%/yr (vol 10.3%, Sharpe 0.44, max drawdown -46.0%). Average exposure was about 70%. — [CXO](https://www.cxoadvisory.com/?p=1115). There is a conflict here: the search snippet attributed "-10.7% vs -9.5%" maximum *annual* drawdown to the 13-asset version, and a Juniata paper reports -46.00% B&H vs -9.56% timing for 1973-2011 ([Juniata](https://admissions.juniata.edu/offices/juniata-voices/media/andrew-and-castro.pdf)). Different drawdown definitions (annual vs monthly) explain part of the gap.
- Post-publication 2006-2012: timing beat buy-and-hold in only 3 of 7 years, but had a higher Sharpe (0.61 vs 0.16 on CXO's page, which may contain a data error). CXO warns that choosing 10 months may carry material data-snooping bias for US stocks, and that outperformance depends heavily on rare events like 2008. — [CXO](https://www.cxoadvisory.com/?p=1115)
- Results are sensitive to which day of the month the rebalance happens ("rebalance timing luck"). — [Newfound Research](https://blog.thinknewfound.com/2013/08/the-luck-of-the-rebalance-timing/)

**S4. 50/200-day golden cross on S&P 500 / SPY**
- Rules: long when the 50-day SMA is above the 200-day SMA, cash otherwise. On weekly bars this is roughly a 10/40-week SMA cross.
- Since 1928, 42 golden crosses produced an average 12-month return of 9.6% vs 7.2% unconditional (2010 data). — [Ritholtz](https://ritholtz.com/2010/06/golden-cross-goes-dark/)
- 1960-2026 (secondary): 33 trades, 79% win rate, about 350-day average hold, CAGR 6.8% vs 7.2% buy-and-hold, price-only. — [Quantified Strategies](https://quantifiedstrategies.substack.com/p/golden-cross-trading-strategy-backtest)
- Since 2000 (StockCharts, Arthur Hill): 83 trades, 4.53%/yr, 34% win rate, max drawdown 14.7%, dividends excluded. The low win rate reflects whipsaws. — [StockCharts](https://articles.stockcharts.com/article/articles-arthurhill-2016-06-trading-strategy---crossing-to-the-dark-side---quantifying-the-golden-cross-for-the-sp-500/)
- SPY 2010-2024 working paper (not peer reviewed): 9.7% annualized, -33.7% max drawdown, Sharpe 0.745. The worst drawdowns come when a crash outruns the 200-day average's lag, as in 2020. — [vankyle00 trading-models](https://vankyle00.github.io/trading-models/docs/models/01-sma-crossover-spy.html)
- Since 1944: "slightly better risk-adjusted returns but at the cost of destroying profitability." 46.3% of signals had maximum adverse excursion above 4%. — [Price Action Lab](https://priceactionlab.com/Blog/?p=68157)
- Price vs 200-day SMA, 1960 onward: CAGR 6.45% vs 7% buy-and-hold, max drawdown 28%, no dividends. — [Quantified Strategies](https://quantifiedstrategies.substack.com/p/trend-following-strategy-in-s-and-33c)

**S5. Donchian / Turtle channel breakout**
- Background on Donchian channels (N-period highest high and lowest low). — [Wikipedia](https://en.wikipedia.org/wiki/Donchian_channel)
- S&P 500 index Donchian backtests exist only in practitioner blogs and do not control for survivorship. — [Quantified Strategies](https://quantifiedstrategies.substack.com/p/donchian-channels-do-they-work-backtest); [QuanTest](https://quantest-web.pages.dev/en/blog/donchian-channel-breakout/)
- Turtle rules **[UNVERIFIED this session; widely documented in the "Original Turtle Trading Rules" PDF and Faith 2003]**:
  - Volatility: N = 20-day EMA of true range.
  - Position size: Unit = 1% of equity / (N x $ per point).
  - System 1: enter on a 20-day breakout, skipped if the previous S1 breakout was a winner; exit on a 10-day opposite extreme.
  - System 2: enter on a 55-day breakout; exit on a 20-day opposite extreme.
  - Stops and pyramiding: initial stop 2N; add a unit every ½N, up to 4 units per market.
  - Exposure caps: 6 units for closely correlated markets, 10 for loosely correlated, 12 per direction.
  - Drawdown rule: cut notional equity by 20% for each 10% drawdown.
  - The original fetch failed (redirect), so verify before use. Weekly translation: S1 ≈ 4-week breakout with 2-week exit; S2 ≈ 11-week breakout with 4-week exit.

**S6. Darvas box**
- No peer-reviewed US backtest found. In a 2005 Stocks & Commodities "Darvas by Guppy" simulation on the *current* Nasdaq-100 (survivorship-biased), taking every 100-day-high breakout worked better than waiting for a box to form. The account gained 120% from April 1999 to April 2000, then suffered a 66% drawdown. Costs were $8 per trade with 5% of equity per position. — [Traders' Tips June 2005](https://traders.com/documentation/feedbk_docs/2005/06/TradersTips/TradersTips.html)
- Thai market (2026, non-US): 6,801 signals with RS and uptrend filters gave a median of +0.15R at 30 days and a 30% stop rate. Without both filters, median R turned negative. — [MOEasymmetry](https://moeasymmetry.netlify.app/articles/darvas-box-thai-data-3289-setups)
- Commercial Darvas screeners (Trendlyne) backtest on current constituents, which builds in survivorship bias. — [Trendlyne](https://trendlyne.com/fundamentals/back-tests/691112)

**S7. Kernel-regression chart patterns (Lo, Mamaysky & Wang 2000) [CONTEXT, pre-2010]**
- Method: nonparametric kernel regression smooths prices, and patterns are identified algorithmically from local extrema (head-and-shoulders, inverse H&S, broadening, triangles, rectangles, double tops/bottoms). The test compares conditional and unconditional return distributions for US stocks, 1962-1996. — [MIT abstract](https://web.mit.edu/~alo/www/Papers/techanal.html); [NBER w7613](https://www.nber.org/papers/w7613)
- Conclusion: "several technical indicators do provide incremental information and may have some practical value." This is a distributional result, not a trading P&L. — [EconPapers](https://econpapers.repec.org/RePEc:nbr:nberwo:7613)
- The CFA Digest summary says traditional patterns such as H&S may not be optimal for detecting anomalies or trading profits. Double tops and bottoms were the most frequent patterns. — [CFA Institute Digest 2001](https://rpc.cfainstitute.org/-/media/documents/article/cfa-digest/2001/dig-v31-n1-811-pdf.pdf)
- **[UNVERIFIED]** Implementation details from memory: 38-day rolling windows (35 days plus a 3-day lag before the pattern must complete), bandwidth by cross-validation scaled by 0.3, and conditional returns measured on the day after completion. Effects were stronger on Nasdaq than on NYSE/AMEX. The horizon is days, not weeks, so this is not natively a positional system.

**S8. CNN image-based price patterns (Jiang, Kelly & Xiu 2023, J. Finance 78:3193-3249)**
- Publication confirmed: J. Finance 2023, vol. 78, pp. 3193-3249, doi 10.1111/jofi.13268. Inputs are stock-level OHLC/MA/volume chart images, and a CNN predicts up/down return direction. — [Yale Economics](https://economics.yale.edu/research/re-imagining-price-trends); [SSRN 3756587 via Scinapse](https://www.scinapse.io/papers/3122254071)
- Image models have "significantly higher Sharpe ratios" than trend, momentum and reversal benchmarks, and do especially well in extreme deciles. — [Rzepczynski blog](https://mrzepczynski.blogspot.com/2023/11/more-ways-to-find-price-trends.html)
- Equal-weight long-short Sharpe ratios of 7.2, 6.8 and 4.9 are reported for 5-, 20- and 60-day images. These are at the short (about 5-day) holding horizon. One source says the Sharpe falls to "slightly above 1" when the universe is restricted to the 500 largest stocks. I could not confirm whether these figures come from JKX's tables or BSIC's replication. — [BSIC "Technical Analysis on Steroids"](https://bsic.it/wp-content/uploads/2026/03/Technical-Analysis-on-Steroids.pdf) (via search snippet; full PDF exceeded fetch size)
- BSIC's own simplified 20-day-ahead model: 17.25% cumulative over 5 years, vol 8.7%, Sharpe 0.42. — [BSIC](https://bsic.it/?p=19661)
- Follow-up (Zhu & Zhu 2024, Chinese A-shares 2014-2023): ResNet-derived "triple-I" weights improve 1-day portfolios a lot. For one-week portfolios they show "no remarkable advantage," described as "consistent with Jiang, Kelly and Xiu (2023), indicating the difficulty to grab informative general price patterns from price chart images for making longer-term return predictions." Time-scale transfer to one-month holding raised Sharpe only modestly: MOM 0.16→0.21, STR 0.37→0.52, WSTR 0.98→1.05, TREND 0.85→0.88, ALPHA 0.73→0.79. — [Zhu & Zhu 2024, arXiv 2408.08483](https://arxiv.org/abs/2408.08483)

**S9. Volatility-adjusted trend following on equity ETFs / single stocks**
- The S1 portfolio is itself a volatility-targeted trend system: 30% vol target per name, 1/max(200, N) scaling, 200% leverage cap. Open risk (loss if every stop hits) stays near 17% of equity. Drawdowns can exceed open risk because of gap-downs and upward re-sizing. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)

**S10. ATR / chandelier trailing exits**
- The best-documented positional ATR exit is the 10x ATR(42) stop anchored to the all-time high (S1), which is a chandelier-style stop: highest high minus k x ATR. 8-12 ATR multiples were tested in 2005. Tighter stops slightly lowered win rate and slightly raised the payoff ratio. — [review of Wilcox-Crittenden](https://adiscountedview.blogspot.com/2016/04/research-review-does-trend-following.html); [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)

### Inferences
- **Weekly-bar translation (researcher's mapping, not from sources):**
  - S1: entry when the weekly close is at a new all-time high (or 52-week high). Stop = highest weekly close minus about 10 x ATR(42 days) ≈ 4-5 x weekly ATR(9), checked on weekly closes.
  - S2: rank monthly on P/52wk-high and hold the top 30% for 6 months.
  - S3: monthly close vs 10-month SMA (≈ 43-week SMA).
  - S4: 10-week vs 40-week SMA.
  - Weekly checks reduce whipsaw and cost but add gap risk to stops.
- Typical holding periods:
  - S1: winners about 1 year, losers much shorter.
  - S2: 6 months by construction.
  - S3/S4: multi-month trades, about 350-day average for the golden cross.
  - Turtle S2 on weekly bars: weeks to months.
- **Strategy-catalogue extras the writer can add as codeable but evidence-light** (no sources fetched): sector/ETF relative-strength rotation (e.g., top-N of about 10 sector ETFs by 6-12-month return, gated by SMA10), and Faber-style GTAA with a momentum top-N filter. I did not retrieve stats for these this session.

### Gaps
- No verified Sharpe or max-drawdown figures for Darvas box or Donchian/Turtle systems on survivorship-free US stock universes.
- I could not extract JKX's own table values for 20-day images with 20-day holding or 60/60 horizons (the paper PDF was not fetched), its turnover, or its value-weighted results.
- No Allocate Smartly page was retrieved (404). No 2013-2026 update of Faber GTAA stats was found.
- Profit factor and time-in-market are not reported for most strategies, except about 70% exposure for SMA10 GTAA-5 and about 350-day average holds for the golden cross.
- The Turtle rules and LMW details are unverified this session (see markers above).
- The Lobão & Fernandes 2017 Darvas/52-week result is mixed; no peer-reviewed US 52-week-high replication covering 2010-2024 was found.

---

## Q2. Which approaches have robust post-2010 / out-of-sample evidence, and which mainly reduce drawdowns?

### Takeaway
The strongest post-2005 out-of-sample evidence is for single-stock ATH breakout with a wide ATR trailing stop and vol-scaled sizing. It has a 2005-2024 OOS confirmation and 1991-2024 alpha of about 6%/yr gross, but it only works after costs at ≥ $1-10M AUM. Index trend filters (10-month SMA, golden cross) mostly cut drawdowns and volatility, with roughly equal or lower CAGR than buy-and-hold since 2000. 52-week-high cross-sectional ranking weakened or reversed after 2000 in the US. Image/CNN patterns are mostly a short-horizon (≤ 1 week) phenomenon.

### Cited Findings
- ATH breakout: trade statistics hold out of sample for 2005-2024. 1991-2024 gross CAGR was 15.02% vs 11.18% for the market, with alpha 6.19% significant at p = 0.05%. The strategy lost 17.0% in 2022 vs the market's -20.2%, and gained 8.1% in 2023 vs 26.5%. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Net of realistic costs, the ATH strategy has negative alpha below about $0.5M AUM and positive alpha from $1M up. The sweet spot is about $10M. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Faber SMA10's main benefit is risk reduction. S&P 500 1901-2012: return +0.9%/yr, vol down from 17.9% to 12.0%, max drawdown cut from -83.5% to -50.3%. Post-publication (2006-2012), it won only 3 of 7 years. Outperformance rests largely on avoiding 2008. — [CXO](https://www.cxoadvisory.com/?p=1115)
- Golden cross:
  - CAGR is below buy-and-hold since 1960 (6.8% vs 7.2%). — [Quantified Strategies](https://quantifiedstrategies.substack.com/p/golden-cross-trading-strategy-backtest)
  - Better risk-adjusted but less profitable. — [Price Action Lab](https://priceactionlab.com/Blog/?p=68157)
  - SPY 2010-2024: drawdown of -33.7% still occurs when a crash outruns the 200-day lag. — [vankyle00](https://vankyle00.github.io/trading-models/docs/models/01-sma-crossover-spy.html)
- 52-week high: significantly negative in the US 2001-2014 subperiod. — [Lobão & Fernandes 2017](https://econpapers.repec.org/RePEc:cuf:journl:y:2017:v:18:i:2:lobao). It shows less decay than JT momentum. — [SSRN 4587697 copy](https://www.scribd.com/document/694152012/SSRN-id4587697)
- Image patterns: at one-week horizon the advantage is not remarkable, and at one-month horizon Sharpe gains are small. Longer-horizon image prediction is "difficult," consistent with JKX. — [Zhu & Zhu 2024](https://arxiv.org/abs/2408.08483). Restricting to the largest 500 stocks drops the Sharpe to about 1. — [BSIC](https://bsic.it/wp-content/uploads/2026/03/Technical-Analysis-on-Steroids.pdf)
- Data-snooping concern for the choice of the 10-month window. — [CXO](https://www.cxoadvisory.com/?p=1115). Rebalance-date sensitivity. — [Newfound](https://blog.thinknewfound.com/2013/08/the-luck-of-the-rebalance-timing/)

### Inferences
- Classification:
  - **Return-adding (with caveats):** ATH/new-high breakout with ATR trailing stop on a broad, liquid, point-in-time universe, at sufficient AUM.
  - **Drawdown-reducing, roughly return-neutral or negative:** 10-month SMA, 50/200 cross, and price vs 200-day on SPY or index ETFs.
  - **Weak or decayed in the US post-2000:** 52-week-high long-short ranking.
  - **Unproven at positional horizon:** Darvas, Lo-Mamaysky-Wang patterns, and CNN image patterns.
- Trend filters on equity ETFs should be judged by Sharpe, MAR and drawdown, not CAGR. They lag in V-shaped crashes such as 2020 and in choppy markets such as 2022, where whipsaws occur.

### Gaps
- No independent, peer-reviewed post-2010 OOS test of Faber SMA10 or the golden cross on SPY with costs was retrieved. AQR/Man trend papers (e.g., "A Century of Evidence on Trend-Following") were not fetched this session.

---

## Q3. How much do survivorship bias and universe choice affect breakout/new-high strategies on single stocks?

### Takeaway
Survivorship bias matters a lot for breakout systems because their profits come from a small tail of outliers. Fewer than 7% of trades drive most profits, so dropping delisted losers or adding later-joining winners distorts results directly. Credible studies (Wilcox-Crittenden 2005; Zarattini et al. 2025) use survivorship-free databases (Norgate) with point-in-time index membership. Blog tests on current S&P 500 or Nasdaq-100 members are biased upward. No source found quantified the bias in CAGR terms for a Donchian or ATH system.

### Cited Findings
- Zarattini et al. use Norgate's survivorship-free data, including delisted and merged securities, and require point-in-time Russell 3000 membership for the portfolio version. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf)
- Fewer than 7% of trades generate most cumulative profits. — [Concretum](https://concretumgroup.com/does-trend-following-still-work-on-stocks/)
- Current-constituent tests exclude failed firms (e.g., Lehman) and include future joiners before they joined (e.g., Tesla added to the S&P 500 in December 2020). Breakout systems are "highly exposed" to this bias (vendor claim, not measured). The S&P 500 had 858 distinct constituents over a 19-year span, per Norgate data. — [Enlightened Stock Trading](https://enlightenedstocktrading.com/stock-trading-systems-survivorship-bias-problems); [FXStreet](https://www.fxstreet.com/amp/analysis/how-many-stocks-in-the-sp-500-202510160541)
- The 2005 Darvas/Nasdaq-100 test used *current* members, which illustrates the bias in published practitioner work. — [Traders' Tips 2005](https://traders.com/documentation/feedbk_docs/2005/06/TradersTips/TradersTips.html)
- Lookahead check: shift signals back one bar; if performance collapses, the test had lookahead. — [learning-ta](https://learning-ta.pages.dev/learn/backtesting-pitfalls)
- Universe size and liquidity matter for cost. Liquidity filters ($10 price, $1M CPI-adjusted dollar volume) and AUM drive net results. — [Zarattini et al. 2025](https://concretumgroup.com/wp-content/uploads/2026/02/Does-Trend-Following-Still-Work-on-Stocks.pdf). For CNN patterns, restricting to the top 500 stocks cuts the Sharpe sharply. — [BSIC](https://bsic.it/wp-content/uploads/2026/03/Technical-Analysis-on-Steroids.pdf)

### Inferences
- The bias works in two directions for new-high systems. Excluding delisted stocks removes stopped-out losers, though the wide trailing stop limits each loss to about 1R except on gaps. Using current members also adds stocks *because* they later trended up into the index, which inflates the outlier tail that drives profits. The second effect is probably the larger one for long-only breakout systems.
- Implementation requirements:
  - point-in-time membership (Norgate or CRSP);
  - include delisting returns;
  - unadjusted-price filters for minimum price;
  - next-open execution;
  - cost modeling scaled to AUM.

### Gaps
- No source quantified survivorship bias in CAGR or Sharpe terms (biased vs unbiased universe) for Donchian, ATH or 52-week breakout systems on US stocks. This needs an in-house replication.
