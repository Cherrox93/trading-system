# Inside Bar Breakout

## META
- Name: Inside Bar Breakout
- Category: breakout
- Difficulty: intermediate
- Timeframes: 15m, 1h
- Best Market: trending
- Estimated Win Rate: 48-55%
- Risk Reward: 1:2
- Tokens: any

## Description
Inside Bar is a candle (or series of candles) whose range (high-low) fits entirely within the range of the previous candle ("mother bar").
It signals temporary equilibrium and energy compression — the market pauses before a decisive move.
Breakout from inside bar in the direction of the overarching trend is a trend-following strategy with a precise entry.
Works best when the inside bar is preceded by a strong impulse (mother bar has a clearly defined body).

## Entry Conditions

### LONG (inside bar breakout upward)
- Clear mother bar with bullish body (body >50% of range) or after strong bullish impulse
- Inside bar: high <= mother bar high AND low >= mother bar low (fully inside)
- Up to 2-3 consecutive inside bars allowed (double/triple IB = stronger setup)
- Price breaks high of inside bar / mother bar with close above
- Breakout candle volume >130% of average
- ADX > 20 (trend present) — do not enter in ranging market
- Overarching trend (higher TF): bullish

### SHORT (inside bar breakout downward)
- Mother bar with bearish body or after strong bearish impulse
- Inside bar inside mother bar
- Price breaks low with close below
- Volume >130% of average
- ADX > 20, overarching trend: bearish

## Exit Conditions

### Take Profit
- Method 1: 1.5× inside bar range projected from breakout
- Method 2: mother bar high/low projected (for 50%) + next swing (for rest)
- Method 3: R:R 1:2 from SL

### Stop Loss
- LONG: mid-point of inside bar (50% between high and low of inside bar)
- Alternative: low of inside bar − 0.2%
- SHORT: mid-point of inside bar or high + 0.2%

### Trailing Stop
- In strong trend: trailing stop at low of previous candle (for LONG)
- After reaching R:R 1:1: move SL to breakeven

## Confirming Signals
- Pullback entry: price returns to inside bar high after breakout (retest), enter on confirmation
- EMA 9 and 21 aligned with direction (EMA9 > EMA21 for LONG)
- Inside bar at key S/R that was just broken (breakout + IB = strong setup)
- Neutral funding rate (not overcrowded)
- Mother bar is clearly large relative to previous candles (high momentum)

## When NOT to Enter
- ADX < 20 — no trend, inside bar in ranging → false signals
- Inside bar lasts >8 candles on 15m (too long — this is already consolidation, use different strategy)
- Wick-only breakout (not a close)
- Key S/R directly at target (1.5× IB range)
- Macro news active
- Mother bar has very small body (<30% of range) — weak impulse

## Risk Management
- Risk per trade: 0.5% of capital
- SL at mid-point gives narrower SL = larger position at same risk
- If price returns to mid-point IB after entry — close (setup invalidated)
- Max 2 IB breakouts simultaneously
- This strategy works best on pullback entry (retest) — patience pays off

## Setup Example
```
Token: ARB, timeframe: 1h
Trend: bullish (EMA9 > EMA21 > EMA50 ✓)
ADX: 27 ✓

Mother bar: bullish (open 1.80, close 1.87, body 3.9% ✓)
Inside bar: high 1.870, low 1.852 (range = 0.018 = 0.96%)
  IB inside MB ✓

Breakout candle: close 1.875 (above IB high 1.870 ✓)
Volume: 141% of average ✓

Entry: 1.875
SL: mid-point IB = 1.861 (0.75% risk)
  or low IB − 0.2% = 1.850 (1.34% — too wide)
TP: 1.875 + 1.5×0.018 = 1.902 (+1.44%, R:R 1:1.9 ✓)
Or next swing: 1.920 (+2.4%, R:R 1:3.2 ✓)
```

## Configuration Parameters
- `ib_max_candles`: max inside bar candles (default 3)
- `mother_bar_min_body_pct`: min mother bar body (default 50%)
- `adx_min`: min ADX (default 20)
- `volume_multiplier`: min breakout volume (default 1.3)
- `sl_type`: 'midpoint' or 'low_ib' (default 'midpoint')
- `tp_multiplier`: TP = IB range × multiplier (default 1.5)
