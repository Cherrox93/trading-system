# ADX Trend Rider

## META
- Name: ADX Trend Rider
- Category: trend_following
- Difficulty: intermediate
- Timeframes: 1h, 4h
- Best Market: strong trends (ADX > 30)
- Estimated Win Rate: 44-52%
- Risk Reward: 1:4 (ride the trend)
- Tokens: BTC, ETH, majors

## Description
Uses ADX (Average Directional Index) to identify and ride strong existing trends.
ADX measures trend strength regardless of direction — high ADX means strong trend (up or down).
Entry on pullbacks within the trend, NOT on breakouts. Lower risk than breakout approach.
This strategy deliberately enters AGAINST short-term momentum to catch mid-trend continuation.

## Core Concept: ADX Phases
```
ADX < 20: No trend — avoid this strategy entirely, use mean reversion
ADX 20-25: Emerging trend — smaller position, looser stop
ADX 25-40: Strong trend — full position, this strategy's sweet spot
ADX > 40: Very strong trend — reduce position (parabolic, may snap back)
ADX > 50: Extreme — close to end of move, avoid new entries
```
+DI > -DI = bullish trend; -DI > +DI = bearish trend.

## Entry Conditions

### LONG (pullback in uptrend)
- ADX(14) > 28 on entry timeframe
- +DI > -DI (bullish ADX direction)
- Price pulls back to EMA20 on 1h OR EMA50 on 4h
- Pullback candle shows rejection (lower wick ≥ 50% of candle) OR next candle is bullish engulf
- RSI drops to 40-55 range during pullback (not oversold — healthy correction)
- Volume on pullback < 70% of average (weak selling = counter-trend correction)
- Volume on entry candle (reversal) ≥ 120% average

### SHORT (pullback in downtrend)
- ADX(14) > 28
- -DI > +DI (bearish ADX direction)
- Price bounces to EMA20 (1h) or EMA50 (4h)
- Bounce candle shows rejection (upper wick ≥ 50%) OR bearish engulf
- RSI rises to 45-60 range during bounce
- Volume on bounce < 70% average (weak buying)

## Exit Conditions

### Take Profit
- TP1 (33% position): previous swing high/low (LONG: prev swing high; SHORT: prev swing low)
- TP2 (33% position): 2.5× ATR(14) from entry
- TP3 (34% position): trailing stop at 2× ATR below price high (LONG), close when ADX drops < 20

### Stop Loss
- LONG: below the pullback low + ATR(14) × 0.5 buffer
- SHORT: above the bounce high + ATR(14) × 0.5 buffer
- Never wider than 2.5% from entry

### Exit Signals (before TP)
- ADX drops below 20: trend ending, exit all immediately
- +DI/-DI crossover against position: trend direction changed, exit
- Price closes below EMA50 (LONG) — trend broken

## Confirming Signals
- HTF (daily) trend matches 1h/4h direction
- EMA alignment: EMA20 > EMA50 > EMA100 (all trending same direction)
- OI stable or slightly rising (not declining = no mass exodus)
- Pullback depth ≤ 38.2% Fibonacci of previous swing

## When NOT to Enter
- ADX < 20 or declining sharply (trend dying)
- Pullback deeper than 61.8% Fibonacci (potential reversal, not pullback)
- Price already at major HTF S/R level (may stop trend)
- Upcoming major macro event within 4h (FOMC, CPI, etc.)
- Funding rate > 0.1% for LONG entries (over-leveraged longs = stop hunt risk)
- Previous pullback entry failed at same EMA (EMA no longer holding)

## Risk Management
- Risk per trade: 0.5-1.0% (lower than breakout due to more entries per trend)
- Scale in: 50% on first pullback touch, 50% if holds and continues
- Exit all if daily timeframe trend reverses (DI crossover on daily)
- Maximum 1 ADX rider position per correlated pair (e.g., only 1 of BTC/ETH)

## Setup Example
```
Token: BTC, timeframe: 1h
ADX(14): 35 ✓, +DI: 28, -DI: 18 (bullish ✓)
Trend: up for last 12h, price at 68,500
Pullback: retraces to EMA20 at 67,800
Pullback candle: bearish but wick below = rejection ✓
RSI at pullback: 48 ✓
Volume at pullback: 60% average ✓
Volume at entry candle: 130% average ✓

Entry: 67,850 (at close of reversal candle)
Pullback low: 67,650
SL: 67,650 − ATR(350)×0.5 = 67,475 (−0.55% risk)
TP1: prev swing high 68,900 (+1.54%)
TP2: 67,850 + 2.5×350 = 68,725 (+1.29%)
TP3: trailing 2×ATR, continue ride
```

## Configuration Parameters
- `adx_min`: 28
- `adx_strong`: 40 (reduce position above this)
- `adx_exit`: 20 (exit all when ADX drops below)
- `pullback_ema_period_1h`: 20
- `pullback_ema_period_4h`: 50
- `rsi_pullback_long_range`: [40, 55]
- `rsi_pullback_short_range`: [45, 60]
- `volume_pullback_max_ratio`: 0.70
- `sl_atr_buffer`: 0.5
- `tp1_fraction`: 0.33
- `tp2_atr_multiplier`: 2.5
- `trailing_atr_multiplier`: 2.0
