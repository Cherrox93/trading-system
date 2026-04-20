# Whale Wallet Follow

## META
- Name: Whale Wallet Follow
- Category: hybrid
- Difficulty: advanced
- Timeframes: 15m, 1h
- Best Market: any
- Estimated Win Rate: 52-58%
- Risk Reward: 1:2
- Tokens: any

## Description
Strategy based on tracking large on-chain transactions (whale movements) as a directional signal.
When a large player (whale) executes a transaction >100k USD on a DEX or transfers tokens to/from an exchange, it signals their intent.
Transfer to exchange = potential sale (bearish), purchase on DEX = potential rise (bullish).
Requires access to on-chain data or whale activity aggregators (e.g. Whale Alert API).

## Entry Conditions

### LONG (whale buying on-chain)
- Transaction >100,000 USD on DEX (swap/buy) within the last 30 minutes
- Purchase was directed at the given token (buy pressure)
- Direction aligned with 1h trend (bullish or neutral)
- Neutral funding rate (−0.02% to +0.02%) — whale not entering overcrowded trade
- Price has not yet risen >1.5% since whale transaction (not too late)
- RSI < 65 (not overbought before entry)

### SHORT (whale selling / transferring to exchange)
- Transfer >100,000 USD of token to centralized exchange (potential sale)
- Or: large swap of token to stablecoin on DEX (direct sale)
- Trend neutral or bearish
- Neutral funding rate
- Price has not fallen >1.5% yet
- RSI > 35

## Exit Conditions

### Take Profit
- Target 1 (70% of position): 1% move from entry in direction of whale transaction
- Target 2 (30% of position): 2% move (if whale is "smart money" effect lasts longer)
- Close if whale account executes reverse transaction

### Stop Loss
- 0.5% opposite to entry direction
- Time stop: 4h from entry — if no move, close (whale transaction did not work)

### Trailing Stop
- After reaching 0.7%: trailing stop 0.3% behind price
- Fast strategy — do not hold longer than 6h

## Confirming Signals
- Known smart money wallet (addresses known for historical profitability)
- Multiple whale transactions in the same direction (several whales simultaneously)
- On-chain volume increase after whale transaction
- Funding rate starting to shift in direction of whale transaction
- Technical confirmation: EMA or S/R alignment with direction

## When NOT to Enter
- Transaction was more than 2h ago (price effect has already occurred)
- Price rose >1.5% from whale buy (too late to enter)
- Whale account is new or unidentified (may be wash trading)
- Large sell wall directly above price (whale cannot break through alone)
- No on-chain data available (strategy requires monitoring tools)
- Whale transaction is clearly OTC or rebalancing (not informational)

## Risk Management
- Risk per trade: 0.4-0.5% of capital (information may be false)
- Do not enter without technical confirmation (trend or S/R)
- Max 2 whale follow positions simultaneously
- This strategy has additional risk of "false signals" from whale washtrading
- Monitor follow-up whale activity for 2h after entry

## Setup Example
```
Token: WLD, timeframe: 15m
09:15 UTC: Whale Alert — 250,000 WLD bought on DEX (≈$308,625)
  Address: known profitable wallet (5 previous accurate buys)

Analysis:
  Time since transaction: 12 minutes ✓ (<30 min)
  Price increase since buy: 0.3% (1.2300 → 1.2336, below 1.5% ✓)
  1h trend: bullish (EMA9 > EMA21 ✓)
  Funding rate: +0.008% (neutral ✓)
  RSI 15m: 52 ✓

Entry: 1.2340
SL: 1.2278 (−0.5% = 0.5% risk)
TP1: 1.2464 (+1.0%) — close 70%
TP2: 1.2588 (+2.0%) — close 30%
Time stop: 13:15 UTC (4h)
```

## Configuration Parameters
- `min_transaction_usd`: min whale transaction value (default 100,000 USD)
- `max_age_minutes`: max transaction age (default 30 minutes)
- `max_price_move_pct`: max price move from whale tx (default 1.5%)
- `sl_pct`: stop loss (default 0.5%)
- `tp1_pct`: first target (default 1.0%)
- `tp2_pct`: second target (default 2.0%)
- `time_stop_hours`: time-based exit (default 4h)
- `require_trend_confirm`: require trend confirmation (default True)
