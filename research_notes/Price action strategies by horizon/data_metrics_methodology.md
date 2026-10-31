# Data, Backtest Methodology and Metrics for Price-Action Strategies on US Stocks/ETFs (as of Oct 2026)

Note on method: I used about 15 tool calls. Official pages were used where they were reachable: Alpaca docs, Massive pricing, Alpha Vantage docs and support, Tiingo pricing, FirstRate SPY page, backtesting.py docs. The IBKR commissions page returned HTTP 403. Some limits rest only on community or third-party evidence, and each one is marked as such. Metric formulas are standard textbook and literature definitions. They are cited to the original papers where possible, and anything from memory rather than a fetched page is listed under Inferences or Gaps.

## Q1. What is the best free way to get multiple years of SPY/QQQ 1–5 minute bars in 2026, and what exactly is required?

### Takeaway
The best free route is the Alpaca Market Data API on the free Basic plan. It needs a free Alpaca account plus an API key and secret, and it serves minute bars from 2016 onward, about 10 years. Request `feed=sip` with an end time more than 15 minutes old to get consolidated (all-exchange) bars instead of IEX-only bars. Massive (formerly Polygon) free gives only 2 years. Yahoo gives days to weeks. Alpha Vantage intraday history is now a premium endpoint. For 2000 onward, a one-off paid purchase from FirstRate Data (or Databento using its $125 signup credit) is the low-cost option.

### Cited Findings
**Alpaca (best free long history)**
- Basic (free) plan is the default for paper and live accounts. Real-time equities come from the IEX exchange only. Historical data runs "since 2016". The historical limit is "latest 15 minutes", with 200 historical API calls per minute and 30 WebSocket symbols. — [Alpaca docs: About Market Data API](https://docs.alpaca.markets/docs/about-market-data-api)
- Algo Trader Plus costs $99/month and covers all US exchanges, history since 2016 with no restriction, and 10,000 historical calls per minute. — [Alpaca docs](https://docs.alpaca.markets/docs/about-market-data-api)
- An Alpaca v1.1 docs page describes the free plans as "real time IEX or 15 mins delayed SIP". — [Alpaca docs v1.1](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api)
- Alpaca staff on the forum: licensing rules exclude only the most recent 15 minutes of SIP data from the free plan. Older SIP historical data is the same on free and paid plans. Users should explicitly specify `feed=sip` so they do not silently get the IEX-only subset. — [Alpaca forum: 15-minute historical delay](https://forum.alpaca.markets/t/solutions-for-getting-bars-missing-due-to-15-minute-historical-delay/8913); [Alpaca forum: Can't read SPY minutes](https://forum.alpaca.markets/t/cant-read-spy-minutes/14293)
- A third-party doc reports a 403 error when `feed=sip` is requested with an end time inside the last 15 minutes. This is unverified against official docs. A forum reply mentions `feed='delayed_sip'` as an alternative. — [Alpaca forum thread](https://forum.alpaca.markets/t/solutions-for-getting-bars-missing-due-to-15-minute-historical-delay/8913)
- The Alpaca API returns no intraday data before 2016. — summarised in search results citing [Wealth-Lab discussion](https://wealth-lab.com/Discussion/9430)

**Massive (formerly Polygon.io)**
- Free Stocks Basic plan: $0/month, 5 API calls per minute, 2 years of historical data, end-of-day data, and minute aggregates included. A paid Starter tier extends history to 5 years with 15-minute-delayed data. Stocks Advanced costs $199/month with "20+ years of history". — [Massive pricing](https://massive.com/pricing) (Advanced tier confirmed on fetch; Basic tier details from search snippet of same page); [Massive KB request limits](https://massive.com/knowledge-base/article/what-is-the-request-limit-for-massives-restful-apis)
- A developer tool reports that requests older than about 2 years return NOT_AUTHORIZED on free keys. — [glama.ai MCP listing](https://glama.ai/mcp/servers/jz0nwfalmu) (secondary)
- One DEV Community review lists a $29 "Basic" plan, which conflicts with the official page and looks outdated. — [DEV Community review](https://dev.to/pickuma/polygonio-api-review-querying-18-billion-market-data-points-with-one-http-request-23n3)

**Yahoo / yfinance (unofficial scraper, no key)**
- 1m bars are limited to about 7 days per request and roughly the last 30 days overall. Error text: "1m data not available…". — [Streamlit forum](https://discuss.streamlit.io/t/how-to-show-an-error-message-when-the-interval-of-historical-data-is-too-small-or-big/13726); [yfinance issue #2128](https://github.com/ranaroussi/yfinance/issues/2128)
- 2m, 5m, 15m and 30m bars must fall within the last 60 days. — [yfinance issue #2451](https://github.com/ranaroussi/yfinance/issues/2451)
- Measured limits from a Rust port: 1m has a maximum age of 29 days and a maximum span of 8 days per request (chunk into 7-day windows). 5m, 15m and 30m have a maximum age of 58 days. Yahoo returns HTTP 422 if the span is exceeded. — [finance-query chart.rs](https://docs.rs/crate/finance-query/2.5.1/source/src/endpoints/chart.rs)
- The 1h limit of about 730 days is widely cited, but I did not fetch a primary source for it in this session (see Gaps).

**Alpha Vantage**
- TIME_SERIES_INTRADAY supports 1min, 5min, 15min, 30min and 60min. The `month=YYYY-MM` parameter supports "any month in the last 25+ years since 2000-01". `outputsize=full` returns the trailing 30 days, or the full month when `month` is set. The docs state "This is a premium endpoint", and premium is needed for realtime, delayed and historical intraday data. — [Alpha Vantage documentation](https://www.alphavantage.co/documentation/)
- Free key: 25 API requests per day. — [Alpha Vantage support](https://alphavantage.co/support/); [Alpha Vantage premium](https://www.alphavantage.co/premium)
- Premium plans reportedly cost $49.99 to $249.99/month for 75 to 1,200 requests per minute (third-party). The official docs list 150, 300, 600 and 1,200 requests per minute tiers. — [macroption](https://www.macroption.com/alpha-vantage-api-limits/); [Alpha Vantage documentation](https://www.alphavantage.co/documentation/)

**Tiingo**
- Free Starter plan: $0, 50 requests per hour, 1,000 per day, 500 unique symbols per month, 1 GB per month. Power plan: $30/month, 10,000 per hour, 100,000 per day, 40 GB. The pricing page says "30+ years" of price history, which refers to EOD. It lists an "IEX feed" but gives no intraday history depth. — [Tiingo pricing](https://www.tiingo.com/about/pricing)
- The riingo R package says IEX intraday ranges "are not well documented". Supported frequencies include 1min, 5min and 2hour. A 2018 user report found about 4 months of history and 5,000 minutes per call (anecdotal and dated). — [riingo README](https://search.r-project.org/CRAN/packages/riingo/readme/README.html)

**Paid / one-off long history**
- FirstRate Data SPY: from 3 Jan 2000 to present (page lists end 29 Oct 2026), with 1-min, 5-min, 30-min, 1-hour and 1-day bars. A free sample is available. After one month of free updates, updates need an annual $99.95 subscription. The page does not show the purchase price. — [FirstRate SPY](https://firstratedata.com/i/etf/SPY)
- FirstRate free offering: "1 year of free intraday data" for popular datasets. Samples are limited to 2 weeks. — [FirstRate free intraday data](https://firstratedata.com/free-intraday-data)
- Databento: pay-as-you-go ($/GB) or subscription. New accounts get $125 in free credits, which one third party says expire after 6 months. The exact cost of any query can be checked free before running it. OHLCV-1m is a separate schema. — [Databento pricing](https://databento.com/pricing); [Databento quickstart](https://databento.com/docs/quickstart)
- An older forum report puts 5 years of SPY tick data at $78.16, covered by the signup credit (anecdotal). — [NexusFi Databento](https://nexusfi.com/d/data-providers/databento/)

**Academic / free datasets**
- The HighFreq R package includes SPY 1-minute OHLC bars from 2008-01-02 to 2014-05-19. — [HighFreq hf_data](https://rdrr.io/github/algoquant/HighFreq/man/hf_data.html)
- Quantpedia's one-minute SPY trend-following study used Algoseek data. — [Quantpedia](https://quantpedia.com/building-and-testing-trend-following-strategies-on-one-minute-spy-data/)
- I found no reliable Kaggle SPY 1-minute dataset covering 2008 to present.

### Inferences
- Longest free SPY/QQQ 1-minute history: Alpaca at about 10 years (2016 to present), followed by Massive free at 2 years. Yahoo (about 30 days at 1m, 60 days at 5m) is only useful for forward-collection or sanity checks. Alpha Vantage's `month` parameter would reach 2000, but it is premium now, and 25 calls per day is impractical anyway.
- Requirements for Alpaca: a free account (paper-only is enough), an API key ID and secret, the `alpaca-py` SDK, `feed=sip`, an `end` at least 15 minutes in the past, paging under 200 calls per minute, and the Alpaca market-data terms of use. Prefer SIP over IEX for price-action work. IEX is a small slice of volume (low single-digit percent historically), so IEX-only bars have distorted highs, lows and volume.
- If you need pre-2016 data or want to include the 2008 crisis regime, one-off FirstRate Data or Databento purchases are the cheapest clean route. Databento's $125 credit likely covers SPY and QQQ OHLCV-1m for its full history, but check with its free cost-estimate endpoint.
- Confirm whether the adjustment for splits and dividends matches what the strategy needs. ETF dividends matter for multi-day holds. Alpaca bars have an `adjustment` parameter (raw, split, dividend, all).

### Gaps
- The yfinance 1h limit of about 730 days and the precise 1m limit (7 vs 29/30 days) come from community and third-party sources. Yahoo publishes no official limits.
- I could not confirm Kibot pricing or Tiingo IEX intraday depth from official pages.
- FirstRate SPY purchase price was not shown on the page. Databento's exact SPY 1m cost is not published (the query-cost API gives it).
- I could not fetch Massive Basic plan details directly from the rendered pricing page. They come from the search snippet of that page and secondary sources.

## Q2. Which pitfalls most inflate price-action backtests, and how to model them conservatively?

### Takeaway
The biggest inflators fall into two groups: (a) execution-timing errors, and (b) selection bias. Timing errors include deciding on a bar's close or high/low and filling at that same bar's prices, and assuming the target fills before the stop inside one OHLC bar. Selection bias comes from testing many rule variants and keeping the best, plus survivorship-biased universes. Model conservatively in five ways. Fill at the next bar's open. When stop and target are both inside one bar, assume the stop hit first, or resolve with lower-timeframe data. Fill gap-throughs at the open, not at the stop. Charge per-share or bps slippage plus commissions. Deflate the Sharpe for the number of trials.

### Cited Findings
- backtesting.py's `trade_on_close=True` fills market orders at the current bar's close. The default (False) fills at the next bar's open. `spread` is a bid-ask rate. `commission` can be a rate, a (fixed, relative) tuple or a callable, and since v0.4.0 it is charged on both entry and exit. — [backtesting.py docs](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html)
- Alpaca IEX-only bars are a subset of consolidated trades. Staff advise `feed=sip` to avoid that subset, which affects the high, low, volume and signals derived from them. — [Alpaca forum](https://forum.alpaca.markets/t/cant-read-spy-minutes/14293)
- Selection bias under multiple testing: the expected maximum Sharpe ratio of N independent strategy trials with zero true skill rises with N. The Deflated Sharpe Ratio corrects for the number of trials, non-normality and track-record length. — [Bailey & López de Prado (2014), "The Deflated Sharpe Ratio", SSRN 2460551](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- Probability of backtest overfitting (CSCV) measures how often the in-sample-best configuration underperforms the median out of sample. — [Bailey, Borwein, López de Prado, Zhu (2015), "The Probability of Backtest Overfitting", SSRN 2326253](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
- IBKR Pro Tiered US stock commission is commonly quoted at $0.0035/share at the lowest volume tier, plus exchange, clearing and regulatory fees. Fixed pricing is $0.005/share, $1 minimum, capped at 1% of trade value. IBKR Lite and most US retail brokers charge $0 commission. — [IBKR commissions page](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php) (returned 403 to fetch, so figures are not re-verified this session; see Gaps)

### Inferences (engineering guidance; standard practice, not single-sourced)
1. **Same-bar look-ahead.** A signal computed from bar t's close, high or low must execute at bar t+1's open at the earliest. Never use the signal bar's high or low as an entry fill unless it is a pre-placed stop or limit order defined before the bar opened. Breakout entries are buy-stops at levels known from bar t-1, filled at max(open, level).
2. **Intrabar ambiguity (OHLC).** When both stop and target lie inside [low, high] of the same bar, the path is unknown. The conservative default is stop first (worst case). Better: resolve with 1-minute bars when testing on 5m, daily or weekly bars, or report both pessimistic and optimistic bounds. Also, entry-bar stops: a stop placed on the entry bar can be hit in that same bar.
3. **Gaps.** If the open is beyond the stop, fill at the open, not the stop price. This matters a lot for daily and weekly swing systems held overnight and over earnings. Limit-order targets that gap through fill at the better open only if modelled correctly. Do not give price improvement beyond the open.
4. **Limit-fill realism.** Require price to trade through the limit by at least one tick, or touch it with a probability less than 1. A touch-fill assumption inflates mean-reversion results.
5. **Close versus next open.** Fills "at close" need a market-on-close order and a signal computed before the close (for example at 15:59), or else they are look-ahead. Use next open, or the close of a later 1-minute bar.
6. **Slippage.** SPY and QQQ: 0.5 to 1 bp per side, or $0.01 per share (1 tick), is a conservative floor for marketable orders. Mid- and small-cap stocks: 5 to 20+ bps, or scale with spread and volatility (for example half-spread plus k·σ·sqrt(participation)). Stops are market orders, so add an extra tick on stop exits.
7. **Commissions.** Model IBKR Tiered as $0.0035/share plus roughly $0.0002 to $0.003/share in exchange, clearing and pass-through fees. Model zero-commission retail as $0 commission but with wider effective spread (payment-for-order-flow execution quality). Model SEC Section 31 fees and FINRA TAF on sells.
8. **Survivorship.** Single-ETF tests (SPY, QQQ) avoid it. Stock-universe tests need point-in-time constituents including delisted tickers. Free APIs generally drop delisted names.
9. **Data snooping.** Log every variant tested (count N). Report the Deflated Sharpe or PBO. Reserve a sealed final test period. Prefer few parameters with plateau-shaped performance.
10. **Walk-forward.** Use rolling or anchored windows (for example optimise on 3 years, test on 1 year, step 1 year), choose parameters only from in-sample data, and concatenate out-of-sample segments for the reported equity curve. Purge or embargo overlapping holding periods at window boundaries (López de Prado).
11. **Session handling.** Use regular-hours bars only, unless pre- and post-market are intended. Handle half-days and DST. Ensure "daily" bars are built from RTH 09:30 to 16:00 ET when combined with intraday data.
12. **Corporate actions.** Use split-adjusted prices for signals. Total-return (dividend-adjusted) prices are appropriate for multi-day P&L. Do not mix.

### Gaps
- I could not fetch the IBKR commissions page (403). The $0.0035 tiered figure and the fixed-pricing terms come from prior knowledge and are not re-verified for 2026.
- I did not confirm from backtesting.py docs how it resolves SL and TP in the same bar. From memory of its source, it handles SL with priority (pessimistic) when both are hit, but this is unverified here.
- I found no peer-reviewed quantification of how much intrabar-ordering bias inflates typical price-action backtests.

## Q3. Full metric set and formulas, plus which open-source library gives the most complete trade-level metrics on Python 3.13 / Windows

### Takeaway
Report three layers: return and risk (CAGR, volatility, Sharpe, Sortino, Calmar, MaxDD and duration, Ulcer), trade-level stats (win rate, payoff, profit factor, expectancy, SQN, hold time, exposure, turnover) and robustness (skew, kurtosis, tail ratio, PSR and DSR, bootstrap or Monte Carlo of trades). backtesting.py natively outputs the broadest built-in trade-level set (including SQN, Profit Factor, Expectancy, Kelly, Exposure, durations). Combine it with quantstats on the equity curve and custom PSR, DSR and bootstrap code.

### Cited Findings
- backtesting.py `Backtest.run()` returns: Start, End, Duration, Exposure Time [%], Equity Final/Peak, Return, Buy & Hold Return, Return (Ann.), Volatility (Ann.), CAGR, Sharpe, Sortino, Calmar, Alpha, Beta, Max/Avg Drawdown, Max/Avg Drawdown Duration, # Trades, Win Rate, Best/Worst/Avg Trade, Max/Avg Trade Duration, Profit Factor, Expectancy, SQN, Kelly Criterion, plus the `_equity_curve` and `_trades` DataFrames. SQN is the default `optimize()` target. Version 0.6.6 is shown in the docs. — [backtesting.py docs](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html)
- vectorbt is split into a free open-source edition and a paid PRO edition. Recent development reportedly focuses on PRO. — [AlgoLab 2026 comparison](https://algolab.co.kr/blog/python-backtesting-library-comparison-2026)
- NautilusTrader reportedly supports Python 3.12 to 3.14 on Linux, macOS ARM64 and Windows. It is an open-source, event-driven engine with backtest and live parity (secondary source). — [BrightCoding blog, May 2026](https://blog.brightcoding.dev/2026/05/30/stop-rewriting-strategies-for-live-trading-use-nautilus-trader-instead)
- A comparison table lists zipline-reloaded as Python 3.10+. RustyBT is an Apache-2.0 fork built on zipline-reloaded that ships cp313 wheels. — [DEV comparison](https://dev.to/pickuma/python-backtesting-frameworks-compared-backtrader-vectorbt-and-zipline-reloaded-41l8); [RustyBT PyPI](https://pypi.org/project/rustybt/0.2.1/)
- PSR and DSR: PSR(SR*) = Φ[ (SR̂ − SR*)·√(T−1) / √(1 − γ₃·SR̂ + ((γ₄−1)/4)·SR̂²) ], where γ₃ is skew and γ₄ is (non-excess) kurtosis of returns and T is the number of observations. DSR is the PSR with SR* = SR₀ = √V[{SR_n}]·((1−γ)·Φ⁻¹[1−1/N] + γ·Φ⁻¹[1−1/(N·e)]), where γ ≈ 0.5772 (Euler–Mascheroni) and N is the number of independent trials. — [Bailey & López de Prado, "The Sharpe Ratio Efficient Frontier" (2012)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1821643); [Bailey & López de Prado, "The Deflated Sharpe Ratio" (2014)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- SQN (Van Tharp) = √N × mean(R) / stdev(R), where R is per-trade R-multiples (P&L divided by initial risk). Tharp caps N at 100 when comparing systems. — [Van Tharp Institute](https://www.vantharp.com/) (definition as implemented in backtesting.py; see the [docs](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html))

### Metric formula reference (standard definitions)
Let r_t be periodic simple returns, P the periods per year (252 daily, 52 weekly, 252×390 for 1-minute RTH bars), E_t equity, and trades i = 1..N with P&L p_i.
- **CAGR** = (E_end / E_start)^(1/years) − 1.
- **Annualised volatility** = std(r_t)·√P.
- **Sharpe** = mean(r_t − rf_t)/std(r_t − rf_t) · √P. Compute on daily returns even for intraday systems, since intraday Sharpe annualisation is distorted by autocorrelation and overnight gaps.
- **Sortino** = (mean(r_t) − MAR)·√P / DD, where DD = √(mean(min(0, r_t − MAR)²)) over all periods. This is the downside deviation, not the std of negative returns only.
- **Max drawdown** = max_t (1 − E_t / max_{s≤t} E_s). **Max DD duration** = the longest time between equity peaks (peak to recovery).
- **Calmar** = CAGR / |MaxDD|, usually over a 36-month window. **MAR ratio** = CAGR / |MaxDD| over the full history.
- **Ulcer Index** = √(mean(D_t²)), where D_t = percent drawdown from the running peak. **Ulcer Performance Index (Martin ratio)** = (CAGR − rf)/UI.
- **Win rate** = N_win / N.
- **Payoff ratio** = avg win / |avg loss|.
- **Profit factor** = Σ gains / |Σ losses|.
- **Expectancy per trade** = W·avgWin − (1−W)·|avgLoss|, equal to mean(p_i). In R-multiples, it is mean(R_i).
- **Average trade** = mean(p_i) in $ or %. **Average hold** = mean(exit_time − entry_time).
- **Exposure / time in market** = bars with an open position / total bars.
- **Kelly fraction** ≈ W − (1−W)/payoff.
- **Tail ratio** = |95th percentile of r| / |5th percentile of r| (quantstats/pyfolio convention).
- **Skew and kurtosis** use the sample third and fourth standardised moments. Report excess kurtosis, and convert to non-excess for the PSR.
- **Turnover** = Σ|traded notional| / mean equity, annualised. **Cost drag** = gross CAGR − net CAGR, or Σ costs / mean equity per year. **Break-even cost** = gross edge per trade / shares per trade.
- **Bootstrap and Monte Carlo of trades.** Resample trade returns with replacement (or permute their order) 5,000 to 10,000 times. Rebuild equity curves and report percentiles of CAGR, MaxDD and the probability of ruin. Use a block bootstrap if trades are serially dependent.

### Inferences
- **Library fit on Windows / Python 3.13** (based on the cited evidence plus general knowledge; verify on PyPI before install):
  - **backtesting.py**: simplest API for single-asset bar-by-bar price-action rules (stop and limit orders, SL and TP). It has the most complete built-in trade stats, and the `_trades` DataFrame holds entry and exit times and prices, PnL and duration. Licence is AGPL-3.0 from memory (not confirmed on the fetched page). It is single-instrument per run.
  - **vectorbt (open source)**: very fast parameter sweeps. Its `Portfolio.stats()` and `trades.stats()` cover win rate, profit factor, expectancy, SQN and durations. The open edition gets slow updates, and Numba and NumPy version pins can lag new Python versions. Licence is Apache 2.0 with Commons Clause (from memory).
  - **nautilus_trader**: most realistic event-driven fills (bar or tick, order types, latency). It reportedly supports 3.12 to 3.14 on Windows. It has a steeper learning curve and fewer ready-made trader-style stats. Licence is LGPL-3.0 (from memory).
  - **zipline-reloaded**: daily-focused, bundle-based. It is awkward for minute-level price action and has heavier Windows installs.
  - **quantstats**: equity-curve tearsheets (Sharpe, Sortino, Calmar, Ulcer, tail ratio, skew, kurtosis, drawdown tables). It has no trade-level engine.
  - **ml4t-backtest**: I found no reliable source in this session (see Gaps).
- **Recommended stack:** backtesting.py (or nautilus_trader when fill realism matters), then `stats._trades`, then custom SQN, R-multiple and bootstrap code, then quantstats on the daily-resampled equity curve, then a custom PSR and DSR using the logged trial count N.

### Gaps
- I did not verify licence fields and Python 3.13 wheel availability on PyPI for backtesting.py, vectorbt, nautilus_trader, zipline-reloaded or quantstats this session. The licences above are from memory.
- No information was found on "ml4t-backtest" (package status, licence, metrics).
- I did not fetch the Van Tharp primary text on SQN. The definition comes from backtesting.py's implementation and general usage.
