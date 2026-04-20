# Keltner Channel + Bollinger Band Squeeze

## META
- Name: Keltner-Bollinger Squeeze (TTM Squeeze)
- Category: volatility_breakout
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: pre-breakout consolidation
- Estimated Win Rate: 60-67%
- Risk Reward: 1:3.0
- Tokens: any (best on high-vol alts)

## Description
The "Squeeze" occurs when Bollinger Bands (BB) move INSIDE Keltner Channels (KC) — indicating extreme volatility compression.
This is a coiling spring: low volatility precedes high volatility moves. When BBs expand outside KC, the squeeze fires.
The momentum histogram (based on MACD-style calculation) indicates direction of the breakout.
This strategy has an unusually high R:R because the move after a squeeze is typically explosive.

## Squeeze Detection
- **Squeeze ON** (red dots): BB inside KC → volatility compressed → coiling
- **Squeeze OFF** (green dots): BB expands outside KC → breakout imminent
- Momentum bar: positive and rising = bullish breakout; negative and falling = bearish

## Entry Conditions

### LONG — Bullish Squeeze Release
- Squeeze transitions from ON to OFF (BBs break outside KC)
- Momentum histogram is POSITIVE (above zero) and RISING
- Price closes above KC midline (EMA20)
- Volume surges > 150% of 20-bar average on breakout candle
- Higher timeframe (4h) is in uptrend

### SHORT — Bearish Squeeze Release
- Squeeze OFF fires
- Momentum histogram NEGATIVE and FALLING
- Price closes below KC midline
- Volume surge confirms

## Exit Conditions

### Take Profit
- Measured move: width of the consolidation range projected in breakout direction
- BB upper band as dynamic resistance (LONG)
- BB lower band as dynamic support (SHORT)
- Momentum histogram reversal (crossing zero line): take partial profits

### Stop Loss
- Re-entry into the squeeze zone (price closes back inside KC midline area)
- ATR(14) × 2.0 below the breakout candle low (LONG)
- Maximum 1.5% from entry

## Confirming Signals
- Squeeze lasted > 10 candles (longer = more energy stored = bigger breakout)
- Volume gradually declining during squeeze (distribution exhausted)
- RSI at 50-55 at breakout start (room to run in both directions)
- Open interest building during squeeze (positioning for breakout)

## When NOT to Enter
- Squeeze fires with low volume (false breakout risk high)
- Momentum histogram is flat or unclear direction
- Multiple failed squeezes in same zone recently
- News-driven squeeze: fundamentals can override technical setup

## Risk Management
- Risk per trade: 0.5-1.0% (tight SL enables larger position relative to expected move)
- Scale in: 70% on breakout candle close, 30% on first pullback to KC
- Set trailing stop at KC midline once +1.5% in profit

## Setup Example
```
Token: WLD, 1h chart
10-candle squeeze detected (BB inside KC for 10h)
Momentum histogram: +0.0042 and rising ✓
Breakout candle: closes above KC at $2.150, volume 180% ✓
EMA20: $2.120 (price above it ✓)

Entry: $2.155 (candle close)
SL: below KC midline = $2.090 → 3.0% risk... too wide
  → Use ATR method: ATR=0.032, SL = 2.155 − (0.032×2) = $2.091
  → Reduce position size: risk 0.8% / 3.0% SL = 0.27× normal size
TP: consolidation range was 2.05-2.15 = $0.10 width
  → TP = 2.15 + 0.10 = $2.25 (breakout measured move)
R:R: 0.10/0.064 = 1:1.6 — acceptable
```

## Configuration Parameters
- `bb_period`: 20, `bb_std`: 2.0 (Bollinger standard)
- `kc_period`: 20, `kc_atr_multiplier`: 1.5 (Keltner standard)
- `momentum_period`: 12 (histogram period)
- `min_squeeze_candles`: 8 (minimum squeeze length to enter)
- `volume_breakout_threshold`: 1.5 (volume multiplier on breakout)
