# MACD Histogram Reversal

## META
- Name: MACD Histogram Reversal
- Category: momentum
- Difficulty: intermediate
- Timeframes: 15m, 1h
- Best Market: any
- Estimated Win Rate: 51-57%
- Risk Reward: 1:1.8
- Tokens: any

## Description
The MACD histogram (difference between the MACD line and signal line) shows the strength and direction of momentum.
Strategy enters when the histogram reaches extreme values (minimum or maximum from the last 20 candles) and starts reversing direction — signaling weakening dominant trend and upcoming move.
Histogram reversal at a key S/R level is a particularly effective setup.

## Entry Conditions

### LONG (histogram at minimum and reversing)
- MACD histogram reaches minimum from last 20 candles (new negative extreme)
- Next candle: histogram rises (becomes less negative or moves to positive)
- Price at key S/R, EMA or Pivot Level support
- EMA 9 and EMA 21 nearby (no huge distance — price not too far)
- RSI in range 30-50 (not overbought)
- Volume: at least neutral (not falling)

### SHORT (histogram at maximum and reversing)
- MACD histogram reaches maximum from last 20 candles
- Next candle: histogram falls (becomes less positive or negative)
- Price at key S/R resistance
- RSI in range 50-70
- Volume neutral or decreasing

## Exit Conditions

### Take Profit
- Target: MACD histogram at zero (zero line = no momentum in given direction)
- Price-wise: translate zero MACD to price level (where EMA 9 = EMA 21 = crossover)
- Alternative: previous swing in direction

### Stop Loss
- LONG: new price minimum from last 20 candles − 0.3%
- SHORT: new maximum + 0.3%
- If histogram makes a new extreme without reversing — close (setup invalidated)

### Trailing Stop
- After reaching 50% toward TP: trailing stop at Low/High of last 5 candles

## Confirming Signals
- RSI divergence at the same point (double reversal signal)
- Volume decreasing at extreme histogram (weakening momentum)
- Stochastic RSI at extreme levels (double overbought/oversold confirmation)
- Candle with long wick at extreme histogram (physical rejection)
- Higher timeframe shows same pattern (multi-TF alignment)

## When NOT to Enter
- Histogram at extreme level but has not yet reversed (wait for confirmation)
- Strong trend without any signs of slowing (MACD can stay extreme for long)
- New fundamental news triggered new momentum (MACD legitimizes move)
- ADX > 40 — momentum too strong for reversal
- Histogram reversed but price not confirmed (MACD leading, but wait for price)

## Risk Management
- Risk per trade: 0.5% of capital
- This strategy gives signals less frequently than EMA or VWAP — do not force it
- Max 2 MACD reversals open simultaneously
- If MACD histogram makes a new extreme after entry — close immediately

## Setup Example
```
Token: SOL, timeframe: 15m
MACD (12,26,9):
  MACD Line: −0.85
  Signal: −0.72
  Histogram: −0.13 (lowest of 20 candles)

Next candle:
  Histogram: −0.09 (rising → reversal ✓)
  Price: 143.80 (at EMA 21 = 143.65 ✓)
  RSI: 44 ✓

Entry: 143.90
SL: 142.50 (20-candle minimum − 0.3% = 0.97% risk)
TP: level where MACD = 0, EMA 9 = EMA 21 ≈ 145.50 (+1.11%)
R:R: 1:1.14 (may be too low — wait for better setup or extended TP)
Better TP: 146.50 (previous swing) = R:R 1:1.8 ✓
```

## Configuration Parameters
- `macd_fast`: fast MACD EMA (default 12)
- `macd_slow`: slow MACD EMA (default 26)
- `macd_signal`: signal line (default 9)
- `histogram_lookback`: candles for extreme comparison (default 20)
- `sl_buffer_pct`: buffer behind extreme (default 0.3%)
- `require_price_confirm`: require price confirming candle (default True)
