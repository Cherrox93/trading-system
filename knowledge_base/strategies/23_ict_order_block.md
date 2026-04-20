# ICT Order Block Entry

## META
- Name: ICT Order Block (OB) Retest
- Category: mean_reversion
- Difficulty: advanced
- Timeframes: 15m, 1h, 4h
- Best Market: trending
- Estimated Win Rate: 52-60%
- Risk Reward: 1:3.0
- Tokens: large_cap
- Source: ict_research
- Added: 2026-04-15

## Description
An Order Block (OB) is the last opposing candle before a strong
institutional move. It represents where institutions placed massive
orders — these orders often remain "active" and price returns to that
zone to fill them before continuing. A Bullish OB is the last bearish
candle before a strong rally. A Bearish OB is the last bullish candle
before a strong decline. This is one of the strongest S/R zones in ICT.

## Entry Conditions
BULLISH OB (LONG entry):
- Identify the last bearish (red) candle directly
  before a strong bullish impulsive candle (displacement)
- Open/Close of that bearish candle = Bullish Order Block
- Price returns to the OB zone (open of that candle or its midpoint)
- Entry on OB test with confirmation on the lower TF
- Displacement after OB must break at least one swing high

BEARISH OB (SHORT entry):
- Last bullish candle before a strong bearish displacement
- Price returns to that zone from below
- Entry on test with bearish confirmation

## Exit Conditions
### Take Profit
Next liquidity zone: equal highs/lows, FVG,
previous swing high/low, or next OB on the correct side.
Minimum 3× risk for OB on 1h/4h.

### Stop Loss
Below/above the entire Order Block (beyond the zone).
Invalidation: if price closes through the full OB.
Typically 0.4-1.0% from entry.

## Confirming Signals
- FVG in the same area as the OB (confluence)
- Liquidity sweep before OB retest (additional confidence)
- CHoCH or BOS on the lower TF at the retest
- Volume higher than average at the displacement creating the OB

## When NOT to Enter
- OB is "mitigated" — price has passed through it multiple times
  (loses validity)
- No clear displacement after the OB (move must be strong)
- OB on lower TF contradicts the trend on the higher TF
- Funding rate extremely positive/negative
  (> 0.05% or < −0.05%)

## Risk Management
Risk per trade: 0.5-1.0% of capital.
OB on higher TF (4h, 1d) carries more weight.
Strongest setup: OB + FVG + Liquidity Sweep
in the same area (Triple Confluence).
Close half position at 1.5R, trail the rest
to target.

## Setup Example
```
SOL in uptrend on 4h. Strong bullish candle
($140→$155, displacement) preceded by a bearish candle
($143→$138 open/close). OB identified: $138–$143.
Price returns to $140 (OB midpoint). Bullish CHoCH on 15m.
Entry LONG @ $140, SL @ $137.5 (below OB),
TP @ $158 (next equal highs). R:R = 1:7.
```

## Configuration Parameters
- `displacement_threshold`: minimum displacement candle size
  in % (default 1.0%)
- `ob_entry_level`: entry at 50% or 100% of OB (default 50%)
- `mitigation_count`: max times OB can be tested
  (default 2)
