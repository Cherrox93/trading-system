# Order Flow Imbalance

## META
- Name: Order Flow Imbalance
- Category: volume
- Difficulty: advanced
- Timeframes: 1m, 5m
- Best Market: any
- Estimated Win Rate: 53-59%
- Risk Reward: 1:1.5
- Tokens: large_cap

## Description
Strategy based on real-time analysis of the imbalance between buy and sell orders in the order book.
When pressure on one side exceeds 60%, price statistically follows that direction in the short term.
Requires access to order book data (bid/ask depth) — best from DEX level or aggregated feed.
This is one of the more advanced strategies requiring fast execution.

## Entry Conditions

### LONG
- Buy imbalance: sum of bid orders in top 5 order book levels > 60% of sum of ask orders
- Large buy orders (>10k USD combined) visible on bid side within 1% of price
- Price at a key support level or POC (Volume Profile)
- Candle delta (buy volume − sell volume) > 0 in the last 2 minutes
- No large sell wall (iceberg order) directly above price

### SHORT
- Sell imbalance: sum of ask orders in top 5 levels > 60% of sum of bid orders
- Large sell orders (>10k USD combined) visible on ask side within 1% of price
- Price at a key resistance or POC
- Candle delta < 0 in the last 2 minutes
- No large buy wall directly below price

## Exit Conditions

### Take Profit
- Target: next liquidity zone (order accumulation on the other side)
- Typical move: 0.3-0.8% within 5-15 minutes
- Close when imbalance drops below 55% (signal weakening)

### Stop Loss
- Tight SL: 0.25-0.35% from entry price
- Close immediately if imbalance reverses (>60% in opposite direction)

### Trailing Stop
- No trailing stop — this strategy requires fast exit
- Either TP or SL — do not hold longer than 30 minutes

## Confirming Signals
- Prints (actual transactions) going in imbalance direction (tape reading)
- Absorption: large orders on one side "eating" opposing orders — price can't move
- Time & Sales showing aggressive market orders in imbalance direction
- RSI in neutral zone (40-60) — no overcrowded trade
- Neutral funding rate

## When NOT to Enter
- Imbalance 55-60% — signal too weak
- Large orders appearing and disappearing quickly (spoofing — fake walls)
- Bid/ask spread > 0.08% (too expensive)
- Token 24h volume < 10M USD (liquidity too low for OF)
- No access to real-time order book data
- Market news active — OF becomes unreadable

## Risk Management
- Risk per trade: 0.3-0.4% of capital (smaller — fast strategies)
- Max 3 open OF positions simultaneously (scalping)
- Fees are critical — use only on markets with low fees (<0.05%)
- If 5 consecutive losses — break for minimum 1h
- Daily limit: max 10 trades with this strategy

## Setup Example
```
Token: WLD, timeframe: 1m
Order book (top 5 levels):
  Bids (total): 45,000 USD
  Asks (total): 18,000 USD
  Imbalance: 71.4% bid ✓

Large bid orders: 12,500 USD at 1.2300 ✓
Price: 1.2320 (at support 1.2300 ✓)
Delta last 2 minutes: +2,400 (buy dominant ✓)

Entry: 1.2325 (market)
SL: 1.2290 (0.28% risk)
TP: 1.2400 (0.61% gain, R:R 1:2.2 ✓)
Position lifetime: max 20 minutes
```

## Configuration Parameters
- `imbalance_threshold`: min % imbalance (default 60%)
- `large_order_usd`: definition of "large" order (default 10,000 USD)
- `depth_levels`: how many order book levels (default 5)
- `sl_pct`: stop loss (default 0.3%)
- `tp_pct`: take profit (default 0.6%)
- `max_hold_minutes`: max position hold time (default 30)
- `min_volume_24h`: min liquidity (default 10,000,000 USD)
