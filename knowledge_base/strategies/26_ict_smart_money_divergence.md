# ICT Smart Money Divergence (SMT)

## META
- Name: ICT Smart Money Divergence (SMT) Entry
- Category: mean_reversion
- Difficulty: advanced
- Timeframes: 15m, 1h
- Best Market: volatile
- Estimated Win Rate: 52-58%
- Risk Reward: 1:2.5
- Tokens: large_cap
- Source: ict_research
- Added: 2026-04-15

## Description
Smart Money Divergence (SMT) occurs when two correlated assets behave
differently at the same price level. Example: BTC forms a new higher high,
ETH does not confirm (lower high) — this is bearish SMT. Or BTC forms a
lower low but ETH does not confirm — bullish SMT. SMT signals institutional
manipulation and weakness in the move. One of the strongest reversal signals
in ICT when it appears at key liquidity zones.

## Entry Conditions
BEARISH SMT (SHORT entry):
- Pair A (e.g., BTC) forms a new higher high
- Pair B (e.g., ETH) does not confirm — its high is lower
- SMT appears at buy-side liquidity (above equal highs)
- Pair A performs a liquidity grab while B refuses to confirm
- Enter SHORT on Pair A (stronger) or B (weaker)
  after bearish CHoCH/BOS confirmation

BULLISH SMT (LONG entry):
- Pair A forms a new lower low
- Pair B does not confirm — its low is higher
- SMT at sell-side liquidity
- Enter LONG after bullish CHoCH

## Exit Conditions
### Take Profit
Target: opposite liquidity on the divergence side.
Bearish SMT: sell-side liquidity below.
Bullish SMT: buy-side liquidity above.

### Stop Loss
Above/below the extreme of the pair that performed the grab
(the furthest extended point).
Typically 0.5-1.0% from entry.

## Confirming Signals
- SMT at an important liquidity level (equal highs/lows)
- FVG in the direction of the reversal
- Funding rate difference between pairs (one pair has high
  funding, the other is normal)
- RSI of both pairs at an extreme

## When NOT to Enter
- Correlation between pairs is not high (different sectors)
- SMT appears in the middle of consolidation without structure
- Only one pair is visible in the system
  (no comparison point)
- Volume difference between pairs is too large

## Risk Management
Risk per trade: 0.5-0.8% of capital.
SMT is a rare but strong signal.
Always require additional confirmation
(CHoCH, FVG, OB) before entering.
Do not enter on SMT alone without market structure.

## Setup Example
```
BTC and ETH in correlation. BTC breaks $65,000
(previous equal highs) → $65,400. ETH remains
at $3,150 (does not confirm a higher high — was at $3,200).
Bearish SMT. BTC wick back below $65,000.
Bearish CHoCH on BTC 15m. Entry SHORT BTC @ $64,900,
SL @ $65,500, TP @ $63,200. R:R = 1:2.8.
```

## Configuration Parameters
- `primary_token`: main pair to trade (e.g., BTC)
- `secondary_token`: comparison pair (e.g., ETH)
- `divergence_threshold`: minimum divergence in %
  (default 0.3%)
