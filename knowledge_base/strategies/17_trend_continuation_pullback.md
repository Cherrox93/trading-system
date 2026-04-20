# Trend Continuation Pullback

## META
- Name: Trend Continuation Pullback
- Category: momentum
- Difficulty: intermediate
- Timeframes: 15m, 1h
- Best Market: trending
- Estimated Win Rate: 53-59%
- Risk Reward: 1:2.5
- Tokens: any

## Description
Trend-following strategy with entry during a correction (pullback), not at a breakout.
Instead of chasing price at new highs/lows, we wait for price to pull back to a key moving average (EMA 21 or EMA 50) or Fibonacci retracement, then continue the main trend.
This approach provides a better risk-to-reward ratio than breakout entry because SL is closer to entry.

## Entry Conditions

### LONG (pullback in uptrend)
- ADX > 25 (strong trend) on used TF
- Series of higher highs and higher lows (clear uptrend)
- EMA 9 > EMA 21 > EMA 50 (trend alignment)
- Price pulls back to EMA 21 or EMA 50 zone
- RSI drops to 40-55 range during pullback (not oversold — healthy correction)
- Reversal candle at EMA (pin bar, bullish engulfing) — end of correction
- Volume during pullback decreasing (no selling pressure)
- Volume at entry candle >= average (buyers returning)

### SHORT (pullback in downtrend)
- ADX > 25
- Series of lower highs and lower lows
- EMA 9 < EMA 21 < EMA 50
- Pullback to EMA 21 or EMA 50 from below
- RSI rises to 45-60 during pullback
- Bearish candle at EMA

## Exit Conditions

### Take Profit
- Target: new trend high (for LONG) or new low (SHORT) — minimum
- Aggressive: Fibonacci extension projection (1.618× previous impulse)
- Safe: previous swing high (for LONG) + 0.5%

### Stop Loss
- LONG: 0.3% below pullback low (absolute correction minimum)
- SHORT: 0.3% above pullback high
- Alternative: below EMA 50 (deeper SL, triggered less often)

### Trailing Stop
- Activate trailing after reaching previous swing high (for LONG)
- Trailing: low of previous 15m candle (for LONG) — aggressive
- Or: EMA 21 (looser trailing)

## Confirming Signals
- Fib retracement: pullback to 38.2% or 50% of previous impulse (golden zone)
- Confluence with S/R level or Pivot at EMA
- Impulse volume > pullback volume by at least 50% (trend dominates)
- MACD at zero or slightly positive during pullback (not deeply negative)
- Higher TF: trend strong and showing no signs of weakening

## When NOT to Enter
- ADX < 25 — trend too weak, pullback may be reversal
- Pullback deeper than 61.8% Fibonacci (correction too deep = suspicious)
- EMA 9 crossed below EMA 21 during pullback (trend weakened)
- Pullback lasts longer than 50% of previous impulse time (consolidation, not correction)
- RSI during pullback drops below 30 (too deep = potential reversal)
- Fundamental news may change direction

## Risk Management
- Risk per trade: 0.6-0.7% of capital (high-quality setup)
- Patience: do not enter without a clear reversal candle at EMA
- Max 2 pullback positions simultaneously (same direction)
- This strategy has the best EV when scaling — add to position if trend continues

## Setup Example
```
Token: SOL, timeframe: 1h
Trend: bullish, ADX = 32 ✓
EMA: EMA9=147.5, EMA21=145.8, EMA50=142.0 (aligned ✓)
Series: 3 consecutive higher highs (140.0, 143.5, 147.8)

Pullback:
  Price pulls back from 147.8 to 145.5 (meeting EMA21 ✓)
  RSI at pullback: 48 (healthy ✓)
  Pullback volume: decreasing (3 candles with decreasing vol ✓)

Entry candle: bullish engulfing at EMA21 (145.6-146.2)
Volume: 112% of average (buyers returning ✓)

Entry: 146.20
SL: pullback low − 0.3% = 145.20 (0.68% risk)
TP: previous high 147.80 + new high (~150.0) = R:R 1:2.6 ✓
Fib extension 1.618: 147.8 + (147.8-140.0)×0.618 = 152.6 (aggressive target)
```

## Configuration Parameters
- `adx_min`: min ADX for trend (default 25)
- `pullback_ema`: EMA to which price pulls back (default 21)
- `rsi_pullback_min`: min RSI during pullback (default 38)
- `rsi_pullback_max`: max RSI during pullback (default 58)
- `fib_golden_zone`: entry only at Fib 38.2-61.8% (default True)
- `require_reversal_candle`: require reversal candle (default True)
- `sl_type`: 'pullback_low' or 'below_ema50' (default 'pullback_low')
