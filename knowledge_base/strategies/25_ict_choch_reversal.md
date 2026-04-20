# ICT Change of Character (CHoCH) Reversal

## META
- Name: ICT Change of Character (CHoCH) Trend Reversal
- Category: mean_reversion
- Difficulty: advanced
- Timeframes: 15m, 1h, 4h
- Best Market: volatile
- Estimated Win Rate: 48-56%
- Risk Reward: 1:3.0
- Tokens: large_cap
- Source: ict_research
- Added: 2026-04-15

## Description
Change of Character (CHoCH) is the first signal of a trend change —
earlier than BOS. In an uptrend, CHoCH is the break of the last
Higher Low (HL). In a downtrend — the break of the last Lower High (LH).
CHoCH signals that institutions have begun changing direction.
This is a more aggressive setup than BOS (lower WR but higher R:R)
because you enter earlier in a potential reversal.
Requires additional confirmation.

## Entry Conditions
BULLISH CHoCH (LONG entry from downtrend):
- Downtrend: series of Lower Highs and Lower Lows
- Price breaks above the last LH — this is bullish CHoCH
- Confirmation: bullish displacement candle closing
  above the LH
- Entry on retrace to the FVG or OB that formed
  during the CHoCH displacement
- Additional confirmation: liquidity sweep below
  the last LL before CHoCH

BEARISH CHoCH (SHORT entry from uptrend):
- Uptrend: series of HH and HL
- Price breaks below the last HL — bearish CHoCH
- Bearish displacement closing below HL
- Entry on retrace to FVG/OB after CHoCH

## Exit Conditions
### Take Profit
Target: external liquidity levels on the new side of the trend.
Bullish CHoCH: previous swing highs (external liquidity).
Bearish CHoCH: previous swing lows.
Aggressive target: 3-5× risk.

### Stop Loss
Below/above the last extreme point
before CHoCH (behind the entire structure).
Typically 0.8-1.5% from entry.

## Confirming Signals
- Liquidity sweep before CHoCH (classic ICT manipulation)
- RSI divergence on the higher TF
- FVG at displacement confirming the strength of the move
- Shift in funding rate direction

## When NOT to Enter
- CHoCH without clear displacement (weak signal)
- No liquidity sweep before CHoCH (less certain)
- Conflicting trend on higher TF (e.g., bullish CHoCH on 15m
  but 4h is still bearish)
- Market in consolidation without clear structure
- High-impact news within 30 minutes

## Risk Management
Risk per trade: 0.5-0.8% of capital (conservative,
because CHoCH is an aggressive setup).
If price does not form a new trend
within 5 × 15m candles after CHoCH — exit at break-even.
Close half at 1.5R, trail the rest.

## Setup Example
```
BTC downtrend on 1h. Series of LL. Price sweeps last LL
($63,500) going to $63,200 (liquidity grab below).
Immediate bullish displacement candle: $63,200→$64,800.
Breaks last LH @ $64,200 — bullish CHoCH.
Pullback to FVG @ $63,900. Entry LONG @ $63,900,
SL @ $63,100, TP @ $67,000. R:R = 1:3.9.
```

## Configuration Parameters
- `require_liquidity_sweep`: require a sweep before CHoCH
  (default true)
- `displacement_min_size`: minimum displacement candle size
  in % (default 1.5%)
- `choch_confirmation_tf`: TF for CHoCH confirmation
  (default 15m)
