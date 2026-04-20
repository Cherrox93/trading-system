# Market Microstructure & Order Book Analysis

## META
- Name: Market Microstructure and Order Book Analysis
- Category: microstructure, order_flow
- Difficulty: advanced
- Timeframes: 1m, 5m, 15m (real-time data critical)
- Best Market: high-liquidity tokens, active sessions
- Estimated Win Rate: 58-68% (when signals are clear)
- Risk Reward: 1:1.5 to 1:2.5
- Tokens: BTC, ETH (best liquidity), top 20 alts

## Description
Market microstructure examines how orders interact in the order book to create price movements.
Unlike indicators that show what HAPPENED, order book analysis shows what IS HAPPENING and what WILL HAPPEN based on order positioning.
Key insight: large limit orders defend price levels, market orders consume liquidity.
The imbalance between buy and sell orders determines short-term price direction.

---

## ORDER BOOK COMPONENTS

### Bid Side (Buy Orders)
- Limit buy orders stacked below current price
- Large bid walls = strong support at that level (price bounces there)
- Thin bid side = price will fall through quickly (no support)

### Ask Side (Sell Orders)
- Limit sell orders stacked above current price
- Large ask walls = strong resistance (price rejection)
- If a large ask wall disappears = buyer absorbed it → bullish

### Order Book Imbalance
```
Bid-Ask Imbalance = (Total Bid Volume - Total Ask Volume) / (Total Bid + Total Ask)
Range: -1.0 (all asks) to +1.0 (all bids)
+0.3 and above = bullish (more buyers than sellers)
-0.3 and below = bearish
```
Measure over top 10-20 price levels from mid-price.

---

## LIQUIDITY STRATEGIES

### Large Limit Order Defense (Support/Resistance)
- Large buy order ($500k+) sitting at a round number or key level = institutional floor
- Price approaches → slows down → reverses
- **Strategy**: enter LONG when price touches the large bid wall with slowing momentum
- **Exit**: if the wall is consumed/removed (abort trade)
- **Risk**: stop below the bid wall level

### Liquidity Sweep (Stop Hunt)
- Institutions need liquidity to fill large orders — they push price to where retail stops are clustered
- Retail LONGs place stops below obvious lows → institutions push price below → sweep stops → reverse
- **Strategy**: wait for the sweep (price spikes below/above key level), then enter opposite direction
- **Entry**: on the reversal candle after the sweep, not during
- **Confirmation**: price quickly returns above the swept level
- This is functionally the same as ICT liquidity grab — same concept, different perspective

### Thin Liquidity (Gap Risk)
- Order book with thin middle (few orders between bid and ask)
- Price will move rapidly through thin zones
- Avoid entries into thin zones — no support for the trade
- Use as TP targets (price moves fast = quick profits)

---

## BID-ASK SPREAD ANALYSIS

### Normal Spread
- BTC: 0.01-0.05% (very tight)
- Major alts: 0.05-0.15%
- Small caps: 0.2-1.0%

### Spread Expansion Signals
- Spread widens 2-3× → liquidity dropping → volatility about to increase
- Widen before news events → wait for spread to normalize before entering
- Wide spread = entry cost is high, R:R degrades

### Trading the Spread
- Always include spread cost in R:R calculation
- On Lighter DEX, spread is typically: maker fee 0%, taker fee 0.05-0.1%
- For scalps: need minimum 0.3% TP to cover costs

---

## MARKET DEPTH ANALYSIS

### Depth Chart Reading
- Visualizes cumulative bid/ask orders vs price
- Steep bid wall (cliff) = concentrated support at one level (institutional order)
- Gradual bid slope = distributed support (retail, less reliable)
- Gap in depth = price will accelerate through this zone

### Absorption Patterns
- Price approaches resistance → large selling → price holds or rises = ABSORBED
- Absorption = buyers are taking all the supply at that level
- After absorption: resistance turns to support → strong LONG entry

### Iceberg Orders
- Large orders split into smaller chunks to hide true size
- Identified by: price level repeatedly refreshing (new orders appear as others fill)
- Iceberg at support = institutional accumulation → LONG

---

## TAPE READING (Time & Sales)

### Reading Order Flow
- Large market buys (aggressive buyers hitting the ask) = bullish pressure
- Large market sells (hitting the bid) = bearish pressure
- Sequence of large buys at ask, then sudden large sell = trap (fade the large sell)

### Volume at Price Levels
- High volume at a price level = that level has significance (many traders agreed)
- Low volume on breakout = potential false breakout
- High volume + price rejection = strong level

### Bid/Ask Trade Ratio
```
If: 70%+ of volume traded at ASK = buyers aggressive = bullish
If: 70%+ of volume traded at BID = sellers aggressive = bearish
Neutral: 45-55% distribution
```

---

## PRACTICAL APPLICATION ON LIGHTER DEX

### Available Data
- Lighter provides order book depth (bids/asks per token)
- Market snapshot includes: price, volume, spread (bid/ask)
- Check `market_snapshot.json` for: `bid_price`, `ask_price`, `bid_size`, `ask_size`

### Spread-Based Filtering
- Never enter if spread > 0.2% for scalp (costs too much)
- For swing trades: spread up to 0.5% acceptable

### Order Size Context
- If signal has high confidence but spread is wide → reduce position size
- If spread is normal and order book shows strong bid support → increase confidence

---

## When NOT to Use Order Book Analysis
- Highly illiquid tokens (order book meaningless, one large order moves price)
- Weekend low-volume sessions (thin books, unreliable signals)
- During macro news release (order book can gap within seconds)
- If order book data is delayed > 5 seconds (stale data)

## Risk Management
- Risk per trade: 0.5-1.0% (microstructure trades are short-duration)
- Always check if your order size is > 10% of visible liquidity (market impact risk)
- Exit quickly if order book structure changes against you

## Configuration Parameters
- `max_spread_scalp`: 0.002 (0.2% maximum spread for scalping)
- `max_spread_swing`: 0.005 (0.5% for swing trades)
- `imbalance_threshold`: 0.30 (30% imbalance for directional bias)
- `min_bid_wall_usdt`: 100000 (minimum wall size to consider institutional)
- `absorption_confirmation_candles`: 2 (candles to confirm absorption)
