# Breakout from Consolidation Box

## META
- Name: Breakout from Consolidation Box
- Category: breakout
- Difficulty: beginner
- Timeframes: 15m, 1h
- Best Market: any
- Estimated Win Rate: 47-54%
- Risk Reward: 1:2
- Tokens: any

## Description
Strategy based on identifying horizontal consolidation (box/rectangle pattern) — a zone where price moves between clear support and resistance levels, bouncing multiple times.
After at least 3 touches of each level, price accumulates energy for a clear breakout.
Entry occurs when the upper (bullish breakout) or lower (bearish breakout) box level is broken with confirmed volume.

## Entry Conditions

### LONG (upper breakout)
- Identify box: min 3 touches of upper level AND min 3 touches of lower level
- Box must last at least 6 candles on the used timeframe
- Price breaks upper level and CLOSES above it (not just a wick)
- Breakout candle volume >150% of 20-candle average
- RSI (14) < 70 (not overbought at entry)
- Higher timeframe trend: bullish or neutral (not aggressively short)

### SHORT (lower breakdown)
- Box with min 3 touches of each level for min 6 candles
- Price breaks lower level with close below
- Volume >150% of average
- RSI (14) > 30
- Higher trend: bearish or neutral

## Exit Conditions

### Take Profit
- "Measured move" method: TP = box width projected from breakout point
- Example: box 1.2000-1.2500, upper breakout at 1.2500 → TP = 1.3000
- TP1 (50% of position): 50% of box height
- TP2 (50% of position): 100% of box height (full measured move)

### Stop Loss
- Retest: close back inside the box (candle closed behind upper level)
- Absolute SL: midpoint of box (if price returns to center — setup invalidated)
- Tight SL: 0.3% below upper box level

### Trailing Stop
- After reaching TP1: trailing at breakout level (upper box level becomes support)
- If retest of breakout level with buy volume — add to position (pullback entry)

## Confirming Signals
- Decreasing volume during consolidation (coiling before breakout)
- BB width decreasing during box (squeeze)
- Breakout confirmed on higher timeframe (1h box + 15m breakout entry)
- Fundamental catalysts coinciding with breakout (upgrade, news)
- Previous breakout from similar box on this token was successful

## When NOT to Enter
- Box has fewer than 3 touches of each level (consolidation too weak)
- Wick-only breakout (not a close) — fake breakout
- Breakout volume < 130% of average (weak conviction)
- Box formed in <2h (consolidation too short)
- Key S/R outside box within 0.5× box width (will block TP)
- Macro news may reverse breakout

## Risk Management
- Risk per trade: 0.5-0.6% of capital
- Win rate of this strategy is 47-54% — R:R must be minimum 1:2
- Pullback entry (retest of upper level after breakout) > direct breakout entry
- Max 2 open breakout positions simultaneously
- Do not enter breakout that occurred >3 candles ago (late entry)

## Setup Example
```
Token: AVAX, timeframe: 1h
Box: 27.50 (lower) — 29.00 (upper)
Box height: 1.50 = 5.45%
Upper level touches: 4 ✓
Lower level touches: 4 ✓
Consolidation time: 16h ✓

Breakout candle: close 29.15 (0.5% above upper ✓)
Volume: 162% of average ✓
RSI: 55 ✓

Entry: 29.15
SL: 28.70 (0.3% under upper box level = 1.55% risk) — too wide?
  → Tight SL: 28.95 (0.3% under upper ✓) = 0.69% risk
TP1: 29.00 + 0.75 = 29.75 (+2.1%) — close 50%
TP2: 29.00 + 1.50 = 30.50 (+4.6%) — close 50%
```

## Configuration Parameters
- `box_min_touches`: min touches of each level (default 3)
- `box_min_candles`: min consolidation candles (default 6)
- `volume_multiplier`: min breakout volume vs average (default 1.5)
- `sl_type`: 'tight' (0.3% under level) or 'mid' (box midpoint) (default 'tight')
- `tp1_fraction`: fraction of box for TP1 (default 0.5)
- `tp2_fraction`: fraction of box for TP2 (default 1.0)
- `tolerance_pct`: tolerance for box definition (default 0.2%)
