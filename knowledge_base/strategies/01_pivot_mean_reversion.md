# Pivot Point Mean Reversion

## META
- Name: Pivot Point Mean Reversion
- Category: mean_reversion
- Difficulty: beginner
- Timeframes: 5m, 15m
- Best Market: ranging
- Estimated Win Rate: 54-60%
- Risk Reward: 1:1.5
- Tokens: any

## Description
Strategy assumes price returns to the central Pivot Point (PP) after rejection from support S1 or resistance R1 levels.
Pivot levels calculated from the daily (or 4h) candle serve as magnetic zones to which price statistically returns in 60-70% of cases.
Entry occurs at a wick rejection from S1 or R1 with volume and RSI confirmation.

## Entry Conditions

### LONG (from S1)
- Price touches S1 ±0.3% (tolerance for slippage)
- Closing candle forms a rejection wick — lower wick >60% of total candle height
- RSI (14) < 35 at S1 touch (oversold)
- Rejection candle volume >120% of 20-candle average
- Candle closing price above S1

### SHORT (from R1)
- Price touches R1 ±0.3%
- Closing candle forms a rejection wick — upper wick >60% of total candle height
- RSI (14) > 65 at R1 touch (overbought)
- Rejection candle volume >120% of 20-candle average
- Candle closing price below R1

## Exit Conditions

### Take Profit
- Target: central Pivot Point (PP) — return to mid-range
- Alternative: 50% of the distance between S1 and PP (safer target)
- If PP reached — move SL to breakeven and wait for full move

### Stop Loss
- LONG: 0.4% below S1 level (under rejection wick)
- SHORT: 0.4% above R1 level
- Absolute maximum: 0.7% (risk_per_trade from database)

### Trailing Stop
- After reaching 50% toward TP: move SL to breakeven
- After reaching 75% toward TP: trailing 0.2% behind price

## Confirming Signals
- Bullish/bearish engulfing at S1/R1 (stronger signal than pin bar alone)
- Order book: large buy orders at S1 / sell orders at R1 visible in order book
- Neutral funding rate (−0.01% to +0.01%) — no single-side dominance
- Previous test of S1/R1 level ended with identical rejection
- Higher timeframe (1h) confirms that S1/R1 is a key level

## When NOT to Enter
- ADX > 30 — strong trend, mean reversion fails
- Macro news within 30 minutes (check economic calendar)
- Funding rate > 0.05% or < −0.05% — overcrowded trade
- Previous 2 attempts from S1/R1 ended in a break (level "broken")
- Bid/ask spread > 0.05% (entry too expensive)
- Token 24h volume < 1M USD (too low liquidity)
- Price moving with strong impulse without retests (breakout mode)

## Risk Management
- Risk per trade: 0.5-0.7% of capital (risk_per_trade)
- Position size: risk_usdt / (entry_price − sl_price)
- Max 1 open position on this strategy simultaneously
- Do not enter if used_usdt > 80% budget_usdt
- Daily loss limit: −2% of capital → stop trading for today

## Setup Example
```
Token: WLD, price 1.2345
Daily pivot: PP=1.2400, R1=1.2600, S1=1.2100
LONG scenario:
- Price drops to 1.2105 (S1 ±0.3% ✓)
- 15m candle closed 1.2140, lower wick to 1.2098 (wick >60% ✓)
- RSI(14) = 32 (oversold ✓)
- Volume 145% of average (✓)
Entry: 1.2140
SL: 1.2098 × 0.996 = 1.2051 (0.73% risk — acceptable)
TP: PP = 1.2400 (R/R = 1:2.2 ✓)
```

## Configuration Parameters
- `pivot_tolerance_pct`: price tolerance at S/R (default 0.3%)
- `wick_rejection_min`: minimum wick % (default 60%)
- `rsi_oversold`: RSI threshold for LONG (default 35)
- `rsi_overbought`: RSI threshold for SHORT (default 65)
- `volume_multiplier`: minimum volume vs average (default 1.2)
- `sl_buffer_pct`: buffer behind S/R level (default 0.4%)
- `tp_partial_pct`: % toward TP for partial close (default 50%)
