# Open Interest Divergence

## META
- Name: Open Interest Divergence
- Category: hybrid
- Difficulty: advanced
- Timeframes: 1h, 4h
- Best Market: any
- Estimated Win Rate: 54-60%
- Risk Reward: 1:2
- Tokens: any

## Description
Open Interest (OI) measures the total number of open contracts in the futures/perpetual market.
OI and price divergence provides valuable information about the strength or weakness of the current move:
- OI rising + price rising = strong trend (new money entering long) — no setup here
- OI rising + price falling = weakening short trend (shorts adding but price not falling — potential squeeze)
- OI falling + price rising = weak rally (positions being closed = profit taking, not new buying)
- OI falling + price falling = capitulation (position closing = trend exhausting)

## Entry Conditions

### LONG (OI rising + price falling — bearish divergence → bullish reversal)
- OI increases for 3+ candles while price falls
- Negative funding rate (shorts paying = conviction to short)
- Price approaching key support S
- RSI < 40 (price oversold)
- Wick rejection or reversal candle at support
- Scenario: shorts will be "squeezed" when price bounces

### SHORT (OI rising + price rising — bullish divergence → bearish reversal)
- OI increases for 3+ candles while price rises
- High and positive funding rate (longs overpaying)
- Price at resistance R
- RSI > 60
- Scenario: longs will be "liquidated" when price falls

## Exit Conditions

### Take Profit
- Target: previous swing in opposite direction
- Or: close 50% when OI starts falling (de-risking)
- Short squeeze target: 5-10% above entry (aggressive move)

### Stop Loss
- LONG: new low from last 24h − 0.5%
- SHORT: new high + 0.5%
- Close if OI and price start moving in the same direction (divergence disappears)

### Trailing Stop
- After reaching 2% profit: trailing 0.8% behind price
- OI strategies have long horizon — trailing allows extracting maximum from squeeze

## Confirming Signals
- Extreme funding rate (>0.05% for long squeeze, <−0.05% for short squeeze)
- Liquidation volume rising (platform data)
- CVD reversing direction during divergence
- Higher timeframe confirms S/R level
- Divergence visible for >6h (longer = stronger)

## When NOT to Enter
- Divergence lasts <2 candles (sample too short)
- OI and price diverge but funding neutral (weak signal)
- No OI data for token (small token, small exchange)
- Last time divergence did not end in squeeze (check history)
- Fundamental news changed market sentiment

## Risk Management
- Risk per trade: 0.5-0.6% of capital
- Strategy requires OI data — verify availability before trading
- Squeezes are rare but powerful — expected value is positive
- Max 1 OI divergence trade simultaneously
- Horizon: 4-24h — be patient

## Setup Example
```
Token: SOL, timeframe: 1h
Last 4h:
  OI: 280M → 295M → 308M → 318M (+13.6% ↑)
  Price: 146.0 → 145.2 → 144.8 → 144.3 (−1.2% ↓)
  DIVERGENCE: OI↑ + price↓ ✓

Funding rate: −0.038% (shorts paying ✓)
RSI: 38 ✓
Support: 144.00 (historical S, 3 touches)

Scenario: shorts entering aggressively but price not continuing to fall
          → short squeeze likely

Entry: 144.35 (at support 144.00 after wick rejection)
SL: 143.30 (new 24h min − 0.5%)
TP: previous swing high = 147.50 (+2.2%)
R:R: 1:2.1 ✓
Expected trigger: squeeze at short liquidations above 144.50
```

## Configuration Parameters
- `oi_divergence_candles`: min divergence candles (default 3)
- `oi_change_pct`: min OI change for signal (default 5%)
- `funding_confirm`: require extreme FR (default True)
- `rsi_threshold_long`: max RSI for LONG (default 40)
- `rsi_threshold_short`: min RSI for SHORT (default 60)
- `sl_buffer_pct`: buffer behind 24h extreme (default 0.5%)
