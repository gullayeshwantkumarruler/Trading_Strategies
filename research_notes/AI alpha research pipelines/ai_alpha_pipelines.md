# AI alpha-research pipelines (2025–2026) and what this project adopts

Survey run 2026-10-27; builds on `research_notes/Equity stat arb alpha and alt data/alpha_signal_research.md`.

## Frameworks found

| Framework | Year | What it does | Evidence / caveat | Code |
|---|---|---|---|---|
| AlphaAgent ([arXiv 2502.16789](https://arxiv.org/abs/2502.16789), KDD 2025) | 2025 | 3 LLM agents (hypothesis → factor expression → evaluation); AST-similarity check against existing alphas, complexity control to fight decay | Self-reported: stable test 2021-01 → 2025-01 on CSI 500 / S&P 500; 81% higher hit ratio; baselines with GPT-3.5 | MIT, GitHub `RndmVariableQ/AlphaAgent` ([trendshift](https://trendshift.io/repositories/66001)) |
| RD-Agent(Q) (Microsoft) | 2025 | Data-centric multi-agent R&D loop over Qlib (factor + model co-evolution) | Main baseline in later papers; needs an LLM API key | Microsoft `RD-Agent` |
| QuantaAlpha ([2602.07085](https://www.alphaxiv.org/abs/2602.07085)) | 2026 | Evolutionary LLM alpha mining reusing validated experience | Self-reported | — |
| Hubble ([2604.09601](https://arxiv.org/abs/2604.09601)) | 2026 | LLM generation + deterministic safety/validity safeguards; ~500 US stocks | Held-out 2025-06 → 2026-03: range and volatility factors stay positive, the weakest trend factor decays — mixed | — |
| AlphaMemo ([2606.20625](https://arxiv.org/html/2606.20625v1)) | 2026 | Search-process memory for self-evolving agents | Warns that reusing past "successes" amplifies overfitting | — |
| AlphaPilot ([2610.15488](https://arxiv.org/html/2610.15488)) | 2026 | Multi-turn tool-using LLM agents trained with RL | Argues GP overfits to backtest feedback | — |
| RL fine-tuning for LLM factor discovery ([2605.15412](https://arxiv.org/pdf/2605.15412)) | 2026 | Turns the feedback loop into policy updates | — | — |
| LLM-MCTS formulaic mining ([2505.11122](https://arxiv.org/html/2505.11122v2)) | 2025 | Monte-Carlo tree search guided by an LLM | — | — |
| AlphaSeek ([2608.13913](https://arxiv.org/pdf/2608.13913)) | 2026 | Trajectory-level self-iteration over multi-source data | Results not read | — |
| Survey: autonomous formulaic alpha discovery ([2608.01789](https://arxiv.org/html/2608.01789v1)) | 2026 | Frames LLM mining as evolutionary computation; flags spurious factors stored as "experience" | — | — |
| Propose, Don't Judge ([2609.27051](https://arxiv.org/abs/2609.27051), from the earlier notes) | 2026 | Frozen anytime-valid referee the agent cannot modify | Cut false admissions 2.6–11×; certified alpha ≈ 0 after costs on CSI 500 | — |
| Agent-driven WorldQuant BRAIN factories (e.g. [QuantGPT](https://github.com/Miasyster/QuantGPT)) | 2026 | LLM designs/backtests/submits to BRAIN | Platform-graded, not independent | GitHub |

Common thread: generation is cheap; **selection** is the problem. The credible designs freeze the evaluation protocol,
penalise redundancy/complexity, and keep a sealed test window.

## Alternative data added this round (free)

- **Wikipedia page views** (Wikimedia REST pageviews API, daily from 2015-07). Evidence is mixed: Pyun (2025 SSRN,
  2016–2023, NYSE/Nasdaq) finds view surges precede higher returns and a profitable long-short
  ([summary](https://alphainacademia.substack.com/p/recent-academic-research-fd2)); Wei & Wang (WWW 2016) find a link
  ([pdf](https://archives.iw3c2.org/www2016/WWW2016-Proceedings/companion/p591.pdf)); Gómez-Martínez et al. (2022) find
  no predictive power for the Nasdaq index ([handle](https://hdl.handle.net/10115/24352)).
- **SEC 8-K event data** from the EDGAR submissions index already cached: 8-K intensity, item codes (2.02 results,
  5.02 executive changes, 1.01 material agreements), and 10-K/10-Q filing delay vs the firm's own history.
- Reused from round 3: point-in-time XBRL fundamentals, Form 4 insider purchases, Lazy Prices similarities, FINRA
  short-volume ratio (2018 →).

## What we build (no LLM API key is configured, so the "agent" role is played by Claude in-session)

1. Formulaic-alpha DSL (Qlib/Alpha101-style operators) over price, volume, FF5 residual, fundamental and alt-data fields.
2. Two proposers: (a) genetic programming; (b) hypothesis-driven agent proposals written and frozen before evaluation.
3. One frozen referee: train 2010–2017 (|IC t| ≥ 3 on monthly rank IC), validation 2018–2021 (same sign, t ≥ 1.5),
   redundancy |ρ| < 0.6 vs admitted alphas, depth ≤ 4; sealed test 2022-01 → 2026-08 untouched until the end.
4. Admitted alphas combined (trained on 2010–2021 only, then frozen) and traded through the cost-aware optimiser on the
   sealed test, against the round-3 composite on the same window.
