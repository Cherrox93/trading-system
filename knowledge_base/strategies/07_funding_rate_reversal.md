# Funding Rate Reversal

## META
- Name: Funding Rate Reversal
- Category: mean_reversion
- Difficulty: intermediate
- Timeframes: 1h, 4h
- Best Market: any
- Estimated Win Rate: 56-63%
- Risk Reward: 1:2
- Tokens: any

## Description
Funding rate is a fee exchanged between holders of long and short positions on perpetual futures markets.
When funding rate is extremely high (>0.05%), it signals an overcrowded long — too many people holding longs and "overpaying" to maintain their positions.
In this scenario price statistically corrects when long positions are closed under funding cost pressure.
The reverse applies to extremely low funding (< −0.05%) — overcrowded short, expect a bounce upward.

## Entry Conditions

### LONG (extremely negative funding — overcrowded short)
- Funding rate < −0.05% (extreme level — too many shorts)
- RSI (14) < 35 (oversold — price already low)
- Open Interest at or near 30-day maximum
- Price at a key support (S1, POC, historical support)
- Confirming reversal candle (pin bar, bullish engulfing)
- Volume increasing on entry candle

### SHORT (extremely positive funding — overcrowded long)
- Funding rate > +0.05% (extreme level)
- RSI (14) > 65 (overbought)
- Open Interest at 30-day maximum
- Price at a key resistance (R1, VAH, historical resistance)
- Confirming reversal candle (pin bar, bearish engulfing)
- Volume increasing

## Exit Conditions

### Take Profit
- Primary target: funding rate return to neutral zone (−0.01% to +0.01%)
- Price-wise: 2-3% move in position direction
- If OI starts dropping drastically (short squeeze / long liquidation) — close early

### Stop Loss
- LONG: new 24h minimum − 0.5%
- SHORT: new 24h maximum + 0.5%
- Or: funding rate returns to neutral zone without price move (signal expired)

### Trailing Stop
- After reaching 1.5% profit: trailing 0.5% behind price
- Close if funding normalizes before reaching TP

## Confirming Signals
- Long positions being liquidated (visible in liquidation data) — confirmation for SHORT
- Short positions being liquidated — confirmation for LONG
- Funding rate was extreme for 2+ hours (not a one-time spike)
- Other tokens in the same category show similar extreme funding
- CVD (Cumulative Volume Delta) starting to reverse direction

## When NOT to Enter
- Funding 0.03-0.05% — signal too weak, too high false signal risk
- Token in strong fundamental trend (new partnership, upgrade) — FR can stay extreme for long
- Last time FR was extreme, price continued (check history)
- No OI data available (not all platforms provide it)
- Macro news may sustain overcrowded trade

## Risk Management
- Risk per trade: 0.5-0.7% of capital
- This strategy has a long horizon (1-4h) — do not panic on short-term fluctuations
- Max 2 funding reversal positions simultaneously
- Do not enter if funding was extreme for < 2 hours
- Remember: you also PAY funding — entering LONG on negative FR = you receive funding

## Setup Example
```
Token: ARB, timeframe: 1h
Funding rate: −0.072% (extremely negative ✓)
RSI (14): 31 (oversold ✓)
OI: 42M USD (28-day maximum ✓)
Support: 1.7800 (historical level ✓)
Candle: bullish engulfing at 1.7820 ✓

Entry: 1.7850
SL: 1.7500 (−1.96% — new 24h min)
TP: 1.8500 (+3.6%, R:R 1:1.8 ✓)
Expected time to TP: 4-12h
Additional gain: you receive funding instead of paying (SHORT squeeze helps)
```

## Configuration Parameters
- `funding_extreme_long`: threshold for overcrowded long (default +0.05%)
- `funding_extreme_short`: threshold for overcrowded short (default −0.05%)
- `funding_min_hours`: min hours at extreme FR (default 2)
- `rsi_oversold`: RSI threshold for LONG (default 35)
- `rsi_overbought`: RSI threshold for SHORT (default 65)
- `sl_buffer_pct`: buffer behind 24h extreme (default 0.5%)
