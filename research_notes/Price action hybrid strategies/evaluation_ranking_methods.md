# Evaluating and Ranking Many Backtested Trading Strategies (with Costs): Methodology Notes

Scope: methods computable on a laptop from each strategy's daily (or per-trade) net return series, for about 40-80 price-action/hybrid rules on US ETFs (1-min intraday, daily swing, weekly positional), with sealed holdouts. These notes cover what to add beyond the metrics already computed (CAGR, vol, Sharpe, Sortino, Calmar, MaxDD, Ulcer, skew/kurt, tail ratio, PSR, DSR, trade stats, cost drag, break-even cost).

Convention used throughout: "Inferences" holds implementation specs and formulas taken from the original papers as I know them. I did not re-fetch every one of those formulas this session, and each is flagged "verify". "Cited Findings" holds only what I confirmed from a fetched or searched source.

---

## 1. Data-snooping and multiple-testing tests (White RC, Hansen SPA, Romano-Wolf StepM, Harvey-Liu-Zhu haircut, BH/BHY FDR, DSR with the right trial count)

### Takeaway
Run the whole family of tested variants, including discarded ones, through a bootstrap family-wise test: Hansen SPA (consistent p-value) for "does anything beat the benchmark?" and Romano-Wolf StepM for "which ones do?". All of these are available in `arch.bootstrap`, which takes losses (use loss = -net return or -excess return). Add Harvey-Liu haircut Sharpe (BHY) and DSR with an effective (correlation-adjusted) trial count as per-strategy deflators.

### Cited Findings
- `arch.bootstrap.SPA(benchmark, models, block_size=None, reps=1000, bootstrap='stationary', studentize=True, nested=False, *, seed=None)`: inputs are **losses** (a T-vector for the benchmark and T x k for the models). Methods are `compute()`, `better_models(pvalue, pvalue_type)` and `critical_values(pvalue)`. `pvalues` returns lower/consistent/upper p-values. "Upper" never recenters (equivalent to White's Reality Check), "consistent" recenters only when a model is within a log(log T) bound (Hansen's recommended version), and "lower" never recenters models worse than the benchmark. block_size defaults to sqrt(T), but the docs advise setting it explicitly. `nested=True` is slow because it runs k extra bootstraps. — [arch SPA docs](https://arch.readthedocs.io/en/latest/multiple-comparison/generated/arch.bootstrap.SPA.html)
- The arch module also provides `StepM(benchmark, models[, size, block_size, ...])` (Romano-Wolf stepwise) and `MCS(losses, size[, reps, block_size, ...])` (Hansen-Lunde-Nason Model Confidence Set). All are bootstrap procedures that control the family-wise error rate, and a model is "better" if its losses are smaller than the benchmark's. — [arch multiple-comparison reference](https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html); [arch overview](https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparisons.html)
- Harvey & Liu "Backtesting": the Sharpe ratio and the t-stat are linked (t = SR x sqrt(T), with SR per period). A t-ratio of 3.0 is very significant for a single test, but after multiple-testing adjustment it can correspond to an adjusted t of about 2.0. The haircut is the percentage drop from the original SR to the SR implied by the adjusted p-value. — [Harvey & Liu, Backtesting (CME-hosted PDF)](https://www.cmegroup.com/content/dam/cmegroup/education/files/backtesting.pdf); [Man Institute summary](https://www.man.com/insights/backtesting)
- Three adjustments are offered. Bonferroni is single-step and the most stringent, Holm is sequential, and BHY controls the FDR and is the most lenient, so it yields higher adjusted SRs. The haircut is non-linear, and the highest Sharpe ratios are penalized only moderately. An R reference implementation exists (quantstrat `haircutSharpe` / `SharpeRatio.haircut`). — [quantstrat haircut.Sharpe.R](https://rdrr.io/github/braverock/quantstrat/src/R/haircut.Sharpe.R); [rdrr SharpeRatio.haircut](https://rdrr.io/github/marsanul/quantstrat/man/SharpeRatio.haircut.html); [Harvey-Liu R code gist](https://gist.github.com/jaymon0703/50a170e4e37da951ea1192888418c82a)
- Secondary summary of the paper: haircuts on SRs below 0.4 are often above 50%, while those on SRs above 1.0 are at most about 25%, so a flat 50% haircut rule is too lenient for weak strategies and too harsh for strong ones. This is a secondary source and should be checked against the paper. — [CXO Advisory](https://www.cxoadvisory.com/big-ideas/navigating-the-data-snooping-icebergs/)
- ml4t-diagnostic: `from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio`. It is called as `deflated_sharpe_ratio(returns, frequency="daily", correlation_method="effective_rank", min_k_eff=2.0)` with a 2-D array holding one column per tested variant, and it returns `sharpe_ratio_annualized`, `probability`, `n_trials_raw` and `n_trials_effective`. The docs say to include every variant considered during selection, including discarded ones. A `deflated_sharpe_ratio_from_statistics()` variant takes accumulated `n_trials` and `variance_trials` plus the selected strategy's T, skew, excess kurtosis and autocorrelation. — [ml4t-diagnostic statistical-tests guide](https://raw.githubusercontent.com/ml4t/diagnostic/main/docs/user-guide/statistical-tests.md)
- ml4t-diagnostic FDR: `benjamini_hochberg_fdr(p_values, alpha=0.05, return_details=True)` returns `rejected` and `adjusted_p_values`, and assumes independent or positively dependent tests. `holm_bonferroni` is available for FWER control. The capability table also lists RAS (Rademacher anti-serum), PBO and White's Reality Check. — [ml4t-diagnostic statistical-tests guide](https://raw.githubusercontent.com/ml4t/diagnostic/main/docs/user-guide/statistical-tests.md); [ml4t/diagnostic GitHub](https://github.com/ml4t/diagnostic)
- The DSR inputs are the expected maximum SR of unskilled trials, skew, kurtosis, T, and the standard deviation of SRs across trials. The effective number of independent trials can be estimated by clustering similar strategies. — [Bailey & Lopez de Prado, DSR (SSRN 2460551)](https://papers.ssrn.com/abstract=2460551); [DSR overview mirror](https://wiki.krisyotam.com/content/wikipedia_en_all_nopic_2026-03/Deflated_Sharpe_Ratio)

### Inferences
- **Implementation spec: SPA/RC/StepM on our strategies**
  - Inputs: a T x k matrix of daily net returns for all k tested variants on a common calendar, with flat days set to 0 (intraday strategies aggregated to daily P&L / capital). Losses are L = -(r - r_f). Use two benchmarks: (a) zero excess return ("does it make money?"), and (b) buy-and-hold SPY or the same ETF ("does it beat holding?").
  - Settings: `bootstrap='stationary'`. Set block_size from `arch.bootstrap.optimal_block_length` (Politis-White) applied to the loss differentials. Use 5-20 days for daily data and 2-4 for weekly. Use reps=5000 for the final run.
  - Pass/fail: the family passes if SPA consistent p < 0.05 (0.10 is acceptable only as "weak evidence"). Individual strategies pass if they appear in `StepM(..., size=0.05).superior_models`.
  - Run these tests separately per horizon family (intraday / swing / positional) and once on the pooled family. Report both, and treat the pooled run as the honest one.
- **White's RC** = the SPA "upper" p-value (non-studentized, no recentering). Report it for completeness, but it is conservative and sensitive to poor or irrelevant models, which is why Hansen's consistent p-value is preferred.
- **Romano-Wolf StepM** gives the set of strategies individually significant with FWER control and is more powerful than Bonferroni because it uses the bootstrap joint dependence. Use it as the primary "which survive" filter. If it rejects nothing, fall back to ranking by DSR/haircut SR without claiming significance.
- **Model Confidence Set** (MCS, size=0.10, method 'R') gives the set of strategies that cannot be distinguished from the best. It is useful for the final shortlist, because it avoids picking one winner by noise.
- **Harvey-Liu haircut, steps (verify against the paper):**
  1. SR_ann gives t = SR_ann x sqrt(years); optionally adjust for autocorrelation with the Lo factor (section 3).
  2. p = 2(1 - Phi(t)).
  3. Compute adjusted p under Bonferroni (p x M), Holm, and BHY, with M = the number of tests (use the total trials logged, not just the survivors). Harvey-Liu-Zhu suggest also adding the field's prior tests.
  4. t_adj = Phi^-1(1 - p_adj/2), then SR_adj = t_adj / sqrt(years).
  5. Haircut = 1 - SR_adj/SR.

  Use BHY as the main figure and Bonferroni as the stress figure. No maintained Python package was found, so port the R code (about 100 lines).
- **t > 3 hurdle:** Harvey, Liu & Zhu (2016) proposed that new factors clear t > 3.0, which corresponds to an annual SR of about 3/sqrt(years). For 10 years of daily data that is SR > 0.95, and for 20 years SR > 0.67. This is a simple, defensible hard gate for "discovery" claims. The original HLZ 2016 RFS paper was not fetched this session (verify the exact wording).
- **BH vs BHY:** BH assumes independence or positive dependence. Strategies on the same ETFs are positively correlated, so BH is usually acceptable, and BHY (dividing alpha by sum_{i=1}^{M} 1/i) is the conservative choice for arbitrary dependence. Feed in per-strategy p-values from HAC t-stats or bootstrap, and use q = 0.10 for the shortlist and q = 0.05 for the final pick.
- **DSR, correct trial count and variance (formula from Bailey & Lopez de Prado 2014, verify):**
  - SR0 = sqrt(V[SR_k]) x [ (1-gamma) Phi^-1(1 - 1/N) + gamma Phi^-1(1 - 1/(N e)) ], with gamma = 0.5772 (Euler-Mascheroni).
  - DSR = Phi( (SR_hat - SR0) sqrt(T-1) / sqrt(1 - g3 SR_hat + (g4-1)/4 SR_hat^2) ), with SR in per-period (daily) units.
  - N must count every configuration tried, including parameter sweeps, discarded rules and earlier research iterations. Estimate N_eff via clustering of the return correlation matrix (ONC / hierarchical) or ml4t's effective-rank method. V[SR_k] is the cross-sectional variance of the trials' per-period SRs (not annualized).
  - Keep a persistent "trial ledger" (CSV of every config run) so that N and V are auditable.
  - Pass threshold: DSR >= 0.95 (strict). DSR 0.90-0.95 counts as "watchlist".

### Gaps
- I did not fetch the Romano & Wolf (2005) or White (2000) originals, or the StepM API page with full defaults. The StepM argument list is confirmed only partially (`size`, `block_size`, and more).
- I did not verify the exact HLZ (2016) t > 3 wording or the Harvey-Liu 2020 "False (and missed) discoveries" profit-hurdle tables (the PDF fetch timed out).
- I found no maintained Python package for the Harvey-Liu haircut. The R code is the reference.

---

## 2. Probability of Backtest Overfitting via CSCV (Bailey, Borwein, Lopez de Prado, Zhu 2017)

### Takeaway
Build the T x N matrix of per-period returns for all N variants, split the rows into S even blocks, and evaluate all C(S, S/2) train/test splits. PBO is the fraction of splits where the in-sample best lands below the OOS median (logit <= 0). The paper suggests rejecting a strategy-selection process with PBO > 0.05 under a Neyman-Pearson reading. In practice, many treat < 0.2-0.3 as acceptable for exploratory selection.

### Cited Findings
- Algorithm, as quoted from the paper:
  1. Form M (T x N) of performance per period per configuration, aligned on a common time index.
  2. Partition the rows into an **even number S** of disjoint submatrices of T/S rows.
  3. Form all combinations of size S/2. **S = 16 gives 12,870 combinations**; the paper's text reads "12,780", which appears to be a typo since C(16,8) = 12,870.
  4. For each combination: train J = the S/2 blocks in original order and test J-bar = the complement. Compute the performance vector R (IS) and R-bar (OOS), find n* = argmax IS, take its OOS relative rank omega-bar = rank/(N+1), and compute the logit lambda = ln(omega-bar/(1-omega-bar)).
  5. Collect the distribution of logits.

  — [Bailey, Borwein, Lopez de Prado, Zhu, "The Probability of Backtest Overfitting" (PDF)](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- PBO = integral of f(lambda) from -inf to 0, the rate at which IS-optimal strategies underperform the median OOS. phi ~ 0 means no significant overfitting and phi ~ 1 means likely overfitting. The paper says a "customary approach would be to reject models for which PBO is estimated to be greater than 0.05". It also suggests using PBO as a Bayesian prior, or weighting strategies by (1 - PBO) or 1/PBO. — [Bailey et al. PBO paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- The same framework gives three more diagnostics:
  - **performance degradation**: a regression of OOS performance on IS performance of the selected n*, where a negative slope signals overfitting;
  - **probability of loss**: the share of splits where the selected strategy's OOS performance is < 0;
  - **stochastic dominance**: whether IS-optimized selection first- or second-order dominates random selection OOS.

  Worked examples in the paper: one strategy had PBO = 74%; a real investment strategy had PBO ≈ 0.04% with about 3% probability of loss. For path-dependent metrics such as return/maxDD, block order matters; for Sharpe it does not. — [Bailey et al. PBO paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- ml4t-diagnostic exposes `compute_pbo`, which takes IS and OOS performance matrices of shape (n_folds, n_strategies) with aligned rows. It tests ranking decay, not Sharpe significance, so it complements DSR. — [ml4t-diagnostic statistical-tests guide](https://raw.githubusercontent.com/ml4t/diagnostic/main/docs/user-guide/statistical-tests.md)

### Inferences
- **Choice of S:** S = 16 is the paper's example (12,870 splits; trivial on a laptop with vectorized numpy). Each block must hold enough data for a stable Sharpe. For daily data, T/S >= about 60-125 trading days means S = 16 needs >= 4-8 years; use S = 8-10 for shorter samples. For weekly strategies use S = 8 (blocks of 1+ year). For 1-minute intraday, aggregate to daily P&L first (the paper requires a common index t).
- **Apply PBO to the selection process, not to one rule:** run it once per rule family, across that rule's parameter grid (N = grid size), to judge whether parameter selection overfits. Run it once across all 40-80 rules to judge whether picking the "best rule" overfits. Use only pre-holdout data; the sealed holdout stays untouched.
- **Python:** write about 40 lines yourself. Use itertools.combinations over block indices, compute Sharpe on the stacked blocks per column, rank with scipy.stats.rankdata, and compute the logit. Alternatively use ml4t `compute_pbo` or the `pypbo` GitHub package (not verified this session). mlfinlab's implementation is now behind a commercial licence (not verified this session).
- **Thresholds for our scorecard:** PBO <= 0.10 is green, 0.10-0.30 amber, and > 0.30 red (a hard fail for that family's selection). Also require probability of loss <= 0.20 and a degradation slope that is not strongly negative.

### Gaps
- I did not verify the current mlfinlab licensing or the status of `pypbo` maintenance.
- The paper gives no formal guidance on minimum block length; the S selection rule above is my inference.

---

## 3. Sharpe uncertainty: bootstrap CIs, MinTRL, Lo (2002) autocorrelation adjustment, Ledoit-Wolf Sharpe-difference test

### Takeaway
For each shortlisted strategy, report a stationary-bootstrap 95% CI for annualized Sharpe, Lo-adjusted Sharpe (autocorrelation), MinTRL vs SR* = 0 and vs SR* = the benchmark's SR, and a Ledoit-Wolf (2008) studentized-bootstrap test of SR(strategy) - SR(SPY). The JK/Memmel test is invalid under fat tails and serial dependence.

### Cited Findings
- Lo (2002): monthly SRs generally cannot be annualized by multiplying by sqrt(12), and serial correlation in monthly hedge-fund returns can overstate annual SR by as much as 65%. — [CFA Institute, Lo 2002 FAJ abstract](https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios)
- The correct scaling replaces sqrt(q) with eta(q) = q / sqrt(q + 2 Σ_{k=1}^{q-1} (q-k) ρ_k). Positive autocorrelation gives eta < sqrt(q), so the naive annualization is too high. This comes from secondary sources, and they note a bug in one R sandbox implementation. — [MetricGate](https://metricgate.com/docs/lo-autocorrelation-sharpe/); [PerformanceAnalytics sandbox LoSharpe.R](https://rdrr.io/github/cloudcell/PerformanceAnalytics/src/sandbox/Shubhankit/noniid.sm/R/LoSharpe.R)
- MinTRL is the minimum number of observed returns needed to assert, at a confidence level, that the true SR exceeds a reference SR. It comes from Bailey & Lopez de Prado, "The Sharpe ratio efficient frontier" (Journal of Risk 2012), and is implemented as R PerformanceAnalytics `MinTrackRecord`. — [risk.net Journal of Risk](https://www.risk.net/journal-risk/2223785/sharpe-ratio-efficient-frontier); [PerformanceAnalytics MinTrackRecord](https://rdrr.io/cran/PerformanceAnalytics/man/MinTrackRecord.html); [PortfolioOptimizer PSR/MinTRL write-up](https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/)
- Ledoit & Wolf (2008, J. Empirical Finance 15:850-859): the Jobson-Korkie test, as corrected by Memmel, is invalid with heavy tails or time-series dependence. They propose a studentized time-series bootstrap CI for the SR difference (reject equality if 0 is outside the CI), as well as HAC inference, with better finite-sample performance. R code is on Wolf's UZH page. — [Ledoit-Wolf 2008 PDF (UZH)](https://uzh.ch/cmsssl/econ/dam/jcr:ffffffff-935a-b0d6-0000-00007214c2bc/jef_2008pdf.pdf); [RePEc record](https://econpapers.repec.org/RePEc:eee:empfin:v:15:y:2008:i:5:p:850-859); [R-SIG-Finance pointer to code](https://mailman.stat.ethz.ch/pipermail/r-sig-finance/2008q4/003366.html)
- Caveat: O'Connor (2024, Econ Journal Watch) argues the LW test can be unreliable, reproduces the problems with the authors' own code, warns against basing portfolio selection on it, and notes that power for SR differences is much lower than for individual SRs. — [O'Connor 2024, Econ Journal Watch](https://econjwatch.org/file_download/1300/OConnorMar2024.pdf)

### Inferences
- **Bootstrap CI (Python):**
  - `from arch.bootstrap import StationaryBootstrap, optimal_block_length`
  - `bs = StationaryBootstrap(b, r)` with b from `optimal_block_length(r)['stationary']`
  - `bs.conf_int(lambda x: np.sqrt(252)*x.mean()/x.std(ddof=1), reps=5000, method='bca')`. Use 'studentized' or 'percentile' if BCa is unstable.

  Pass if the lower 95% bound is > 0 on the full pre-holdout sample. Report the CI width as a stability measure.
- **MinTRL formula (verify against the paper):** MinTRL = 1 + [1 - g3·SR + (g4-1)/4·SR^2] · (z_alpha / (SR - SR*))^2, in observations, with per-period SR, g4 = raw kurtosis, and z_alpha = 1.645 for 95%.
  - Pass if the actual track length T >= MinTRL vs SR* = 0. Bonus if T >= MinTRL vs SR* = the benchmark's SR.
  - Apply the test to the **holdout** length too. A 1-2 year holdout rarely passes for SR < 1.5, so state that explicitly rather than over-reading the holdout.
- **Lo adjustment:** estimate ρ_k on daily returns with k up to about 10 (statsmodels `acf`). Annualize with eta(252) or, more practically, compute SR on non-overlapping monthly returns and scale with eta(12). Also use a Newey-West SE for the mean (statsmodels OLS on a constant with `cov_type='HAC', cov_kwds={'maxlags': L}`) to get an autocorrelation-robust t-stat. That t-stat is also the right input for the HL haircut and BH.
- **LW Sharpe difference:** no maintained Python package was found. Port the R code: a studentized circular block bootstrap of Δ = SR1 - SR2 with a HAC SE via the delta method on (mu1, mu2, E[r1^2], E[r2^2]), with block size from the paper's calibration or 5-10 days. Report it as information rather than a hard gate, given O'Connor's critique and the low power. The SPA/StepM with SPY as benchmark is the primary "beats benchmark" test.

### Gaps
- I did not fetch the exact MinTRL and Lo eta(q) formulas from the primary PDFs; they come from secondary or background sources (flagged "verify").
- I found no maintained Python package for the Ledoit-Wolf 2008 test.

---

## 4. Robustness diagnostics: walk-forward, parameter stability, fill sensitivity, Monte Carlo, regime consistency, alpha/beta, capacity

### Takeaway
These are mostly engineering rather than single-paper methods. Each should produce one scalar for the scorecard: walk-forward efficiency, plateau ratio, fill-stress Sharpe, MC 95th-percentile drawdown, fraction of positive years and regimes, NW-t of alpha vs SPY, and capacity at 10 bp impact.

### Cited Findings
- ml4t-diagnostic provides `WalkForwardCV`, `CombinatorialCV` (combinatorial purged CV family) and `ValidatedCrossValidation`, plus `BacktestProfile` and portfolio/factor-attribution/trade diagnostics with HTML tearsheets. — [ml4t/diagnostic GitHub](https://github.com/ml4t/diagnostic)
- The CSCV "performance degradation" regression (OOS on IS performance of the selected configuration) quantifies how much IS outperformance decays OOS. — [Bailey et al. PBO paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- HAC (Newey-West) inference is the recommended treatment for overlapping or serially correlated observations, and ml4t-diagnostic uses HAC-adjusted statistics with the lag matched to the horizon. — [ml4t-diagnostic statistical-tests guide](https://raw.githubusercontent.com/ml4t/diagnostic/main/docs/user-guide/statistical-tests.md)

### Inferences
These are practitioner standards; none was sourced to a single paper this session.

- **Walk-forward / anchored re-optimization:**
  - Use rolling windows (e.g. 3-year train / 6-month test for daily, 5-year / 1-year for weekly, 60-day / 10-day for intraday) and anchored (expanding) windows.
  - Re-select parameters each window by IS Sharpe and stitch the OOS segments.
  - Metric: walk-forward efficiency WFE = annualized OOS SR / annualized IS SR. Pass if WFE >= 0.5, and the stitched-OOS SR must be > 0 with a bootstrap lower bound > 0.
  - Also report parameter drift: how often the chosen parameter changes across windows. Rules whose best parameter jumps around are fragile.
- **Parameter-stability heatmaps (plateau vs spike):**
  - For 2-D grids, plot SR over (p1, p2) with seaborn/matplotlib.
  - Quantify with the plateau ratio: the median SR of the 3x3 (or ±1-step) neighbourhood around the chosen point divided by the chosen point's SR. Pass if >= 0.7, and the fraction of grid cells with SR > 0 should be >= 60%.
  - Choose parameters at the centre of a plateau (for example, maximize a smoothed SR surface with a Gaussian filter, `scipy.ndimage.gaussian_filter`), not at the peak.
- **Fill-assumption sensitivity:**
  - Re-run each strategy under (a) next-bar open fill, (b) signal-bar close fill, (c) adverse fill (+1 tick or +1 half-spread worse), and (d) a one-bar delay for intraday.
  - Report SR under the worst variant; delay sensitivity is the key one for 1-minute rules. Pass if SR_worst >= 50% of the base SR and > 0. Limit-order rules need a "touch is not a fill" check (require a trade-through of 1 tick).
- **Monte Carlo trade reshuffling / bootstrap for drawdowns:**
  - Resample the per-trade returns (iid shuffle and bootstrap with replacement) or block-bootstrap the daily returns, about 10,000 paths, and record the distribution of max DD, max DD duration, and probability of ruin (DD > X%).
  - Use the 95th-percentile MaxDD for position sizing and the Calmar denominator, and flag strategies whose historical DD is in the left 10% (lucky path).
  - Reshuffling destroys serial dependence, so prefer the block bootstrap for daily series (`arch.bootstrap.StationaryBootstrap`).
- **Regime / subperiod consistency:**
  - Calendar years: share of years with positive net return (pass if >= 60-65%) and worst year.
  - Bull/bear: SPY above/below its 200-day SMA, or drawdown > 20%.
  - Volatility: VIX terciles or VIX > 20 vs < 20. Rate regimes: 2022 hiking. Crisis windows: 2008, 2020-03, 2022.
  - Pass if the SR is positive in >= 2 of 3 VIX terciles and no single year contributes > 40% of total P&L (a concentration check).
  - A Kruskal-Wallis or a regression with regime dummies plus a NW SE can test the dependence formally.
- **Alpha/beta vs SPY (and factor) regression:**
  - `statsmodels.OLS(r_s - rf, sm.add_constant(r_spy - rf)).fit(cov_type='HAC', cov_kwds={'maxlags': int(4*(T/100)**(2/9))})`.
  - Report annualized alpha, beta, NW t(alpha), and the information ratio. Optionally add Fama-French 5 + momentum (pandas-datareader / Ken French library) and a downside-beta / Treynor-Mazuy timing term for swing/positional rules.
  - Pass if NW t(alpha) >= 2 (>= 3 if claiming a discovery under the HLZ standard) and |beta| is consistent with the stated design.
- **Capacity and turnover:**
  - Turnover is the annual sum of |Δposition| / capital; holding period is the average in bars.
  - Capacity: model impact as k·sigma_daily·sqrt(Q/ADV) (square-root law; k ≈ 0.5-1, verify), and find the AUM at which net SR falls by 25% or the impact cost per trade equals 50% of gross edge.
  - With SPY/QQQ/IWM ADV in the tens of billions, capacity is rarely binding for retail sizes, except on thin sector or leveraged ETFs and auction-only fills. Report participation (order size / 1-min bar volume) for intraday rules and cap it at 1-5%.

### Gaps
- I did not source formal academic thresholds for WFE, the plateau ratio or regime-consistency pass rates. The numbers above are practitioner conventions and my recommendations.
- I did not verify square-root impact coefficients for US ETFs this session.

---

## 5. Cost modeling: commissions, half-spreads (Corwin-Schultz, Abdi-Ranaldo, EDGE), auction slippage, borrow, stress multiples

### Takeaway
Model costs per side as commission + exchange/regulatory fees + half-spread + slippage/impact (+ borrow for shorts). Estimate half-spreads from daily OHLC with Abdi-Ranaldo or EDGE as a cross-check on quoted spreads, and rank strategies on net metrics at 1x **and** 2x cost, failing any rule whose net SR goes negative at 2x.

### Cited Findings
- IBKR Pro US stocks/ETFs:
  - **Tiered**: USD 0.0005-0.0035 per share, falling with monthly volume, USD 0.35 minimum per order, with exchange, regulatory and clearing fees passed through.
  - **Fixed**: USD 0.005 per share, USD 1.00 minimum, max 1% of trade value.

  Rates vary by region and client type. — [IBKR Commissions & Fees](https://www.interactivebrokers.ca/en/pricing/commissions-home.php); [IBKR commissions home](https://investors.interactivebrokers.com/en/pricing/commissions-home.php)
- The tier breakpoints (≤300,000 shares/month at $0.0035, >3M at $0.0005) come only from a third-party review and are not confirmed on IBKR's own page (direct page returned 403). — [third-party IBKR review](https://global-brokerresearchcenter.pages.dev/interactive-brokers-review)
- Abdi & Ranaldo (2017, RFS 30(12):4437-4480) estimate bid-ask spreads from daily close, high and low prices. The estimator is Roll-like but uses the covariance of close-to-mid-range returns around the same close price. It is implemented in R package `bidask` (methods "AR" and "AR2" for the two-period version). — [RePEc/IDEAS record](https://ideas.repec.org/a/oup/rfinst/v30y2017i12p4437-4480..html); [bidask spread docs](https://rdrr.io/cran/bidask/man/spread.html); [bidask CRAN PDF](https://search.r-project.org/CRAN/packages/bidask/bidask.pdf)

### Inferences
- **Abdi-Ranaldo formula (from the paper, verify):**
  - Inputs: c_t = log close, eta_t = (log H_t + log L_t)/2.
  - Two-day estimate: s_t^2 = 4 (c_t - eta_t)(c_t - eta_{t+1}). Set negative values to 0, then average over a month: S = sqrt(max(mean s_t^2, 0)) or the mean of sqrt(max(s_t^2, 0)).
  - **Corwin-Schultz (2012):** beta = Σ over 2 days of [ln(H/L)]^2; gamma = [ln(H_{t,t+1}/L_{t,t+1})]^2; alpha = (sqrt(2 beta) - sqrt(beta))/(3 - 2 sqrt2) - sqrt(gamma/(3 - 2 sqrt2)); S = 2(e^alpha - 1)/(1 + e^alpha). Adjust for overnight returns and set negatives to 0.
  - **EDGE (Ardia, Guidotti & Kroencke, JFE 2024)** uses open, high, low and close. It is the most accurate of the three and is available as Python `pip install bidask` (`from bidask import edge`; the PyPI page did not load this session, so verify the API).
- **Use OHLC estimators with care for SPY/QQQ:** quoted spreads are about 1 cent (≈0.2-0.5 bp), below the resolution of daily-OHLC estimators, which are biased upward for ultra-liquid names. For the top-liquidity ETFs, use the quoted spread from 1-minute NBBO/quote data if available. Otherwise assume half-spread = $0.005 (1 tick / 2) plus 0.5-1 bp slippage. Use the OHLC estimators for less-liquid sector/country/leveraged ETFs, or as a cross-check that the assumed cost is not too low.
- **Cost model per round trip, per share (recommended defaults, verify):**
  - IBKR tiered: commission $0.0035 plus about $0.0002-0.003 in pass-through exchange/clearing fees per side. Alpaca: $0 commission, but you still pay the regulatory sell-side fees (SEC Section 31 fee on sell notional, FINRA TAF per share sold) and the spread, with possible payment-for-order-flow price-improvement differences.
  - Spread: half-spread on each side for market orders; 0 for limit fills but subject to a fill-probability haircut.
  - Slippage: intraday 1-min market orders get +0.5-1 half-spread extra at volatile times (first and last 15 minutes).
  - MOO/MOC auction orders: no spread, but the auction price can deviate from the prior last trade. Model them as 0.5-2 bp cost vs the official open/close, which is the price used in the backtest, and only if signals are computed before the auction cutoff (MOC orders are usually due ~15:50 ET at NYSE/Nasdaq; verify). Using the close price in a signal that then trades at that same close is look-ahead.
  - Borrow for shorts: liquid ETFs are mostly general collateral (about 0.25-0.5% p.a. borrow fee, verify with IBKR's short-stock availability tool), plus the short-rebate spread. Inverse ETFs can be an alternative but carry decay.
- **Stress multiples:**
  - Report net SR at 0x (gross), 1x, 2x and 3x the base cost, and the break-even multiple k* at which net SR = 0 (or net CAGR = rf).
  - Pass if net SR at 2x > 0 and k* >= 3 for daily/weekly. For 1-min intraday require k* >= 2 and break-even cost per share >= 3x the assumed all-in cost.
  - Express costs in bp of notional as well as $/share so that results are comparable across ETF prices.

### Gaps
- I could not fetch IBKR's US fee page (403) or Alpaca's current fee schedule. The 2026 SEC Section 31 rate and FINRA TAF were not verified.
- I did not verify MOC/MOO cutoff times or empirical auction slippage for ETFs this session.
- I did not verify the EDGE Python package API or the paper details from the PyPI page.

---

## 6. Combining everything into a single ranking / scorecard, with pass/fail thresholds

### Takeaway
Use a two-stage process. First, a set of hard **gates** (holdout and cost survival, multiple-testing survival, overfitting control). Then a **weighted rank-based composite** among survivors, dominated by holdout net performance and deflated or penalized in-sample statistics. Finish with an MCS/correlation-aware shortlist, so you pick a small, diversified set rather than the single noisiest winner.

### Cited Findings
- Bailey et al. suggest using PBO as a weighting input, with weights (1-PBO) or 1/PBO across strategies. — [Bailey et al. PBO paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- The ml4t-diagnostic docs frame DSR (Sharpe significance under multiple trials) and PBO (ranking decay) as complementary, and recommend logging all variants considered. — [ml4t-diagnostic statistical-tests guide](https://raw.githubusercontent.com/ml4t/diagnostic/main/docs/user-guide/statistical-tests.md)
- The MCS identifies the set of models not significantly worse than the best at a given confidence level. — [arch multiple-comparison reference](https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html)

### Inferences
I found no single published "standard" composite score; the following is a synthesized recommendation.

**Stage 0: hygiene (must hold before any scoring)**
- Trial ledger complete (N, N_eff, V[SR]).
- Holdout sealed until gates 1-4 are evaluated on pre-holdout data.
- Costs at the 1x base model.
- Minimum trade count: >= 100 trades (intraday/swing) or >= 30 (weekly).

**Stage 1: hard gates on pre-holdout data (fail any one and the strategy is out)**

| # | Test | Pass threshold |
|---|------|----------------|
| G1 | Net SR at 1x cost; bootstrap 95% CI lower bound | SR > 0.5 and lower bound > 0 |
| G2 | Net SR at 2x cost | > 0 (break-even multiple k* >= 3 for daily/weekly, >= 2 for intraday) |
| G3 | DSR with N_eff and V[SR] of the full trial ledger | >= 0.95 (0.90-0.95 counts as watchlist) |
| G4 | HL haircut SR (BHY, M = total trials) | > 0, and haircut <= 50% |
| G5 | PBO (CSCV, S = 8-16) of the family the rule was chosen from | <= 0.30 (green <= 0.10) |
| G6 | Romano-Wolf StepM vs zero-excess benchmark (FWER 5%) | included; family-level SPA consistent p < 0.05 |
| G7 | Parameter plateau ratio | >= 0.7 |
| G8 | Walk-forward efficiency | >= 0.5, and stitched OOS SR > 0 |
| G9 | Fill-stress (worst fill or one-bar delay) | SR >= 50% of base and > 0 |
| G10 | Regime/year consistency | >= 60% positive years; no year > 40% of P&L; SR > 0 in >= 2/3 VIX terciles |

**Stage 2: sealed holdout (once only)**
- Gate H1: holdout net SR > 0 and holdout SR >= 0.5 × IS SR. Also report the holdout PSR vs 0 and MinTRL, and acknowledge low power if T_holdout < MinTRL.
- Gate H2: holdout MaxDD <= the MC 95th-percentile MaxDD from IS. A breach suggests a regime change or overfitting.

**Stage 3: composite score among survivors**

Convert each metric to a cross-sectional percentile rank (0-1) within the surviving set. Ranks are robust to scale and outliers. Then:

Score = 0.25·rank(holdout net SR at 1x)
      + 0.15·rank(DSR)
      + 0.10·rank(1 - PBO)
      + 0.10·rank(-SPA/StepM adjusted p)  [or HL haircut SR]
      + 0.10·rank(net SR at 2x cost)
      + 0.10·rank(stability = mean of plateau ratio, WFE, fraction of positive years)
      + 0.10·rank(NW t-stat of alpha vs SPY)
      + 0.05·rank(-MC 95% MaxDD / CAGR)
      + 0.05·rank(-|correlation to already-selected strategies|)

- Weights are a judgment call. The guiding principle is that out-of-sample, cost-stressed and deflated quantities dominate, while raw in-sample SR/CAGR get zero weight because they are already embedded in the deflated versions.
- Robustness check: rank with 3-4 alternative weight vectors (equal weights; holdout-only; deflation-heavy) and keep the strategies that stay in the top quintile under all of them (rank-stability filter). Kendall's tau between rankings should be > 0.6.

**Stage 4: final selection**
- Take the top survivors that lie inside the MCS (size = 0.10, losses = -net returns).
- Then greedily add by score, subject to a pairwise daily return correlation < 0.5, giving a diversified book. Optionally weight by (1 - PBO) × inverse-vol.
- Record everything (scores, gates, trial ledger) so the selection itself is reproducible and auditable.

**Python stack summary:**
- numpy/pandas/scipy for the base computations.
- `arch` (`SPA`, `StepM`, `MCS`, `StationaryBootstrap`, `optimal_block_length`).
- statsmodels (OLS with HAC, `acf`, `multipletests` with method='fdr_bh', 'fdr_by' or 'holm' as an alternative to ml4t).
- `ml4t-diagnostic` (`deflated_sharpe_ratio`, `benjamini_hochberg_fdr`, `compute_pbo`, `WalkForwardCV`, `CombinatorialCV`; requires Python 3.11+/3.12+, so check the version).
- `bidask` (EDGE spreads).
- Custom ports: the Harvey-Liu haircut (from R quantstrat), the Ledoit-Wolf SR difference (from Wolf's R code), and CSCV (about 40 lines).

### Gaps
- I found no peer-reviewed source prescribing composite weights; the weights and the 0.5 correlation cap are my recommendations.
- I did not survey 2022-2026 papers on backtest evaluation (for example, newer work on the RAS / Rademacher anti-serum bound by Paleologo, or on CPCV variants). ml4t-diagnostic lists RAS, but I did not fetch its details. That is worth a follow-up.
- The ml4t-diagnostic Python version requirement differs between sources: the GitHub README says 3.11+, while PyPI 0.1.4 lists 3.12-3.14 ([PyPI](https://pypi.org/project/ml4t-diagnostic/0.1.4/)).
