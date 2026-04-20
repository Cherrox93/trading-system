# Timeframe Momentum Arbitrage

## META
- Name: Timeframe Momentum Arbitrage
- Category: multi_timeframe
- Difficulty: advanced
- Timeframes: 5m entry, 15m context, 1h bias
- Best Market: transitioning markets (trend starting or ending)
- Estimated Win Rate: 50-58%
- Risk Reward: 1:2.5
- Tokens: BTC, ETH, SOL, high-liquidity alts

## Description
Exploits temporary momentum divergences between timeframes.
Lower timeframes often lead higher timeframes at turning points — 5m momentum reversal
can precede 1h trend change by 30-60 minutes.
This strategy uses misalignment between timeframes as an entry signal rather than waiting
for full alignment (unlike 20_multi_timeframe_confluence which requires agreement).

## Core Concept: Momentum Cascade
```
Markets transmit momentum from lower to higher timeframes:
5m reversal → 15m reversal → 1h reversal → 4h reversal

Entry opportunity exists WHILE the cascade is in progress:
- 5m and 15m already reversed
- 1h still in old direction (hasn't confirmed yet)
- 4h: no change

This "leads" the 1h signal by 1-3 candles. Higher risk, higher reward.
```

## Measuring Momentum: Relative RSI Method
```
For each timeframe, compute RSI(14) momentum direction:

Momentum_TF = (RSI_now − RSI_5_periods_ago) / 5

Positive: accelerating bullish momentum on that TF
Negative: accelerating bearish momentum on that TF
Near zero (< 0.5): stalling momentum

Compare across timeframes:
  5m_momentum, 15m_momentum, 1h_momentum
```

## Entry Conditions

### LONG (momentum cascade up: 5m and 15m turning bullish vs. 1h still bearish)
- 5m RSI Momentum: positive and > 1.0 (accelerating up)
- 15m RSI Momentum: turned positive in last 3 candles (freshly reversed)
- 1h RSI Momentum: still negative (hasn't confirmed yet = entry window)
- 4h trend: NOT in confirmed downtrend (4h RSI > 35, or price above 4h EMA100)
- Price on 1h is near key support (reversal candidate, not middle of nowhere)
- 5m stochastic K crossed above D in last 3 candles (momentum confirmation)
- 5m MACD histogram turning positive (crossing zero or at least less negative)

### SHORT (momentum cascade down)
- 5m RSI Momentum: negative and < -1.0
- 15m RSI Momentum: turned negative in last 3 candles
- 1h RSI Momentum: still positive
- 4h trend: NOT in confirmed uptrend (4h RSI < 65, or price below 4h EMA100)
- Price near key resistance
- 5m stochastic K crossed below D
- 5m MACD histogram turning negative

## Entry Timing (precise)
```
After conditions above confirmed:
1. Wait for 5m candle to close confirming the setup
2. Enter at open of next 5m candle
3. Do NOT enter during 5m candle — wait for close (signals can invalidate intra-candle)
```

## Exit Conditions

### Take Profit
- TP1 (50% position): when 15m RSI Momentum crosses zero (momentum delivered)
- TP2 (50% position): when 1h RSI Momentum confirms direction (cascade completes)
  - Or 2.5× ATR(14) from 15m timeframe from entry

### Stop Loss
- LONG: below nearest 15m swing low + ATR(15m) × 0.5
- SHORT: above nearest 15m swing high + ATR(15m) × 0.5
- Max 1.5% from entry

### Invalidation (exit immediately)
- 5m momentum reverses back against position before 15m confirms
- 4h trend fully reverses against position (trend assumption broken)
- 1h confirms against direction after more than 3 1h-candles pass without cascade

## Cascade Failure Pattern (Risk)
```
Most common failure:
- 5m and 15m turn bullish
- 1h does NOT turn — instead ADDS momentum downward
- = 5m/15m move was just a brief correction in 1h downtrend
- = Entry was premature, 4h trend too strong to overcome

Mitigation:
- Check 4h trend carefully before entry (hard block if 4h confirmed trend)
- Set time-based stop: if cascade not complete in 3 × 15m candles (45min), exit
- Size at 50-75% of normal (higher risk of failure than standard confluence)
```

## Momentum Score (Pre-Trade Calculation)
```
Compute a composite score before each potential entry:

Score = 0
IF 5m_momentum > 1.0: +2
IF 15m_momentum reversed in last 3 candles: +2
IF 1h_momentum opposite (arbitrage gap exists): +1
IF 4h_momentum NOT against: +1
IF 5m stoch crossed: +1
IF MACD histogram direction matches: +1
IF price at structural S/R: +1

Enter only if Score ≥ 6
Maximum possible score: 9
Best setups: 7-9
```

## Setup Example
```
Token: SOL, 2026-03-15 14:00 UTC
1h chart: downtrend last 4h, RSI(14): 38, momentum −1.8 (bearish)
15m chart: RSI turning, last 3 candles: RSI 34→37→41, momentum +1.4 (fresh reversal ✓)
5m chart: RSI 42→48→55, momentum +2.6 ✓, stoch K crossed D ✓, MACD turning ✓
4h: downtrend, RSI 45 (not extreme — not a hard block ✓)
Price: at 15m support zone 148.50

Score: 5m momentum✓(+2) + 15m reversed✓(+2) + 1h gap✓(+1) + 4h ok✓(+1) + stoch✓(+1) + MACD✓(+1) + S/R✓(+1) = 9/9

Entry: 148.55 (5m candle close confirm)
ATR(15m): 0.90
SL: 148.50 − (swing low 147.80) − 0.5×0.90 = 147.35 (−0.81%)
TP1: when 15m momentum crosses zero (~149.50 est., +0.64%)
TP2: 2.5×0.90 = +2.25 → 150.80 (+1.51%)
R:R TP2: 1:1.9 ✓
```

## Configuration Parameters
- `rsi_period`: 14
- `momentum_lookback_periods`: 5
- `momentum_min_5m`: 1.0
- `momentum_reversed_15m_candles`: 3
- `stoch_k_period`: 14
- `stoch_d_period`: 3
- `macd_fast`: 12
- `macd_slow`: 26
- `macd_signal`: 9
- `min_momentum_score`: 6
- `time_stop_15m_candles`: 3
- `max_sl_pct`: 1.5
- `tp1_fraction`: 0.5
- `tp2_atr_multiplier_15m`: 2.5
- `4h_block_rsi_bull_max`: 65
- `4h_block_rsi_bear_min`: 35
