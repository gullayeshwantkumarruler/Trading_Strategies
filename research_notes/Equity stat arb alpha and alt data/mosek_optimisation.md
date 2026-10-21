# MOSEK and convex-optimisation portfolio construction for equity stat arb (as of Oct 2026)

Context: our FF5-residual stat-arb book has gross Sharpe of about 1.3, 70-80% daily turnover, and negative net Sharpe at 5 bp. These notes cover MOSEK itself, the cookbook formulations, how stat-arb books use optimisation, free solvers, and the evidence that cost-aware construction rescues fast signals.

Open-access PDFs downloaded to `C:\Users\Acer\Pictures\research_papers\paper1\papers\stat_arb_alt_data\`. None were executed.
- `MOSEK_Portfolio_Cookbook_v1.6.pdf`, from https://docs.mosek.com/MOSEKPortfolioCookbook-a4paper.pdf
- `Boyd2017_MultiPeriod_Trading_Convex_Optimization.pdf`, from arXiv 1705.00109
- `Boyd2024_Markowitz_Portfolio_Construction_at_Seventy.pdf`, from arXiv 2401.05080

## Q1. Exact install and licence steps for MOSEK on Windows with Python 3.13, and calling it from CVXPY

### Takeaway
`pip install mosek` installs MOSEK 11.2.6, the current release, which supports Python 3.9 to 3.14, so 3.13 works. Put the licence file at `%USERPROFILE%\mosek\mosek.lic`, which is `C:\Users\Acer\mosek\mosek.lic` on this machine. The free Personal Academic licence requires an academic email at a degree-granting institution. Anyone else can get a 30-day full-feature trial. From CVXPY, call `prob.solve(solver=cp.MOSEK)`.

### Cited Findings
- The PyPI package is `Mosek`, installed with `pip install mosek`. The latest version is 11.2.6 and `requires_python` is `<3.15,>=3.9`. — [PyPI JSON](https://pypi.org/pypi/Mosek/json)
- The install guide is titled for version 11.2.6. `pip install mosek` installs only the client package. The floating licence server and OptServer need the full distribution. — [MOSEK install docs](https://docs.mosek.com/latest/install/installation.html)
- **Windows licence location:** save the file as `%USERPROFILE%\mosek\mosek.lic` and create the `mosek` folder if it doesn't exist. The `msktestlic` tool checks the licence and prints the "License path" in use. — [Licensing quickstart](https://docs.mosek.com/latest/licensing/quickstart.html); [Install docs](https://docs.mosek.com/latest/install/installation.html)
- **Other ways to point MOSEK at a licence:**
  - Set the environment variable `MOSEKLM_LICENSE_FILE`, for example `MOSEKLM_LICENSE_FILE=c:\users\mylogin\licenses\mosek.lic`.
  - Set it to `@hostname` or `port@hostname` to use a floating-licence token server.
  - Pass `-l` to the command-line tools.
  - Call `putlicensepath` on the Env (Optimizer API) or the Model (Fusion API) before the first optimisation.
  — [Client setup](https://docs.mosek.com/latest/licensing/client-setup.html)
- **Personal Academic licence:** free for faculty, students and staff of degree-granting institutions, for research or educational use only. You must request it with an academic email. It has all features except the AMPL shell and no size limits. It lasts 365 days and is renewable. — [MOSEK academic licences](https://www.mosek.com/products/academic-licenses/)
- **Institutional Academic licence:** a floating licence served by a licence server. It lasts 2 years and is renewable. You need the server's hostname and hostid. MOSEK advises the personal licence unless several concurrent users share one network. — [MOSEK academic licences](https://www.mosek.com/products/academic-licenses/)
- **Trial licence:** available to anyone and valid for 30 days from the online application. It includes all features, has no size limits and is not hardware-bound. Request it at https://www.mosek.com/products/trial/. — [MOSEK trial](https://www.mosek.com/products/trial/)
- **Calling MOSEK from CVXPY:** use `prob.solve(solver=cp.MOSEK, mosek_params={'MSK_IPAR_NUM_THREADS': 4})`. Parameter names are strings such as `'MSK_DPAR_BASIS_TOL_X'`. Other options include `bfs`, `accept_unknown`, `eps` and `save_file`. — [CVXPY solver docs](https://www.cvxpy.org/tutorial/solvers/index.html)
- **Dualisation:** since CVXPY 1.1.6, the MOSEK interface dualises all continuous problems. If MOSEK is slow on a problem, try `mosek_params={'MSK_IPAR_INTPNT_SOLVE_FORM': 'MSK_SOLVE_DUAL'}`, or switch it. — [CVXPY solver docs](https://www.cvxpy.org/tutorial/solvers/index.html)
- **Problem classes MOSEK supports via CVXPY:** LP, QP, SOCP, SDP, exponential cone, power cone and MIP. It does not support mixed-integer SDP. — [CVXPY solver docs](https://www.cvxpy.org/tutorial/solvers/index.html)
- **Python APIs:** MOSEK has the Fusion API (object-oriented modelling, used throughout the Portfolio Cookbook) and the low-level Optimizer API. Recent Fusion code uses operator syntax such as `x == xp - xm`, `xp.T @ vp` and `xp <= up * yp`. — [MOSEK Portfolio Cookbook, ch. 6](https://docs.mosek.com/portfolio-cookbook/transaction.html)

### Inferences
- **Recommended Windows sequence:**
  1. Run `py -3.13 -m pip install mosek` in the project venv.
  2. Request a Personal Academic licence if eligible, otherwise a trial.
  3. Save the emailed `mosek.lic` to `C:\Users\Acer\mosek\mosek.lic`.
  4. Verify with `python -c "import mosek; print(mosek.Env.getversion())"`, or run a tiny CVXPY problem with `solver=cp.MOSEK`.
- **Eligibility:** the academic licence depends on having a university email address. A private or independent researcher without one would need a trial, then a commercial licence.
- **Version compatibility:** licence-version compatibility between MOSEK 10 and 11 was not documented on the pages fetched. Obtain a licence after installing 11.x to be safe.
- **Fusion syntax:** the operator-overloaded Fusion syntax (`@`, `==`, `<=`) is newer than the `Expr.mul(...)` / `M.constraint(..., Domain...)` style in older tutorials, blog posts and GitHub notebooks. Older code still works in principle, but expect mixed styles across sources.

### Gaps
- Whether a `cp313-win_amd64` wheel exists for 11.2.6 was not verified, because the PyPI JSON was truncated before the file list. The `requires_python` range strongly implies it does.
- The exact 11.2.6 release date was not retrieved.
- Commercial licence pricing was not researched.

## Q2. Which formulations (with cookbook code) are most useful for a daily-rebalanced market-neutral stat-arb book of 300-500 stocks?

### Takeaway
The workhorse is a single-period convex problem. It maximises alpha·w, minus a risk penalty from a factor risk model, minus trading costs (linear spread cost plus 3/2-power impact), minus holding or borrow cost. It is subject to dollar, beta and sector neutrality, factor-exposure bounds, position and participation limits, a leverage limit and, optionally, a turnover limit. This is an SOCP or power-cone problem. MOSEK solves the 500-asset, 20-50-factor case in about 0.07-0.10 s. Mixed-integer features (fixed costs, cardinality, minimum trade size) are optional extras and the only parts that strictly need a commercial-grade MIP solver.

### Cited Findings
- **Cookbook v1.6 (updated 5 Nov 2025) chapters:**
  - Markowitz (mean-variance, conic formulation)
  - Input data preparation
  - Estimation error (mean and covariance shrinkage)
  - Factor models (including shrinkage as a factor model)
  - Transaction costs (variable, fixed, market impact, cardinality, buy-in threshold)
  - Benchmark-relative optimisation (factor model on active returns)
  - Other risk measures (deviation, tail risk such as CVaR and EVaR, expected utility)
  - Risk budgeting / risk parity
  - Robust optimisation (return and factor-model uncertainty)
  - Multi-period optimisation
  - Regression and regularisation
  - Appendices: conic refresher, mixed-integer models, MCOS

  The PDF is free to download. — [Portfolio Cookbook index](https://docs.mosek.com/portfolio-cookbook/index.html)
- **Linear (spread) costs, cookbook ch. 6.** Split trades into buys and sells with `xp, xm >= 0`, `x == xp - xm`, cost `xp.T @ vp + xm.T @ vm`:
  ```python
  xp = M.variable("xp", N, Domain.greaterThan(0.0))
  xm = M.variable("xm", N, Domain.greaterThan(0.0))
  M.constraint('pos-neg-part', x == xp - xm)
  varcost_terms = xp.T @ vp + xm.T @ vm
  ```
  — [Cookbook ch. 6](https://docs.mosek.com/portfolio-cookbook/transaction.html)
- **Market impact (3/2 power), cookbook ch. 6.** Impact cost is a_i|x̃_i|^β with β=3/2 and a_i = c_i σ_i / q_i^(β−1), where q_i is volume. It is modelled with the power cone (t_i, 1, x̃_i) ∈ P₃^(1/β,(β−1)/β):
  ```python
  M.constraint('budget', Expr.sum(x) + xf + t.T @ a == 1.0)
  M.constraint('mkt_impact', Expr.hstack(t, Expr.constTerm(N, 1.0), x),
               Domain.inPPowerCone(1.0 / beta))
  ```
  The cookbook warns that t can be set larger than needed (so cost acts like a free asset). It recommends a penalty on t or adding a risk-free asset. — [Cookbook ch. 6](https://docs.mosek.com/portfolio-cookbook/transaction.html)
- **Fixed costs, cookbook ch. 6 (MIP).** Binaries y⁺ and y⁻ with `xp <= up*yp` and `yp + ym <= 1`, and fixed cost `yp.T @ fp + ym.T @ fm`. — [Cookbook ch. 6](https://docs.mosek.com/portfolio-cookbook/transaction.html)
- **Cardinality, cookbook ch. 6 (MIP).** −u∘y ≤ x̃ ≤ u∘y with 1ᵀy ≤ K. The cookbook gives the maths only, no Fusion code. — [Cookbook ch. 6](https://docs.mosek.com/portfolio-cookbook/transaction.html)
- **Buy-in threshold, cookbook ch. 6 (MIP).** A semicontinuous trade, either 0 or in [ℓ, u]: `xp >= lp*yp` and `xm >= lm*ym`. — [Cookbook ch. 6](https://docs.mosek.com/portfolio-cookbook/transaction.html)
- **Boyd et al. 2024 "Markowitz++" (eq. 19).** Maximise
  R^wc − γ^hold φ^hold(w,c) − γ^trade φ^trade(z)
  subject to:
  - 1ᵀw + c = 1 and z = w − w^pre
  - weight limits, leverage L = ‖w‖₁ ≤ L^tar and cash limits
  - trade limits and turnover T = ½‖z‖₁ ≤ T^tar
  - worst-case risk σ^wc ≤ σ^tar

  Other pieces:
  - Trading cost φ^trade(z) = κ^spread·|z| + κ^impact·|z|^{3/2}, with κ^impact_i = a s_i v_i^{-1/2} and a ≈ 1.
  - Robust return: R^wc = R̄ − ρᵀ|w|.
  - Robust risk: (σ^wc)² = σ² + ϱ(Σ_i Σ_ii^{1/2}|w_i|)².

  — [Boyd, Johansson, Kahn, Schiele, Schmelzer 2024, JPM](https://arxiv.org/abs/2401.05080)
- **Same paper on constraints:**
  - Participation limits look like |z| ≤ 0.05v, i.e. 5% of forecast volume.
  - Factor neutrality is a linear equality (Σ^f Fᵀw)_i = 0.
  - Shorting cost is the linear holding cost κ^short·(−w)₊.
  - A minimum-holding-size constraint is non-convex but has a convex heuristic (§4.3).
  - Hard constraints are softened with "priority" penalty parameters, set from percentiles of historical Lagrange multipliers.

  — [Boyd et al. 2024](https://arxiv.org/abs/2401.05080)
- **Same paper on the factor model:** a factor model Σ = FΣ^fFᵀ + D cuts solve complexity from O(n³) to O(nk²). Factors can be fundamental (Fama-French, industries) or statistical PCA. — [Boyd et al. 2024](https://arxiv.org/abs/2401.05080)
- **Solve times (same paper, Table 2).** MOSEK on the Markowitz++ problem, averaged over 30 random instances:

  | Assets n | Factors k | Solve time (s) |
  |---|---|---|
  | 100 | 10 | 0.01 |
  | 500 | 20 | 0.07 |
  | 500 | 50 | 0.10 |
  | 2,000 | 50-100 | about 0.22 |
  | 10,000 | 100 | 0.89 |
  | 50,000 | 500 | 17.8 |

  Open-source solvers such as Clarabel were "a bit longer". — [Boyd et al. 2024](https://arxiv.org/abs/2401.05080)
- **Single-period vs multi-period:** in cvxportfolio, the single-period optimisation (SPO) policy is built as `SinglePeriodOpt(alpha_source, [gamma_risk*factor_risk, gamma_trade*tcost_model, gamma_hold*hcost_model], [leverage_limit])`. Multi-period optimisation (MPO) plans H trades but executes only the first. — [Boyd et al. 2017, Multi-Period Trading via Convex Optimization](https://arxiv.org/abs/1705.00109)
- **cvxportfolio policy class:** `cvxportfolio.MultiPeriodOptimization(objective, constraints, planning_horizon, terminal_constraint, ...)` implements the MPO model in ch. 5 of the 2017 paper. — [cvxportfolio docs](https://cvxportfolio.readthedocs.io/en/stable/optimization_policies.html)

### Inferences
- **Recommended problem for our book.** A convex, MIP-free problem in CVXPY, with n = 300-500 and k ≈ 5-20 factors (FF5 + sectors + PCA):
  ```python
  import cvxpy as cp
  w  = cp.Variable(n); z = w - w_prev
  f  = F.T @ w                               # factor exposures (k)
  risk = cp.sum_squares(L_f.T @ f) + cp.sum_squares(cp.multiply(np.sqrt(d), w))  # Sigma_f = L_f L_f^T
  tcost = kappa_spread @ cp.abs(z) + kappa_imp @ cp.power(cp.abs(z), 1.5)        # 3/2 impact -> power cone
  hcost = kappa_short @ cp.neg(w)                                               # borrow
  obj = cp.Maximize(alpha @ w - g_risk*risk - g_trade*tcost - g_hold*hcost)
  cons = [cp.sum(w) == 0,                    # dollar neutral
          beta_mkt @ w == 0,                 # beta neutral
          S.T @ w == 0,                      # sector neutral (S = sector dummies)
          cp.abs(F_style.T @ w) <= f_max,    # FF5/style exposure bounds
          cp.norm1(w) <= L_max,              # gross leverage
          cp.abs(w) <= w_max,                # position limits
          cp.abs(z) <= 0.05*adv_frac,        # participation
          0.5*cp.norm1(z) <= T_max]          # optional hard turnover cap
  cp.Problem(obj, cons).solve(solver=cp.MOSEK)  # or cp.CLARABEL
  ```
  The structure follows Boyd et al. 2024 eq. 19 and cvxportfolio. This sketch is ours and has not been run. Replacing `cp.power(..., 1.5)` with a quadratic impact term `cp.sum_squares` gives a pure QP or SOCP and is faster.
- **Order of value for a 70-80%/day turnover signal:**
  1. The trade-cost penalty γ_trade with realistic κ, which is the biggest lever.
  2. Partial trading toward a target (no-trade region from the ℓ1 term).
  3. Factor/sector neutrality, so turnover isn't spent on factor noise.
  4. A turnover cap as a safety net.

  MIP features add little for 300-500 liquid names.
- **When to use the cookbook's power-cone and exponential-cone formulations:** power cones for 3/2 impact, exponential cones for Kelly/log-utility and EVaR. They matter if we want physically realistic impact curves. A quadratic proxy is usually good enough for daily rebalancing at modest AUM.

### Gaps
- MOSEK's full cone list was not re-fetched in this session. It covers quadratic, rotated quadratic, primal/dual power, primal/dual exponential, and PSD cones. Verify on https://docs.mosek.com/modeling-cookbook/ if needed.
- The cookbook's multi-period chapter (ch. 11) code was not extracted. It is in the downloaded PDF.
- The cookbook's risk-parity (ch. 9) and CVaR/EVaR (ch. 8) code snippets were not extracted. They are in the downloaded PDF.
- github.com/MOSEK/PortfolioOptimization notebook contents were not checked.

## Q3. What evidence exists that turnover-penalised or multi-period optimisation materially improves net performance of fast signals?

### Takeaway
The evidence is consistent and sometimes large: cost-aware construction often turns unprofitable high-turnover strategies into profitable ones. The main sources are Gârleanu-Pedersen (theory: "aim in front, trade partially"), Boyd et al. 2017 and 2024 (backtests where the trade-aversion parameter is "critical" and where turnover drops from about 1,145x to 26-39x per year while Sharpe rises), Baldi-Lanfranchi 2024 (net max squared Sharpe up to 2.5x, mostly for high-turnover factors like momentum), and Fan et al. 2024/25 (cost-aware large-universe estimator beats penalised mean-variance on post-cost Sharpe). However, most of these results use synthetic forecasts or survivor-biased data, so magnitudes for our book must be tested in our own backtest.

### Cited Findings
- **Gârleanu & Pedersen (JF 2013):**
  - The optimal policy is to "aim in front of the target" and "trade partially towards the current aim".
  - The aim portfolio is a weighted average of the current and expected future Markowitz portfolios.
  - Slower-decaying signals get more weight.
  - Applied to commodity futures, it beat naive benchmarks net of costs.

  — [NBER w15205](https://www.nber.org/papers/w15205); [accepted manuscript](https://research-api.cbs.dk/ws/portalfiles/portal/60191441/lasse_heje_pedersen_et_al_dynamic_trading_acceptedmanuscript.pdf)
- **Boyd et al. 2017, SPO backtest.** Setup: S&P 500 names 2012-2016, 5 bp half-spread, 1 bp holding cost, 3/2-power impact, synthetic forecasts with IC ≈ 0.15 and 54% sign accuracy. Findings:
  - "the choice of trading aversion parameter is critical".
  - For some γ_trade values the results were too poor to fit on the plot. The best γ_trade was about 5-7.
  - Large holding-cost multipliers (γ_hold = 10-100) acted as useful regularisation, even though the true holding cost was 1 bp.

  — [Boyd et al. 2017](https://arxiv.org/abs/1705.00109), §7.3, Figs 7.2-7.4, Table 7.2
- **Boyd et al. 2017, MPO vs SPO.** MPO with only a 2-day horizon had a Pareto frontier well above SPO. For example, at about 5% excess risk MPO earned about 17% excess return vs about 11% for SPO, per Fig. 7.7 (read from the chart). The authors attribute this mostly to using a forecast of tomorrow's return as well as today's. — [Boyd et al. 2017](https://arxiv.org/abs/1705.00109), §7.4
- **Boyd et al. 2017, compute.** One SPO day took about 0.25 s, 0.15 s of it in the solver (ECOS at the time). The 3/2-power cost terms "slow the optimizer". Replacing them with squared terms gave more than 2x speedup. — [Boyd et al. 2017](https://arxiv.org/abs/1705.00109), §7.5
- **Boyd et al. 2024 backtest.** Setup: 74 S&P 100 names, 2000-2023, 17-year out-of-sample, daily rebalance, realised bid-ask spreads, synthetic IC 0.15 forecasts.

  | Policy | Sharpe | Annual turnover | Max drawdown |
  |---|---|---|---|
  | Basic Markowitz | 0.19 | 1,145 | 78.9% |
  | Turnover-limited (T^tar = 25) | 1.54 | 26.1 | 25.0% |
  | Leverage-limited | 1.86 | 383.6 | 14.9% |
  | Markowitz++ (all terms) | 4.32 | 28.0 | 7.0% |
  | Tuned Markowitz++ | 4.65 | 38.6 | 6.4% |

  The tuned version re-tunes γ parameters each year on the prior 2 years. The authors caution about survivorship bias and synthetic forecasts. — [Boyd et al. 2024](https://arxiv.org/abs/2401.05080), Table 1
- **Baldi-Lanfranchi (May 2024), transaction-cost-aware factors:**
  - Factors rebalance only partially toward the target at an optimised trading intensity τ (a Gârleanu-Pedersen-style idea).
  - When trading is costly, these factor models increase net maximum squared Sharpe by up to 2.5x.
  - The benefit is largest for high-turnover factors such as momentum, "that are otherwise unprofitable net of costs".
  - Optimal intensity is lower for factors on persistent characteristics and for characteristics correlated with costs, and higher for slow-decaying premia.

  — [Baldi-Lanfranchi 2024 (AFA)](https://afajof.org/management/viewp.php?n=135184)
- **Detzel, Novy-Marx & Velikov (2023), per Baldi-Lanfranchi:** before-cost inference favours high-turnover factors, because the cost component is wrongly counted as gain. — [cited in Baldi-Lanfranchi 2024](https://afajof.org/management/viewp.php?n=135184)
- **Fan, Medeiros, Yang & Yang, "Cost-aware Portfolios in a Large Universe of Assets" (arXiv 2412.11575, v2 Aug 2025):**
  - Method: a multi-stage mean-variance estimator with quadratic costs (equivalent to perturbing the covariance) or ℓ1 proportional costs, plus SCAD regularisation.
  - Simulation, p = 2000 and quadratic costs: Sharpe was 2.85 vs 2.60 for penalised mean-variance and 1.28 for cost-aware-but-unregularised mean-variance in stage 1. Turnover was 3.56% vs 4.08% and 15.69%.
  - It also uses S&P 500 and Russell 2000 data from 2017-2020, but those real-data numbers were not extracted.

  — [arXiv 2412.11575](https://arxiv.org/html/2412.11575)
- **QREF 2025 (UZH):** builds costs into the portfolio-selection stage and reports that net Sharpe ratios often rise, especially for high-turnover strategies. Less precise but lower-turnover estimators can raise post-cost Sharpe. This is a search-snippet summary; the full text was not read. — [QREF 2025 PDF](https://www.econ.uzh.ch/dam/jcr:cd9c657f-16d3-4155-872d-e5ebae7557ac/qref_2025.pdf)
- **Older large-universe evidence (arXiv 1709.06296):** explicitly adjusting for costs cut turnover to under 1% of the cost-unaware level and produced positive net Sharpe. This is a search-snippet summary from a pre-2023 paper. — [arXiv 1709.06296](https://arxiv.org/pdf/1709.06296)

### Inferences
- **Why naive trading fails for our book:** at 70-80% daily one-way turnover and 5 bp per side, cost drag is about 0.75 × 2 × 5 bp × 252 ≈ 19% per year of gross notional. That is far above what a gross Sharpe of 1.3 at typical stat-arb volatility can absorb. Naive "trade fully to the signal" construction is the textbook failure case these papers address.
- **What the papers suggest is achievable:** cutting turnover by roughly an order of magnitude while keeping most of the alpha. That happens when the signal has some persistence (half-life of more than one day) or when today's trades can be netted across days.
- **Practical test plan:**
  1. Run SPO with γ_trade swept log-spaced (1, 2, 5, 10, 20, as Boyd 2017 did).
  2. Add a no-trade band via the ℓ1 spread term.
  3. Try MPO with H = 2-5, using forecasts of alpha decay (cvxportfolio `MultiPeriodOptimization`).
  4. Compare with a Gârleanu-Pedersen partial-adjustment rule, w_t = (1−τ)w_{t−1} + τ·aim, with τ tuned.
- **Caveats on the evidence:** if the FF5-residual alpha decays within one day (pure short-term reversal), cost-aware smoothing loses much of the alpha. In that case the gain depends on blending in slower signals (multi-signal alpha). Gârleanu-Pedersen's point that slower signals deserve more aim weight is directly relevant.
- **Tuning discipline:** the 2024 paper tunes 5 γ parameters annually on a 2-year lookback. Treat this as hyperparameter search inside walk-forward validation to avoid overfitting.

### Gaps
- No 2023-2026 paper was found that specifically documents an FF5- or PCA-residual daily stat-arb book being rescued by cost-aware optimisation with real (non-synthetic) alphas and stated net Sharpe. Most evidence uses factor portfolios, synthetic forecasts or simulations.
- Real-data results of Fan et al. (S&P 500 / Russell 2000) were not extracted.
- The QREF 2025 paper's authors and exact figures were not verified.

## Q4. When is MOSEK actually needed vs free solvers (MIP, power cones, SDP, speed at scale)?

### Takeaway
For a continuous convex problem with 300-500 stocks and a factor risk model, free solvers are enough. That covers QP/SOCP problems, including 3/2-power impact via power cones, which Clarabel and SCS support. Clarabel (CVXPY's default for SOCP) gives interior-point accuracy and is "a bit slower" than MOSEK. MOSEK earns its place for:
1. Mixed-integer conic problems (cardinality, fixed costs or buy-in thresholds combined with SOCP risk or power-cone impact). Free CVXPY solvers either can't do these (Clarabel, OSQP, SCS) or handle only MILP and continuous QP (HiGHS).
2. Robust, fast, high-accuracy solves of large conic problems with exponential or power cones, and SDPs.
3. Production reliability or thousands of backtest solves where a few-x speedup matters.

### Cited Findings
- **CVXPY solver support:**
  - MOSEK: LP/QP/SOCP/SDP/EXP/POW/MIP.
  - SCS: everything except MIP.
  - OSQP: LP and QP only.
  - HiGHS: LP, QP and MILP only.
  - Clarabel: LP/QP/SOCP/SDP/EXP/POW, no MIP. The flattened table on the source page made the column alignment uncertain.
  - ECOS: probably LP/SOCP/EXP and MIP via ECOS_BB, also from the flattened table.

  CVXPY defaults to Clarabel for SOCPs, OSQP for QPs, and SCS as the general fallback. — [CVXPY solver docs](https://www.cvxpy.org/tutorial/solvers/index.html)
- **Boyd et al. 2024 speed comparison:** MOSEK solved the 74-asset problem in about 23 ms per day including overhead, about 63% of it in the solver. Open-source ECOS, Clarabel and SCS gave "similar results". For large factor-model problems, Clarabel solve times "were a bit longer" than MOSEK. — [Boyd et al. 2024](https://arxiv.org/abs/2401.05080), §5.6
- **Clarabel's own benchmarks (authors' claim):** it outperforms state-of-the-art solvers on QPs, large-scale SOCPs and sparse SDPs. — [Clarabel paper, arXiv 2405.12762](https://arxiv.org/pdf/2405.12762)
- **Independent SOCP benchmark:** a 2026 arXiv paper used the public Mittelmann SOCP instances. Shifted geometric mean times were Gurobi about 6.1 s, COPT-GPU about 9.7 s, Clarabel about 14.7 s and MOSEK about 16.4 s. The table caption and contents look mismatched (18 vs 21 instances), so treat these numbers with caution. — [arXiv 2608.09159](https://arxiv.org/pdf/2608.09159), via search summary
- **Mittelmann's own benchmark pages:** these remain the standard reference. His INFORMS 2025 talk exists, but the SOCP table was not retrieved. — [Mittelmann INFORMS 2025 slides](https://plato.asu.edu/talks/informs2025.pdf)
- **GPU solvers for very large portfolio QPs:** CuClarabel benchmarks portfolio QPs with n = 5,000-25,000 against MOSEK and Gurobi and reports the GPU variant as fastest. It is not a like-for-like CPU comparison. — [CuClarabel, arXiv 2412.19027](https://arxiv.org/pdf/2412.19027)
- **FlashFolio (2026):** a GPU portfolio solver compared to MOSEK on H100 vs 16 CPU cores. — [arXiv 2604.22625](https://arxiv.org/pdf/2604.22625)
- **Code generation:** CVXPYgen-generated code is about 6x faster than CVXPY at N=10 and 2.5x faster at N=100. — [CVXPYgen paper, arXiv 2203.11419](https://arxiv.org/pdf/2203.11419)
- **cvxportfolio:** an open-source Python library built on CVXPY. Its signature `MultiPeriodOptimization` policy is model-predictive control. Since the end of 2023 it has run daily example strategies on the development (master) branch. Versioned docs exist for 1.0.x. — [cvxportfolio docs](https://cvxportfolio.readthedocs.io)
- **skfolio:** a BSD-3 library built on scikit-learn and CVXPY, requiring Python ≥ 3.10. It supports transaction costs, management fees and turnover constraints as optimisation features. Its home page names neither a default solver nor MOSEK. — [skfolio.org](https://skfolio.org/)

### Inferences
- **Recommendation for our book:** prototype and backtest with CVXPY + Clarabel, or OSQP if the impact term is quadratic, which is free with no licence friction. Switch to `solver=cp.MOSEK` only when one of these applies:
  - adding cardinality, minimum-trade or fixed-cost binaries
  - Clarabel shows numerical issues such as inaccurate or near-infeasible statuses on tight neutrality constraints
  - running large hyperparameter sweeps where MOSEK's speed advantage cuts wall-clock time
- **Speed at our scale:** at n ≤ 500 with a factor model, every interior-point solver should take on the order of 0.01-0.1 s per solve, so solver choice is not the bottleneck. Python and CVXPY overhead per day can rival solve time. Use CVXPY `Parameter`s to avoid recompiling, or CVXPYgen.
- **PyPortfolioOpt and Riskfolio-Lib:** both are CVXPY-based and geared to allocation (mean-variance, HRP, risk parity, CVaR). They are less suited than cvxportfolio or hand-written CVXPY for daily trade-level stat arb with cost models. Riskfolio-Lib's docs recommend MOSEK for some risk measures, but this was not verified in this session.
- **Neutrality and integer trades:** the free Clarabel/SCS/OSQP stack handles dollar, beta and sector neutrality, since these are linear. Only integer lot sizes or name-count limits push toward MOSEK, or Gurobi/COPT/SCIP.

### Gaps
- No independent, recent (2025-2026) head-to-head of MOSEK vs Clarabel on realistic 300-500-asset long-short portfolio problems with power-cone costs was found. The best evidence is the Boyd 2024 remark ("a bit longer") and the authors' own benchmarks.
- Riskfolio-Lib and PyPortfolioOpt docs were not fetched. Their current versions and solver recommendations are unverified.
- PyPortfolioOpt's maintenance status in 2026 is unverified.
- Mittelmann's current SOCP and MISOCP benchmark tables were not retrieved.
