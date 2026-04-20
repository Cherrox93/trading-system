# ATR Dynamic Risk Management

## META
- Name: ATR Dynamic Risk Management
- Category: risk_management
- Difficulty: intermediate
- Timeframes: all (applied as overlay to any strategy)
- Best Market: all markets
- Estimated Win Rate: N/A (enhances all strategies)
- Risk Reward: improves all by adapting to volatility
- Tokens: all

## Description
Dynamic stop-loss and take-profit system based on ATR (Average True Range).
Fixed % stops fail in crypto because volatility changes 5-10× between low-vol accumulation and high-vol breakouts.
ATR automatically widens stops in volatile conditions and tightens in calm conditions.
This module REPLACES fixed % TP/SL from other strategies when volatility is abnormal.

## Core Principle: Volatility Regimes
```
Measure ATR(14) relative to its own 50-period average:

ATR Ratio = Current ATR / ATR_50_period_average

Ratio < 0.7: LOW volatility (compressed)
  → Use tighter stops, can accept lower R:R
Ratio 0.7-1.3: NORMAL volatility
  → Standard multipliers from strategy
Ratio 1.3-2.0: HIGH volatility
  → Widen stops, reduce position size 30%
Ratio > 2.0: EXTREME volatility
  → Widen stops, reduce position size 50%, or skip trade
```

## ATR Multiplier Table

### Stop-Loss Multipliers (distance from entry to SL)
```
Timeframe | Low Vol | Normal | High Vol | Extreme
5m        | 0.8×    | 1.2×   | 1.8×     | 2.5×
15m       | 1.0×    | 1.5×   | 2.2×     | 3.0×
1h        | 1.5×    | 2.0×   | 2.8×     | 3.5×
4h        | 2.0×    | 2.5×   | 3.5×     | 4.5×
```

### Take-Profit Multipliers (TP1 / TP2)
```
Timeframe | Low Vol     | Normal      | High Vol    | Extreme
5m        | 1.5 / 3.0  | 2.0 / 4.0  | 2.5 / 5.0  | 3.0 / 6.0
15m       | 1.5 / 3.0  | 2.0 / 4.0  | 2.5 / 5.0  | 3.0 / 6.0
1h        | 2.0 / 4.0  | 2.5 / 5.0  | 3.0 / 6.0  | 4.0 / 8.0
4h        | 2.5 / 5.0  | 3.0 / 6.0  | 4.0 / 8.0  | 5.0 / 10.0
```

## Position Size Adjustment by Volatility
```
Base position size from Kelly/Fixed Fractional formula
Then adjust:

ATR Ratio < 0.7: size × 1.2 (can take larger position in calm market)
ATR Ratio 0.7-1.3: size × 1.0 (no change)
ATR Ratio 1.3-2.0: size × 0.7 (30% reduction)
ATR Ratio > 2.0: size × 0.5 (50% reduction)

NEVER exceed maximum per-trade risk from position_sizing_risk strategy.
```

## Trailing Stop Implementation

### Standard ATR Trailing
- After entry, trail stop at: entry price + n×ATR(14) below highest close (LONG)
- Update trail every candle close — never move stop backwards
- `n` depends on timeframe and volatility regime (see table below)

```
Trailing Multiplier Table:
Timeframe | Low Vol | Normal | High Vol
5m        | 1.0×    | 1.5×   | 2.0×
15m       | 1.2×    | 1.8×   | 2.5×
1h        | 1.5×    | 2.0×   | 3.0×
4h        | 2.0×    | 2.5×   | 3.5×
```

### Chandelier Exit (preferred)
Most robust trailing stop method:
```
LONG: Chandelier Stop = Highest High (n periods) − ATR(14) × multiplier
SHORT: Chandelier Stop = Lowest Low (n periods) + ATR(14) × multiplier

n = 22 candles (default)
multiplier = 3.0 (normal), 2.0 (low vol), 4.0 (high vol)
```
This prevents premature exits on normal retracements.

## Applying Dynamic TP/SL to Other Strategies

### Override Rules
1. Calculate ATR ratio before each trade
2. Look up correct multipliers from table
3. Compute SL distance = ATR(14) × SL_multiplier
4. Compute TP1 = ATR(14) × TP1_multiplier, TP2 = ATR(14) × TP2_multiplier
5. If SL distance exceeds structural level by > 50%, use structural level (tighter)
6. Always check final R:R ≥ 1.5 before entering — if ATR makes SL too wide, skip trade

### Priority
- Strategy structural stops (swing highs/lows) take priority IF they give better R:R
- ATR stops are the FLOOR — never set SL tighter than ATR-based minimum
- ATR stops are the CEILING in extreme vol — never wider than 4×ATR for scalp

## Volatility-Based Trade Filtering
```
Before entering any trade, check:

If ATR_ratio > 2.5: SKIP the trade entirely
  → Extreme volatility = unpredicable price action = no edge

If ATR_ratio > 1.5 AND strategy is reversal/mean-reversion: REDUCE to 50% size
  → Volatility expansions favor trend-following, not reversals

If ATR_ratio < 0.6 AND strategy is trend-following: SKIP or wait
  → Compressed volatility = no trend = breakout strategies need vol to work
```

## Setup Example
```
Token: SOL, timeframe: 15m
ATR(14): 0.85 (current)
ATR 50-period avg: 0.60
ATR ratio: 0.85/0.60 = 1.42 → HIGH volatility regime

Base signal: RSI divergence LONG entry at 145.00

Standard (fixed) SL would be: 1.5% = 142.83
ATR-based SL: 0.85 × 2.2 = 1.87 (distance from entry)
ATR SL price: 145.00 − 1.87 = 143.13

Position size adjustment: × 0.7 (high vol)
If base size = $500, adjusted size = $350

ATR TP1: 145.00 + 0.85 × 2.5 = 147.13 (+1.47%)
ATR TP2: 145.00 + 0.85 × 5.0 = 149.25 (+2.93%)
R:R: 1:1.86 (TP2) — acceptable ✓

Without ATR adjustment, fixed 1.5% SL would have been too tight for current volatility → likely stopped out on normal noise.
```

## Configuration Parameters
- `atr_period`: 14
- `atr_avg_period`: 50
- `vol_regime_low`: 0.7
- `vol_regime_high`: 1.3
- `vol_regime_extreme`: 2.0
- `vol_skip_threshold`: 2.5
- `chandelier_period`: 22
- `chandelier_multiplier_normal`: 3.0
- `position_size_high_vol_factor`: 0.7
- `position_size_extreme_vol_factor`: 0.5
- `position_size_low_vol_factor`: 1.2
- `min_rr_ratio`: 1.5
