# Aggressive Order Flow Analysis

## META
- Name: Aggressive Order Flow Analysis
- Category: orderbook_analysis
- Difficulty: advanced
- Timeframes: 1m, 5m, 15m
- Best Market: trending and transitioning markets
- Estimated Win Rate: 53-60%
- Risk Reward: 1:2
- Tokens: BTC, ETH, SOL (high volume required)

## Description
Analyzes the flow of aggressive (market) orders to identify who is in control — buyers or sellers.
Unlike passive orderbook analysis, flow analysis focuses on EXECUTED trades: where are market
orders landing and how forcefully?
CVD (Cumulative Volume Delta) is the core metric. It separates "buying pressure" from "selling pressure"
over time to reveal institutional accumulation/distribution patterns invisible in price charts.

## Core Metric: Cumulative Volume Delta (CVD)

### What CVD Measures
```
Each trade is classified:
- Buy-initiated (market buy = aggressor): adds +volume to CVD
- Sell-initiated (market sell = aggressor): adds −volume to CVD

CVD = running sum of (buy volume − sell volume)

Rising CVD: net buying pressure (even if price flat = accumulation)
Falling CVD: net selling pressure (even if price rising = distribution warning)
```

### CVD Divergences (Most Powerful Signal)
```
Bullish CVD divergence:
- Price makes lower low
- CVD makes higher low (buyers stepping in at lower prices)
→ Signal: buyers absorbing selling pressure → reversal or bounce coming

Bearish CVD divergence:
- Price makes higher high
- CVD makes lower high (sellers increasing as price rises)
→ Signal: distribution in progress → reversal or correction coming
```

## Delta Bar Analysis

### Reading Individual Candles
```
Each candle has a "delta" = buy volume − sell volume for that period

Large positive delta + green candle: strong bullish confirmation ✓
Large negative delta + red candle: strong bearish confirmation ✓
Large positive delta + red candle: absorption (buyers losing → bearish signal)
Large negative delta + green candle: absorption (sellers losing → bullish signal)
Small delta + large candle body: move driven by passive orders (less reliable)
```

### Volume Clustering
```
At what price levels does the most volume transact?

High volume at resistance + negative delta = distribution → expect breakdown
High volume at support + positive delta = accumulation → expect bounce
High volume at resistance + positive delta = absorption (bulls failing) → bearish
```

## Entry Conditions

### LONG (flow supports buying)
- CVD rising over last 10 bars on entry timeframe (net buying pressure)
- Price at or near support level identified on HTF
- Individual bar deltas: last 3 bars show ≥ 2 bars with positive delta
- No bearish CVD divergence on HTF (1h when using 5m for entry)
- CVD higher high alongside price higher high (confirming move, not distributing)
- Buy/Sell ratio of last 10 trades > 1.3 (recent aggression is bullish)

### SHORT (flow supports selling)
- CVD declining over last 10 bars
- Price at or near resistance level on HTF
- Last 3 bars: ≥ 2 bars with negative delta
- No bullish CVD divergence on HTF
- CVD lower low alongside price lower low
- Sell/Buy ratio of last 10 trades > 1.3

## Advanced Flow Patterns

### Exhaustion Pattern
```
Signal of trend exhaustion before reversal:
- Price continuing in trend direction
- Volume increasing (panic buyers/sellers piling in)
- Delta shrinking (opposite side absorbing)
- CVD flattening or reversing while price still moving

Interpretation: last-minute participants entering, professionals distributing
Enter counter-trend when CVD reversal confirmed by 2 candles
```

### Institutional Absorption
```
Institutions cannot reveal their size — they work orders over time:
- Price drops to support
- Large sell volume prints BUT price barely moves
- CVD shows big negative delta but price holds

= Institutions absorbing supply (buying everything being sold)
→ Strong LONG signal: enter when absorption confirmed (3+ candles)
```

### Stop Run Detection via Flow
```
Classic stop-run signature:
1. Sharp price spike through obvious level
2. Massive volume spike (stops triggered)
3. Delta reverses immediately (market orders in spike direction dry up)
4. CVD turns against the spike within 1-2 candles

→ Enter reversal: stop-run confirmation is strongest flow signal available
→ Works best combined with 08_liquidity_sweep strategy
```

## Exit Conditions

### Take Profit
- When CVD shows divergence against position (distribution if long, accumulation if short)
- At S/R level with flow exhaustion pattern
- When buy/sell ratio drops below 1.1 (aggression fading)

### Stop Loss
- Below entry candle low (LONG) or above entry candle high (SHORT)
- If CVD sharply reverses before SL is hit: exit at market (flow is wrong)
- Max 1.0% from entry

## Interpreting Flow Without Direct CVD Data
If CVD is unavailable, approximate using:
```
Estimate positive delta: candles where close > open (green) × volume
Estimate negative delta: candles where close < open (red) × volume
Rolling sum of estimated delta = approximate CVD
Accuracy: ~70% of true CVD (better than nothing)
```

## Configuration Parameters
- `cvd_lookback_bars`: 10
- `delta_bar_lookback`: 3
- `min_delta_bars_in_direction`: 2
- `buy_sell_ratio_min`: 1.3
- `cvd_divergence_lookback`: 20
- `absorption_candles_confirm`: 3
- `exhaustion_cvd_flatten_candles`: 3
- `max_sl_pct`: 1.0
- `cvd_reversal_exit_enabled`: true
