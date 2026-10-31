# Price action backtests — swing, positional and intraday (US ETFs / stocks)

Code: `strategies/price_action/` (`engine.py` trade-level engine + metrics, `data.py` yfinance daily + Alpaca minute,
`swing.py`, `positional.py`, `intraday.py`). Results: `strategies/price_action/results/`. Report this builds on:
`reports/Price action strategies by horizon.md`.

Engine conventions (the report's conservative rules): signals at bar close; fills either at that close (market-on-close
proxy) or the next bar's open; stop-before-target when both are touched in one bar; gaps through a stop fill at the open;
costs in bp per side (swing/positional) or $0.0035/share commission + slippage per share (intraday). Metrics per variant:
CAGR, vol, Sharpe, Sortino, Calmar, max drawdown and duration, Ulcer, exposure, skew, kurtosis, tail ratio, PSR, trades,
trades/yr, win rate, profit factor, payoff, expectancy, avg win/loss, avg hold, SQN, cost drag; deflated Sharpe over every
variant run. Validation: the SPY RSI(2) replication reproduces the published figures (266 vs 265 trades, 76.7% vs 77% wins,
CAGR 5.0%, Sharpe 0.81, max DD −14.8%; 1993–2026, 2 bp, fill at close).

## Swing (daily bars; 15 ETFs; development 1993–2015, sealed holdout 2016–2026; pullback holdout 2020–2026)

Median across 15 ETFs at 6 bp per side (`results/swing_all.csv`):

| Strategy | Holdout Sharpe (close fill / next-open) | PF | Win rate | Exposure | Max DD | Dev Sharpe (close) |
|---|---|---|---|---|---|---|
| RSI(2) < 10 above SMA200, exit > SMA5 | 0.37 / 0.31 | 1.53 | 69% | 9–12% | −15% | 0.45 |
| RSI(2) + IBS < 0.2 | 0.42 / 0.38 | 1.93 | 73% | 5–7% | −11% | 0.46 |
| RSI(3) + IBS ≤ 0.5 (Pagonidis) | 0.28 / 0.09 | 1.57 | 67% | 2–4% | −13% | 0.42 |
| Large 5-day decline pullback (holdout 2020–26) | 0.29 / 0.43 | 1.48–1.69 | 68–71% | 7–9% | −11% | 0.32 |
| 3 down days above SMA200 | 0.44 / 0.35 | 1.78 | 70% | 8–11% | −14% | 0.44 |
| IBS < 0.2 (exit IBS > 0.8 / 5 days) | 0.61 / 0.52 | 1.46 | 63% | 23–37% | −20 to −25% | 0.34 |
| 20-day high breakout, exit 10-day low | 0.39 / 0.42 | 1.74–1.88 | 50% | 44–46% | −21% | 0.06 |
| NR7 breakout | −0.06 / −0.08 | 0.97 | 36–42% | 13–17% | −22% | −0.16 |
| Inside-bar breakout | 0.11 / 0.06 | 1.08 | 44–45% | 9–13% | −15% | −0.18 |
| Bullish engulfing, 5-day hold | 0.14 / 0.25 | 1.36–1.71 | 50% | 4–5% | −13% | 0.11 |
| Hammer, 5-day hold | 0.02 / 0.01 | ≈1.0 | 57–59% | 7–10% | −24% | 0.11 |
| Buy & hold (median ETF) | 0.72 | | | 100% | | 0.41 |

SPY detail at 6 bp, holdout 2016–2026 (fill at close / next open): RSI(2) Sharpe 0.65 / 0.44, 92 trades, 74% / 69% wins,
PF 2.26 / 1.73, max DD −12.5% / −13.3% vs SPY buy-and-hold Sharpe 0.87 and DD −33.7%; RSI(2)+IBS 0.61 / 0.38; 3 down days
0.68 / 0.56. Cost sensitivity (holdout, next-open, median Sharpe at 2 / 6 / 10 bp): RSI(2) 0.40 / 0.31 / 0.23,
RSI(2)+IBS 0.47 / 0.38 / 0.29, pullback 0.49 / 0.43 / 0.36, IBS 0.72 / 0.52 / 0.32, NR7 0.12 / −0.08 / −0.28.

Findings:
- Mean-reversion edges persist out of sample (PF 1.5–1.9, ~70% winners, positive SQN), but with 5–12% time in market
  they do not beat buy-and-hold's Sharpe in the 2016–2026 bull market on most ETFs; they are capital-efficient
  (return per unit of exposure) and shallow-drawdown overlays.
- Filling at the next open costs 0.05–0.2 Sharpe versus market-on-close (the overnight bounce is part of the edge);
  RSI(3)+IBS depends most on the close fill.
- The popular pattern setups (NR7, inside bars, hammer, engulfing) show no edge, matching the literature.
- Combined book (RSI(2), RSI(3)+IBS, pullback × SPY QQQ IWM DIA SMH XLK MTUM, equal capital, 6 bp): holdout Sharpe 0.72
  (close) / 0.69 (next open), CAGR 3.5%, max DD −8% vs SPY 0.87, 14.9%, −34% — the report's success criterion
  (Sharpe above SPY) is not met; the drawdown criterion is.
- Deflated Sharpe over all 992 swing variants: best (IBS on XLP, close fill, 2 bp) SR 0.85, P = 0.897 — just below 0.9.

## Positional (weekly / monthly; holdout 2013–2026, ATH 2015–2026)

| Strategy | Holdout Sharpe | vs buy & hold | Max DD vs B&H | Notes |
|---|---|---|---|---|
| Faber 10-month SMA, 5-ETF GTAA (SPY EFA IEF VNQ DBC) | 0.73 median (0.50–0.92 across 21 rebalance days) | 0.68 | −16% vs −27% | passes the report's criterion; timing luck is large |
| Faber SMA10 on SPY | 0.82 (0.59–0.99) | 0.91 | −27% vs −34% | full-history Sharpe 0.75 vs 0.64 |
| Faber SMA10 on QQQ | 0.96 | 0.96 | −29% vs −35% | full history 0.58 vs 0.42, DD −41% vs −83% |
| Weekly 10/40 SMA cross, SPY / QQQ | 0.80 / 0.97 | 0.94 / 1.03 | −32% / −27% vs −32% / −35% | 6–9 trades in 14 years |
| Weekly close vs 43-week SMA, SPY / QQQ | 0.90 / 1.01 | 0.94 / 1.03 | −19% / −26% | |
| Weekly Donchian 20/10, SPY / QQQ | 0.87 / 0.75 | 0.94 / 1.03 | −14% / −24% | weak on EFA, EEM, TLT |
| Sector RS rotation (top 3 of 9 by 26-week return) | 0.81 | 0.88 (equal-weight sectors) | −31% vs −37% | turnover 6.7×/yr |
| 52-week-high proximity rotation (19 country/sector ETFs) | 0.72 | 0.76 | −28% vs −36% | turnover 15×/yr |
| ATH + 10×ATR(42) trailing stop, 42 ETFs (book: 1/max(open,10)) | 0.50 daily / 0.54 weekly | SPY 0.81 / 0.85 | −22% / −27% vs −34% | trade level matches the paper (below) |
| ATH, current S&P 500 members (survivorship-biased, close-only ATR proxy) | 0.36 | SPY 0.81 | −31% vs −34% | 4.2% CAGR |

ATH breakout trade statistics on ETFs (`results/positional_ath_R_stats.csv`), R = 10×ATR42/entry:
daily — 410 trades, win rate 53% (holdout 59%), avg win +1.39R, avg loss −0.56R, expectancy +0.47R, payoff 2.5,
median hold 166 days, top 7% of trades ≈ 40% of profits; weekly — 146 trades, 61% wins, expectancy +0.77R.
The trade-level shape matches Zarattini et al. (2025), but as a portfolio it earns 4–7%/yr: stop-outs cluster on sharp
down days (exit-day losses ≈ −11.6%/yr versus +17.4%/yr while held in the stock version), and large caps / ETFs lack the
small-cap outliers that drive the paper's 15% gross.

Deflated Sharpe across 214 daily positional variants: best = Faber SPY offset 1, SR 0.85, P ≈ 1.00 — but this measures
SR > 0 for mostly-long equity exposure, not alpha over buy-and-hold.

## Intraday (Alpaca 1-minute SIP bars, SPY and QQQ, 2016 → Oct 2026)

2,698 SPY and 2,697 QQQ sessions (Jan 2016 → 29 Oct 2026), regular hours on a 390-minute grid; costs $0.0035/share
commission + slippage (base $0.001/share, swept 0–3¢). Development 2016–2022 / holdout 2023–2026; the Noise Area is split
as the paper's overlapping replication window (2016 → Feb 2024) and a true out-of-sample window (Mar 2024 → Oct 2026).

| Strategy | Symbol | Full Sharpe | Dev / replication | Holdout / OOS | CAGR | Max DD | Win rate | PF | Break-even slippage |
|---|---|---|---|---|---|---|---|---|---|
| **Noise Area + VWAP stop, 1x** | QQQ | **1.28** | 1.27 | **1.31** | 10.9% | −10.9% | 45% | 1.39 | > 3¢ |
| **Noise Area + VWAP stop, vol-targeted (≤ 4x)** | QQQ | **1.30** | 1.29 | **1.32** | 19.5% | −20.4% | 45% | 1.38 | > 3¢ |
| Noise Area, base exit, 1x | QQQ | 0.99 | 0.92 | 1.23 | 10.8% | −24.5% | 55% | 1.28 | > 3¢ |
| Noise Area + VWAP stop, 1x | SPY | 0.78 | 0.99 | **0.00** | 5.1% | −10.8% | 44% | 1.23 | > 3¢ |
| Noise Area + VWAP stop, vol-targeted | SPY | 0.90 | 1.15 | 0.14 | 12.9% | −28.7% | 44% | 1.25 | > 3¢ |
| Noise Area, base exit, 1x | SPY | 0.46 | 0.51 | 0.29 | 3.9% | −12.7% | 54% | 1.12 | > 3¢ |
| 5-min ORB (risk 1%, ≤ 4x) | QQQ | 0.79 | 1.03 | 0.31 | 20.2% | −27.4% | 24% | 1.16 | 2.2¢ |
| 5-min ORB | SPY | 0.27 | 0.55 | −0.35 | 3.6% | −43.0% | 20% | 1.04 | 0.9¢ |
| Last-half-hour momentum (prev close → 10:00 predictor) | SPY / QQQ | −0.46 / −0.40 | −0.70 / −0.51 | 0.20 / −0.13 | | | 48–50% | 0.91 | none |
| Last-half-hour momentum (prev close → 15:30 predictor) | SPY / QQQ | −0.12 / 0.12 | 0.18 / 0.44 | −0.97 / −0.68 | | | 47–50% | 0.98 | ≤ 0.4¢ |
| Gap fade (0.1–0.5% gaps) | SPY / QQQ | 0.18 / −0.41 | 0.37 / −0.07 | −0.17 / −1.00 | | | 69–70% | | 1.3¢ / none |
| Gap and go (> 1% gaps, stop at prior close) | SPY / QQQ | −0.15 / 0.04 | | −0.49 / −0.19 | | | 49–51% | | none / 1.2¢ |

Sharpe vs slippage (full period): Noise Area VWAP 1x QQQ 1.30 → 1.28 → 1.19 → 1.08 → 0.85 → 0.62 at 0 / 0.1 / 0.5 / 1 /
2 / 3¢; SPY 0.80 → 0.21; QQQ ORB 0.82 → −0.28 (break-even 2.24¢ — exactly the independent replication's 2.2¢, which
validates the engine and the fills). Noise Area VWAP 1x yearly Sharpe, SPY / QQQ: 2016 −0.91 / −0.13, 2017 −0.83 / 1.12,
2018 2.36 / 2.74, 2019 0.29 / 0.69, 2020 0.20 / 0.26, 2021 2.22 / 1.29, 2022 1.68 / 1.55, 2023 2.26 / 2.61,
2024 0.84 / 1.88, 2025 0.16 / 0.89, 2026 YTD −0.99 / 1.64.

Findings:
- **The Noise Area momentum strategy with the VWAP trailing stop is the one intraday rule that holds out of sample — on
  QQQ** (Sharpe 1.31 at 1x over Mar 2024 → Oct 2026, the window after the paper; it passes the report's > 0.7 and
  ≥ 3× break-even criteria). On SPY it replicates in-sample (0.99 vs the paper's 1.24 on 2007–2024) but earns nothing out
  of sample (Sharpe 0.00; 2026 YTD −0.99) — the edge has faded on the instrument the paper was published on.
- It is robust to costs (break-even above 3¢/share; ~0.9 trades per day, decisions only on the half-hour).
- The 5-min ORB reproduces the published gross result and dies at ~2¢ slippage; out of sample (2023–26) it is weak on
  QQQ (0.31) and negative on SPY.
- Classic market intraday momentum (first half-hour → last half-hour) is negative in 2016–2026 on both ETFs even before
  costs; gap fade / gap-and-go templates show no reliable edge.
- Deflated Sharpe over the 18 base-cost intraday variants: best = Noise Area VWAP vol-targeted QQQ, SR 1.29,
  **P = 0.947**.

## Overall verdict across horizons

| Horizon | What works (net, out of sample) | What does not |
|---|---|---|
| Intraday | Noise Area + VWAP stop on QQQ (OOS Sharpe ≈ 1.3, cost-robust) | Same rule on SPY after Feb 2024; 5-min ORB net; last-half-hour momentum; gap rules |
| Swing | Daily mean reversion in uptrends (RSI(2)/IBS/3-down-days/pullback): PF 1.5–1.9, 70% winners, shallow drawdowns, but low exposure → lower Sharpe than buy-and-hold in 2016–26 | NR7, inside bars, candlestick patterns |
| Positional | Trend filters (Faber SMA10, 43-week SMA, weekly Donchian) as drawdown control; GTAA SMA10 beats buy-and-hold risk-adjusted | ATH + 10×ATR breakout as a large-cap/ETF portfolio (4–7%/yr), 52-week-high and RS rotations (≈ equal weight) |

Caveats: single-instrument intraday tests on two ETFs; swing/positional ETF universes chosen with hindsight; single-stock
ATH test uses current S&P 500 members and a close-only ATR proxy; every variant is logged and deflated, but parameters
were the published ones (no optimisation), so the main risk is regime change rather than overfitting.

Plots: `results/intraday_equity.png`, `results/swing_spy_equity.png`.
