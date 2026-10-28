"""Agent-proposed alphas — written by Claude (acting as the hypothesis/factor agent of an
AlphaAgent / RD-Agent-style loop) on 2026-10-27, BEFORE any of them was evaluated, and frozen here.

Contamination note: round 3 already showed 2010-2026 ICs for a few base signals (Amihud, low-vol, low-beta, MAX,
gross profitability, issuance, accruals, SUE, 1-month reversal). Those appear below as baselines and are not "blind";
every alt-data and interaction proposal is new. The referee decides sign from TRAIN, so signs here are only the
hypothesis.
"""

PROPOSALS = [
    # ---- price / volume / residual
    (("neg", ("ts_sum", "resid", 21)), "1-month residual reversal (baseline, seen in round 3)"),
    (("sub", ("ts_sum", "resid", 252), ("ts_sum", "resid", 21)), "residual momentum 12-1 (Blitz et al.)"),
    (("neg", ("ts_std", "resid", 63)), "low idiosyncratic volatility (baseline, seen)"),
    (("div", ("ts_mean", ("abs", "ret"), 21), ("ts_mean", "dvol", 21)), "Amihud illiquidity premium (baseline, seen)"),
    (("neg", ("ts_corr", ("rank", "close"), ("rank", "volume"), 21)), "price-volume co-movement (Alpha158 CORR)"),
    (("ts_corr", "ret", ("ts_delay", "ret", 1), 63), "own return autocorrelation: momentum vs mean-reverting names"),
    (("ts_zscore", "volume", 63), "abnormal-volume / visibility premium (Gervais-Kaniel-Mingelgrin)"),
    (("div", ("ts_delta", "close", 63), ("mul", ("ts_std", "ret", 63), "close")), "vol-adjusted 3-month momentum"),
    (("neg", ("ts_max", "ret", 21)), "lottery demand / MAX (baseline, seen)"),
    (("neg", ("decay", "resid", 10)), "linearly-decayed short-term residual reversal"),
    (("mul", ("neg", ("ts_sum", "resid", 5)), ("neg", ("ts_zscore", "volume", 21))),
     "low-volume moves reverse, high-volume moves continue (Campbell-Grossman-Wang)"),
    (("neg", ("div", ("ts_std", "ret", 21), ("ts_std", "ret", 126))), "volatility compression precedes calm drift"),
    (("ts_corr", "resid", ("ts_delay", "resid", 1), 63), "residual autocorrelation (speed of mean reversion)"),
    (("neg", ("ts_rank", ("ts_std", "resid", 21), 252)), "idiosyncratic-vol regime: names in their own calm regime"),
    (("ts_zscore", ("ts_mean", "dvol", 5), 252), "liquidity shock: sudden dollar-volume increase"),
    # ---- fundamentals (point-in-time)
    (("rank", "gpa"), "gross profitability (Novy-Marx; baseline, seen)"),
    (("rank", "issuance"), "net share issuance (raw = -issuance growth; baseline, seen)"),
    (("rank", "accruals"), "low accruals (raw = -accruals; baseline, seen)"),
    (("rank", "sue"), "post-earnings-announcement drift (baseline, seen)"),
    (("ts_delta", "roe", 252), "improving profitability (Q-factor ROE change)"),
    (("add", ("rank", "gpa"), ("rank", "bm")), "quality + value combination (AQR QMJ-style)"),
    (("mul", ("rank", "sue"), ("rank", ("ts_sum", "resid", 63))), "earnings surprise confirmed by residual drift"),
    (("rank", "ey"), "earnings yield"),
    (("mul", ("rank", ("ts_sum", "resid", 252)), ("rank", "gpa")), "quality momentum"),
    # ---- new alt data: Wikipedia attention
    (("ts_zscore", "wiki", 63), "attention surge precedes higher returns (Pyun 2025)"),
    (("sub", ("ts_mean", "wiki", 5), ("ts_mean", "wiki", 252)), "abnormal attention vs 1-year baseline"),
    (("mul", ("neg", ("ts_sum", "resid", 5)), ("neg", ("sub", ("ts_mean", "wiki", 5), ("ts_mean", "wiki", 63)))),
     "no-news reversal: fade residual moves NOT accompanied by attention spikes"),
    (("neg", ("ts_corr", "wiki", ("abs", "ret"), 63)), "attention that does not track volatility = informed interest"),
    # ---- new alt data: SEC 8-K events and filing timing
    (("neg", ("ts_sum", "k8_502", 126)), "executive turnover (8-K item 5.02) precedes underperformance"),
    (("ts_sum", "k8", 63), "8-K disclosure intensity"),
    (("mul", ("neg", ("ts_sum", "resid", 5)), ("neg", ("ts_sum", "k8", 5))),
     "no-news reversal: fade residual moves without any 8-K that week"),
    (("neg", "filing_delay"), "late 10-K/10-Q filers (vs own history) underperform"),
    (("ts_sum", "k8_101", 252), "material definitive agreements (deal activity)"),
    (("mul", ("rank", "sue"), ("rank", ("ts_sum", "k8_202", 63))), "SUE only where a results 8-K was filed (fresh news)"),
    # ---- round-3 alt data
    (("ts_sum", "insider_opp", 21), "opportunistic insider purchases (round 3: negative in large caps)"),
    (("rank", "lp_jac"), "Lazy Prices: non-changers outperform"),
    (("mul", ("rank", "lp_jac"), ("rank", "sue")), "text stability x earnings surprise"),
    (("neg", ("ts_mean", "svr", 20)), "FINRA short-volume ratio (only 2018->: cannot pass TRAIN; logged)"),
    (("mul", ("rank", "accruals"), ("rank", "lp_jac")), "earnings quality: low accruals and unchanged disclosures"),
    (("neg", ("mul", ("rank", "beta"), ("rank", ("ts_std", "resid", 63)))), "low beta and low idio risk jointly"),
]
