# ICT Premium and Discount Zones

## META
- Name: ICT Premium/Discount Array Positioning
- Category: mean_reversion
- Difficulty: intermediate
- Timeframes: 1h, 4h, 1d
- Best Market: ranging
- Estimated Win Rate: 55-63%
- Risk Reward: 1:2.0
- Tokens: any
- Source: ict_research
- Added: 2026-04-15

## Description
ICT defines Premium and Discount zones using the 50%
Fibonacci midpoint between a swing high and swing low.
Above 50% = Premium (expensive) = institutions SELL.
Below 50% = Discount (cheap) = institutions BUY.
Buy in Discount, sell in Premium — a simple but powerful rule
for filtering the direction of all other ICT setups.
No bullish setup should be taken in the Premium zone, and vice versa.

## Entry Conditions
LONG in DISCOUNT:
- Identify the current swing range (swing high, swing low)
- Calculate 50% Fibo (equilibrium)
- Price below 50% = Discount zone
- Look for bullish OB, FVG, or liquidity sweep
  only when price is in Discount
- Entry at confluence within the Discount zone

SHORT in PREMIUM:
- Price above 50% = Premium zone
- Look for bearish OB, FVG, liquidity sweep
  only when price is in Premium
- Entry at confluence within the Premium zone

Additional levels:
- 79% Fibo = Deep Discount (very cheap — strong bullish)
- 21% Fibo = Deep Premium (very expensive — strong bearish)

## Exit Conditions
### Take Profit
Bullish (from Discount): target = Premium zone or
opposite external liquidity.
Bearish (from Premium): target = Discount zone or
external sell-side liquidity.

### Stop Loss
Below the swing low (bullish from Discount) or
above the swing high (bearish from Premium).

## Confirming Signals
- Higher TF bias aligned (e.g., 4h in Discount when trading 1h)
- OB or FVG in the Discount/Premium area
- Liquidity sweep upon entering the zone

## When NOT to Enter
- Market in a strong trend (Discount/Premium zones can
  be broken quickly)
- No clear swing high/low to define the range
- Entering long in Premium or short in Discount
  (against the rule)

## Risk Management
Risk per trade: 0.7-1.5% of capital.
Premium/Discount is a FILTER for other strategies,
not a standalone strategy. Always use it as
context for entry decisions.

## Setup Example
```
BTC swing range: $62,000 (LL) → $68,000 (HH).
Equilibrium (50%): $65,000. Price at $63,500 = Discount.
Bullish FVG at $63,200–$63,600. Price tests the FVG.
Context: Discount + FVG + 4h uptrend.
Entry LONG @ $63,400, SL @ $61,800, TP @ $67,500.
R:R = 1:2.6.
```

## Configuration Parameters
- `swing_lookback`: how many candles back to search for swing high/low
  (default 50)
- `discount_threshold`: Discount zone threshold in Fibo
  (default 0.50 = 50%)
- `deep_discount`: deep Discount level (default 0.79)
