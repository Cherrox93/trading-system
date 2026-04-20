# ICT Liquidity Grab Reversal

## META
- Name: ICT Liquidity Grab Reversal (Stop Hunt)
- Category: mean_reversion
- Difficulty: intermediate
- Timeframes: 5m, 15m, 1h
- Best Market: volatile
- Estimated Win Rate: 54-62%
- Risk Reward: 1:2.5
- Tokens: any
- Source: ict_research
- Added: 2026-04-15

## Description
Strategy based on a core ICT principle: institutions deliberately push price
above/below obvious levels (swing highs/lows, equal highs/lows) to trigger
retail traders' stop-losses and collect liquidity. After liquidity is collected,
price reverses sharply toward the true institutional move. Identifying this
moment provides an entry with a very favorable R:R.

## Entry Conditions
- Identify a clear liquidity level: equal highs, swing high/low,
  or a psychological round number level
- Price moves above (buy-side liquidity) or below
  (sell-side liquidity) that level — triggering stop-losses
- Immediate reversal — long wick piercing the level
  without the candle closing above/below it
- CHoCH or BOS appears on the lower timeframe (5m) after
  the sweep on the higher TF (15m/1h)
- Entry on close of the first reversal candle after the sweep

## Exit Conditions
### Take Profit
Next liquidity level on the opposite side of the market.
Target: opposite liquidity pool, Fair Value Gap,
or previous swing high/low before the sweep.
Minimum target: 2× risk (R:R 1:2).

### Stop Loss
Above/below the highest point of the sweeping wick
(beyond the extreme point of the liquidity grab).
Typically 0.3-0.8% from entry depending on ATR.

## Confirming Signals
- Funding rate neutral or opposite to the swept direction
- Volume spike at the moment of sweeping
- RSI divergence (price at new extreme, RSI does not confirm)
- Fair Value Gap (FVG) visible on the lower TF after the sweep

## When NOT to Enter
- No clear, obvious liquidity level before the sweep
- Price closed above/below the swept level
  (may be a genuine breakout, not a sweep)
- High-impact news within 15 minutes
- Spread > 0.05% (too wide for precise entry)
- No confirming volume for the move

## Risk Management
Risk per trade: 0.5-1.0% of capital.
Maximum leverage: 3×.
Never average a losing position after a liquidity grab —
if price continues the sweep, the setup is invalid.
Close if there is no reversal within 3 × 15m candles.

## Setup Example
```
BTC forms equal highs at $65,000 for 4 hours.
Retail traders place SL above $65,000.
Price moves to $65,150 (sweep), wick on 15m.
No close above $65,000 — candle closed at $64,900.
Entry SHORT @ $64,900, SL @ $65,200, TP @ $64,000.
R:R = 1:3. ICT Liquidity Grab setup confirmed.
```

## Configuration Parameters
- `liquidity_lookback`: number of candles back to search for
  equal highs/lows (default 20)
- `wick_threshold`: minimum wick above the level in % (default 0.1%)
- `confirmation_candles`: how many candles after the sweep to wait for
  confirmation (default 1-2)
- `min_rr`: minimum R:R to enter (default 2.0)
