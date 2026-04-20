# Pin Bar Reversal

## META
- Name: Pin Bar Reversal
- Category: mean_reversion
- Difficulty: beginner
- Timeframes: 5m, 15m, 1h
- Best Market: any
- Estimated Win Rate: 55-61%
- Risk Reward: 1:2
- Tokens: any

## Description
Pin bar (also called Hammer or Shooting Star) is a candle with a long wick and small body, signaling price rejection from a certain level by the market.
Hammer (long lower wick) at support = bullish signal. Shooting Star (long upper wick) at resistance = bearish signal.
The wick must constitute at least 70% of the total candle range (high-low), and the body cannot be larger than 30%.
One of the simplest and most effective candlestick formations.

## Entry Conditions

### LONG (Hammer at support)
- Long lower wick: at least 70% of candle range (high-low)
- Small body: max 30% of candle range
- Body in upper half of candle (close near high)
- Candle at a key support level (S1, POC, EMA, historical S/R)
- Candle volume >120% of 20-candle average
- Next candle confirms (closes higher than high of previous) — optional but recommended

### SHORT (Shooting Star at resistance)
- Long upper wick: at least 70% of candle range
- Small body: max 30% of range
- Body in lower half of candle (close near low)
- At key resistance
- Volume >120% of average
- Confirmed by next candle (close below low of previous)

## Exit Conditions

### Take Profit
- TP1: 2× wick length projected from entry price
- TP2: next key S/R in position direction
- Alternative: R:R 1:2 (minimum)

### Stop Loss
- LONG: 0.2-0.3% below wick low (behind the "rejected" level)
- SHORT: 0.2-0.3% above wick high
- Rule: SL must be behind the wick, not at it

### Trailing Stop
- After reaching TP1: move SL to breakeven
- After reaching 75% toward TP2: trailing 0.3% behind price

## Confirming Signals
- S/R level has many historical touches (strong zone)
- RSI divergence at pin bar formation (additional confirmation)
- Wick volume > volume of several preceding candles (rejection with force)
- Higher timeframe identifies the same level as key
- Pin bar appears after a series of candles in one direction (at end of move)
- Wick broke a key level and returned (pin bar + liquidity sweep combination)

## When NOT to Enter
- Wick < 60% of candle range (formation too weak)
- Strong trend in wick direction (may be "exhaustion wick" before continuation)
- Pin bar appears in the middle of consolidation (not at a clear level)
- Multiple pin bars in a row without market reaction (level not respected)
- No confirming volume (wick without volume = less reliable)
- Bid/ask spread > 0.05% (wick may be a liquidity artifact)

## Risk Management
- Risk per trade: 0.5-0.6% of capital
- Strategy works on all timeframes — higher TF = more reliable signal
- Max 3 open pin bar positions simultaneously (on different tokens)
- Best to enter after next candle confirmation — reduces WR but increases certainty
- Daily limit: max 5 trades with this strategy

## Setup Example
```
Token: WLD, timeframe: 15m
Support level: 1.2100 (historical S/R, 4 previous touches)

Pin bar candle:
  Open: 1.2135
  High: 1.2160
  Low: 1.2055 (wick below support 1.2100 — sweep!)
  Close: 1.2145

Analysis:
  Range = 1.2160 − 1.2055 = 0.0105
  Lower wick = 1.2145 − 1.2055 = 0.0090 (85.7% of range ✓)
  Body = 1.2160 − 1.2145 = 0.0015 (14.3% of range ✓)
  Volume: 135% of average ✓

Entry: 1.2145 (at pin bar close)
SL: 1.2050 (0.2% under low = 0.78% risk)
TP1: 1.2145 + 2×0.0090 = 1.2325 (+1.48%)
TP2: next resistance 1.2400 (+2.10%)
```

## Configuration Parameters
- `wick_min_pct`: min wick % relative to range (default 70%)
- `body_max_pct`: max body % relative to range (default 30%)
- `volume_multiplier`: min volume vs average (default 1.2)
- `require_confirmation`: require next confirming candle (default False)
- `sl_buffer_pct`: buffer behind wick (default 0.25%)
- `tp1_wick_multiplier`: TP1 = wick × multiplier (default 2.0)
