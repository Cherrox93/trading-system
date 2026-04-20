# ICT Market Structure Shift (MSS) with Displacement

## META
- Name: ICT Market Structure Shift (MSS) Reversal
- Category: mean_reversion
- Difficulty: advanced
- Timeframes: 5m, 15m, 1h
- Best Market: volatile
- Estimated Win Rate: 50-58%
- Risk Reward: 1:3.5
- Tokens: large_cap
- Source: ict_research
- Added: 2026-04-15

## Description
Market Structure Shift (MSS) is a stronger version of CHoCH —
a rapid displacement that breaks internal structure and signals
an immediate change in market character. MSS differs from CHoCH in
the strength of the move: MSS requires a large displacement candle
(engulfing or marubozu), while CHoCH can be subtle. MSS often
appears after a liquidity sweep and is the first signal on the lower TF
before a full reversal on the higher TF. Very precise entry timing.

## Entry Conditions
BULLISH MSS (LONG entry):
- Downtrend on 15m/1h
- Liquidity sweep below the last swing low
- Immediate large bullish candle (marubozu or engulfing)
  breaking the last Lower High — MSS
- FVG visible in the body of this displacement candle
- Entry on pullback to the FVG of the displacement candle
  (usually immediate, within 2-3 candles)

BEARISH MSS (SHORT entry):
- Uptrend on 15m/1h
- Liquidity sweep above the last swing high
- Large bearish displacement candle breaking LH
- FVG in displacement, pullback to FVG
- Entry SHORT

## Exit Conditions
### Take Profit
Target: external liquidity (opposite swing highs/lows).
Aggressive: 3-5× risk.
Minimum: nearest FVG or OB zone.

### Stop Loss
Below/above the extreme point of the liquidity sweep
(further than the point that triggered the MSS).
Typically 0.5-1.2% from entry.

## Confirming Signals
- Displacement candle > 2× ATR(14) — shows strength
- FVG within displacement (imbalance confirming the move)
- Volume spike at MSS
- SMT divergence on a correlated pair

## When NOT to Enter
- Displacement candle is small (< 1× ATR) — weak MSS
- No liquidity sweep before MSS
- Pullback to FVG too deep (> 80% of candle) — may
  be a fakeout
- Market in consolidation on the higher TF

## Risk Management
Risk per trade: 0.5-0.8% of capital.
MSS requires a fast decision — entry window is small
(pullback to FVG usually lasts 2-5 × 5m candles).
If you miss the entry — do not chase it.

## Setup Example
```
ETH downtrend 15m. Sweep below $3,150 to $3,120.
Immediate bullish candle $3,120→$3,210 (MSS —
broke last LH @ $3,180). FVG in candle:
$3,160–$3,185. Pullback to $3,170. Entry LONG @ $3,170,
SL @ $3,115, TP @ $3,320. R:R = 1:2.7.
```

## Configuration Parameters
- `mss_min_displacement`: minimum MSS candle size
  in ATR (default 1.5× ATR)
- `fvg_entry`: enter at FVG within displacement (default true)
- `max_entry_candles`: max candles to enter after MSS
  (default 3)
