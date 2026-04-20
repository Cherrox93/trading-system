# Market Depth Imbalance

## META
- Name: Market Depth Imbalance
- Category: orderbook_analysis
- Difficulty: advanced
- Timeframes: 1m, 5m (entry timing only — use HTF for direction)
- Best Market: liquid markets with deep orderbooks
- Estimated Win Rate: 55-62% (when used as entry precision tool)
- Risk Reward: 1:1.5 (tight entries = tight stops)
- Tokens: BTC, ETH, SOL (high liquidity required)

## Description
Analyzes real-time orderbook depth imbalance to time entries precisely.
Unlike 41_orderbook_microstructure (which tracks individual large orders), this strategy
measures aggregate bid/ask imbalance across the full visible book depth.
Used as an entry trigger overlay for signals from other strategies.

## Core Concepts

### Bid/Ask Imbalance Ratio
```
Calculate sum of volume at each bid level (top 10 bids) and ask level (top 10 asks):

Total_Bid_Volume = sum(qty at bid_1 through bid_10)
Total_Ask_Volume = sum(qty at ask_1 through ask_10)

Imbalance_Ratio = Total_Bid_Volume / Total_Ask_Volume

> 1.5: Significant bid pressure → bullish short-term
> 2.0: Strong bid imbalance → high-confidence bullish
< 0.67: Significant ask pressure → bearish short-term
< 0.50: Strong ask imbalance → high-confidence bearish
0.67-1.5: Balanced → no signal
```

### Depth Wall Detection
A "wall" is an unusually large order at a specific price level:
```
Wall = single order with qty > 3× average order size at that depth level

Bid wall: strong support level (may absorb selling)
Ask wall: strong resistance level (may absorb buying)

BUT: walls can be spoofing — confirm they hold for ≥ 3 ticks before trusting
```

### Order Book Sweep
When a large market order eats through multiple price levels rapidly:
```
Sweep up: aggressive buying, multiple ask levels cleared
Sweep down: aggressive selling, multiple bid levels cleared

Sweep direction often indicates short-term momentum continuation for 1-3 candles.
```

## Entry Conditions

### LONG Entry (imbalance supports direction from primary strategy)
- Primary strategy (HTF) gives LONG signal
- On 1m/5m: Bid/Ask ratio > 1.5 (bids dominating)
- Ask wall at primary strategy TP level (provides natural exit target)
- No large ask wall within 0.3% above entry (clear path)
- Recent book sweep was upward (aggressive buyers present)
- Bid refreshing: when bids are filled, new bids appear immediately (sign of absorption)

### SHORT Entry
- Primary strategy gives SHORT signal
- Bid/Ask ratio < 0.67 (asks dominating)
- Bid wall at primary strategy TP level
- No large bid wall within 0.3% below entry
- Recent sweep was downward

## Exit Conditions

### Take Profit
- When opposite imbalance appears (ratio crosses to opposite zone)
- When price reaches identified ask wall (LONG) or bid wall (SHORT)
- After book sweep in opposite direction

### Stop Loss
- LONG: below nearest bid wall that was present at entry (if wall removed → exit)
- SHORT: above nearest ask wall at entry
- Always max 0.5% from entry (depth-based entries are precision tools)

### Urgent Exit Signals
- Large wall at entry vanishes before price reaches it (spoofing)
- Book imbalance flips rapidly against position (> 2.0 ratio in opposite direction)
- Sudden increase in spread > 3× normal (liquidity drying up)

## Imbalance Fade Setup (Contrarian)
Sometimes strong imbalance is exhausted and reverses:
```
Setup: Imbalance ratio > 2.5 (extreme)
But price not moving in direction of imbalance (bids not pushing price up)
= Bids are being absorbed by hidden large sellers

Signal: FADE the imbalance — SHORT when extreme bid imbalance fails to move price
Confirm: 3+ candles with high bid ratio but flat/declining price
Entry: on first candle where price drops despite bid imbalance still present
Target: 0.5% (quick — these setups resolve fast)
```

## Market Depth Reading Checklist (before entry)
```
1. Calculate Bid/Ask ratio over top 10 levels
2. Identify largest walls within ±1% of current price
3. Check if imbalance aligns with primary strategy direction
4. Verify no spoofing: wall has been present ≥ 3 price ticks without moving
5. Check recent sweeps (last 5 minutes) — direction?
6. Confirm spread is normal (not widened)
7. If all checks pass: enter with reduced size (precision entry, not full position)
```

## Limitations
- Orderbook data is ephemeral — what you see may change in milliseconds
- Large players hide orders in iceberg orders (visible qty ≠ full order)
- Spoofing is common in crypto — walls appear and disappear
- This strategy requires low latency data feed; works poorly on delayed data
- Never use as standalone signal — always combine with HTF directional bias

## Configuration Parameters
- `book_depth_levels`: 10
- `imbalance_long_threshold`: 1.5
- `imbalance_strong_long`: 2.0
- `imbalance_short_threshold`: 0.67
- `imbalance_strong_short`: 0.50
- `wall_size_multiplier`: 3.0
- `wall_min_ticks_age`: 3
- `sweep_lookback_min`: 5
- `max_sl_pct`: 0.5
- `spread_spike_multiplier`: 3.0
- `fade_setup_min_ratio`: 2.5
- `fade_setup_lookback_candles`: 3
