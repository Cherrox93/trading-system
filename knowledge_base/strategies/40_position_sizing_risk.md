# Position Sizing & Risk Management Systems

## META
- Name: Position Sizing and Risk Management
- Category: risk_management
- Difficulty: intermediate
- Timeframes: all (applied to every trade)
- Best Market: all markets
- Estimated Win Rate: N/A (risk management, not a signal)
- Risk Reward: improves all strategies
- Tokens: all

## Description
Position sizing determines how much to risk per trade — the most important factor in long-term profitability.
A strategy with 50% win rate and 1:2 R:R is profitable IF position sizing is consistent.
The same strategy with poor position sizing leads to ruin even with 60% win rate.

---

## KELLY CRITERION

### Full Kelly Formula
```
Kelly % = W - (1-W)/R
Where:
  W = win rate (e.g., 0.60 for 60%)
  R = average win / average loss ratio
```
Full Kelly maximizes long-term growth but causes extreme drawdowns.
**NEVER use full Kelly in live trading.**

### Half Kelly (Recommended)
```
Position Size = (Kelly %) / 2
```
Half Kelly reduces drawdown by ~75% while maintaining ~75% of maximum growth rate.

### Practical Example
```
Win rate: 58%, Avg win: $45, Avg loss: $25
R = 45/25 = 1.8
Kelly = 0.58 - (0.42/1.8) = 0.58 - 0.233 = 0.347 = 34.7%
Half Kelly = 17.35% of account per trade

If account = $1000 → risk $173 per trade (at 17% of account)
This is too high for crypto — apply additional fraction (1/4 Kelly):
1/4 Kelly = 8.7% → risk $87 per trade
```
**Crypto recommendation: use 1/4 Kelly due to high volatility.**

---

## FIXED FRACTIONAL POSITION SIZING

### Method
Risk a fixed % of current account balance per trade (1-2%).
```
Position Size (USDT) = Account × Risk_Pct / Stop_Loss_Pct
Example:
  Account = $1000
  Risk per trade = 1.0%
  SL = 2.0% from entry
  Position size = $1000 × 0.01 / 0.02 = $500
  With 5x leverage: $500 position on $100 margin
```
This automatically reduces size after losses (protective) and increases after wins (compounds).

### Advantage Over Fixed Size
- After 5 consecutive losses: account = $950
  → Next trade risk = $9.50 (not $10) — prevents ruin
- After 5 wins: account = $1,050
  → Next trade risk = $10.50 — compounds growth

---

## STOP-LOSS STRATEGIES

### 1. Fixed Percentage Stop
- SL at fixed % from entry (e.g., 1.5% always)
- Simple, consistent, but ignores market structure
- Use only when no clear structural level available

### 2. Structure-Based Stop (Recommended)
- SL placed BELOW the last swing low (LONG) or ABOVE the last swing high (SHORT)
- Then add ATR(14) × 0.5 buffer to avoid stop runs
- Position size adjusted to maintain fixed risk %

### 3. ATR-Based Stop
```
SL Distance = ATR(14) × multiplier
Typical multipliers:
  - Scalp (5m-15m): 1.0-1.5×
  - Swing (1h-4h): 2.0-2.5×
  - Position (4h+): 3.0×
```
ATR adapts to current volatility — wider in volatile markets, tighter in calm markets.

### 4. Trailing Stop
Moves with price, locking in profits:
- **ATR Trailing**: trail at ATR(14) × 2 below highest price reached (LONG)
- **Percentage Trailing**: trail at fixed % (e.g., 1.5%) below highest price
- **MA Trailing**: close if price closes below EMA20 (for trend trades)

### 5. Time-Based Stop
- If trade not moving in expected direction within X candles → exit
- Prevents capital being tied up in stagnant trades
- Example: 15m scalp → exit after 20 candles if not at 50% TP

---

## RISK/REWARD ANALYSIS

### Minimum R:R Requirements
- Scalp (5m-15m): minimum 1:1.5 (preferably 1:2)
- Swing (1h-4h): minimum 1:2 (preferably 1:3)
- Position (4h+): minimum 1:3

### Win Rate Required for Profitability
```
Breakeven win rate = 1 / (1 + R)
At R:R 1:1 → need 50% win rate
At R:R 1:2 → need 33% win rate
At R:R 1:3 → need 25% win rate
```
This means a strategy with 35% win rate IS profitable at R:R 1:2.

### Expected Value Formula
```
EV = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
Example: 55% WR, avg win $30, avg loss $20
EV = (0.55 × 30) - (0.45 × 20) = 16.5 - 9 = +$7.50 per trade
```
Only trade setups with positive EV.

---

## DRAWDOWN MANAGEMENT

### Daily Loss Limits
- Soft limit: -2% daily → reduce position size by 50%
- Hard limit: -4% daily → stop trading for the day
- Weekly limit: -10% → pause all trading, review strategy

### Consecutive Loss Protocol
- 2 consecutive losses: no change, continue
- 3 consecutive losses: reduce position size by 25%
- 5 consecutive losses: reduce by 50%, review setups
- 7 consecutive losses: stop, full strategy review required

### Drawdown Recovery Math
```
Drawdown % → Required gain to recover:
-10% → need +11.1% gain
-20% → need +25% gain
-30% → need +42.9% gain
-50% → need +100% gain
```
This is why protecting capital is more important than maximizing gains.

---

## PORTFOLIO DIVERSIFICATION WITHIN THE SYSTEM

### Correlation Management
- Don't open LONG positions on multiple highly correlated tokens simultaneously
- BTC + ETH + BNB = highly correlated (avoid all long together)
- BTC + a DeFi token + a GameFi token = lower correlation

### Position Count Rules
- Maximum 3 concurrent positions (prevents overexposure)
- Maximum 2 positions in same sector (DeFi, L1, GameFi)
- If a macro event (FOMC, CPI) is coming → reduce to 1 position

### Budget Allocation
```
Per-trade maximum: 30-50% of available budget (never 100%)
Keep minimum 30% in reserve for opportunities
```

## Configuration Parameters
- `risk_per_trade`: 0.5-2.0% (from personality setting in DB)
- `daily_loss_limit_pct`: 4.0 (hard stop for the day)
- `max_concurrent_positions`: 3
- `kelly_fraction`: 0.25 (1/4 Kelly for crypto)
- `atr_sl_multiplier`: 1.5 (scalp), 2.0 (swing), 3.0 (position)
- `trailing_atr_multiplier`: 2.0 (default trailing stop)
