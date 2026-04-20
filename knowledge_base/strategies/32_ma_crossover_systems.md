# Moving Average Crossover Systems

## META
- Name: Moving Average Crossover Systems
- Category: trend_following
- Difficulty: beginner
- Timeframes: 15m, 1h, 4h
- Best Market: trending
- Estimated Win Rate: 48-55%
- Risk Reward: 1:2.5
- Tokens: BTC, ETH, high-cap alts

## Description
Moving average crossovers identify trend direction and momentum shifts. Three main systems:
1. **Golden/Death Cross**: 50 EMA × 200 EMA (major trend shifts, higher timeframes)
2. **Fast System**: 9 EMA × 21 EMA (short-term momentum, 15m-1h)
3. **Triple MA**: 20 EMA / 50 EMA / 200 EMA (trend confirmation at multiple levels)
WMA (weighted) reacts faster to recent price; EMA standard for most systems; SMA more stable for long-term.

## Entry Conditions

### LONG — Golden Cross / Fast Cross
- Fast MA crosses above slow MA (EMA9 > EMA21, or EMA50 > EMA200)
- Price is ABOVE both MAs at the time of entry (not below — avoid entering during fake-out)
- Volume on the crossover candle > 20-candle average
- For 9/21 system: EMA50 must be sloping upward (macro trend alignment)
- Pullback entry: price retraces to touch the fast MA after the cross → enter on bounce

### SHORT — Death Cross / Fast Cross Down
- Fast MA crosses below slow MA
- Price is BELOW both MAs
- Volume confirms
- EMA50 sloping downward

## Exit Conditions

### Take Profit
- Golden Cross / Death Cross: target distance = 2× distance between MAs at cross
- Fast system (9/21): exit when MAs start converging (momentum slowing)
- Trailing stop: trail 1 ATR(14) below the fast MA (LONG)

### Stop Loss
- Below the slow MA (LONG): if price closes below EMA21 or EMA50, trend invalidated
- ATR(14) × 2.0 as maximum
- Hard stop: below the swing low that preceded the cross

## Confirming Signals
- Higher timeframe MA alignment (15m cross confirmed by 1h uptrend)
- MACD histogram positive and rising
- Price holding above VWAP (institutional bias)
- Open interest increasing (new money entering, not just shorts covering)
- Funding rate shifting from negative to neutral/positive (sentiment turn)

## When NOT to Enter
- Choppy/ranging market: MAs will whipsaw (check ADX < 20 = range, avoid)
- Price too far extended from MAs (> 5% distance): wait for pullback
- MA cross occurs inside consolidation range: false signal
- News-driven spike caused the cross — structurally invalid

## Risk Management
- Risk per trade: 1.0-1.5% (trend trades run longer, bigger SL needed)
- Trail stop as trend develops: move SL to each new higher low (LONG)
- Maximum hold: 4-8 candles on 15m, 3-5 days on 4h

## Setup Example
```
Token: BTC, 1h chart
EMA9 crosses above EMA21 ✓
EMA50 sloping upward ✓, price above EMA50 ✓
Volume: 148% of 20-bar average ✓
Strategy: pullback entry
  → Price retests EMA9 on next candle, bounces
  → Enter on close above EMA9
SL: below EMA21 (0.8% below entry)
TP: 2× MA spread distance = 2.0%
R:R: 1:2.5 ✓
```

## Configuration Parameters
- `fast_ema`: fast MA period (default 9)
- `slow_ema`: slow MA period (default 21)
- `trend_ema`: macro trend MA (default 50)
- `ma_type`: EMA / SMA / WMA (default EMA)
- `volume_threshold`: volume multiplier required (default 1.2)
- `atr_trail_multiplier`: trailing stop in ATR units (default 1.0)
