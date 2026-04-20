# OBV + Chaikin Money Flow Volume Analysis

## META
- Name: OBV and Volume Flow Analysis
- Category: volume_analysis
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: pre-breakout, trend reversal identification
- Estimated Win Rate: 57-64%
- Risk Reward: 1:2.0
- Tokens: any with real volume data

## Description
On-Balance Volume (OBV) is a cumulative volume indicator: adds volume on up days, subtracts on down days.
It measures buying/selling pressure and often LEADS price — OBV breaks out before price does.
Chaikin Money Flow (CMF) measures whether money is flowing into (positive) or out of (negative) an asset over N periods.
CMF > 0.1 = strong accumulation. CMF < -0.1 = strong distribution. Key: divergence between volume flow and price.

## OBV Strategies

### OBV Breakout (Lead Indicator)
- OBV breaks above previous high while price hasn't yet → accumulation occurring → bullish
- OBV breaks below previous low while price holds → distribution → bearish
- Enter in direction of OBV breakout, before price confirms

### OBV Divergence (Reversal Signal)
- **Bullish divergence**: price makes lower low, OBV makes higher low → buyers absorbing selling
- **Bearish divergence**: price makes higher high, OBV makes lower high → sellers distributing into rally
- This is the highest-quality OBV signal

### OBV Trend Confirmation
- OBV rising in uptrend = healthy trend, increasing buying pressure
- OBV falling in uptrend = trend weakening, exit signals coming
- OBV flat in uptrend = neutral, watch for change

## CMF Strategies

### CMF Confirmation
- Price at support + CMF turning positive (> 0.05): accumulation at support → LONG
- Price at resistance + CMF turning negative (< -0.05): distribution at resistance → SHORT
- CMF > 0.15 for 5+ candles = strong institutional buying — trade any pullback as LONG

### CMF Divergence
- Price drops, CMF stays positive → smart money buying dips → reversal coming
- Price rises, CMF stays negative → distribution into rally → reversal coming

## Entry Conditions

### LONG
- OBV: higher highs and higher lows (OBV uptrend) while price consolidates or pulls back
- CMF > 0.05 and rising
- Price at support / Fib / EMA confluence
- Bullish candle pattern (engulfing, hammer) at the level
- RSI: not overbought (< 65)

### SHORT
- OBV: lower lows and lower highs (OBV downtrend) while price consolidates or pushes up
- CMF < -0.05 and falling
- Price at resistance
- Bearish candle pattern
- RSI: not oversold (> 35)

## Exit Conditions

### Take Profit
- OBV reaches new all-time high (LONG) → momentum peak possible → partial exit
- CMF crosses back to opposite side (0 line)
- Next S/R level

### Stop Loss
- OBV makes a lower low that invalidates the bullish structure (LONG)
- CMF crosses strongly negative (< -0.1) during LONG hold
- ATR(14) × 1.5 from entry

## Confirming Signals
- Volume Profile: price at high-volume node + positive CMF (institutional support)
- OBV leading price by 2-5 candles consistently (reliable in this asset)
- Multiple timeframe OBV agreement

## When NOT to Enter
- Volume data is unreliable / very low (below $500k 24h)
- OBV and CMF conflict (OBV rising, CMF falling = mixed signal)
- Single high-volume candle distorting OBV without follow-through

## Risk Management
- Risk per trade: 0.8-1.2%
- Volume divergences are slower signals — more valid on 1h+ timeframes
- OBV alone is weak: always combine with price action at key level

## Setup Example
```
Token: LINK, 1h chart
Scenario: Bullish OBV divergence
Price: $14.50 → drops to $13.80 (lower low)
OBV: 2,450,000 → rises to 2,510,000 (higher low!) ← DIVERGENCE
CMF: +0.08 (accumulation at lows) ✓
Price at Fib 61.8% ($13.85) ✓
Hammer candle at low ✓

Entry: $13.90
SL: below swing low $13.55 → 2.5% risk (wide)
  → Reduce size: 0.6% risk budget / 2.5% SL
TP: back to previous high $14.80 (+6.5%)
R:R: 1:2.6 ✓
```

## Configuration Parameters
- `obv_lookback`: 20 (periods for OBV trend)
- `cmf_period`: 21 (CMF calculation period, default)
- `cmf_threshold_strong`: 0.15 (strong accumulation level)
- `cmf_threshold_entry`: 0.05 (minimum CMF for entry)
- `divergence_min_bars`: 5 (minimum distance between pivot comparisons)
