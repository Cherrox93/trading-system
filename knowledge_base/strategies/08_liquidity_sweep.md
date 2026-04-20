# Liquidity Sweep (Stop Hunt)

## META
- Name: Liquidity Sweep
- Category: mean_reversion
- Difficulty: advanced
- Timeframes: 5m, 15m
- Best Market: any
- Estimated Win Rate: 57-64%
- Risk Reward: 1:2
- Tokens: any

## Description
Liquidity Sweep (also known as "stop hunt" or "liquidity grab") is when price briefly breaks an obvious swing high/low, "taking" the accumulated stop loss orders there, then immediately returns.
Market makers and large players deliberately direct price to areas where stop orders are concentrated, to fill their large positions at better prices.
A wick below swing low (or above swing high) with a quick return is the classic setup.

## Entry Conditions

### LONG (bottom sweep — sweeping long stop losses)
- Identify obvious swing low from the last 4-12 hours (clear level)
- Price penetrates swing low (wick below) and CLOSES above it
- Wick below swing low must be visible (min 0.3% below the level)
- Volume spike at sweep — >180% of average (market makers active)
- Candle after sweep: bullish, closing in upper half of range
- RSI at sweep < 40 (selling momentum exhausted)
- Sweep candle is "engulfing" or "pin bar" — clear formation

### SHORT (top sweep)
- Obvious swing high from the last 4-12 hours
- Price penetrates swing high (wick above) and closes below it
- Wick above swing high min 0.3% above the level
- Volume spike >180% of average
- Candle after sweep: bearish, closing in lower half of range
- RSI at sweep > 60

## Exit Conditions

### Take Profit
- Primary target: midpoint of range between sweep point and previous swing high (for LONG)
- Aggressive target: previous swing high (full reversal)
- Safe: 50% retracement from swing low to sweep candle high

### Stop Loss
- LONG: 0.2% below the sweep wick (absolute price minimum)
- SHORT: 0.2% above the wick
- Rule: SL should be BEHIND the wick — not at the level

### Trailing Stop
- After reaching 1% profit: trailing stop at low of last 3 candles

## Confirming Signals
- Liquidation data: spike in long liquidations at bottom sweep (confirms stop hunting)
- Funding rate jumps at sweep (indicates brief panic)
- CVD (Volume Delta) reverses immediately after sweep
- Higher timeframe (1h) shows bullish bias (for LONG sweep)
- Multiple obvious SL levels in one zone (e.g. round numbers: 1.2000, 1.2050)

## When NOT to Enter
- No clear volume spike at sweep (weak setup)
- Wick is small (<0.2% below level) — may be normal correction
- Price in strong downtrend (sweep may be continuation, not reversal)
- Sweep occurred at important fundamental data
- Previous sweep of the same level ended in continued decline
- Swing low is "new" (<2h ago) — too few SL orders accumulated there

## Risk Management
- Risk per trade: 0.5% of capital (precise SL = lower costs)
- This is a high-probability setup but requires fast execution
- Do not wait for "additional confirmation" — setup disappears quickly
- Max 2 sweep positions simultaneously
- If setup was good but TP not reached after 2h — consider closing

## Setup Example
```
Token: SOL, timeframe: 5m
Swing low from last 6h: 143.50
Situation:
- 5m candle: open 143.55, low 143.10, close 143.80
- Wick below 143.50: to 143.10 (−0.28% sweep ✓)
- Close 143.80 above swing low ✓
- Volume: 215% of average ✓
- RSI at low: 36 ✓

Entry: 143.80 (at close of sweep candle)
SL: 143.05 (0.2% under wick = 0.52% risk)
TP: midpoint 143.50-146.00 = 144.75 (+0.66%)
   or swing high 146.00 (+1.53%)
R:R basic: 1:1.3 (low but WR 60%+ = positive EV)
R:R aggressive: 1:2.1 ✓
```

## Configuration Parameters
- `swing_lookback_hours`: horizon for swing high/low (default 6h)
- `min_wick_pct`: min wick size (default 0.3%)
- `volume_spike_multiplier`: min volume vs average (default 1.8)
- `sl_buffer_pct`: buffer behind wick (default 0.2%)
- `rsi_threshold_long`: max RSI for LONG entry (default 40)
- `rsi_threshold_short`: min RSI for SHORT entry (default 60)
