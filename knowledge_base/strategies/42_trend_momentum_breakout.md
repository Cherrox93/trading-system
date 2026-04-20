# Trend Momentum Breakout

## META
- Name: Trend Momentum Breakout
- Category: trend_following
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: trending (not range/sideways)
- Estimated Win Rate: 48-55%
- Risk Reward: 1:3 (let winners run)
- Tokens: BTC, ETH, high-liquidity alts

## Description
Captures strong directional moves by entering on breakouts from consolidation when momentum confirms trend continuation.
Opposite of reversal strategies — this strategy assumes the trend continues, not reverses.
High importance in trending markets where reversal strategies fail repeatedly.

## Entry Conditions

### LONG (upward breakout)
- Price forms consolidation (range ≤ 1.5% width) for minimum 8 candles on 15m or 4 candles on 1h
- Breakout candle closes ABOVE consolidation high with strong body (body ≥ 60% of candle range)
- Volume on breakout candle ≥ 200% of 20-period average
- EMA20 > EMA50 > EMA200 (all aligned upward = confirmed uptrend)
- RSI between 55-75 at breakout (momentum but not extreme overbought)
- ADX(14) > 25 — confirms existing trend strength before breakout
- No major resistance within 1.5× SL distance above entry

### SHORT (downward breakout)
- Consolidation of ≥ 8 candles, range ≤ 1.5%
- Breakout candle closes BELOW consolidation low, strong bearish body ≥ 60%
- Volume ≥ 200% average
- EMA20 < EMA50 < EMA200 (all aligned downward)
- RSI between 25-45 at breakout
- ADX(14) > 25

## Exit Conditions

### Take Profit
- TP1 (partial, 50% position): 1× ATR(14) from entry
- TP2 (remaining 50%): 3× ATR(14) from entry OR next major S/R level
- Let TP2 run with trailing stop after TP1 hit

### Stop Loss
- SL: below consolidation low (LONG) or above consolidation high (SHORT)
- Add 0.3% buffer beyond the structure
- SL distance should be ≤ 1.5% for scalp, ≤ 3% for swing

### Trailing Stop (after TP1 hit)
- Trail at EMA20 on entry timeframe — close if price closes below EMA20 (LONG)
- Or trail at 1.5× ATR below highest price reached

## Confirming Signals
- Higher timeframe (4h/1d) trend matches breakout direction
- Increasing OI (open interest) on breakout — new money entering
- CVD positive and rising during breakout candle
- No funding rate extreme (avoid breakouts when funding > 0.05%)
- Price held above broken consolidation for ≥ 2 candles (retest confirms)

## When NOT to Enter
- ADX < 20 at time of breakout — not a trending market, likely false breakout
- EMAs tangled or against breakout direction
- Breakout into major HTF resistance (daily/weekly level)
- Volume during consolidation was declining significantly (low interest)
- Previous 2+ breakouts in same direction failed (resistance is real)
- Funding rate extreme (>0.05% or <-0.05%) — crowded trade

## Risk Management
- Risk per trade: 0.75% of capital (higher R:R compensates lower WR)
- Never chase breakout more than 0.5% above consolidation top
- If price returns inside consolidation after breakout → immediate exit (false breakout)
- Max 2 trend-following positions simultaneously

## Setup Example
```
Token: ETH, timeframe: 15m
Scenario: 10-candle consolidation between 3,450 and 3,500
EMAs: 3,440 < 3,465 < 3,480 (all aligned up ✓)
ADX(14): 31 ✓
Volume on breakout: 230% average ✓
RSI at breakout: 62 ✓

Entry: 3,502 (just above consolidation)
SL: 3,447 (below consolidation low − 0.3% buffer = −1.57%)
TP1: 3,502 + ATR(3,050-3,502 range, ATR≈35) = 3,537 (+1.0%)
TP2: 3,502 + 3×35 = 3,607 (+3.0%)
R:R TP2: 1:1.9 on full position, 1:3.1 on half position
```

## Configuration Parameters
- `consolidation_candles_min`: 8 (15m), 4 (1h)
- `consolidation_range_max_pct`: 1.5
- `breakout_body_min_pct`: 0.60
- `volume_breakout_multiplier`: 2.0
- `adx_min`: 25
- `rsi_long_range`: [55, 75]
- `rsi_short_range`: [25, 45]
- `sl_buffer_pct`: 0.3
- `tp1_atr_multiplier`: 1.0
- `tp2_atr_multiplier`: 3.0
