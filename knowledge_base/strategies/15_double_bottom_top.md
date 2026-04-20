# Double Bottom / Double Top

## META
- Name: Double Bottom / Double Top
- Category: mean_reversion
- Difficulty: beginner
- Timeframes: 15m, 1h
- Best Market: any
- Estimated Win Rate: 56-62%
- Risk Reward: 1:2
- Tokens: any

## Description
Double Bottom (W pattern) and Double Top (M pattern) are classic trend reversal formations.
Double Bottom: price forms two similar bottoms (second bottom with higher RSI = divergence), then breaks the "neckline" (resistance between bottoms) with volume.
Double Top: price forms two similar peaks (second with weaker RSI), then breaks the neckline (support).
These formations are among the best-proven and most easily recognized by the market.

## Entry Conditions

### LONG (Double Bottom)
- First bottom: clear swing low after decline
- Second bottom: similar price level (±0.5% from first bottom)
- RSI at second bottom higher than at first (bullish divergence ✓)
- Price breaks neckline (local swing high between bottoms) with close above
- Neckline break candle volume >140% of average
- Time between bottoms: minimum 6 candles on used TF

### SHORT (Double Top)
- First peak: clear swing high after rise
- Second peak: similar level (±0.5% from first)
- RSI at second peak lower (bearish divergence ✓)
- Price breaks neckline (local swing low between peaks)
- Break candle volume >140% of average
- Time between peaks: minimum 6 candles

## Exit Conditions

### Take Profit
- Classic method: TP = neckline ± (neckline - bottom/peak)
- That is: distance from bottom to neckline projected upward from neckline
- TP1 (50%): 50% of full projected move
- TP2 (50%): 100% projected move (classic target)

### Stop Loss
- LONG: 0.3% below the lowest of the two bottoms
- SHORT: 0.3% above the highest of the two peaks
- If formation is "wide" and SL too large (>2%) — skip setup

### Trailing Stop
- After reaching TP1: trailing stop at neckline (now turned into support)
- If neckline retest with volume — add to position

## Confirming Signals
- RSI divergence is mandatory for high-quality setup
- Volume rising at neckline break (critical!)
- MACD histogram reversing direction at second bottom/peak
- Second bottom/peak does not break first (if it does = formation invalidated)
- Formation time: optimally 1-4 hours on 15m TF

## When NOT to Enter
- Second bottom clearly lower than first (this is not Double Bottom — trend continuation)
- No neckline break — do not enter anticipating (wait for confirmation!)
- Breakout volume < 120% of average (weak confirmation)
- Formation too small: neckline-to-bottom distance < 1% (TP too small)
- Neckline at key S/R that was never broken before (hard block)
- RSI shows no divergence (formation without divergence = lower probability)

## Risk Management
- Risk per trade: 0.6-0.7% of capital (higher WR)
- Do not enter while bottom/peak is forming — ALWAYS wait for neckline break
- Max 2 D-bottom/D-top open simultaneously
- Daily limit: max 4 trades with this strategy

## Setup Example
```
Token: WLD, timeframe: 15m
Trend before formation: bearish (price falling for 2h)

First bottom: 1.1900 (swing low 14:00 UTC)
RSI at first bottom: 28

Rise to neckline: 1.2150

Second bottom: 1.1920 (swing low 15:30 UTC, ±0.17% from first ✓)
RSI at second bottom: 33 (higher than 28 = bullish divergence ✓)
Time between bottoms: 18 × 5m candles ✓

Neckline: 1.2150
Break candle: close 1.2175 ✓
Volume: 152% of average ✓

Entry: 1.2175 (at neckline break close)
SL: 1.1885 (lower of bottoms − 0.3% = 2.37% risk — TOO WIDE!)
  Correction: use SL 0.7% = 1.2090 (acceptable, 0.70% risk)
  But invalidates setup if price pulls back to 1.2090 instead of below 1.1885

TP1: 1.2150 + (1.2150 − 1.1920) × 0.5 = 1.2265 (+0.74%)
TP2: 1.2150 + (1.2150 − 1.1920) = 1.2380 (+1.68%)
R:R: TP2 = 1:2.4 ✓
```

## Configuration Parameters
- `bottom_tolerance_pct`: allowable deviation between bottoms (default 0.5%)
- `min_candles_between`: min candles between bottoms (default 6)
- `volume_multiplier`: min volume at break (default 1.4)
- `require_rsi_divergence`: require RSI divergence (default True)
- `sl_type`: 'pattern_low' (under bottom) or 'fixed_pct' (default 'fixed_pct')
- `sl_fixed_pct`: SL if fixed (default 0.7%)
- `tp1_fraction`: projected fraction for TP1 (default 0.5)
