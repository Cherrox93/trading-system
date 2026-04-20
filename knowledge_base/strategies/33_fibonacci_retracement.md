# Fibonacci Retracement & Extension

## META
- Name: Fibonacci Retracement and Extension
- Category: mean_reversion, trend_following
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: trending with clear impulse moves
- Estimated Win Rate: 55-63%
- Risk Reward: 1:2.0
- Tokens: BTC, ETH, major alts

## Description
Fibonacci retracement identifies pullback zones within a trend using ratios derived from the Fibonacci sequence.
Key levels: 23.6%, 38.2%, 50%, 61.8% (golden ratio), 78.6%.
The 61.8% level ("golden ratio") is statistically the most reliable reversal zone.
Extensions (127.2%, 161.8%, 261.8%) define TP targets beyond the initial swing high.
Draw from swing low to swing high (LONG) or swing high to swing low (SHORT).

## Entry Conditions

### LONG (Pullback in Uptrend)
- Identify clear impulse move up (at least 3-5% move with strong volume)
- Price retraces to 38.2%-61.8% zone
- At the Fib level: bullish candle pattern (pin bar, engulfing, hammer)
- RSI on pullback: 40-55 (mild oversold in uptrend, not extreme)
- Pullback volume declining (healthy retracement, not new selling)
- EMA20 or EMA50 confluent with the Fib level (strongest setups)

### SHORT (Pullback in Downtrend)
- Identify clear impulse move down
- Price retraces up to 38.2%-61.8% zone
- At the Fib level: bearish candle pattern (shooting star, bearish engulfing)
- RSI 45-60 range on bounce
- Declining volume on the bounce

## Exit Conditions

### Take Profit (Extensions)
- TP1: 127.2% extension of the original impulse move (safe target)
- TP2: 161.8% extension (main target)
- TP3: 261.8% extension (only in strong trends, trail stop)
- Partial: close 50% at TP1, trail remaining to TP2

### Stop Loss
- Below the 78.6% Fib level (structure still intact)
- Hard stop: below the swing low that started the impulse (full invalidation)
- ATR(14) × 1.2 buffer below the chosen Fib level

## Confirming Signals
- Multiple Fib levels from different timeframes cluster at the same price
- Pivot Point S/R level at the same zone as Fib (confluence)
- Order block (ICT) at the Fib level
- Fair Value Gap at the Fib zone
- Volume Profile: high-volume node at Fib level (price spends time there)

## When NOT to Enter
- Impulse move was news-driven (Fib levels less reliable on fundamental moves)
- Price blows through 61.8% with momentum — trend may be reversing
- Multiple failed attempts at same Fib level in recent session
- Spread or slippage would erode R:R below 1:1.5

## Risk Management
- Risk per trade: 0.8-1.2% (depends on SL distance to 78.6%)
- Golden ratio (61.8%) trades: can use slightly larger size (higher reliability)
- Do not enter Fib trade if the impulse was less than 2% (too small to be meaningful)

## Setup Example
```
Token: SOL, 1h chart
Impulse: 150.00 → 165.00 (+10% move, strong volume)
Retracement levels:
  38.2%: 159.27
  50.0%: 157.50
  61.8%: 155.73 ← target entry zone
  78.6%: 153.21 ← SL below this

Price pulls back to 155.90 (≈61.8% ✓)
EMA50 at 155.50 (confluence ✓)
Hammer candle forms at 155.73 ✓
RSI = 47 (mild pullback ✓)

Entry: 156.10 (above hammer close)
SL: 152.80 (below 78.6% with buffer) → 2.1% risk
TP1: 127.2% ext = 169.08 → +8.3%
TP2: 161.8% ext = 174.27 → +11.6%
R:R to TP1: 1:4.0 ✓
```

## Configuration Parameters
- `fib_levels`: [0.236, 0.382, 0.5, 0.618, 0.786] (standard)
- `fib_extensions`: [1.272, 1.618, 2.618] (TP targets)
- `primary_entry_zone`: 0.382-0.618 (default)
- `sl_fib_level`: 0.786 (stop below this)
- `atr_buffer_multiplier`: 1.2 (ATR buffer below SL Fib)
- `min_impulse_pct`: 2.0 (minimum impulse size to draw Fibs)
