# Session Open Momentum

## META
- Name: Session Open Momentum
- Category: momentum
- Difficulty: intermediate
- Timeframes: 1m, 5m
- Best Market: volatile
- Estimated Win Rate: 50-56%
- Risk Reward: 1:2
- Tokens: large_cap

## Description
The first 5-15 minutes after the opening of a key trading session often feature increased volume and a clear directional move — "opening momentum".
Particularly significant sessions for cryptocurrencies: 08:00 UTC (Europe), 13:00 UTC (US pre-market), 21:00 UTC (Asia/daily reset).
Strategy based on identifying breakout of the overnight/previous range (Asia range) at session open with high volume.

## Entry Conditions

### LONG (bullish session open)
- Time: 07:55-08:05 UTC or 12:55-13:05 UTC (±5 minutes from open)
- Strong bullish candle in first 5 minutes: body >0.5% of price, close near high
- Volume of this candle >200% of average volume from the last hour
- Price breaks overnight high (Asia range high or last 8h high) with close above
- RSI on 5m: >55 and rising (bullish momentum)
- No major resistance within 1.5% above breakout

### SHORT (bearish session open)
- Time: ±5 minutes from key session open
- Strong bearish candle: body >0.5%, close near low
- Volume >200% of average
- Price breaks overnight low with close below
- RSI < 45 and falling

## Exit Conditions

### Take Profit
- Target 1: 1.5× overnight range (Asia range) projected from breakout point
- Target 2: key daily S/R beyond overnight range
- Alternative: close at next session open (time-based exit)

### Stop Loss
- LONG: low of breakout candle − 0.2% (tight — fast execution)
- SHORT: high of breakout candle + 0.2%
- Absolute: midpoint of overnight range

### Trailing Stop
- This strategy works fast — if no move after 30 minutes: close
- After reaching 1%: trailing stop at low of last 3 × 5m candles

## Confirming Signals
- Previous day at same time had a clear move (pattern repeats)
- Bitcoin/overall market moving in the same direction (market risk)
- Neutral funding rate before session open
- News/events before session (earnings, CPI, other catalysts)
- Pre-session volume: volume 30 minutes before session was low (accumulation)

## When NOT to Enter
- No clear move in first 5 minutes (flat open = no setup)
- Fundamental news published within last hour (changes context)
- Overnight range was very wide (>3%) — risk too high
- Volume < 180% of average (weak open)
- Token was already +3% before open (late — do not chase)
- Weekend trading (Friday-Sunday) — weaker pattern

## Risk Management
- Risk per trade: 0.4-0.5% of capital (smaller TF = smaller risk)
- Strategy is time-limited: max 2 entries per session
- Tight SL is critical — fast market pierces positions without warning
- Do not hold position through session close (no momentum after 2h)
- Daily limit: max 3 trades with this strategy

## Setup Example
```
Token: SOL, timeframe: 5m
Time: 08:00 UTC (London open)

Overnight range (00:00-08:00 UTC):
  Asia high: 145.80
  Asia low: 143.20
  Asia range: 2.60 (1.8%)

08:00 UTC candle:
  Open: 145.75
  Close: 146.40 (breakout above Asia high 145.80 ✓)
  Body: 0.45% ✓
  Volume: 235% of hourly average ✓
  RSI 5m: 62 and rising ✓

Entry: 146.40 (at close)
SL: 146.15 (candle low − 0.2% = 0.17% risk — VERY TIGHT)
  Alternative: 145.50 (Asia range midpoint = 0.62% risk)
TP1: Asia range × 1.5 = 145.80 + 3.90 = 149.70 (+2.26%)
TP2: daily resistance = 151.00 (+3.14%)
R:R with tight SL: 1:13 (unrealistic — use alternative SL 145.50)
R:R with alt SL: 1:2.7 ✓
```

## Configuration Parameters
- `session_times_utc`: session open times (default [8, 13, 21])
- `session_window_minutes`: window ±X minutes from open (default 10)
- `volume_spike_multiplier`: min volume vs hourly average (default 2.0)
- `body_min_pct`: min breakout candle body (default 0.5%)
- `asia_range_hours`: how many hours is "overnight range" (default 8)
- `max_position_minutes`: max position hold time (default 120)
- `sl_type`: 'candle_low' or 'range_mid' (default 'range_mid')
