# Stochastic Momentum Strategy

## META
- Name: Stochastic Momentum
- Category: momentum
- Difficulty: beginner
- Timeframes: 5m, 15m, 1h
- Best Market: ranging, mild trend
- Estimated Win Rate: 52-58%
- Risk Reward: 1:1.8
- Tokens: any liquid

## Description
Stochastic oscillator (14,3,3) measures closing price position relative to the high-low range over N periods.
Values below 20 = oversold, above 80 = overbought. The %K/%D crossover within extreme zones provides high-probability reversal entries.
Works best when combined with a support/resistance level or trend context from a higher timeframe.

## Entry Conditions

### LONG
- Stochastic %K crosses above %D while both are below 20 (oversold zone)
- %K value at cross: ideally 10-18 (deeper = stronger signal)
- Price is at or near a known support level (pivot, EMA, previous low)
- RSI(14) < 40 (confirming oversold)
- Candle closes above the open (bullish close)

### SHORT
- Stochastic %K crosses below %D while both are above 80 (overbought zone)
- %K value at cross: ideally 82-90
- Price near resistance (pivot, EMA, previous high)
- RSI(14) > 60
- Candle closes below the open (bearish close)

## Exit Conditions

### Take Profit
- Primary: Stochastic reaches opposite extreme zone (80 for LONG, 20 for SHORT)
- Secondary: Previous structure high/low, R:R minimum 1:1.5
- Partial close at 50% position when %K crosses 50 level

### Stop Loss
- Below the swing low that formed the oversold signal (LONG)
- Above the swing high that formed the overbought signal (SHORT)
- ATR(14) × 1.5 as maximum SL width

## Confirming Signals
- Bullish/bearish divergence between Stochastic and price (strongest setup)
- Stochastic double bottom in oversold zone before cross (LONG)
- Volume spike on the crossover candle
- Higher timeframe (4h) Stochastic also oversold/overbought (multi-TF alignment)
- Funding rate neutral (not overcrowded)

## When NOT to Enter
- ADX > 28: strong trend — stochastic stays in extreme zone without reversing
- News event within 15 minutes
- %K/%D cross happens outside the extreme zones (50-area cross = weak)
- First cross after a long trend — wait for confirmation retrace
- Spread > 0.05%

## Risk Management
- Risk per trade: 0.7-1.0% (standard momentum risk)
- Do not enter if previous stochastic trade from same zone lost
- Max 2 stochastic trades per session

## Setup Example
```
Token: ETH, 15m chart
Stochastic(14,3,3): %K=12, %D=15 → %K crosses above %D at 14
Both below 20 ✓, RSI=34 ✓
Price at EMA200 support ✓
Entry: market order on candle close
SL: below swing low − 0.3% (ATR buffer)
TP: when stochastic reaches 75+ or previous resistance
R:R example: SL=0.9%, TP=1.8% → R:R 1:2 ✓
```

## Configuration Parameters
- `stoch_period`: Stochastic K period (default 14)
- `stoch_smooth_k`: %K smoothing (default 3)
- `stoch_smooth_d`: %D period (default 3)
- `oversold_level`: entry zone maximum (default 20)
- `overbought_level`: entry zone minimum (default 80)
- `atr_sl_multiplier`: SL width in ATR units (default 1.5)
