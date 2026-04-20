# On-Chain: Whale Tracking & Exchange Flows

## META
- Name: On-Chain Whale and Exchange Flow Analysis
- Category: on_chain, sentiment
- Difficulty: advanced
- Timeframes: 4h, 1d (on-chain data is slow-moving)
- Best Market: macro turning points, trend confirmation
- Estimated Win Rate: 55-65% (as confirmation, not standalone)
- Risk Reward: 1:3.0 (used for higher-conviction entries)
- Tokens: BTC, ETH (most on-chain data available)

## Description
On-chain analysis examines blockchain data to understand what large holders ("whales") and institutions are doing.
Unlike technical analysis which only sees price, on-chain sees the ACTUAL movement of coins — who is accumulating, who is distributing, whether coins are moving to exchanges (selling pressure) or out (holding/accumulation).
Key principle: smart money (whales, institutions) move coins before price moves. On-chain leads price.

---

## EXCHANGE INFLOWS / OUTFLOWS

### Exchange Inflows (Bearish Signal)
Large amounts of BTC/ETH moving TO exchanges = preparation to sell.
- **Signal**: exchange inflow spike > 2× 30-day average
- **Implication**: expect selling pressure within 24-72h
- **Action**: reduce LONG exposure, tighten SLs on existing longs

### Exchange Outflows (Bullish Signal)
Coins leaving exchanges = moving to cold wallets = long-term holding.
- **Signal**: sustained outflow > 7 consecutive days, OR single large outflow
- **Implication**: supply leaving market → price supportive
- **Action**: bias toward LONG, dips become buying opportunities

### Stablecoin Inflows (Bullish)
Stablecoins (USDT, USDC) moving TO exchanges = dry powder ready to buy.
- Large stablecoin inflow to exchanges → buying pressure incoming
- Especially bullish if combined with BTC outflow from exchanges

---

## WHALE WALLET MONITORING

### Accumulation vs Distribution
Wallets holding 1000+ BTC (whales) change behavior:
- **Accumulation phase**: whale count increasing, wallet sizes growing → early bull signal
- **Distribution phase**: large wallets reducing holdings → early bear signal

### Whale Transfer Alerts
- Large transfer from known whale wallet to exchange = imminent sell
- Large transfer from exchange to unknown wallet = accumulation (likely)
- Transfers between whale wallets = portfolio rebalancing (neutral)

### HODLer Behavior
- Long-term holders (LTH, coins not moved > 155 days) selling = distribution to new buyers
- LTH accumulating = conviction at current prices is high

---

## ON-CHAIN METRICS FOR ENTRY TIMING

### NUPL (Net Unrealized Profit/Loss)
Estimates the overall profit/loss position of all holders.
- NUPL > 0.75 (Greed/Euphoria): most holders in extreme profit → distribution risk, avoid LONG
- NUPL 0.5-0.75 (Optimism): mid-bull, LONGs still good
- NUPL 0-0.25 (Hope): recovery from bottom, good LONG zone
- NUPL < 0 (Capitulation): below cost basis → historically best LONG entry (cycle bottoms)

### MVRV Ratio (Market Value / Realized Value)
- MVRV > 3.5: historically signals cycle tops → extreme caution for LONGs
- MVRV 1.0-2.0: fair value range, neutral
- MVRV < 1.0: price below average cost basis → historically excellent LONG zone

### Puell Multiple
Measures miner revenue relative to 365-day average.
- Puell > 4: miners in extreme profit → historically near tops
- Puell < 0.5: miners stressed → historically near bottoms (good LONG)
- Use on BTC only (ETH different economics post-merge)

---

## PRACTICAL TRADING INTEGRATION

### On-Chain Context for Entry
Before entering any significant LONG position:
1. Check NUPL: avoid if > 0.75
2. Check MVRV: avoid if > 3.5
3. Check exchange flows: avoid if large inflow spike occurred < 48h ago
4. Check stablecoin supply on exchanges: is buying power available?

### Whale Alert Integration
- When whale alert services show large BTC/ETH moving to exchanges: hedge or wait
- When sustained outflows: increase confidence on bullish technical setups

### Funding Rate + On-Chain Combination
- High funding rate (longs paying) + exchange inflow → strong short signal
- Negative funding + exchange outflow → strong long signal

## When On-Chain Signals Are LESS Reliable
- Altcoins (less on-chain data, often manipulated)
- Short-term trades (< 4h): on-chain is too slow
- Bear market liquidation cascades: technical analysis overrides on-chain

## Risk Management
- On-chain is MACRO context, not an entry trigger
- Never enter solely on on-chain signal — wait for technical entry
- Use on-chain to SIZE your position: favorable on-chain = larger size
- Unfavorable on-chain = reduce position size by 30-50%

## Setup Example
```
Macro context (BTC):
- NUPL: 0.45 (optimism zone ✓, not extreme)
- MVRV: 1.8 (fair value range ✓)
- Exchange flows: 3 days of sustained outflows ✓
- Stablecoins on exchanges: increasing ✓ (dry powder)

Technical: BTC pulling back to EMA50 on 4h
  + Fibonacci 38.2% confluence
  + Bullish engulfing candle

On-chain CONFIRMS bullish bias → use larger position (30% budget vs normal 15%)
```

## Configuration Parameters
- `nupl_greed_threshold`: 0.75 (avoid LONGs above)
- `mvrv_top_threshold`: 3.5 (avoid LONGs above)
- `exchange_inflow_multiplier`: 2.0 (alert when inflow spikes above 2× average)
- `outflow_bullish_days`: 5 (consecutive days of outflow = bullish)
- `puell_top`: 4.0, `puell_bottom`: 0.5
