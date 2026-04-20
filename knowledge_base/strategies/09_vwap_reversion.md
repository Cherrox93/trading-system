# VWAP Reversion

## META
- Name: VWAP Reversion
- Category: mean_reversion
- Difficulty: beginner
- Timeframes: 5m, 15m
- Best Market: ranging
- Estimated Win Rate: 53-58%
- Risk Reward: 1:1.5
- Tokens: large_cap

## Description
VWAP (Volume Weighted Average Price) is the average transaction price weighted by volume, calculated from session open.
It is widely used by institutions as a "fair value" price benchmark — price statistically returns to VWAP after deviation.
Strategy enters when price deviates >1.5% from VWAP and shows signs of return, targeting the VWAP itself as TP.

## Entry Conditions

### LONG (price below VWAP — return upward)
- Price is > 1.5% below VWAP
- RSI (14) < 40 (oversold on short TF)
- Volume decreasing as price moves further from VWAP (no conviction for continued decline)
- Candle forms a pin bar or bullish engulfing at distance from VWAP
- No strong fundamental catalyst for continuation of move

### SHORT (price above VWAP — return downward)
- Price is > 1.5% above VWAP
- RSI (14) > 60
- Volume decreasing as price rises (buyers losing strength)
- Candle forms pin bar or shooting star at extreme
- Neutral or slightly positive funding rate (not overcrowded)

## Exit Conditions

### Take Profit
- Target: VWAP (return to fair value)
- Alternative: half the distance to VWAP (safer target, faster TP)
- Close if VWAP is reached, do not hold further (VWAP is the limit)

### Stop Loss
- LONG: new session (daily) minimum − 0.3%
- SHORT: new session maximum + 0.3%
- Time stop: if after 45 minutes price has not moved toward VWAP — close

### Trailing Stop
- No trailing stop — simple strategy: TP=VWAP, SL=new extreme
- Exception: if price crossed VWAP, trailing stop 0.3% behind VWAP

## Confirming Signals
- VWAP bands: price outside 2× standard deviation from VWAP (stronger signal)
- Other tokens at VWAP at the same time (market reset, not just one token)
- Asian or European session (calmer market, VWAP more respected)
- No big news within 1h
- Volume at VWAP touch larger than at deviation (institutions buying at VWAP)

## When NOT to Enter
- Price deviated for <30 minutes — too short, may be continuation
- Strong fundamental news causing re-pricing (VWAP will lose significance)
- Price was at VWAP within the last 15 minutes (distance too small)
- Extreme funding rate (>0.05%) — overcrowded trade may push further
- Weekly/monthly market close — higher volatility, VWAP less stable
- VWAP calculated from <2h of data (session too young)

## Risk Management
- Risk per trade: 0.4-0.5% of capital (frequent strategy — lower risk)
- Max 2 VWAP positions simultaneously (can be on different tokens)
- Daily limit: max 6 trades with this strategy
- Time stop is important — do not hold a position that "gets stuck"
- If VWAP starts falling/rising fast — setup invalidated

## Setup Example
```
Token: WLD, timeframe: 5m, 14:00 UTC
Session VWAP: 1.2500
Current price: 1.2312 (−1.51% from VWAP ✓)
RSI: 38 ✓
Volume last 5 candles: decreasing ✓
Candle: pin bar at 1.2300 ✓

Entry: 1.2315
SL: 1.2200 (new session minimum − 0.3% = 0.93% risk)
TP: VWAP = 1.2500 (+1.5%, R:R 1:1.6 ✓)
Time stop: 14:45 UTC (30 minutes)
```

## Configuration Parameters
- `vwap_deviation_min_pct`: min deviation from VWAP for signal (default 1.5%)
- `vwap_deviation_strong_pct`: strong signal (default 2.5%)
- `rsi_oversold`: RSI threshold for LONG (default 40)
- `rsi_overbought`: RSI threshold for SHORT (default 60)
- `time_stop_minutes`: max position hold time (default 45)
- `vwap_min_age_minutes`: min VWAP age (default 120)
