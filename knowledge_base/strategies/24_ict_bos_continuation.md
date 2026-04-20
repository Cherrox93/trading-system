# ICT Break of Structure Continuation

## META
- Name: ICT Break of Structure (BOS) Trend Continuation
- Category: momentum
- Difficulty: intermediate
- Timeframes: 15m, 1h, 4h
- Best Market: trending
- Estimated Win Rate: 55-63%
- Risk Reward: 1:2.0
- Tokens: any
- Source: ict_research
- Added: 2026-04-15

## Description
Break of Structure (BOS) confirms trend continuation when price
breaks the previous swing high (uptrend) or swing low (downtrend).
BOS = institutions are continuing in the same direction.
After a BOS, look for a retrace to a support zone (bullish) or resistance
(bearish) to join the institutional move with a favorable R:R.
BOS differs from CHoCH — BOS = continuation, CHoCH = potential reversal.

## Entry Conditions
BULLISH BOS (LONG entry):
- Uptrend: series of Higher Highs (HH) and Higher Lows (HL)
- Price breaks above the previous HH — this is BOS
- Wait for a pullback to the support zone (previous HH
  now acting as support, FVG or OB in the discount zone)
- Entry on retrace with bullish structure confirmation
  on the lower TF
- RSI returning from oversold (< 40) during the retrace

BEARISH BOS (SHORT entry):
- Downtrend: Lower Highs (LH) and Lower Lows (LL)
- Price breaks below the previous LL — BOS
- Wait for pullback to resistance (previous LL now acting as resistance)
- Entry with bearish structure confirmation on LTF

## Exit Conditions
### Take Profit
Target: next liquidity zone in the direction of the trend.
Bullish: next equal highs, liquidity pool above.
Bearish: next equal lows, liquidity pool below.
Minimum 2× risk.

### Stop Loss
Below the last HL (bullish) or above the last LH (bearish).
Structure invalidation = exit.
Typically 0.5-1.2% from entry.

## Confirming Signals
- Multiple timeframe alignment: BOS on 1h confirmed
  by trend on 4h
- EMA 9 above EMA 21 (bullish) during retrace
- No FVG that could "pull" price back
- Volume rising at BOS (institutional momentum)

## When NOT to Enter
- BOS without clear displacement (weak, non-institutional)
- Retrace exceeds 61.8% Fibonacci of the previous move
  (may be CHoCH instead of BOS)
- Conflicting signals on higher TF (4h in downtrend
  while entering LONG on BOS 15m)
- Funding rate extremely high (> 0.08%) on LONG

## Risk Management
Risk per trade: 0.7-1.2% of capital.
BOS on higher TF = greater confidence, larger size.
If pullback takes too long without an entry —
skip, look for the next BOS.
Trailing stop after reaching 1R profit.

## Setup Example
```
AVAX uptrend 4h. Previous HH @ $30.00. Price forms BOS
breaking $30.00 to $31.50. Pullback to $30.20 (previous
HH now support, FVG in the area). RSI returns to 42.
Bullish pin bar on 15m. Entry LONG @ $30.20,
SL @ $29.50, TP @ $32.80 (next liquidity). R:R = 1:3.7.
```

## Configuration Parameters
- `bos_confirmation`: require candle close
  above/below the level (default true)
- `max_pullback_pct`: maximum pullback after BOS
  in % (default 61.8% Fib)
- `min_impulse_size`: minimum BOS move in % (default 0.8%)
