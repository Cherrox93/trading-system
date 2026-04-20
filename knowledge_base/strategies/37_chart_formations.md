# Chart Formations — Major Patterns

## META
- Name: Chart Formations Trading
- Category: reversal, continuation, breakout
- Difficulty: intermediate
- Timeframes: 1h, 4h, 1d (minimum 20-50 candles to form)
- Best Market: trending and transitional
- Estimated Win Rate: 58-68%
- Risk Reward: 1:2.0 to 1:5.0
- Tokens: BTC, ETH, any with sufficient history

## Description
Chart formations are price patterns that develop over multiple candles/bars, encoding collective market psychology.
They require proper timeframe (too short = noise, too long = rare). The measured move rule gives objective TP.
Most formations have a "measured move" target: the height of the pattern projected in breakout direction.

---

## REVERSAL FORMATIONS

### 1. Head and Shoulders (H&S) — TOP
Structure: three peaks where middle (head) is highest, two shoulders at equal height.
Neckline connects the two troughs between shoulders.
- **Trigger**: price breaks below neckline with increased volume
- **TP (measured move)**: distance from head to neckline, projected DOWN from breakout
- **SL**: above the right shoulder
- **Time to form**: 20-60 candles on 1h, weeks on 4h
- **Win rate**: 65-72% (one of most reliable reversals)

### 2. Inverse Head and Shoulders — BOTTOM
Mirror of H&S: three troughs, middle deepest.
- Neckline connects two peaks between troughs
- **Trigger**: break above neckline + volume surge
- **TP**: head-to-neckline distance projected UP
- **SL**: below the right shoulder
- **Win rate**: 68-74%

### 3. Double Top (M Formation)
Two peaks at approximately the same level, forming resistance.
- **Trigger**: break below the valley between the two tops + volume
- **TP**: height of the formation projected down from neckline
- **SL**: above both tops
- Valid if: peaks within 3% of each other, valley > 10% below peaks
- **Win rate**: 60-65%

### 4. Double Bottom (W Formation)
Two troughs at approximately same level, forming support.
- **Trigger**: break above the peak between the two bottoms
- **TP**: measured move up
- **SL**: below both bottoms
- **Win rate**: 62-68%

### 5. Triple Top / Triple Bottom
Same as double but three tests — stronger reversal signal.
- Three failed attempts to break S/R = high conviction reversal
- **Win rate**: 65-70% (more confirmation than double)

---

## CONTINUATION FORMATIONS

### 6. Bull Flag / Bear Flag
Short consolidation (flag) after strong impulse (pole).
- Flag: parallel channel, slightly counter-trend
- **Entry**: breakout from flag in direction of pole
- **TP (measured move)**: pole length projected from breakout point
- **SL**: opposite side of flag
- **Time**: 5-20 candles (quick consolidation)
- **Win rate**: 65-75% (one of best continuation patterns)

### 7. Bull Pennant / Bear Pennant
Like flag but consolidation forms a triangle (converging trendlines) instead of channel.
- **Entry**: breakout from converging trendlines
- **TP**: pole projected from breakout
- **Win rate**: 60-68%

### 8. Ascending Triangle
Horizontal resistance + rising support trendline.
- **Bullish continuation** (in uptrend) or reversal at base (neutral)
- **Entry**: close above horizontal resistance + volume
- **TP**: triangle height projected up
- **SL**: below last swing low before breakout

### 9. Descending Triangle
Horizontal support + falling resistance.
- **Bearish** — break below support
- **TP**: triangle height projected down

### 10. Symmetrical Triangle
Both trendlines converging, no clear bias.
- **Entry**: breakout direction determines trade
- Higher probability in direction of prior trend
- **TP**: widest part of triangle projected from apex

### 11. Rising Wedge
Both support and resistance sloping UP, but resistance flatter.
- **Bearish** despite upward appearance — buyers weakening
- **Entry**: break below lower trendline
- **Win rate**: 63-68%

### 12. Falling Wedge
Both slopes DOWN, support steeper.
- **Bullish** — sellers exhausting
- **Entry**: break above upper trendline
- **Win rate**: 65-70%

### 13. Cup and Handle
Rounded bottom (cup) followed by small downward consolidation (handle).
- Long-term bullish pattern, 20-100 candle formation
- **Entry**: breakout above handle resistance
- **TP**: cup depth projected up from breakout
- **Win rate**: 65-72%

---

## MEASURED MOVE CALCULATION

For all patterns:
```
TP = Breakout Point + (Pattern Height × 1.0)  [conservative]
TP = Breakout Point + (Pattern Height × 1.5)  [extended]
```
Pattern height = distance from formation's high to low (or head to neckline, etc.)

---

## VOLUME CONFIRMATION RULES
- Volume should DECREASE during formation (consolidation absorbing pressure)
- Volume must INCREASE significantly on breakout candle (ideally 2× average)
- Low-volume breakout = high false breakout risk → wait for retest

## Entry Strategies
1. **Aggressive**: enter on breakout candle close (risk false breakout)
2. **Conservative**: wait for pullback retest of broken level (better R:R, miss some moves)
3. **Split**: 50% on breakout, 50% on retest

## When NOT to Enter
- Formation on very low timeframe (< 15m): too much noise
- Price broke out with single spike candle (news-driven)
- Multiple recent failed breakouts from same level
- Pattern is lopsided (shoulders very unequal, triangle too acute)

## Risk Management
- Risk per trade: 1.0-1.5% (formations can take time to play out)
- If price re-enters pattern after breakout: close position (false breakout)
- Best formation trades run 2-5× the pattern height — be patient with TP

## Configuration Parameters
- `min_pattern_candles`: 15 (minimum candles to form valid pattern)
- `peak_symmetry_tolerance`: 0.03 (3% tolerance for double top/bottom)
- `volume_breakout_multiplier`: 2.0 (breakout candle volume vs average)
- `measured_move_multiplier`: 1.0 (conservative) or 1.5 (extended)
- `entry_type`: "breakout" or "retest" or "split"
