# Regional Markets: Strategies and Free Data for China (A/H), Japan and Europe (2023-2026 focus)

Scope note: this pass used about 20 tool calls. Coverage is strongest for the China anomaly literature, China microstructure (SSE rules, stamp duty), the Japan TSE PBR reform, cross-country momentum and the akshare API. European single-stock factor evidence and yfinance and stooq data-quality issues are thinner, and are flagged as gaps. Older seminal work is marked **[CONTEXT, pre-2023]**.

Downloaded PDFs (open hosts only) to `C:\Users\Acer\Pictures\research_papers\paper1\papers\regional_markets\`:
- `DErcole_Yamada_Wagner_2025_TSE_capital_efficiency.pdf`: ECGI WP 1038/2025, April 2026 version (from ecgi.global).
- `Liu_Stambaugh_Yuan_2019_Size_Value_China_NBER.pdf`: NBER w24458 **[CONTEXT, pre-2023]**.
- Two attempted downloads returned HTML landing pages, not PDFs, and were deleted: Jansen-Swinkels-Zhou (pure.eur.nl) and Fieberg-Metko-Zaremba (open.icm.edu.pl). The URLs are listed below for manual download.

---

## Q1. Which strategies have the best recent evidence in China, Japan and Europe?

### Takeaway
- **China A-shares:** the most robust signals are short-term (residual) reversal, lottery/MAX and turnover-type "trading" anomalies, and earnings-yield value, all tied to the retail-dominated, T+1, price-limited market. Classic 12-1 momentum and plain size are weak or absent, and most of a 469-anomaly zoo fails in China.
- **Japan:** the main 2023-2026 story is the TSE "cost of capital / PBR<1" reform. Low-PBR, high-ROE firms were repriced upward after the reform, which was an investor-attention event, not a fundamentals change. Classic momentum remains historically weak in Japan.
- **Europe:** recent evidence is mostly practitioner commentary (value and momentum led in Q4 2024). Cross-country momentum, both country-index and factor-level, has fresh 2024 peer-reviewed support.

### Cited Findings

**China: anomaly landscape**
- Jansen, Swinkels and Zhou (Pacific-Basin Finance Journal 68, 2021, art. 101607) test 32 anomalies on A-shares from 2000 to 2019. Value, risk and trading anomalies carry over to China. Size, quality and past-return anomalies are substantially weaker, *except* strong **residual momentum** and **residual reversal**. Residual reversal and return seasonalities hold out of sample, while connected-firm momentum does not. Short-sale restrictions, SOE prevalence and reforms are not the main drivers. The anomalies appear across large, mid and small caps. Open PDF (CC BY): https://pure.eur.nl/files/58642799/Anomalies_in_the_China_A_share_market.pdf — [EUR Pure](https://pure.eur.nl/en/publications/anomalies-in-the-china-a-share-market/) **[CONTEXT, 2021]**
- Li et al. (Management Science, 2024) replicate **469 anomaly variables** on A-share data and find that **most do not produce significant raw return spreads**. This is a strong multiple-testing warning for China. — [search summary of PolyU record](https://ira.lib.polyu.edu.hk/handle/10397/115240) (full text not verified)
- Zhang and Zhu (International Review of Economics & Finance, vol. 96, 2024) argue that **only a strong short-term contrarian (reversal) effect** exists in China, and link it to the **T+1 rule**. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/reveco/v96y2024ipbs1059056024006452.html) (paywalled; exact rules and numbers not obtained)
- Liu, Huang and Chao (Journal of Systems Science and Mathematical Sciences, 2024) build a **residual-return reversal** strategy and attribute the reversal to **liquidity shocks rather than sentiment**. — [JSSMS top-access list](https://sysmath.cjoe.ac.cn/jweb_xtkxysx/EN/top_access)

**China: lottery / MAX**
- Gu, Hu and Xiong (Accounting & Finance 65(1), 2025, pp. 883-911): the lottery-like anomaly in China is driven mainly by **overnight returns**. It is stronger where retail gambling preference and limits to arbitrage are high. — [IDEAS/RePEc](https://ideas.repec.org/a/bla/acctfi/v65y2025i1p883-911.html)
- Wang (SSRN WP, March 2024, doi 10.2139/ssrn.4771500) reports a **factor-level MAX premium**: factors with high recent maximum daily returns beat low-MAX factors by about **0.82%/month risk-adjusted** in China, with a similar pattern in the US and G7. — [HKBU scholars record](https://scholars.hkbu.edu.hk/en/publications/lottery-preference-for-factor-investing-in-chinas-a-share-market/)
- **[CONTEXT, 2021]** Gao, Han and Xiong document losses from chasing MAX stocks in China, and a reversed MAX effect among Chinese equity funds. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/ecofin/v58y2021ics1062940821000966.html)

**China: size / shell value / value (CH-3)**
- **[CONTEXT, 2019]** Liu, Stambaugh and Yuan, "Size and Value in China" (JFE 2019; NBER w24458). The size factor **excludes the smallest 30% of stocks** as likely reverse-merger shells, created because tight IPO approval gives listings a "shell value". Value is measured by the **earnings-to-price (E/P)** ratio, which subsumes B/M. The CH-3 size and value factors have FF-3 annualized alphas of **5.64% and 16.80%**. — [NBER PDF](https://www.nber.org/papers/w24458.pdf), [Wharton PDF](https://faculty.wharton.upenn.edu/wp-content/uploads/2018/03/Size-and-Value-in-China.pdf)
- A later critique argues that CH-3 is weakened by a **structural break in the IPO market after the 2017 policy changes**, and that dropping the bottom 30% can overstate alphas. It proposes conditioning on reverse-merger activity instead. Publication venue and date are unconfirmed. — [Quantpedia: Evaluating Factor Models in China](https://quantpedia.com/evaluating-factor-models-in-china/)
- No official 2024+ CH-3 update was found. — same search, [IBKR Quant summary](https://www.interactivebrokers.com/campus/ibkr-quant-news/evaluating-factor-models-in-china/)

**China: limit-up / limit-down effects (mostly CONTEXT)**
- **[CONTEXT]** Jiang, Gao et al. (NBER w24014), using Shenzhen account data for 2012-2015, show that large investors push stocks to the **10% upper limit on day 0 and net-sell on day 1**, a pump-and-dump-like pattern. Prices overreact to the initial shock. — [NBER](https://www.nber.org/papers/w24014.pdf); [CUHK summary](https://cbk.bschool.cuhk.edu.hk/do-daily-price-limits-stabilize-the-markets/)
- **[CONTEXT]** In 2000-2011 data, next-day *continuation* follows **63.7%** of limit-up hits and **75.9%** of limit-down hits. — [arXiv 1503.03548](https://arxiv.org/pdf/1503.03548)
- **[CONTEXT]** Another 2000-2011 study finds a **cooling-off** rather than a magnet effect, and notes that the literature is contested. — [PMC4395215](https://pmc.ncbi.nlm.nih.gov/articles/PMC4395215); see also [VoxChina: Daily Price Limits and the Magnet Effect](https://voxchina.org/show-3-49.html)
- **[CONTEXT]** After a limit hit opens, expected returns follow a "W" pattern that implies a high probability of a repeat hit the next day, and the pattern depends on the market trend. — [Physica A 2017, IDEAS](https://ideas.repec.org/a/eee/phsmap/v465y2017icp464-471.html)

**Japan: TSE capital-efficiency (PBR) reform**
- D'Ercole, Wagner and Yamada, "Investor Repricing of Chronic Undervaluation: Evidence from the TSE Capital Efficiency Initiative" (ECGI Finance WP 1038/2025, April 2026 revision; SFI RP 25-19; **forthcoming, Journal of Corporate Finance**):
  - After the 2023-2024 initiative, investors **favored low-PBR firms, particularly those with high ROE**.
  - The effects are concentrated among *persistently* undervalued firms. They **rise smoothly with the degree of undervaluation and do not jump at the PBR=1 threshold**, and they are robust to endogenous treatment.
  - The TSE's consolidated compliance list (which firms had disclosed plans) triggered strong reactions, even though the plans were already public, so it acted as a salient-information event.
  - There were no short-run gains in realized profitability or analyst EPS revisions. Illiquidity fell and valuation ratios rose for low-PBR firms.
  - Little persistent "price-of-shame" effect.
  - Sources: [ECGI page](https://www.ecgi.global/publications/working-papers/investor-repricing-of-chronic-undervaluation-evidence-from-the-tokyo), [PDF](https://www.ecgi.global/sites/default/files/2026-09/fin-1038-2025_investor_repricing_of_chronic_undervaluation_evidence_from_t_1_0.pdf), [SFI](https://www.sfi.ch/en/publications/n-25-19-sticks-carrots-and-investor-behavior-evidence-from-japan), [SSRN 5086589](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5086589)
- Background on the reform: the TSE asked Prime and Standard companies to act on cost of capital and stock price. About **43% of Japanese companies traded below PBR 1** as of July 2022, versus 5% in the US and 24% in Europe. — [Harvard Law School Forum on Corp Gov, Oct 2025](https://corpgov.law.harvard.edu/2025/10/21/tokyo-stock-exchange-initiative-on-cost-of-capital-and-stock-price-conscious-management/)
- A 2023 asset-manager note linked the Request (March 2023) to rising prices of PBR<1 stocks, with buybacks and dividend hikes expected. It also said the TSE wanted structural fixes, not one-off payouts. — [Asset Management One, Apr 2023](https://www.am-one.co.jp/pdf/english/113/AMO_Opinion_Report_230428.pdf)
- Example corporate responses: Japan Post HD estimated its cost of equity at about 5% (CAPM) with ROE below it, and JR East put its cost of equity at about 5-6% with a target PBR above 1.0. — [Japan Post](https://www.japanpost.jp/en/ir/library/presentation/pdf/20231113_01.pdf), [JR East](https://www.jreast.co.jp/e/press/2024/pdf/20241120.pdf)

**Japan: momentum weakness**
- No 2023-2026 peer-reviewed paper was found. Older and thesis work:
  - **[CONTEXT, 2014]** Calendar effects (January and May losses) erode momentum in Japan. — [Mikova & Teplova, Economic Alternatives 2014](https://ideas.repec.org/a/nwe/eajour/y2014i3p25-42.html)
  - **[CONTEXT]** An undated thesis argues that momentum exists in Japan but is masked, and offers a limited-attention / salience explanation. — [U. Hawai'i ScholarSpace](https://scholarspace.manoa.hawaii.edu/items/fd71a76a-1d0c-4be5-86d1-adcaeb72b50a)
  - **[CONTEXT]** Asness (2011) argues that momentum's failure in Japan does not overturn the global evidence (the value-momentum combination works). — cited via [EUR thesis](https://thesis.eur.nl/pub/53133/Thesis.pdf)

**Europe / cross-country**
- WisdomTree's factor review: in **Q4 2024, momentum and value led in Europe and quality was weakest**, with size and growth also lagging. European valuations declined while US growth valuations rose. This is single-issuer commentary. — [WisdomTree Q4 2024 factor review](https://www.wisdomtree.com/gb/insights/blog/looking-back-at-equity-factors-in-q4-2024-with-wisdomtree/pdf)
- **Cross-country factor momentum:** Fieberg, Metko and Zaremba (Economics Letters, Feb 2024) find that factors in countries with strong recent factor returns keep outperforming. The result is positive in **140 of 145 anomalies**, with an average **0.16%/month** and a Sharpe ratio of about **0.47**. — [WP PDF](https://open.icm.edu.pl/bitstreams/fe3c87f1-8f5a-4a2f-8a43-3eac7dfdcfbf/download), [Alpha Architect](https://alphaarchitect.com/cross-country-factor-momentum/)
- **Country-ETF momentum:** a study of **15 developed-market iShares country ETFs, April 1996 to September 2023**, finds significant winner-minus-loser profits that survive risk adjustment. — [Pennsylvania Economic Review 31(1)](https://digitalcommons.wcupa.edu/pennsylvania-economic-review/vol31/iss1/2)
- QuantConnect / Quantpedia strategy: hold the **top-5 country ETFs by 6-month return**, rebalanced monthly. The reported outperformance (about 90%/yr for 2002-2022 vs. equal-weight) looks implausible. Treat it as an unverified illustration. — [QuantConnect](https://www.quantconnect.com/learning/articles/investment-strategy-library/momentum-effect-in-country-equity-indexes), [Quantpedia #15](https://quantpedia.com/Screener/Details/15)
- **[CONTEXT, 2019]** Alpha momentum and alpha reversal in country and industry indexes (Zaremba et al., Journal of Empirical Finance). — [Napier repository](https://napier-repository.worktribe.com/output/3011105/alpha-momentum-and-alpha-reversal-in-country-and-industry-equity-indexes)

### Inferences
- **China, practical shortlist for a 30-100 stock long-only universe:**
  1. **Weekly or monthly short-term reversal**, ideally residual (industry/market-neutral) reversal: buy last month's or last week's losers.
  2. **Avoid high-MAX / lottery stocks**: exclude the top MAX(1-month) decile, or overweight low-MAX.
  3. **E/P value**.
  4. **Low turnover / low abnormal turnover**.

  All are long-only expressible, which matters because shorting is impractical (see Q2). Given Li et al. (2024), keep the hypothesis set small and pre-registered.
- **China, size:** the CH-3 "shell value" premium depends on the IPO regime. The post-2017 tightening on reverse mergers and the 2023 shift to a registration-based IPO system plausibly shrink shell value, so a backtest should split samples around 2017 and 2023. The 2023 registration reform is not verified in this pass.
- **China, limit-up chasing:** the evidence is mixed and old, and it is not executable in daily-close backtests. A stock that closes at limit-up usually cannot be bought (the queue at the limit is full), and one at limit-down usually cannot be sold.
- **Japan:** the reform signal is a **low-PBR × high-ROE** screen within TOPIX/Prime, for example the bottom PBR tercile intersected with the top ROE tercile. Its post-2023 excess return is likely partly a one-off repricing (the paper finds no fundamental change), so out-of-sample persistence after 2025 is uncertain.
- **Japan, momentum:** pure 12-1 momentum is a weak standalone. If used, combine it with value, or use residual momentum.
- **Europe:** standard multi-factor approaches (value, momentum, quality, low-vol) apply. For a small universe (Euro Stoxx 50 / DAX), country or sector ETF momentum may be more robust than single-stock factors.

### Gaps
- No exact portfolio rules or performance numbers for the 2024 China reversal papers: Zhang & Zhu is paywalled and Liu-Huang-Chao is in Chinese.
- No 2023-2026 peer-reviewed study of the limit-up next-day effect was found. Chinese-language journals (涨停板效应) were not searched.
- No 2023-2026 study explaining Japan's momentum weakness was found.
- No quantitative 2023-2026 European single-stock factor premia from Robeco, Man or AQR. Only WisdomTree commentary surfaced. Ken French's Developed Europe and Japan factor files would give a direct free check, but were not verified in this pass.
- H-share / AH-premium strategies were not researched.
- The D'Ercole et al. return magnitudes (abnormal returns by PBR bucket) are in the downloaded PDF but were not extracted. Only the abstract was read.

---

## Q2. Market-microstructure constraints a backtest must model

### Takeaway
A-share backtests must enforce:
- **T+1** (no same-day round trip);
- **daily price limits**: ±10% main board, ±20% STAR and ChiNext, ±5% risk-warning (ST) stocks, and no limits on the first 5 STAR IPO days;
- **100-share lots** (STAR orders of at least 200 shares);
- **seller-side stamp duty of 0.05% since 28 Aug 2023** (0.1% before);
- **effectively no shorting** for most investors.

Japan and Europe are closer to US conventions. The main differences are the trading calendar, currency, and transaction taxes (UK stamp duty, French and Italian FTT).

### Cited Findings
- **SSE main board:** "a 10% daily price limit on the auction trading of all A-share and B-share stocks". No limit applies on the first trading day after an IPO, secondary offering, resumption after suspension, or relisting. — [SSE Stock Trading Mechanism](https://english.sse.com.cn/start/trading/mechanism/)
- **SSE STAR Market:** 20% price limit during auction trading, with **no limit on the first five trading days after IPO**. Limit orders must be **at least 200 and at most 100,000 shares**, and market orders are capped at 50,000. — [SSE](https://english.sse.com.cn/start/trading/mechanism/)
- **Risk-warning (ST) stocks:** "subject to a price limit of 5% on each trading day". — [SSE](https://english.sse.com.cn/start/trading/mechanism/)
- **Lot size:** main board buy orders must be in multiples of **100 shares**, and odd-lot remainders under 100 can be sold in one order. **Tick size** is RMB 0.01. — [SSE](https://english.sse.com.cn/start/trading/mechanism/)
- **Auctions:** opening and closing call auctions execute all trades at one price that maximizes matched volume. — [SSE](https://english.sse.com.cn/start/trading/mechanism/)
- **STAR and ChiNext** stocks both have a 20% daily limit (Hong Kong investor-education guide on Stock Connect). It also covers trading-day and holiday differences between Stock Connect and the home markets. — [IFEC HK](https://ifec.org.hk/web/en/financial-products/investment/stock/stockconnect/major-risks.html)
- **Stamp duty** was cut from **0.1% to 0.05%, charged on the seller**, effective **28 August 2023** (MOF Announcement [2023] No. 39). It also applies to Northbound Stock Connect. It was the first cut since 2008, when the rate went from 0.3% to 0.1%. — [gov.cn](https://english.www.gov.cn/policies/policywatch/202308/28/content_WS64ec5513c6d0868f4e8dee23.html), [21jingji/CBN](https://m.21jingji.com/article/20230828/herald/faab376b468f1b96cbaa8baac81c1c42.html), [HKEX circular](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/HKSCC/2023/ce_HKSCC_SET_039_2023.pdf)
- **T+1 matters for returns:** Zhang & Zhu (2024) attribute China's strong short-term contrarian effect to the T+1 rule. — [IDEAS](https://ideas.repec.org/a/eee/reveco/v96y2024ipbs1059056024006452.html)
- **Overnight returns:** the lottery anomaly is concentrated in overnight returns (Gu-Hu-Xiong 2025), so open-vs-close execution assumptions matter a lot. — [IDEAS](https://ideas.repec.org/a/bla/acctfi/v65y2025i1p883-911.html)
- Jansen et al. (2021) find that **short-sale restrictions are not a major driver** of anomaly returns in China. — [EUR Pure](https://pure.eur.nl/en/publications/anomalies-in-the-china-a-share-market/)
- **IPO price-limit regime:** a policy that produced consecutive limit-ups after IPO raised returns, turnover, volatility and beta for about 2 years after listing. Exclude recent IPOs or model this. — [Clemson dissertation](https://open.clemson.edu/all_dissertations/2160)

### Inferences
Backtest rules for A-shares:
- **Position limits:** cap the position change at 0 for any day the stock closes at its limit:
  - no buys at the upper limit;
  - no sells at the lower limit.
  - Detect limits from the prior close × (1 ± limit). The limit depends on the board, which you can read from the code prefix: 60xxxx SSE main, 688xxx STAR, 00xxxx SZSE main, 300xxx ChiNext, and 8xxxxx/4xxxxx/920xxx BSE (BSE limit ±30%, not verified here).
  - Suspended days have zero volume and should block trading.
- **T+1:** a stock bought on day t cannot be sold before t+1. Daily-bar strategies trading at the close already satisfy this, but intraday or open-to-close strategies do not.
- **Costs:** a reasonable cost model is seller stamp duty of 0.05% (0.1% before 2023-08-28), commission of about 0.02-0.03% each side (min about RMB 5), a small transfer fee, plus slippage.
- **Shorting:** model as long-only, or long vs. a CSI 300 / CSI 500 futures hedge. Margin securities lending is limited, and was further restricted from 2023 to 2024. These restriction details are not verified in this pass.
- **Japan:**
  - lot size is 100 shares;
  - daily price limits are absolute-yen bands that depend on the price level;
  - T+2 settlement (not verified in this pass);
  - costs are low;
  - JPY/USD exposure matters if a backtest is denominated in USD (EWJ vs. DXJ hedged).
- **Europe:**
  - UK stamp duty of 0.5% on purchases;
  - France and Italy financial-transaction taxes on large caps;
  - multiple currencies (EUR, GBP, CHF, SEK);
  - different holidays across exchanges.

  None of these were verified in this pass. Treat them as checklist items to confirm.

### Gaps
- No official source was obtained for: T+1 (it is standard knowledge but uncited here), BSE ±30% limits, ChiNext's no-limit IPO window, current margin and short-selling rules, or commission levels.
- Possible 2025 changes to SZSE/SSE price limits for risk-warning stocks (5% → 10%) were not verified. Check the current exchange rules before hard-coding 5%.
- Japan price-limit bands, Japan settlement, and EU FTT and UK stamp-duty details were not sourced.

---

## Q3. Most reliable free way to pull 10+ years of daily data and constituents

### Takeaway
- **China:** use **baostock** (free, no token, 1990s onward, front- or back-adjusted, historical CSI 300 / SSE 50 / CSI 500 membership by date) or **akshare** (East Money / Sina / Tencent scrapers, plus CSIndex current constituents with weights).
- **Japan, Europe and HK:** **yfinance** with exchange suffixes is the easiest route, but adjusted prices for non-US tickers (especially .SS/.SZ) can be missing dividend adjustments. Use `repair=True` and cross-check against stooq or a second source.
- **Constituents:** there is no free point-in-time source for Nikkei, TOPIX or STOXX. Current lists only, so survivorship bias must be acknowledged.

### Cited Findings
**baostock (China)**
- Official quick start: `bs.login()`, then `bs.query_history_k_data_plus("sh.601398", "date,code,open,high,low,close,volume,amount,adjustflag", start_date=..., end_date=..., frequency="d", adjustflag="3")`. Codes use the `sh.` / `sz.` prefix. — [PyPI baostock](https://pypi.org/project/baostock/)
- Wrappers pass `adjustflag` straight through and handle empty results. One that switches between libraries strips the `sh.`/`sz.` prefix before calling akshare (akshare uses bare 6-digit codes). — [glama MCP baostock source](https://glama.ai/mcp/servers/@24mlight/a-share-mcp-is-just-i-need/blob/4a2d4b730e13a689782f0adef7e0446a4f3cf926/src/baostock_data_source.py), [akshare wrapper](https://glama.ai/mcp/servers/@jamesdingAI/stockreport-mcp/blob/b3baeb1054a2153ef1235e29d571e7c11abc65a4/src/akshare_data_source.py)

**akshare (China)**
- Daily stock bars: `ak.stock_zh_a_hist(symbol="600519", period="daily", start_date="20140101", end_date="20241231", adjust="qfq")`. `adjust` takes "" (raw), "qfq" (forward-adjusted) or "hfq" (back-adjusted). — [akshare stock skill docs](https://skillselion.com/skills/skills.volces.com/akshare-stock)
- **CSI 300 constituents:**

  | Function | Source | Fields | History |
  |---|---|---|---|
  | `ak.index_stock_cons(symbol="000300")` | Sina | code, name, inclusion date (纳入日期) | Latest list only. Docs warn some rows can be duplicated. |
  | `ak.index_stock_cons_csindex(symbol="000300")` | China Securities Index (official) | date, index code, constituent code and name, exchange | Single date |
  | `ak.index_stock_cons_weight_csindex(symbol="000300")` | China Securities Index (official) | same as above, plus **weight %** | Single date |

  No historical CSI 300 constituent function is documented. — [akshare index docs](https://akshare.akfamily.xyz/data/index/index.html)
- **Index daily history:**
  - `ak.index_zh_a_hist(symbol="000300", period="daily", start_date, end_date)` (East Money; includes turnover);
  - `ak.stock_zh_index_daily(symbol="sh000300")` (Sina, full history);
  - `ak.stock_zh_index_daily_em(symbol="sh000300")`;
  - `ak.stock_zh_index_daily_tx`.

  HK index daily data is available via `stock_hk_index_daily_sina` / `_em`, and global indices via `index_global_hist_em` / `_sina`. — [akshare index docs](https://akshare.akfamily.xyz/data/index/index.html)

**yfinance (all regions)**
- `.SS` / `.SZ` tickers on Yahoo have been reported to show **no dividend or split adjustment** even when adjustment is requested, and some symbols fail to resolve. — [Wealth-Lab forum](https://www.wealth-lab.com/Forum/Posts/No-Dividend-Split-adjustment-reflected-in-PricePane-31609)
- A third-party index of the yfinance repo says `history(repair=True)` targets common non-US data errors, including manually applying **missing dividend adjustments** to Adj Close. This was not confirmed against official docs. — [Algolia DocSearch of yfinance repo](https://docsearch.algolia.com/mcp/docs/repo/ranaroussi/yfinance)
- Yahoo has had missing whole days of history: issue #2621 covers 5 Nov 2025, and the reporter says it is a Yahoo-side problem, not a yfinance bug. — [GitHub yfinance #2621](https://github.com/ranaroussi/yfinance/issues/2621)
- General Yahoo download errors and workarounds. — [Robot Wealth](https://robotwealth.com/solved-errors-downloading-stock-price-data-yahoo-finance/)

**Survivorship / point-in-time**
- The CH-3 exclusion of the bottom 30% and IPO-regime breaks mean universe construction itself drives results in China. — [NBER w24458](https://www.nber.org/papers/w24458.pdf), [Quantpedia](https://quantpedia.com/evaluating-factor-models-in-china/)

### Inferences
These are practitioner conventions not individually sourced in this pass. Verify before use.

**yfinance suffixes**

| Suffix | Exchange | Example |
|---|---|---|
| `.SS` | Shanghai | `600519.SS` |
| `.SZ` | Shenzhen | `000001.SZ` |
| `.HK` | Hong Kong, 4-digit | `0700.HK` |
| `.T` | Tokyo | `7203.T` |
| `.DE` | Xetra | `SAP.DE` |
| `.PA` | Paris | `MC.PA` |
| `.L` | London (GBp pence) | `SHEL.L` |
| `.AS` | Amsterdam | `ASML.AS` |
| `.MI` | Milan | |
| `.MC` | Madrid | |
| `.SW` | Swiss | |
| `.ST` | Stockholm | |
| `.CO` | Copenhagen | |
| `.HE` | Helsinki | |
| `.BR` | Brussels | |

Indices:

| Ticker | Index |
|---|---|
| `000300.SS` | CSI 300 |
| `^N225` | Nikkei 225 |
| `^STOXX50E` | Euro Stoxx 50 |
| `^STOXX` | STOXX 600 |
| `^GDAXI` | DAX |
| `^HSI` | Hang Seng |
| `^FTSE` | FTSE 100 |

`.L` prices are in pence, so divide by 100 for GBP.

**US-listed country ETFs** (USD, US calendar)

| ETF | Exposure |
|---|---|
| FXI | China large-cap H/red-chip |
| MCHI | MSCI China |
| ASHR | CSI 300 A-shares |
| KWEB | China internet |
| EWJ | MSCI Japan |
| DXJ | Japan, JPY-hedged, export tilt |
| EZU | EMU |
| VGK | FTSE Developed Europe |
| EWG | Germany |
| EWU | UK |
| EWQ | France |
| EWN | Netherlands |
| EWL | Switzerland |
| EWH | Hong Kong |

Most have history from the 1996-2011 period, so 10+ years is available. They suit the country-rotation strategy (Pennsylvania Economic Review study above).

**Recommended pipeline per region (30-100 stocks, 10+ years)**
- **China:**
  1. Take the current constituents from `ak.index_stock_cons_weight_csindex("000300")`, or historical membership from baostock `query_hs300_stocks(date=...)`. That baostock function is not verified in this pass; check the baostock docs.
  2. Pull prices with baostock `query_history_k_data_plus(..., adjustflag="2")` (forward-adjusted) or `"1"` (back-adjusted), with akshare `stock_zh_a_hist(adjust="hfq")` as a fallback. The adjustflag mapping 1=hfq, 2=qfq, 3=none is not verified here.
  3. Pull `isST`, `tradestatus` and `pctChg` fields from baostock to model suspensions and limits.
- **Japan:**
  1. Nikkei 225 or TOPIX Core30 / Large70 constituents from the Nikkei and JPX websites. These are current lists only.
  2. Prices from yfinance `XXXX.T` with `auto_adjust=True, repair=True`. Cross-check with stooq (`pandas_datareader.data.DataReader("7203.JP", "stooq")`).
  3. Book-to-price and ROE for the PBR screen are not reliably free. yfinance `.info` gives only a current snapshot.
- **Europe:** Euro Stoxx 50 / DAX constituents from Wikipedia tables (`pd.read_html`), then yfinance with the local suffix, converted to one currency via yfinance FX tickers (`EURUSD=X`, `GBPUSD=X`).
- **Calendar alignment:** China has the Golden Week and Spring Festival closures, Japan has Golden Week and year-end closures, and European exchange holidays differ. Never forward-fill across a different market's holiday when computing cross-market signals. Align on each market's own calendar (e.g. `exchange_calendars` / `pandas_market_calendars` with XSHG, XTKS, XETR, XPAR, XLON).

**Survivorship bias**
- Current-constituent universes overstate returns. This is especially true for China, where delisting accelerated after 2020, and for Japan, where TSE market restructuring in 2022 moved firms between segments.
- Mitigations:
  - use baostock's dated index membership for China;
  - for Japan and Europe, state the bias explicitly, or use ETFs and indices, which have no survivorship problem.

### Gaps
- Official baostock docs were not reachable (baostock.com returned an empty page). The `query_hs300_stocks` / `query_zz500_stocks` date parameter and the adjustflag mapping are unverified.
- tushare's free-tier limits in 2025-2026 (points system) were not researched.
- Current stooq coverage and the pandas-datareader stooq status for .JP and .DE tickers were not verified.
- No free point-in-time constituent source for Nikkei 225, TOPIX, Euro Stoxx 50, STOXX 600 or DAX was found.
- Yahoo's history length for .SS/.SZ (often from about the mid-2000s, with gaps) and for .T was not quantified.
