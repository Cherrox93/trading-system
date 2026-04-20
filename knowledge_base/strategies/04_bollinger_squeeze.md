# Bollinger Bands Squeeze Breakout

## META
- Name: Bollinger Bands Squeeze Breakout
- Category: breakout
- Difficulty: intermediate
- Timeframes: 15m, 1h
- Best Market: volatile
- Estimated Win Rate: 45-52%
- Risk Reward: 1:2.5
- Tokens: any

## Description
Strategy based on identifying periods of volatility compression (squeeze), when Bollinger Bands narrow to a minimum, followed by a sharp expansion (volatility expansion) and breakout.
Squeeze is identified by BB Width (distance between upper and lower band) below 2% of price.
Setup has a lower win rate than mean reversion, but the risk-to-reward ratio is higher (strong moves after squeeze).

## Entry Conditions

### LONG (upper breakout)
- BB Width < 2% for at least the last 5 candles (squeeze active)
- Candle closes above the upper BB band (breakout)
- Breakout candle volume >150% of 20-candle average
- RSI > 50 and rising (bullish momentum)
- Keltner Channel: if available — BB inside KC confirms squeeze
- Price not at a key resistance (check daily S/R)

### SHORT (lower breakout)
- BB Width < 2% for at least the last 5 candles
- Candle closes below the lower BB band
- Breakout candle volume >150% of average
- RSI < 50 and falling
- No key support within 1% below

## Exit Conditions

### Take Profit
- Target 1 (30% of position): BB Width × 1 projected from breakout point
- Target 2 (40% of position): BB Width × 2 projected
- Target 3 (30% of position): next key S/R or BB Width × 3
- Alternative: close when RSI reaches 70 (LONG) or 30 (SHORT)

### Stop Loss
- LONG: candle close back below the upper BB band
- SHORT: candle close back above the lower BB band
- Absolute SL: middle BB band (SMA 20) — if price returns to center, setup invalidated

### Trailing Stop
- After reaching Target 1: trailing stop at middle BB band
- Trailing is not mandatory — can manage through fixed targets

## Confirming Signals
- Momentum Oscillator (MOM) rising/falling in breakout direction
- ATR (14) starting to rise after squeeze (expansion confirmation)
- No large sell/buy walls in order book near TP
- Higher timeframe trend aligned with breakout direction
- Previous squeeze ended with a strong move (pattern repeats)

## When NOT to Enter
- BB Width > 3% — no squeeze, price already in trend
- False breakout: price breaks band but volume < 130% of average
- "Fake squeeze" — Width < 2% but only for 1-2 candles (too short)
- Key S/R level directly at upper/lower band
- Extreme funding rate in breakout direction (overcrowded)
- Market before important macro data (squeeze may be "calculated silence")
- ADX < 15 AND all recent breakouts ended in reversal

## Risk Management
- Risk per trade: 0.5-0.6% of capital (lower WR — control risk)
- Strategy has low WR but high R/R — you need 4+ trades to evaluate
- Do not double down after a loss (martingale forbidden)
- Max 1 open breakout position simultaneously
- If 3 squeeze breakouts in a row end in loss — pause strategy for 24h

## Setup Example
```
Token: AVAX, timeframe: 1h
BB (20, 2.0):
  Upper band: 28.90
  Middle (SMA 20): 28.50
  Lower band: 28.10
  BB Width = (28.90 - 28.10) / 28.50 = 2.81% → squeeze for 8 candles = 1.75% ✓

Breakout candle: close 29.05 (above upper band 28.90 ✓)
Volume: 167% of average ✓
RSI: 58 and rising ✓

Entry: 29.05
SL: close below 28.90 → ~28.85 (0.69% risk)
TP1: 29.50 (+1.5%) — close 30%
TP2: 30.00 (+3.3%) — close 40%
TP3: 30.60 (+5.3%) — close 30%
```

## Configuration Parameters
- `bb_period`: BB period (default 20)
- `bb_std`: BB standard deviation (default 2.0)
- `squeeze_width_pct`: max BB Width for squeeze (default 2.0%)
- `squeeze_min_candles`: min candles in squeeze (default 5)
- `volume_multiplier`: min volume vs average (default 1.5)
- `tp1_multiplier`: BB Width × multiplier for TP1 (default 1)
- `tp2_multiplier`: BB Width × multiplier for TP2 (default 2)
- `tp3_multiplier`: BB Width × multiplier for TP3 (default 3)
