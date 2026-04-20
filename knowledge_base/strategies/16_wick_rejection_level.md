# Wick Rejection Level

## META
- Name: Wick Rejection Level
- Category: mean_reversion
- Difficulty: beginner
- Timeframes: 5m, 15m
- Best Market: ranging
- Estimated Win Rate: 57-63%
- Risk Reward: 1:1.8
- Tokens: any

## Description
Multiple price rejections from the same level (visible as wicks on the chart) create a "rejection zone" — strong support or resistance.
Each subsequent touch of that level increases its credibility: two wick rejections = strong signal, three = very strong.
Strategy enters on the third (or subsequent) touch of the level, anticipating another rejection.
This is one of the simplest strategies with a high win rate, especially in ranging markets.

## Entry Conditions

### LONG (multiple wick rejections from support)
- Minimum 2 previous wick rejections from the same level (±0.2%)
- Wick at each touch was clear (>0.3% below the level)
- Price returns to the same level for the 3rd+ time
- RSI < 50 at entry (not already overbought at support)
- Volume at current touch >= previous rejections
- Closing candle confirms (close above the rejection level)

### SHORT (multiple wick rejections from resistance)
- Minimum 2 previous wick rejections from the same resistance (±0.2%)
- Wick above level was >0.3% above
- Price returns 3+ times to the level
- RSI > 50
- Confirming volume

## Exit Conditions

### Take Profit
- Target: zone on the opposite side (for ranging market: previous resistance for LONG or support for SHORT)
- Alternative: 1.5× distance between two key levels
- Minimum R:R 1:1.8

### Stop Loss
- LONG: 0.3% below the lowest wick of previous rejections
- SHORT: 0.3% above the highest wick
- Rule: SL behind historical rejection extreme

### Trailing Stop
- After reaching 50% toward TP: trailing stop at entry level (minimum breakeven)
- If price strongly breaks the level — close immediately

## Confirming Signals
- Level coincides with Pivot Point, EMA or Volume Profile (multiple confluence)
- Wick rejections on multiple timeframes (e.g. visible on 5m and 15m)
- Each subsequent rejection is more "aggressive" (longer wick)
- Neutral funding rate (allows objective reading of supply/demand)
- Time between rejections is similar (rhythmic rejections = stronger level)

## When NOT to Enter
- Only 1 previous rejection (too few — wait for second)
- Gap between rejections was long (>6h on 15m TF) — level "expired"
- Price "slides" along the level instead of clearly bouncing
- ADX > 30 — trending market, S/R levels less effective
- Fundamental news may destroy the level
- Bid/ask spread > 0.05% (wicks may be an artifact)

## Risk Management
- Risk per trade: 0.5% of capital
- Strategy is intuitive and easy — do not overuse (max 4 trades daily)
- If level is broken with volume — do not look for another rejection
- Max 2 wick rejection positions simultaneously

## Setup Example
```
Token: WLD, timeframe: 5m
Rejection level: 1.2200

History:
  14:05 - wick to 1.2185, close 1.2215 (rejection 1)
  14:45 - wick to 1.2188, close 1.2210 (rejection 2)
  15:20 - price returns to 1.2200 (third attempt)

Current setup:
  Wick to 1.2192, close 1.2218 (rejection 3 ✓)
  RSI: 44 ✓
  Volume: 123% of average ✓

Entry: 1.2218
SL: 1.2178 (min wick − 0.3% = 0.33% risk)
TP: next resistance = 1.2400 (+1.65%, R:R 1:5 ✓)
  Or safer TP: 1.2350 (+1.16%, R:R 1:3.5 ✓)
```

## Configuration Parameters
- `min_rejections`: min previous rejections (default 2)
- `level_tolerance_pct`: level tolerance (default 0.2%)
- `wick_min_pct`: min wick size (default 0.3%)
- `max_level_age_candles`: max level age (default 50 candles)
- `sl_buffer_pct`: buffer behind deepest wick (default 0.3%)
- `adx_max`: max ADX (default 30)
