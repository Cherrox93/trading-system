# Macro Event Filter

## META
- Name: Macro Event Filter
- Category: risk_management
- Difficulty: beginner
- Timeframes: all
- Best Market: all — applied as pre-trade check
- Estimated Win Rate: N/A (filter, not signal)
- Risk Reward: protects capital by avoiding high-uncertainty events
- Tokens: all

## Description
Prevents trading before and during high-impact macro events that cause unpredictable price spikes.
During FOMC, CPI, NFP, and similar events, technical analysis becomes unreliable — price can
move 3-10% in seconds regardless of setup quality.
This filter instructs agents to pause new entries during defined blackout windows.

## High-Impact Events Requiring Full Blackout

### Tier 1 — Full blackout (no new trades, close open positions > 3h before)
- **FOMC** (Federal Open Market Committee) — interest rate decisions, ~8× per year
  - Blackout: 2h before announcement + 1h after
  - Typical impact: 3-8% move in BTC/ETH within minutes
- **US CPI** (Consumer Price Index) — monthly
  - Blackout: 1h before + 30min after
  - Typical impact: 2-5% move
- **US NFP** (Non-Farm Payrolls) — first Friday of month
  - Blackout: 1h before + 30min after
- **Fed Chair Speech** (Jerome Powell press conference post-FOMC)
  - Blackout: during speech + 30min after

### Tier 2 — Reduced position size (50% of normal), no new mean-reversion trades
- **US PPI** (Producer Price Index)
- **US GDP** (quarterly)
- **ECB Rate Decision**
- **US Retail Sales**
- **JOLTS Job Openings**
- Crypto-specific: **Bitcoin Halving** (every 4 years — not dangerous, but very hyped)
- Blackout: 30min before + 15min after

### Tier 3 — Monitor only, no position changes unless strong signal
- **BOJ** (Bank of Japan), **BOE** decisions
- **US Core PCE**
- **Michigan Consumer Sentiment**

## Crypto-Specific Events

### Exchange/Protocol Events (24h blackout when detected)
- Large exchange going offline or halting withdrawals (BankRun risk)
- Major protocol exploit/hack in top 20 token
- Regulatory action (SEC lawsuit, exchange ban in major country)
- Stablecoin depeg event (USDT/USDC losing $0.999 peg)

### On-Chain Events (reduce size 30%)
- Whale movement > 1,000 BTC from cold wallet to exchange (potential sell)
- Large miner outflow detected (>3,000 BTC in 24h)
- ETF net outflows > $500M in single day

## Implementation Logic

### Pre-Trade Check (run before every entry decision)
```
1. Query upcoming macro events for next 2 hours
2. If Tier 1 event within 2h: BLOCK all new entries
3. If Tier 1 event within 1h: CLOSE all open positions that are profitable
4. If Tier 2 event within 30min: BLOCK mean-reversion entries, allow trend-following with 50% size
5. If Tier 3 event within 15min: Log warning, no automatic action

Post-event:
6. After Tier 1 event: wait full cooldown window before resuming
7. After Tier 2 event: wait 15min before resuming
8. If price moved > 3% during event: extend cooldown by additional 1h (still unstable)
```

### Event Calendar Integration
When no live API available, use heuristic schedule:
```
FOMC meetings (2025 schedule reference, verify each year):
- January, March, May, June, July, September, October, December
- Typically Wednesday 14:00 EST (19:00 UTC / 21:00 CET)

CPI releases: Second or third week of each month
- Tuesday 08:30 EST (13:30 UTC / 15:30 CET)

NFP: First Friday of each month
- 08:30 EST (13:30 UTC / 15:30 CET)
```

## Sentiment Integration

### Fear & Greed Index
```
Extreme Fear (< 20): 
  → Reduce SHORT positions (capitulation may be near)
  → Prefer LONG setups with smaller size
  → Good for liquidity sweep LONG entries

Extreme Greed (> 80):
  → Reduce LONG positions
  → Prefer SHORT setups or avoid trend-following longs
  → High risk of sudden deleveraging event

Normal range (20-80): no adjustment
```

### Funding Rate as Sentiment Signal
```
Funding > 0.05% per 8h (annualized 54%+):
  → Market heavily long, crowded trade
  → LONG entries: reduce size 40%, raise bar for entry quality
  → SHORT entries: slight edge (crowding unwind risk)

Funding < -0.03% per 8h:
  → Market heavily short
  → SHORT entries: reduce size 40%
  → LONG entries: slight edge (short squeeze potential)

Funding < -0.08% per 8h:
  → Extreme short: avoid new shorts entirely
```

## When to Override the Filter
**Never override Tier 1 FOMC/CPI blackouts.**
The expected cost of the blackout (missed opportunity) is always less than the expected cost of being wrong-footed in a binary event.

Only valid exception: position already has ≥ 3% profit and stop is at breakeven — can keep (risk-free).

## Configuration Parameters
- `fomc_blackout_before_min`: 120
- `fomc_blackout_after_min`: 60
- `cpi_blackout_before_min`: 60
- `cpi_blackout_after_min`: 30
- `tier2_blackout_before_min`: 30
- `tier2_blackout_after_min`: 15
- `post_event_extension_if_moved_pct`: 3.0
- `post_event_extension_min`: 60
- `funding_long_caution_threshold`: 0.0005
- `funding_short_caution_threshold`: -0.0003
- `funding_short_block_threshold`: -0.0008
- `fear_greed_extreme_threshold`: 20
- `fear_greed_greed_threshold`: 80
