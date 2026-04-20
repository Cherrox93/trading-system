# Multi-Timeframe Confluence

## META
- Name: Multi-Timeframe Confluence
- Category: hybrid
- Difficulty: advanced
- Timeframes: 5m, 15m, 1h
- Best Market: any
- Estimated Win Rate: 60-67%
- Risk Reward: 1:2.5
- Tokens: any

## Description
The "everything aligns" strategy — entry ONLY when signals from at least 3 different timeframes and different indicators all point to the same direction.
Confluence dramatically increases win rate (60-67%) at the cost of rare setups.
Requires more time to identify, but it is the most effective of all 20 strategies.
Motto: "Less often but more surely."

## Entry Conditions

### Required Confluence for LONG (ALL must be satisfied)

**Timeframe 1h (Trend — macro direction):**
- EMA 9 > EMA 21 > EMA 50 (trend alignment bullish)
- Price above EMA 50
- RSI (14) on 1h: 45-65 (not overbought)

**Timeframe 15m (Momentum — medium):**
- Price at key S/R support on 15m
- MACD: MACD line > Signal (bullish momentum)
- Volume: rising for last 3 candles

**Timeframe 5m (Entry — precision):**
- Clear reversal formation: pin bar, engulfing, inside bar breakout
- RSI (14) on 5m: < 45 (local dip — good entry)
- Entry candle volume: >130% of 20-candle average

**Additional verification:**
- Funding rate: neutral or slightly negative (0.00% to −0.02%)
- Level on 5m coincides with level on 15m AND 1h (triple confluence)

### Required Confluence for SHORT (all reversed)
- 1h: EMA alignment bearish, price < EMA 50, RSI 35-55
- 15m: price at resistance, MACD bearish, volume rising
- 5m: bearish reversal formation, RSI > 55
- Funding rate: neutral or slightly positive

## Exit Conditions

### Take Profit
- Target 1 (40%): 1× risk (psychological breakeven)
- Target 2 (40%): 2× risk
- Target 3 (20%): 3× risk (aggressive, in strong trend)
- Close if confluence on any TF starts breaking down

### Stop Loss
- Set behind the confluence level (behind the S/R that generated the signal)
- Typically: 0.5-0.8% from entry (precise — high setup confidence)
- Never wider than 1.2% (if level is that far — wait for better setup)

### Trailing Stop
- After reaching Target 1: move SL to breakeven
- After reaching Target 2: trailing stop behind EMA 21 on 15m

## Confirming Signals
- 4th confirming timeframe (4h macrotrend bullish for LONG)
- Volume Profile POC alignment with entry level
- RSI divergence on at least one TF
- Open Interest neutral or rising in setup direction
- Token outperforming BTC on 1h timeframe

## When NOT to Enter
- Even one of 3 TFs does not confirm (no exceptions to confluence rule)
- Setup is "almost ready" — wait or skip
- Fundamental news within 1h
- Three consecutive confluence trades were losing — review parameters

## Risk Management
- Risk per trade: 0.7% of capital (highest in system — justified by 60-67% WR)
- This strategy is rare: max 1-2 setups per day per token
- Max 3 confluence positions simultaneously (on different tokens)
- Do not "lower standards" when there has been no setup for a while — quality > quantity
- Keep a log of how many confluence points each setup satisfied (optimization)

## Full Setup Example

```
Token: WLD, 10:30 UTC

=== 1H ANALYSIS ===
EMA9=1.2480, EMA21=1.2350, EMA50=1.2100 (aligned bullish ✓)
Price=1.2380 > EMA50 ✓
RSI 1h: 52 (neutral ✓)
Conclusion 1h: BULLISH TREND

=== 15m ANALYSIS ===
Support 15m: 1.2360 (4 previous touches)
Price at 1.2365 (at support ✓)
MACD 15m: line > signal (+0.003) ✓
Volume 3 candles: 92, 107, 124 (rising ✓)
Conclusion 15m: BULLISH MOMENTUM at support

=== 5m ANALYSIS ===
Pin bar at 1.2358 (low wick −0.25% under support, close 1.2382)
RSI 5m: 42 (local dip ✓)
Pin bar volume: 138% of average ✓
Conclusion 5m: BULLISH ENTRY SIGNAL

=== CONFLUENCE CHECK ===
✓ 1h trend bullish
✓ 15m momentum bullish + at support
✓ 5m pin bar + RSI dip
✓ Level 1.2360 visible on all 3 TFs
✓ Funding rate: +0.003% (neutral)
SETUP COMPLETE — ENTER

Entry: 1.2382
SL: 1.2340 (0.3% under confluence level = 0.34% risk)
TP1: 1.2424 (+0.34%) — psychological breakeven
TP2: 1.2466 (+0.68%, R:R 1:2 ✓)
TP3: 1.2550 (+1.36%, R:R 1:4 — aggressive)
```

## Configuration Parameters
- `require_all_timeframes`: all TFs must confirm (default True)
- `timeframes`: list of TFs for analysis (default ['5m', '15m', '1h'])
- `min_confluence_score`: min confluence points (default 6/6 — all)
- `sl_max_pct`: max SL (default 1.2%)
- `tp1_r_multiple`: TP1 = R×1 (default 1.0)
- `tp2_r_multiple`: TP2 = R×2 (default 2.0)
- `tp3_r_multiple`: TP3 = R×3 (default 3.0)
- `funding_max_abs`: max |funding rate| (default 0.02%)
