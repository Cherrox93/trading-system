# EMA Crossover Momentum

## META
- Name: EMA Crossover Momentum
- Category: momentum
- Difficulty: beginner
- Timeframes: 15m, 1h
- Best Market: trending
- Estimated Win Rate: 48-55%
- Risk Reward: 1:2
- Tokens: any

## Description
Classic trend-following strategy based on the crossover of two exponential moving averages (EMA 9 and EMA 21).
A buy signal is generated when the faster EMA 9 crosses EMA 21 from below, a sell signal — from above.
The strategy works best in markets with a clear trend and high momentum, fails in consolidations generating false signals (whipsaws).

## Entry Conditions

### LONG
- EMA 9 crosses EMA 21 from below (golden cross) on a closed candle
- Previous candle closed above both EMAs (direction confirmation)
- MACD histogram above zero and rising (momentum confirms)
- Volume on crossover candle >130% of 20-candle average
- ADX > 20 (trend present)
- Price above EMA 50 (macro trend bullish)

### SHORT
- EMA 9 crosses EMA 21 from above (death cross) on a closed candle
- Previous candle closed below both EMAs
- MACD histogram below zero and falling
- Volume on crossover candle >130% of average
- ADX > 20
- Price below EMA 50

## Exit Conditions

### Take Profit
- Target 1 (50% of position): 1.5% from entry in trend direction
- Target 2 (remaining 50%): next key S/R zone or 3% from entry
- Alternative: close when EMA 9 crosses back through EMA 21

### Stop Loss
- Below/above the last swing low/high before the crossover
- Minimum 0.3% from entry price
- Maximum 1% from entry price (if swing is further — skip setup)

### Trailing Stop
- After reaching 1.5% profit: trailing stop 0.5% behind price
- After reaching Target 1: move SL to breakeven

## Confirming Signals
- RSI (14) in range 45-65 for LONG / 35-55 for SHORT (not overbought at entry)
- Higher highs and higher lows (for LONG) or lower highs and lower lows (SHORT) in the last 5 candles
- Bollinger Bands widening — volatility expansion in trend direction
- No key resistance/support level within 1% of entry
- Volume rising in trend direction for 3+ candles

## When NOT to Enter
- ADX < 20 — no trend, too many false crossovers
- Price in the middle of consolidation (BB width < 1.5%)
- Crossover occurred directly at a key S/R (bounce likely)
- 3 previous crossovers within 10 candles (ranging market — filter out)
- Extreme funding rate (>0.05%) on bullish crossover — overcrowded long
- Macro news within 15 minutes
- Volume <80% of average (weak confirmation)

## Risk Management
- Risk per trade: 0.5-0.7% of capital
- After 2 consecutive losses with this strategy: pause until next 1h candle
- Max 2 open momentum positions simultaneously (do not stack directions)
- Do not enter crossover if price is already >3% from EMA 21 (late entry)
- Daily limit: max 4 trades with this strategy

## Setup Example
```
Token: SOL, timeframe: 15m
EMA 9 = 144.80, EMA 21 = 144.50
15m candle closed 144.95 with crossover (EMA9 > EMA21)
MACD histogram: +0.12 and rising ✓
Volume: 145% of average ✓
ADX: 24 ✓
Previous swing low: 143.20

Entry: 144.95
SL: 143.20 (1.21% — acceptable)
TP1: 147.10 (+1.5%) — close 50%
TP2: 149.85 (+3.4%) — close rest or trailing
```

## Configuration Parameters
- `ema_fast`: shorter EMA (default 9)
- `ema_slow`: longer EMA (default 21)
- `ema_trend`: trend filter EMA (default 50)
- `adx_min`: minimum ADX (default 20)
- `volume_multiplier`: minimum volume vs average (default 1.3)
- `tp1_pct`: first profit target (default 1.5%)
- `tp2_pct`: second profit target (default 3.0%)
- `trailing_activation_pct`: trailing stop activation level (default 1.5%)
