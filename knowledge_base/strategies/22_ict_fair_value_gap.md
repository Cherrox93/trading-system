# ICT Fair Value Gap (FVG) Retest

## META
- Name: ICT Fair Value Gap Retest
- Category: mean_reversion
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: trending
- Estimated Win Rate: 56-64%
- Risk Reward: 1:2.0
- Tokens: any
- Source: ict_research
- Added: 2026-04-15

## Description
A Fair Value Gap (FVG) forms when price moves so aggressively
that a "gap" is left between candles — the middle candle creates
an imbalance where the high of the previous candle does not overlap
with the low of the next (or vice versa). The FVG represents a zone
where institutions placed large orders. The market often returns
to fill the FVG before continuing the trend.
This provides a precise entry in the direction of the main trend.

## Entry Conditions
BULLISH FVG (LONG entry):
- Uptrend confirmed on higher TF (4h or 1d)
- Identify bullish FVG: low of candle N+1 is higher
  than high of candle N-1 (gap between them)
- Price returns to the FVG (50% level of the gap or full range)
- Entry when price "tests" the lower range of the FVG
- Confirmation: bullish candle closing within the FVG or above it

BEARISH FVG (SHORT entry):
- Downtrend on higher TF
- High of candle N+1 is lower than low of candle N-1
- Price returns to the FVG from below
- Entry at the upper range of the FVG

## Exit Conditions
### Take Profit
Target: next FVG, swing high/low, or liquidity pool
on the correct side of the market.
Minimum: 2× risk.
If trend is strong: trailing stop behind subsequent FVGs.

### Stop Loss
Below/above the FVG (invalidates the gap).
If price closes fully beyond the FVG — setup is invalid.
Typically 0.3-0.6% from entry.

## Confirming Signals
- Order Block (OB) in the same area as the FVG
- RSI < 40 on bullish FVG (oversold at retest)
- Low ATR — market is not too volatile
- Neutral funding rate

## When NOT to Enter
- FVG is old (price has already been in that area after its
  formation — may be "mitigated")
- No clear trend on the higher TF
- FVG formed during a news event (less reliable)
- RSI at extreme in the direction of the FVG retest
  (e.g., RSI > 70 on bullish FVG retest)

## Risk Management
Risk per trade: 0.5-1.5% of capital.
Priority: FVG on a higher TF is more important
than FVG on a lower TF.
Do not enter an FVG that has already been partially filled
and rejected — indicates a weak zone.

## Setup Example
```
ETH in uptrend on 4h.
Strong bullish candle creates FVG: candle N-1 high=$3,100,
candle N+1 low=$3,200 (gap $3,100–$3,200).
Price rises to $3,400 then returns to $3,150 (FVG midpoint).
Bullish pin bar on 15m within the FVG. Entry LONG @ $3,150.
SL @ $3,090 (below FVG), TP @ $3,400 (previous high).
R:R = 1:4.
```

## Configuration Parameters
- `fvg_min_size`: minimum gap size in % of price (default 0.2%)
- `fvg_entry_level`: entry at 50% or 100% of FVG (default 50%)
- `fvg_max_age`: maximum FVG age in candles (default 50)
- `trend_confirmation_tf`: timeframe for trend confirmation
  (default 4h)
