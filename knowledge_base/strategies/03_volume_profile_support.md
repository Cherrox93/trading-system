# Volume Profile Support/Resistance

## META
- Name: Volume Profile Support/Resistance
- Category: volume
- Difficulty: intermediate
- Timeframes: 15m, 1h
- Best Market: any
- Estimated Win Rate: 52-58%
- Risk Reward: 1:1.8
- Tokens: large_cap

## Description
Strategy based on high-volume transaction zones (Volume Profile) — levels where historically the most trades were executed.
Point of Control (POC) is the price with the highest volume, Value Area High (VAH) and Value Area Low (VAL) are the upper and lower boundaries of 70% of volume.
Price returns almost magnetically to these zones, especially to the POC.

## Entry Conditions

### LONG (at VAL or POC from below)
- Price returns to VAL or POC after a previous breakout upward
- Order imbalance on the buy side (>55% of bid vs ask volume in 5-minute window)
- Closing candle above VAL/POC after retest
- Neutral funding rate (−0.02% to +0.02%)
- RSI (14) in range 40-50 (not oversold — clean retest, not panic)
- Retest candle volume < breakout candle volume (lower selling pressure)

### SHORT (at VAH or POC from above)
- Price returns to VAH or POC after a previous breakout downward
- Order imbalance on the sell side (>55% of ask vs bid volume)
- Closing candle below VAH/POC after retest
- Neutral funding rate
- RSI (14) in range 50-60

## Exit Conditions

### Take Profit
- LONG from VAL: target VAH (upper Value Area boundary)
- LONG from POC: target VAH (50% of Value Area distance upward)
- SHORT from VAH: target VAL
- SHORT from POC: target VAL
- Alternative: close 50% at POC, rest at VAH/VAL

### Stop Loss
- LONG: 0.3% below VAL (under volume zone)
- SHORT: 0.3% above VAH
- When entering from POC: SL = 0.4% outside Value Area

### Trailing Stop
- After reaching 50% of VAL→VAH distance: trailing 0.3% behind price

## Confirming Signals
- Multiple historical candles "bounced" from the same POC/VAH/VAL
- Volume delta (buy vs sell) in the zone aligned with direction
- Open Interest not rising during retest (no new positions against us)
- Wick rejections at VAL/VAH from previous sessions
- Level coincides with classic S/R (double confirmation)

## When NOT to Enter
- Price in Low Volume Node (LVN) — low-volume zones are "transparent" to price
- Volume Profile calculated from <24h of data (sample too small)
- Token 24h volume < 5M USD (too low liquidity for VP reading)
- Major fundamental news changed market context
- POC shifted significantly (>1%) in the last 2h (dynamic market)
- ADX > 35 — strong trend destroys Volume Profile structure

## Risk Management
- Risk per trade: 0.5% of capital (more cautious than other strategies — requires experience)
- Minimum token liquidity: 5M USD 24h volume
- Do not enter if Value Area width < 0.5% (zone too tight)
- Max 2 open positions simultaneously
- If price broke VAL/VAH with high volume — do not trade retests

## Setup Example
```
Token: WLD, timeframe: 1h
Volume Profile (last 24h):
  POC = 1.2400
  VAH = 1.2650
  VAL = 1.2150

LONG scenario:
- Price drops to 1.2155 (VAL ✓ tolerance ±0.3%)
- Order imbalance: 62% bid (buy pressure ✓)
- Funding rate: +0.008% (neutral ✓)
- RSI: 46 (neutral ✓)
- Candle closed 1.2175 above VAL ✓

Entry: 1.2175
SL: 1.2115 (−0.5% under VAL) = 0.49% risk
TP: VAH = 1.2650 (+3.9%) or POC = 1.2400 (+1.8%)
```

## Configuration Parameters
- `value_area_pct`: % of volume for Value Area (default 70%)
- `tolerance_pct`: price tolerance at VAH/VAL/POC (default 0.3%)
- `imbalance_threshold`: min % imbalance on one side (default 55%)
- `sl_buffer_pct`: SL buffer outside Value Area (default 0.3%)
- `vp_period_hours`: Volume Profile calculation period (default 24h)
- `min_volume_24h`: minimum token liquidity (default 5,000,000 USD)
