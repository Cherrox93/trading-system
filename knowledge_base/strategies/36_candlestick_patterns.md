# Candlestick Patterns — Complete Reference

## META
- Name: Candlestick Pattern Recognition
- Category: reversal, continuation
- Difficulty: beginner
- Timeframes: 5m, 15m, 1h (higher = more reliable)
- Best Market: any
- Estimated Win Rate: 52-65% (depends on pattern + context)
- Risk Reward: 1:1.5 to 1:3
- Tokens: any

## Description
Candlestick patterns encode supply/demand psychology into visual forms.
They are CONTEXT-DEPENDENT: the same pattern at a key S/R level has 3× higher reliability than in open space.
Always combine with at least one other indicator (volume, RSI, S/R level).
Classification: Reversal (signal change of direction) or Continuation (signal trend resumes).

---

## BULLISH REVERSAL PATTERNS

### 1. Hammer
- Small body in upper 25% of range, long lower wick (2×+ body length), minimal upper wick
- After downtrend, at support
- Confirmation: next candle closes above hammer body
- Win rate at key support: ~62%

### 2. Inverted Hammer
- Small body in LOWER 25% of range, long UPPER wick, at support
- Weaker than hammer, requires strong volume + confirmation candle

### 3. Bullish Engulfing
- Two-candle pattern: small bearish candle followed by large bullish candle that ENGULFS previous body
- Body must engulf (wicks optional), higher volume on second candle
- One of the most reliable reversal signals: win rate 65%+ at key levels

### 4. Morning Star
- Three candles: large bearish, small body (doji-like), large bullish
- Gap between candles (common in futures, optional in crypto)
- Third candle closes above midpoint of first candle
- Very reliable reversal at major lows

### 5. Morning Doji Star
- Same as Morning Star but middle candle is a doji (open = close)
- Stronger signal than regular Morning Star

### 6. Piercing Line
- Two candles: bearish, then bullish opening below previous low but closing above 50% of previous bearish body
- Weaker than engulfing, requires volume confirmation

### 7. Three White Soldiers
- Three consecutive bullish candles, each opening within previous body, each closing near high
- Strong trend reversal / continuation after consolidation
- Volume should increase across the three candles

### 8. Bullish Harami
- Large bearish candle followed by small bullish candle contained within first candle's body
- Reversal of momentum, not full reversal signal — wait for confirmation

### 9. Tweezer Bottom
- Two candles with identical or near-identical lows at a support level
- Rejection of lower prices twice — strong support confirmation

### 10. Dragonfly Doji
- Open = High = Close, entire range is lower wick
- Appears at support, extremely bullish when volume is high

---

## BEARISH REVERSAL PATTERNS

### 11. Shooting Star
- Small body in lower 25% of range, long upper wick, at resistance
- Mirror of Hammer. Volume confirmation important
- Win rate at key resistance: ~60%

### 12. Hanging Man
- Same shape as Hammer but appears AFTER UPTREND at resistance
- Counter-intuitive: bullish-looking candle is bearish signal

### 13. Bearish Engulfing
- Small bullish candle engulfed by large bearish candle
- Most reliable single bearish signal at resistance
- Win rate: 63-67% at key resistance levels

### 14. Evening Star
- Large bullish, small body, large bearish — three-candle top pattern
- Third candle closes below 50% of first candle body

### 15. Dark Cloud Cover
- Bullish candle followed by bearish that opens above previous high, closes below 50% of previous body

### 16. Three Black Crows
- Three consecutive bearish candles, each opening within previous body, closing near low
- Strong reversal after uptrend, trend continuation in downtrend

### 17. Gravestone Doji
- Open = Low = Close, entire range is upper wick at resistance
- Very bearish at tops

### 18. Bearish Harami
- Large bullish candle followed by small bearish candle within previous body

---

## CONTINUATION PATTERNS

### 19. Doji (neutral)
- Open ≈ Close, equal wicks or none
- Indecision: direction depends on following candle
- In strong trend: continuation likely

### 20. Spinning Top
- Small body, wicks on both sides
- Similar to doji: indecision

### 21. Rising Three Methods
- Large bullish candle, three small bearish candles staying within first candle's range, then large bullish
- Continuation of uptrend (institutions absorbing selling pressure)

### 22. Falling Three Methods
- Mirror: large bearish, three small bullish within range, large bearish
- Continuation of downtrend

### 23. On Neck / In Neck
- Bearish candle, bullish candle closing near (not into) previous low — continuation short signal

### 24. Tasuki Gap
- Gap continuation pattern: bullish gap + small pullback that doesn't fill the gap → uptrend resumes

---

## KEY RULES FOR PATTERN TRADING

### Context Requirements (ALL patterns)
1. Pattern must be at a meaningful price level (S/R, Fib, pivot, EMA)
2. Volume on the signal candle must be > 20-bar average (ideally 2×)
3. Pattern must complete (wait for candle close, not in-progress)
4. RSI should not be in extreme zone AGAINST the pattern direction
5. Higher timeframe should agree (or at least not disagree)

### Stop Loss Placement
- Bullish patterns: SL below the wick low of the pattern
- Bearish patterns: SL above the wick high of the pattern
- Add 0.1-0.3% buffer (ATR/20) to avoid stop runs

### Pattern Reliability Ranking (at key S/R levels)
1. Bullish/Bearish Engulfing (65-70%)
2. Morning/Evening Star (63-68%)
3. Hammer / Shooting Star (60-65%)
4. Three Soldiers / Three Crows (60-65%)
5. Harami (52-58%) — requires confirmation
6. Doji (50-55%) — context-dependent

## When NOT to Trade Patterns
- Pattern forms in the middle of a range (no S/R context)
- Volume is below average (institutional disinterest)
- Pattern is tiny relative to ATR (insignificant)
- In last 30 minutes before major macro event

## Risk Management
- Risk per trade: 0.5-1.0% (patterns are entry triggers, not strategies alone)
- Always combine with at least one momentum indicator
- Engulfing + volume + S/R = 3-factor confluence → can use 1.5% risk

## Configuration Parameters
- `min_wick_body_ratio`: 2.0 (wick must be 2× body for hammer/shooting star)
- `engulfing_body_ratio`: 1.1 (engulfing body must be 10%+ larger)
- `volume_confirmation_multiplier`: 1.3 (signal candle volume vs average)
- `sl_buffer_pct`: 0.15 (buffer below/above pattern wick)
