# Recent (2023–2026) Rules-Based Systematic Strategies & Anomalies Implementable on Daily Equity/ETF Data

Scope: non-ML, rules-based strategies, daily data, US / Europe / Japan / China equities and ETFs. Research date: 2026-10-19.
Local PDFs (open-access, downloaded, not executed) in `C:\Users\Acer\Pictures\research_papers\paper1\papers\systematic_strategies\`:
- `2026_Sepp_Lucic_science_practice_trend_following.pdf` (arXiv 2607.19497)
- `2025_Li_Ferreira_network_momentum_trend_following.pdf` (arXiv 2501.07135)
- `2024_Herculano_betting_against_bad_beta.pdf` (arXiv 2409.00416)
- `2024_Korniejczuk_Slepaczuk_multi_pair_stat_arb_graph_clustering.pdf` (arXiv 2406.10695)
- `2023_Jensen_Kelly_Pedersen_replication_crisis_finance_NBERwp.pdf` (NBER w28432; note: this is the Feb-2021 working-paper version of the 2023 JF article)
- `2022_NovyMarx_Velikov_betting_against_BAB.pdf` (author-hosted, rochester.edu; context, published JFE 2022)

Legend: [CONTEXT] = older seminal work, cited only for background. "yfinance" column = can it be reproduced with free daily yfinance data.

---

## Q1. Which anomalies/strategies have new 2023–2026 evidence of persisting out of sample, and which have decayed? (includes the ranking)

### Takeaway
The strongest recent out-of-sample (OOS) evidence is for diversified, volatility-normalised trend following (net Sharpe ~0.5 over 2000–2026) and for the broad factor zoo in aggregate (JKP: most factors replicate, with attenuated but positive post-publication alphas). Clear decay is documented for the classic US turn-of-month window, index-level overnight drift, Dual Momentum/GEM after 2014, naive TSMOM after 2009, and cost-adjusted pairs/stat-arb; low-beta/BAB survives only as a construction-sensitive, factor-explained effect.

### Cited Findings

**Meta-evidence on replication and decay**
- Jensen, Kelly & Pedersen (JF 2023; NBER WP 2021): Bayesian replication rate 84.9% for global factors; 10 of 13 themes replicate at >75% — exceptions are "seasonality", "leverage" and "size"; 10 of 13 themes enter the tangency portfolio, with profitability, investment and size displaced — [NBER w28432 PDF](https://www.nber.org/system/files/working_papers/w28432/w28432.pdf); [JF version](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13249)
- JKP restate McLean & Pontiff (2016): US factor returns are 26% lower out-of-sample and 58% lower post-publication; JKP argue attenuated-but-positive post-publication alpha is what Bayesian learning predicts, and that higher in-sample alpha factors have higher OOS alpha — [NBER w28432](https://www.nber.org/system/files/working_papers/w28432/w28432.pdf)
- JKP cite Jacobs & Müller (2020): the US is "the only country with a reliable post-publication decline in long-short returns" — relevant for applying anomalies to Europe/Japan/China — [NBER w28432](https://www.nber.org/system/files/working_papers/w28432/w28432.pdf)
- JKP: US factor alphas have 71% Spearman correlation with developed ex-US and 48% with emerging-market alphas; size factors are much stronger in emerging markets and micro caps — [NBER w28432](https://www.nber.org/system/files/working_papers/w28432/w28432.pdf)
- Liu (arXiv, Apr 2026): across 1,726 commercially marketed structured strategies from 10 institutions, backtest performance has "only limited portability into the live period"; backtests mostly reflect the pre-launch factor regime, and strategies launched after extreme factor runs deteriorate more (no magnitudes on abstract page) — [arXiv 2604.18821](https://arxiv.org/abs/2604.18821)

**Persisting (2023–2026 evidence)**
- Trend following: Sepp & Lucic (arXiv, Jul 2026) — European (EWMA), American (breakout/stop) and TSMOM systems on 84 liquid futures, net of costs, 31-Dec-1999 to 30-Jun-2026: Sharpe 0.47 / 0.50 / 0.55 vs 0.47 for the SG Trend Index; ~80% correlation with SG Trend Index — [arXiv 2607.19497](https://arxiv.org/abs/2607.19497) (local PDF)
- Turn-of-month (international, wider window): Kayacetin — 30 markets 1994–2023, ~10 bp/day mean over the 8-day TOM window vs ~0 bp otherwise; effect appeared arbitraged in the decade after publication but "comes back in full force", peaking in the US 2019–2023; found in all countries except Japan; stronger in emerging markets — [SSRN 7201062](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7201062); [ScienceDirect version](https://www.sciencedirect.com/science/article/abs/pii/S1042443126000259) (via search snippet; SSRN page returned 403)
- Industry-adjusted short-term reversal: Stosik & Zaremba — conventional 1-month reversal earns almost nothing across 64 countries; industry-adjusted reversal ~0.53%/month and outperforms standard reversal after trading costs — [SSRN 6630998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6630998); [Economics Letters / ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0165176526003095) (via search snippet; SSRN page returned 403)
- Market return concentrated around European open: Bondarenko & Muravyev (JFQA 2023) — using E-mini S&P futures, the 4 hours around the European open account for the entire average market return; the other 20 hours average a noisy zero; reported positive in every year/month/weekday of 2004–2018 per summary — [IDEAS/JFQA](https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html); [Alpha Architect summary](https://alphaarchitect.com/market-return-around-the-clock/)

**Decayed / weakened**
- Classic TOM [0:+3] window: "appears to have disappeared, likely arbitraged away" in US over the past decade; [-3:+3] still significant in most equity markets but substantially weaker — [QuantSeeker, Feb 2025](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)
- Han, Han & Tian (Finance Research Letters, Jan 2025): TOM no longer significant after 2001, attributed to decimalization/liquidity — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1544612324014909) (via search snippet). Conflicts with Kayacetin above (different samples/definitions).
- Overnight drift: Haghani, Ragulin & Dewey (Elm Wealth, Jun 2022) — S&P 500 cross-sectional overnight long-short ~38%/yr gross since 1995 (t≈17), but effect has weakened since 2008–2015 publications; at 1 bp per trade a small trader would have earned nothing over the last ~8 years of the sample; China a notable exception to overnight effect — [Elm Wealth](https://elmwealth.com/night-moves-overnight-drift/)
- Dual Momentum/GEM post-publication: 2008–2026 test — GEM 9.1% CAGR, Sharpe 0.74, MDD −20% vs SPY 11.6% CAGR and 60/40 Sharpe 0.84 — [Quant for Free](https://quant4free.com/analysis/dual-momentum/); Quanterlab 2008–2026: GEM (12m) ~9.3%/yr, Sharpe 0.63, MDD 33.7%; the absolute-momentum gate on SPY alone did better (~10.7%/yr, Sharpe 0.73); the international leg cost 1.4–3.2 pts/yr — [Quanterlab](https://quanterlab.com/research/antonacci-s-dual-momentum-taken-apart-gate-relative-leg-and-blends-across-four-l); Aissaoui: ~5.9%/yr 2014–2021 vs 17.4% pre-publication 1974–2013 — [LinkedIn](https://www.linkedin.com/pulse/dual-momentum-pre-post-publication-performance-abdennour-aissaoui). (Blog-grade sources; numbers differ by window.)
- Naive TSMOM after GFC: benchmark TSMOM Sharpe 0.50 Jul-2010–Sep-2020, ~40% below its full-sample level (consistent with Baltas & Kosowski 2020, Garg et al. 2020) — [Levy & Lopes, arXiv 2106.08420](https://arxiv.org/pdf/2106.08420). Contrast: Sepp & Lucic's net Sharpe ≈0.5 for 2000–2026 is roughly that same post-GFC level, i.e. trend persisted but at lower Sharpe than 1980s–2000s backtests.
- Pairs / stat-arb: replication of Cartea et al. (2023) graph-clustering stat-arb on US equities 03/2000–12/2022: Sharpe 1.17 with zero costs collapses to 0.28 at 0.05% costs (SPY 0.33); annual return 10.24% → 2.44% — [Korniejczuk & Ślepaczuk, arXiv 2406.10695](https://arxiv.org/pdf/2406.10695) (local PDF). ETF cointegration pairs 2000–2024 earned ~1.01% total profit with no costs; distance method insignificant after costs — [Chen & Alexiou via ResearchGate](https://www.researchgate.net/publication/393129635_Cointegration-based_pairs_trading_identifying_and_exploiting_similar_exchange-traded_funds)
- Volatility-managed portfolios: across 103 equity strategies, no systematic Sharpe improvement; OOS market combo Sharpe 0.42 vs 0.46 unmanaged — [Cederburg et al., JFE 2020](https://www.sciencedirect.com/science/article/abs/pii/S0304405X2030132X) [CONTEXT]. DeMiguel et al. (JF 2024): conditional multifactor version has 13% higher OOS net Sharpe than unconditional, but 5 of 9 single-factor vol-managed portfolios have negative Sharpe after estimation error and costs — [JF 2024](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13395). China: vol-managed multifactor OOS Sharpe 1.50 vs 0.99 — [Pacific-Basin Fin. J. 2024](https://www.sciencedirect.com/science/article/abs/pii/S0927538X24003263)
- Volatility targeting alpha in equity index futures mainly accrues to trend exposure (not found in commodities, bonds, FX) — [Hamill, Rattray & Van Hemert via ResearchGate](https://www.researchgate.net/publication/315459451_Trend_Following_Equity_and_Bond_Crisis_Alpha); [UMN seminar abstract "Volatility Targeting Is Trendy"](https://cse.umn.edu/node/165016)
- Factor momentum: reexamination finds the effect exists in aggregate but only four individual factors show positive OOS predictability — [QUB reexamination PDF](https://pureadmin.qub.ac.uk/ws/portalfiles/portal/532038294/A_reexamination_of_factor_momentum.pdf); original Ehsani & Linnainmaa (JF 2022) sample Jul-1973–Dec-2019 — [NBER w25551](https://www.nber.org/system/files/working_papers/w25551/w25551.pdf) [CONTEXT]
- HRP: on S&P 500 constituents, 1/N beat HRP OOS risk-adjusted in all setups — [Future Generation Computer Systems 2025](https://www.sciencedirect.com/science/article/abs/pii/S0167739X25000391); Indian-sector arXiv studies show HRP beating CLA/eigen portfolios OOS — [arXiv 2202.02728](https://arxiv.org/pdf/2202.02728), [arXiv 2210.00984](https://arxiv.org/pdf/2210.00984)

### Ranking: reproducibility (yfinance) × evidence of OOS robustness
Scores are my judgement (1–5) from the cited evidence; "Decay flag" = documented post-publication weakening.

| Rank | Strategy | Reproducible w/ yfinance (1–5) | OOS robustness evidence (1–5) | Product | Decay flag |
|---|---|---|---|---|---|
| 1 | Multi-asset ETF trend following, vol-targeted (EWMA 20/250 or TSMOM 10×10d) | 5 | 4 (Sepp & Lucic 2026, 26 yrs net) | 20 | Partial (lower post-2009 Sharpe) |
| 2 | Absolute-momentum / 10-month SMA gate on equity index ETF | 5 | 3 (2008–2026 OOS Sharpe 0.73) | 15 | No (but gate mainly cuts drawdown) |
| 3 | Cross-asset ETF momentum, top-4 of 13 + selective short (Quantpedia 2025) | 5 | 2 (in-sample 2006–2023 only) | 10 | Unknown |
| 4 | Sector ETF momentum + regime-gated short (Quantpedia 2024) | 5 | 2 (Sharpe 0.60–0.72, in-sample) | 10 | Pure L/S sector momentum unprofitable |
| 5 | TOM [-3:+3] on international/EM country ETFs | 5 | 2–3 (mixed: Kayacetin vs Han et al.) | 10–15 | YES in US [0:+3] |
| 6 | Dual Momentum / GEM | 5 | 2 | 10 | YES (post-2014) |
| 7 | Industry-adjusted short-term reversal (stocks) | 2 (needs industries, survivorship-free universe) | 4 (64 countries, net of costs) | 8 | Conventional reversal decayed |
| 8 | Low-beta / BAB (and Bad-Beta variant) | 2 | 3 (priced by FF6; construction-sensitive) | 6 | Partial |
| 9 | Overnight (close→open) index/ETF | 4 (needs open prices) | 1–2 | 4–8 | YES |
| 10 | Factor momentum | 2 (needs factor returns – Ken French, not yfinance) | 2 | 4 | Weak OOS |
| 11 | HRP / risk parity allocation (ETFs) | 5 | 2 (mixed vs 1/N) | 10 | n/a (allocation) |
| 12 | Pairs / cointegration stat-arb | 4 | 1 (dies at 5 bp) | 4 | YES |
| 13 | Country-ETF "front-running seasonality" | 5 | 1 | 5 | Not robust |

### Inferences
- Effects that survive are slow, diversified, low-turnover ones (trend, monthly momentum with filters); fast-turnover ones (pairs, overnight, conventional reversal) mostly fail once realistic costs of a few bp are applied.
- Since Jacobs & Müller find post-publication decline reliable only in the US, calendar and reversal anomalies are more likely to persist in Europe/Japan/China/EM implementations than in SPY-based tests — consistent with QuantSeeker's finding that TOM is strongest in international ETFs. (Japan is the documented exception for TOM.)
- Much of what "vol targeting" adds on equities is trend exposure; it is safer to treat vol targeting as risk normalisation inside a trend system than as a standalone alpha.

### Gaps
- No 2023–2026 peer-reviewed paper found that tests TSMOM specifically on single-stock or country-ETF equity universes with clean OOS results.
- Liu (2026) decay magnitudes and Kayacetin / Stosik-Zaremba full tables not accessible (abstract/snippet only; SSRN returned 403).
- No dedicated 2023–2026 Japan momentum replication found.

---

## Q2. What exact parameters do the sources use so they can be coded precisely? (strategy catalogue, latest first)

### Takeaway
Precise, code-ready rules exist for: Sepp-Lucic trend systems (EWMA spans 20/250, vol span 33d, TSMOM L=10,M=10), Quantpedia ETF asset momentum (avg of 3/6/9/12m, top-4, 30% short of bottom-1, 20d/250d correlation filter), Quantpedia sector momentum (12m, top-5, 25% short gated by 12m SMA), TOM windows ([0:+3], [-3:+3] with 5 bp costs), the country seasonality rule (T-11 month return, top-8 tapered weights), and Herculano's bad-beta double sort (3-yr rolling betas, monthly). Several thresholds (e.g., exact correlation entry condition) are only in table images and must be treated as free parameters.

### Cited Findings

#### S1. Trend-following systems (European EWMA / American breakout / TSMOM) — Sepp & Lucic, "The Science and Practice of Trend-Following Systems", arXiv 2607.19497, 21 Jul 2026 — [arXiv](https://arxiv.org/abs/2607.19497)
- Signal input: volatility-normalised daily returns z_t = r_t / σ_{t-1}; EWMA volatility span 33 days; EWMA smoothing λ = 1 − 2/(span+1) — (local PDF, Sec. 2, 7.1)
- European system: long-short EWMA filter on z_t with long span 250 and short span 20; position w_t = S_t × σ_target / (σ_t √a), a = 260 — (local PDF, Def. 4.1, Sec. 7.2)
- TSMOM system: aggregate signal over M periods of L days, L = 10, M = 10 — (local PDF, Sec. 7.2)
- American system: breakout entry/stop-loss with scales set to 5; ~50% lower turnover/rolling costs than European and TSMOM — (local PDF, Sec. 7.1–7.2)
- Universe: 84 liquid futures (equity, bond, short rate, FX, commodities); costs volume-based per Hurst et al. (2017) Exhibit B1; grid backtests 1-Jan-1997 to 10-Jul-2026 — (local PDF, Sec. 7)
- Performance (net, monthly, 31-Dec-1999 to 30-Jun-2026): Sharpe 0.47 (European), 0.50 (American), 0.55 (TSMOM) vs 0.47 SG Trend Index; Ledoit-Wolf p-values 0.96/0.82/0.62 (no significant difference) — (local PDF, Sec. 7.2)
- Turnover: volatility-normalised turnover 300–400%/yr for European & TSMOM, 125–200% for American — (local PDF, Sec. 7.2)
- Costs: at empirically observed first-lag autocorrelations, break-even cost for short-memory (fast) signals lies below realistic costs; higher costs push optimal span longer — (local PDF, Intro, App. C)
- On S&P 500 future, weights become extreme in low-vol periods; practitioners use floors; realized vol 18% vs 15% target — (local PDF, Sec. 4)
- yfinance: YES as ETF proxy (SPY, EZU/VGK, EWJ, MCHI/FXI, TLT/IEF, GLD, DBC, UUP); European ETFs via `.L/.DE/.PA` suffixes, Japan `1306.T`, China `510300.SS`. Results are on futures, so ETF replication will differ (funding, roll, fewer markets). [inference]
- [CONTEXT] Moskowitz, Ooi & Pedersen (2012) original TSMOM: diversified TSMOM delivers abnormal returns with little factor exposure and performs best in extreme markets — [NYU PDF](https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf)

#### S2. Network momentum trend (commodities) — Li & Ferreira, "Follow the Leader: Enhancing Systematic Trend-Following Using Network Momentum", arXiv 2501.07135, Jan 2025 — [arXiv](https://arxiv.org/abs/2501.07135)
- Combines univariate trend indicators with lead-lag ("momentum spillover") network indicators; lead-lag via DTW / shape-DTW / Lévy-area; lookback 132 days or ensemble {22, 44, 66, 88, 110, 132} — (local PDF)
- Results: MACD long-side net Sharpe 0.559; NMM-DDTW-E Sharpe 0.357; claimed statistically significant improvement on bootstrapped data — (local PDF)
- Applies to commodity futures only; uses graph learning (borderline ML). Low priority for equity/ETF. yfinance: partial (commodity ETFs).

#### S3. Cross-asset ETF momentum with correlation-filtered short — Pauchlyová & Vojtko (Quantpedia), "Refining ETF Asset Momentum Strategy", 10 Jan 2025 — [Quantpedia](https://quantpedia.com/refining-etf-asset-momentum-strategy/); [SSRN 5095447](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5095447)
- Universe (13): SPY, IWM, EFA, EEM, IYR, QQQ, LQD, IEF, TIP, GLD, USO, DBC, FXE; benchmark equal-weight of the 13
- Signal: average of 3-, 6-, 9-, 12-month momentum; monthly rebalance
- Long: top 4 ETFs equal weight (no filter). Short: bottom-1 ETF at 30% weight (5%–50% tested), active only when the correlation filter (20-day vs 250-day correlation; short works better when short-term > long-term correlation) signals; exact threshold not stated in text
- Sample 10-Apr-2006 to 28-Feb-2023, Yahoo Finance adjusted closes; shorting costs included in simple test
- Performance: qualitative only in text — long-short selective hedge has higher Sharpe and Calmar than long-only momentum and benchmark; plain long-short momentum underperformed the benchmark (tables are images)
- QuantConnect implementation of the same rules — [QuantConnect](https://www.quantconnect.com/research/21050/cross-asset-etf-momentum-with-a-correlation-based-short-hedge/)
- yfinance: YES (all US-listed ETFs).

#### S4. Sector ETF momentum with regime-gated short — Beluska (Quantpedia), "How to Improve ETF Sector Momentum", 10 Oct 2024 — [Quantpedia](https://quantpedia.com/how-to-improve-etf-sector-momentum/)
- Universe: XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY; benchmarks SPY and EW-9 sectors (monthly rebal); Yahoo daily data 22-Dec-1998 to 5-Sep-2024
- Rules: 12-month momentum on monthly prices; 1-month hold; long top 4/5/6 sectors; short bottom-1 at 5%–30%; short only when EW sector benchmark < its 12-month moving average; short cost = 3m rate. Best: 5 long, 1 short @25%
- Performance: Sharpe ~0.60–0.72 for selective-short variants; baseline 3v3 long-short "poor"; short-only ~−7% to −10%/yr
- Caveat: table captions inconsistent (4- vs 5-sector)
- yfinance: YES. European analogues (iShares STOXX Europe 600 sector ETFs on `.DE`) and Japan TOPIX-17 sector ETFs (`1617.T`–`1633.T`) are possible substitutes [inference; tickers not verified in sources].

#### S5. Turn-of-month (TOM) — QuantSeeker, "Turn-of-the-Month Strategies: Do They Still Work?", 9 Feb 2025 — [QuantSeeker](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)
- Windows: [0:+3] (Lakonishok & Smidt 1988: last trading day of month through 3rd day of next) and [-3:+3] (Etula et al. 2020); Ariel (1987) 9-day window described
- Implementation: long-only, enter at close of day 0−4, exit at close of day 0+3; cash earns zero; 5 bp one-way cost
- ETFs: SPY, QQQ, IWM; XLC…XLU; EWA, EWZ, EWC, EWQ, EWG, EWH, EWJ, EWD, EWU; TLT, HYG, UUP, DBA, DBB, DBE, DBP, BTC
- Results: equity ETFs +5–12 bp/day in [-3:3] vs other days (EWZ ~23 bp); US TOM strategies have lower CAGR, similar/lower Sharpe but smaller drawdowns vs buy-and-hold; EWZ, EWD, EWH TOM Sharpe "notably higher"
- Kayacetin (2024–2026): 8-day TOM window, 30 markets 1994–2023, ~10 bp/day; stronger at fiscal-quarter/half-year ends; not in Japan — [SSRN 7201062](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7201062)
- Quantpedia baseline strategy page — [Quantpedia TOM](https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes)
- yfinance: YES (index ETFs and local indices e.g. ^STOXX50E, ^N225, 000300.SS).

#### S6. Country ETF "front-running seasonality" — Quantpedia rule, extended by Allocate Smartly, 29 Apr 2025 — [Allocate Smartly](https://allocatesmartly.com/front-running-seasonality-in-country-etfs-an-extended-test/)
- Universe: 23 country ETFs (MSCI index proxies back to 1971)
- Signal: at month-end close, rank by the return of the month 10 months earlier ("T-11" in author's notation; e.g., end-March ranks by prior-year May)
- Weights: top 8 — ranks 1–3 18.18% each, #4 15.15%, #5 12.12%, #6 9.09%, #7 6.06%, #8 3.03%; monthly rebalance; no costs
- 1971–Mar 2025: 13.2%/yr, vol 19.0%, Sharpe 0.46, MDD −59.1% vs EW benchmark 11.2%, 17.4%, 0.38, −58.6%; not consistently effective; much better excluding late 1990s
- yfinance: YES for ETFs (EWJ, MCHI/FXI, EWG, EWU, EWQ, EZU …) but only from ETF inception (~1996/2000s).

#### S7. Industry-adjusted short-term reversal — Stosik & Zaremba, "Short-Term Reversal Persists Globally – If Properly Measured" (2026) — [SSRN 6630998](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6630998); [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0165176526003095)
- Idea: subtract industry return from each stock's prior-month return, sort on the residual; 64 countries; ~0.53%/month; beats standard reversal after costs (exact formation/weighting not accessible — SSRN 403)
- Related: industry "laggards" double profitability of industry momentum and reversal — [Farkas & Neszveda, EFMA 2024](http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2024-Lisbon/papers/underreaction_STReversal.pdf); reversal lasts ~2 weeks for high-turnover stocks, up to ~3 months for low-turnover — [NBER w30917](https://www.nber.org/system/files/working_papers/w30917/w30917.pdf)
- [CONTEXT] Residual reversal earns roughly twice the risk-adjusted return of conventional reversal — [Blitz et al. 2013, JFM](https://www.sciencedirect.com/science/article/abs/pii/S1386418112000468)
- yfinance: PARTIAL — prices OK, but industry classification must come from elsewhere (yfinance `.info` sector is current, not point-in-time) and delisted stocks are missing (survivorship bias) [inference].

#### S8. Betting Against (Bad) Beta — Herculano, arXiv 2409.00416, 28 Aug 2024 — [arXiv](https://arxiv.org/abs/2409.00416)
- Double sort on Frazzini-Pedersen beta and Campbell-Vuolteenaho "bad" (cash-flow) beta; 3-year rolling windows; monthly rebalance; CRSP 1963:01–2021:12 — (local PDF)
- BABB: 15.0% annual return, 13.8% vol, Sharpe 1.09 vs BAB 11.4%, 11.3%, Sharpe 1.01; success "relies on proper transaction cost mitigation" — (local PDF)
- Novy-Marx & Velikov (JFE 2022): FP beta (1-yr vol × 5-yr correlation) is not a true beta; BAB is priced by FF6 (low-beta stocks co-move with profitability, low asset growth, momentum) — [BABAB PDF](https://mysimon.rochester.edu/novy-marx/research/BABAB.pdf); [JFE](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21002051)
- BAB returns differ across high/low volatility states due to institutional demand shifts — [JFE 2025](https://www.sciencedirect.com/science/article/abs/pii/S0304405X25000029)
- Korea replication: rank-weighting tilts to micro/small caps — [KJFS 2025](https://www.e-kjfs.org/journal/view.php?doi=10.26845%2FKJFS.2025.04.54.2.97)
- yfinance: PARTIAL (needs broad stock universe; bad-beta needs VAR news decomposition inputs). ETF proxy: low-vol ETFs (e.g., USMV/SPLV) [inference].

#### S9. Dual Momentum / GEM — [CONTEXT] Antonacci (2014 book); post-publication tests 2024–2026 — [Antonacci extended backtest](https://medium.com/@garyantonacci_30463/extended-backtest-of-global-equities-momentum-dual-momentum-eb12902612e0); [Quanterlab](https://quanterlab.com/research/antonacci-s-dual-momentum-taken-apart-gate-relative-leg-and-blends-across-four-l)
- Published rule tested by Quanterlab: 12-month lookback; relative leg US vs international equity; absolute-momentum gate vs T-bills, else bonds. OOS numbers in Q1.
- yfinance: YES (SPY, VEU/ACWX, AGG/BND, BIL).

#### S10. Overnight vs intraday
- Rule (Quantpedia/Vojtko & Hanicová): buy SPY at close only if SPY > 20-day average, VIX below its average, and a sentiment indicator above its average; sell next open — [Quantpedia](https://quantpedia.com/strategies/market-sentiment-and-an-overnight-anomaly)
- Microstructure: ETF overnight premium largely from open order imbalances; accounting for these removes ~3/4 of the overnight-intraday gap — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S138641812030032X) [CONTEXT]
- yfinance: YES (Open, Close), but adjusted-open handling of dividends must be checked; China A-shares T+1 makes buy-open/sell-close impossible [inference].

#### S11. Pairs/cointegration — see Q1 decay evidence (Sharpe 1.17→0.28 at 5 bp); Korniejczuk & Ślepaczuk's improved version adds ML signal classifiers + Kelly sizing, so not purely rules-based — [arXiv 2406.10695](https://arxiv.org/abs/2406.10695). Quantpedia country-ETF pairs strategy page — [Quantpedia](https://quantpedia.com/strategies/pairs-trading-with-country-etfs)

#### S12. HRP allocation — [CONTEXT] López de Prado (2016); recent: Schur-complement unification of HRP and min-variance — [arXiv 2411.05807](https://arxiv.org/pdf/2411.05807); comparisons in Q1. yfinance: YES.

#### S13. Factor momentum — Ehsani & Linnainmaa: OOS version extracts PCs from factor returns using only data to month t, trades next month; 1973–2019 — [NBER w25551](https://www.nber.org/system/files/working_papers/w25551/w25551.pdf). yfinance: NO directly (use Ken French / JKP factor data, or factor ETFs MTUM/QUAL/VLUE/USMV/SIZE as rough proxy [inference]).

### Inferences
- The most precisely specified and fully free-data-reproducible items are S1 (with ETF proxies), S3, S4, S5, S6, S9 — all monthly or daily rules on ≤25 US-listed ETFs.
- Parameters hidden in images (S3 correlation threshold, S4 CAGR/MDD) should be grid-searched with an explicit multiple-testing penalty (e.g., deflated Sharpe) rather than tuned.

### Gaps
- Exact correlation-filter entry rule for S3, and CAGR/MDD for S3/S4 (only in table images).
- Exact formation/weighting rules for S7 (SSRN 403).
- Ehsani-Linnainmaa authors' 2024–2026 update not found.

---

## Q3. Which work as multi-country ETF strategies (EWJ, FXI, MCHI, EZU, VGK, etc.)?

### Takeaway
Multi-country ETF implementations with recent evidence are: trend following/absolute momentum (equity index legs are in Sepp-Lucic's universe), cross-asset ETF momentum (EFA/EEM legs), TOM on country ETFs (strongest in EM/international, absent in Japan), and the country-ETF seasonality rule (weak). Momentum transfers poorly to China A-shares and Japan, where reversal dominates.

### Cited Findings
- TOM [-3:+3] statistically significant in most equity markets, strongest in international and EM ETFs (EWZ, EWD, EWH best) — [QuantSeeker](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they); EWJ included in the test universe — same source
- TOM present in all 30 markets except Japan; stronger in emerging economies — [Kayacetin SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7201062)
- Country seasonality rule over 23 country ETFs: Sharpe 0.46 vs 0.38 EW, not robust — [Allocate Smartly](https://allocatesmartly.com/front-running-seasonality-in-country-etfs-an-extended-test/)
- Quantpedia country-index momentum strategy page (12-month momentum in country indices) — [Quantpedia](https://quantpedia.com/strategies/momentum-factor-effect-in-country-equity-indexes); Lazy Man's ETF momentum on 17–23 MSCI developed countries, rebalanced twice yearly — [Quant Investing](https://www.quant-investing.com/blog/lazy-mans-etf-momentum-strategy)
- GEM's international leg cost 1.4–3.2 pts/yr 2008–2026 (US dominance) — [Quanterlab](https://quanterlab.com/research/antonacci-s-dual-momentum-taken-apart-gate-relative-leg-and-blends-across-four-l)
- China A-shares: past-return anomalies weak except strong residual momentum and reversal (32 anomalies, 2000–2019) — [Pacific-Basin Fin. J. 2021](https://www.sciencedirect.com/science/article/pii/S0927538X21001141); intermediate momentum vanished and reversal took over after 2008 — [ScienceDirect 2022](https://www.sciencedirect.com/science/article/abs/pii/S0275531922002197); China shows daily momentum that reverses within a week, Japan shows daily reversals — [Daily Momentum, Princeton PDF](https://wxiong.mycpanel.princeton.edu/papers/DailyMomentum.pdf)
- Overnight effect present in nearly every major market except China — [Elm Wealth](https://elmwealth.com/night-moves-overnight-drift/)
- European-open window carries the whole S&P futures return (relevant for timing EU-listed vs US-listed ETF trades) — [Bondarenko & Muravyev, JFQA 2023](https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html)
- Data note: Quantpedia states Yahoo discontinued free end-of-day CSV downloads from its site (yfinance uses an unofficial API) — [Quantpedia 2025](https://quantpedia.com/refining-etf-asset-momentum-strategy/)

### Inferences
- Suggested free-data country universe (yfinance): US-listed EWJ, FXI, MCHI, EZU, VGK, EWG, EWU, EWQ, EWH, EWZ, EEM, SPY, plus local listings (`1306.T`, `510300.SS`, `^STOXX50E`/`EXS1.DE`). Use US-listed ETFs for a common USD close and avoid Asian/US close-time mismatch in cross-sectional ranking.
- For China, prefer reversal/short-horizon contrarian rules and TOM over 12-month momentum; for Japan, prefer trend/absolute momentum over TOM.
- Cross-sectional stock anomalies (BAB, reversal) on yfinance will carry survivorship bias because delisted tickers are unavailable; ETF-level strategies avoid this.

### Gaps
- No 2023–2026 paper found specifically testing 12-1 country-ETF cross-sectional momentum OOS with US-listed ETFs (EWJ/FXI/MCHI/EZU/VGK).
- Allocate Smartly / Robot Wealth / Return Stacked 2024–2026 posts on vol-targeted trend were not located in searches.
