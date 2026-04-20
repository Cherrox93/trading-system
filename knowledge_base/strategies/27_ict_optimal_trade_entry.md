# ICT Optimal Trade Entry (OTE)

## META
- Name: ICT Optimal Trade Entry (OTE) Fibonacci
- Category: mean_reversion
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: trending
- Estimated Win Rate: 55-62%
- Risk Reward: 1:2.5
- Tokens: any
- Source: ict_research
- Added: 2026-04-15

## Description
Optimal Trade Entry (OTE) is a precise ICT entry method combining
Fibonacci retracement with Order Blocks and FVGs.
The OTE zone lies between 61.8%–79% Fibonacci retracement
after an impulsive move (displacement). This is the "golden zone"
where institutions join the trend after liquidity has been cleared.
Entering in the OTE provides the best R:R with simultaneously
high directional confidence.

## Entry Conditions
BULLISH OTE (LONG entry):
- Identify an impulsive bullish move (displacement): point A→B
- Wait for pullback (B→C)
- OTE zone: 61.8%–79% Fibo from A to B
  (i.e., C should retrace to this zone)
- Within the OTE zone, look for a bullish OB or FVG for precision
- Entry when price touches OTE + structure confirms
- Strongest when OTE aligns with a previous HH (now support)

BEARISH OTE (SHORT entry):
- Impulsive bearish displacement: A→B (decline)
- Pullback to 61.8%–79% Fibo: OTE zone
- Bearish OB or FVG in the OTE zone
- Entry at the upper range of the OTE zone

## Exit Conditions
### Take Profit
Target: point A (start of displacement) or beyond.
Minimum R:R 2.0.
In a strong trend: target = −27% Fibo extension.

### Stop Loss
Above/below point B (furthest point of pullback)
or 1% beyond the 79% Fibo level.

## Confirming Signals
- OTE overlaps with FVG or OB (strongest setup)
- Liquidity sweep upon reaching the OTE zone
- RSI returning from oversold/overbought at OTE
- Higher TF trend aligned with entry direction

## When NOT to Enter
- Pullback exceeds 100% (no structure remaining)
- OTE zone has no OB or FVG (less precise)
- Conflicting trend on 4h
- ATR very high (SL too wide for acceptable R:R)

## Risk Management
Risk per trade: 0.7-1.2% of capital.
OTE is one of the more reliable ICT setups
when it appears with additional confluence (FVG + OB).
Target minimum 2.5× risk using Fibo extension.

## Setup Example
```
SOL bullish displacement: $140 (A) → $155 (B).
Pullback to $146 (61.8% Fibo = OTE zone).
Bullish OB in the zone $145–$147. Entry LONG @ $146,
SL @ $143 (below OTE), TP @ $160 (127% extension).
R:R = 1:4.7.
```

## Configuration Parameters
- `ote_low`: lower boundary of the zone (default 61.8% Fibo)
- `ote_high`: upper boundary of the zone (default 79% Fibo)
- `require_ob_or_fvg`: require OB or FVG in the zone
  (default true)
