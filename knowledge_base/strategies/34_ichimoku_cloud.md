# Ichimoku Cloud System

## META
- Name: Ichimoku Cloud System
- Category: trend_following
- Difficulty: advanced
- Timeframes: 1h, 4h, 1d
- Best Market: trending
- Estimated Win Rate: 55-62%
- Risk Reward: 1:2.5
- Tokens: BTC, ETH, high-volume alts

## Description
Ichimoku Kinko Hyo is a complete trading system providing trend, momentum, support/resistance and signals in one indicator.
Components:
- **Tenkan-sen** (Conversion Line, 9): fast momentum line
- **Kijun-sen** (Base Line, 26): medium-term trend baseline
- **Senkou Span A** (Leading Span A): fast cloud boundary
- **Senkou Span B** (Leading Span B, 52): slow cloud boundary
- **Chikou Span** (Lagging Span): confirms trend by comparing current close to 26 periods ago
The Cloud (Kumo) between Span A and B is the key support/resistance zone.
A bullish cloud: Span A > Span B (green). Bearish cloud: Span B > Span A (red).

## Entry Conditions

### LONG — Full Bullish Alignment
- Price is ABOVE the cloud
- Tenkan-sen is above Kijun-sen (bullish cross or already above)
- Chikou Span is above price from 26 periods ago
- Cloud ahead (26 periods forward) is GREEN (bullish)
- Entry trigger: Tenkan/Kijun bullish cross, or price pullback to Kijun-sen (kiss)

### LONG — Cloud Breakout
- Price closes above the cloud after being inside/below
- Candle close is decisive (> 0.5% above upper cloud boundary)
- Volume > 150% average
- Wait for 1 candle confirmation before entering

### SHORT — Full Bearish Alignment
- Price is BELOW the cloud
- Tenkan-sen below Kijun-sen
- Chikou Span below price from 26 periods ago
- Cloud ahead is RED
- Entry: Tenkan/Kijun bearish cross or price bounce to Kijun resistance

## Exit Conditions

### Take Profit
- Next cloud boundary (if entering below/above cloud)
- Tenkan/Kijun cross in opposite direction (momentum shift)
- For breakout trades: cloud depth × 2 as extension target

### Stop Loss
- LONG: below Kijun-sen (if entering on Kijun kiss)
- LONG breakout: below the cloud (back inside = invalidated)
- SHORT: above Kijun-sen
- ATR(14) × 2.0 maximum

## Confirming Signals
- All 5 components aligned (strongest Ichimoku signal)
- RSI confirming trend direction (> 55 for LONG, < 45 for SHORT)
- MACD aligned with Ichimoku signal
- Volume increasing in trend direction
- No major news in next 4h

## When NOT to Enter
- Price inside the cloud: Ichimoku signals unreliable in the cloud
- Thin cloud (Span A ≈ Span B): weak support/resistance
- Chikou Span conflicting with other signals
- First cloud breakout in ranging market — wait for retest

## Risk Management
- Risk per trade: 1.0-1.5% (wider SLs needed for higher timeframes)
- Best on 4h chart: fewer false signals, better trend quality
- Hold through minor Tenkan/Kijun crosses if Kijun and cloud still support

## Setup Example
```
Token: BTC, 4h chart
Price: 95,000 (above cloud ✓)
Cloud: Span A=92,000, Span B=89,500 (green cloud ✓)
Tenkan: 94,500 > Kijun: 93,200 ✓
Chikou: above price 26 bars ago ✓
Cloud 26 bars forward: green ✓

Setup: price pulls back to Kijun-sen at 93,200 (Kijun kiss)
Bullish candle forms at Kijun ✓
Entry: 93,400
SL: below Kijun −0.5% = 92,735 (0.7% risk)
TP: next resistance / measured move = 98,000 (4.9%)
R:R: 1:7 ✓
```

## Configuration Parameters
- `tenkan_period`: 9 (default)
- `kijun_period`: 26 (default)
- `senkou_b_period`: 52 (default)
- `displacement`: 26 (cloud forward projection)
- `entry_type`: "kijun_kiss" or "tk_cross" or "cloud_breakout"
- `sl_type`: "kijun" or "cloud_edge" or "atr"
