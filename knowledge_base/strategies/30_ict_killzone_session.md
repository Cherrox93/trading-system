# ICT Kill Zone Session Trading

## META
- Name: ICT Kill Zone — London and New York Session Entry
- Category: momentum
- Difficulty: intermediate
- Timeframes: 5m, 15m
- Best Market: any
- Estimated Win Rate: 55-65%
- Risk Reward: 1:2.0
- Tokens: large_cap
- Source: ict_research
- Added: 2026-04-15

## Description
ICT Kill Zones are specific time windows when institutional activity
is highest and setups have the greatest probability. The three main
Kill Zones are: London Open (02:00–05:00 UTC), New York Open
(13:30–16:00 UTC), and London Close (19:00–20:00 UTC).
The crypto market runs 24/7 but these windows still have higher
activity due to global traders and algorithms based on traditional
market sessions. The best ICT setups appear DURING Kill Zones.

## Entry Conditions
LONDON KILL ZONE (02:00–05:00 UTC):
- Check the direction of the previous day (Previous Day High/Low)
- London Open often sweeps the Previous Day High/Low
- Look for liquidity grab + FVG/OB in the first 30-60 minutes
- Entry aligned with the bias derived from Previous Day structures

NEW YORK KILL ZONE (13:30–16:00 UTC):
- Most important window — highest volume
- Often reverses or continues the London trend
- Check: did London perform a sweep and reversal?
  If yes — NY continues the reversal
- If London was trending — look for retrace to OTE
  during NY open and continuation

LONDON CLOSE (19:00–20:00 UTC):
- Often sweeps NY session levels before close
- Small moves, smaller positions

## Exit Conditions
### Take Profit
Intra-session target: Previous Day High/Low,
Asia session high/low, or a clear liquidity zone.
Close positions before the end of the Kill Zone or
upon reaching the target.

### Stop Loss
Below/above the start of the Kill Zone setup.
Typically 0.3-0.7% from entry.

## Confirming Signals
- Clear volume activity at session open
- Liquidity sweep of Previous Session High/Low
- FVG formed at session open
- Funding rate shift at session open

## When NOT to Enter
- Outside the Kill Zone window (setup less reliable)
- Major macro news during Kill Zone
  (FOMC, CPI, NFP — even crypto reacts)
- Kill Zone without a clear move (consolidation)

## Risk Management
Risk per trade: 0.5-1.0% of capital.
Kill Zone trading requires fast decisions.
Close all positions before the end of the window
if TP has not been reached.
Do not hold Kill Zone setups overnight.

## Setup Example
```
NY Kill Zone 13:30 UTC. Previous London High @ $65,200.
NY open — price sweeps $65,200 to $65,450 (liquidity grab).
Immediate bearish reversal, MSS on 5m.
Entry SHORT @ $65,100, SL @ $65,500, TP @ $64,200.
R:R = 1:2.3. Close before 16:00 UTC (end of Kill Zone).
```

## Configuration Parameters
- `london_open_utc`: London Kill Zone start hour
  (default 2)
- `london_open_duration_h`: London KZ duration in hours (default 3)
- `ny_open_utc`: NY Kill Zone start hour (default 13)
- `ny_open_duration_h`: NY KZ duration in hours (default 3)
- `enforce_killzone`: trade only during Kill Zone
  (default false — crypto 24/7)
