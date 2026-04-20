# RSI Divergence Reversal

## META
- Name: RSI Divergence Reversal
- Category: mean_reversion
- Difficulty: intermediate
- Timeframes: 15m, 1h
- Best Market: any
- Estimated Win Rate: 55-62%
- Risk Reward: 1:2
- Tokens: any

## Description
RSI divergence occurs when price reaches a new extreme (higher high or lower low), but RSI does not confirm the move — indicating weakening momentum and an upcoming reversal.
Bullish divergence: price makes a lower low, RSI makes a higher low — Long signal.
Bearish divergence: price makes a higher high, RSI makes a lower high — Short signal.
One of the best-proven technical analysis techniques in cryptocurrencies.

## Entry Conditions

### LONG (Bullish Divergence)
- Price forms a Lower Low (LL) — new lower bottom
- RSI (14) forms a Higher Low (HL) — higher bottom (divergence confirmed)
- Both divergence points visible with at least 2 candles apart
- Price at a key support level S or Pivot S1 (double confirmation)
- Decreasing volume when forming LL (weakening selling pressure)
- Price halt/reversal confirmed by candle (pin bar, engulfing)

### SHORT (Bearish Divergence)
- Price forms a Higher High (HH) — new higher peak
- RSI (14) forms a Lower High (LH) — lower peak (divergence)
- Both divergence points at least 2 candles apart
- Price at a key resistance R or Pivot R1
- Decreasing volume when forming HH
- Reversal candle (bearish engulfing, shooting star)

## Exit Conditions

### Take Profit
- Target: previous swing in position direction (for LONG — previous HH, for SHORT — previous LL)
- Minimum: 2× risk (R:R 1:2)
- If TP is further than 3% away — split position into 2 targets

### Stop Loss
- LONG: 0.3% below the lowest bottom (LL) — divergence invalidation point
- SHORT: 0.3% above the highest peak (HH)
- No wider than 1.5% (if divergence range > 1.5% — skip setup)

### Trailing Stop
- After reaching 1× risk in profit: trailing stop behind each Higher Low (LONG) / Lower High (SHORT)

## Confirming Signals
- Hidden divergence (trend confirmation) — for entries aligned with higher TF trend
- MACD histogram also showing divergence (double divergence = stronger signal)
- Stochastic RSI in oversold zone (LONG) or overbought zone (SHORT) at entry
- Open Interest falling when forming new peak/bottom (weakening commitment)
- No new longs/shorts on funding rate (neutral market)

## When NOT to Enter
- Divergence on only one candle (sample too small — min 2 candles)
- Clear trend with no sign of slowing (ADX > 40 without any pullbacks)
- RSI difference between divergence points < 3 RSI points (too weak)
- Price not at any key S/R (divergence "in the air")
- Fundamental news within 30 minutes
- Hidden divergence suggesting continuation (don't confuse with regular divergence)

## Risk Management
- Risk per trade: 0.6-0.7% of capital (higher WR justifies slightly larger risk)
- Max 2 open divergence positions simultaneously
- Do not combine with EMA crossover in the same direction (risk stacking)
- If divergence invalidated (new extreme with confirmed RSI) — close immediately

## Setup Example
```
Token: WLD, timeframe: 15m

Price: forms LL = 1.1800 (previous bottom = 1.1950)
RSI at LL = 28, RSI at previous bottom = 22

Divergence:
  Price: 1.1950 → 1.1800 (LL ✓)
  RSI:   22    → 28     (HL ✓ = bullish divergence)

Support S1 = 1.1820 (price nearby ✓)
Decreasing volume at LL ✓
Reversal candle: hammer at 1.1810 ✓

Entry: 1.1840 (after confirmation)
SL: 1.1775 (below LL − 0.3% = 0.55% risk)
TP: previous HH = 1.2200 (R:R = 1:2.65 ✓)
```

## Configuration Parameters
- `rsi_period`: RSI period (default 14)
- `divergence_min_candles`: min candles between points (default 2)
- `divergence_min_rsi_diff`: min RSI difference (default 3 points)
- `sl_buffer_pct`: buffer below LL/above HH (default 0.3%)
- `min_rr`: minimum R:R ratio (default 2.0)
- `confirm_candle`: require confirming candle (default True)
