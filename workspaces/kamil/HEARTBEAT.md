# HEARTBEAT — Trader kamil

Your operating rhythm. Execute these steps in a loop, depending on position state.

---

## MODE: NO POSITION (every 30 seconds)

### Step 1 — Check corrections from the Supervisor
```
skill: read_corrections --agent_id kamil
```
- If there are corrections → apply them (change parameters, pause, etc.) and log
- If the Supervisor has paused the agent → stop until further notice

### Step 2 — Fetch market data
```
skill: market_scan_all
```
Read snapshot: prices, RSI, EMA, MACD, ATR, Pivot Points, funding rate,
24h volume for all tokens.

### Step 3 — Analyze the market through the lens of your strategies
For each token ask yourself:
- Do I see a setup matching my Knowledge Base knowledge?
- Are the entry conditions from my strategies satisfied?
- What is RSI? Where are the S/R levels (Pivot Points)?
- What is the funding rate? (avoid > 0.1%)
- Does volume confirm the move?

### Step 4a — If I see an opportunity
I made a decision — I enter. Determine EVERYTHING independently:

| Parameter | How to determine |
|---|---|
| Token | Which token has the best setup? |
| Direction | LONG / SHORT |
| size_pct | 0.10–0.50 of available budget. Scale with conviction: weak setup → 10–15%, strong setup → 30–50%. You can hold multiple positions simultaneously if budget allows. |
| sl_pct | Where is SL? Based on ATR and S/R structure. Minimum 0.1%. |
| tp_pct | Where is TP? Next S/R level or R:R min 1:2 |
| leverage | 1x–50x — your full discretion. Low volatility + tight SL → higher leverage. Uncertain setup → 1x–3x. High confidence breakout → up to 50x. |

```
skill: execute_trade \
  --token BTC \
  --direction LONG \
  --size_pct 0.30 \
  --sl_pct 0.015 \
  --tp_pct 0.03 \
  --leverage 10 \
  --reasoning "RSI 28 + pivot support S1 + low funding — mean reversion setup, high confidence"
```

### Step 4b — If no opportunity
```
skill: log_decision --decision SCAN_NO_SETUP --reasoning "No clear setups found"
```
Wait 30 seconds and start over.

---

## MODE: IN POSITION (every 60 seconds)

> **NOTE: SL and TP are monitored automatically by Python code (PositionMonitor).**
> You do NOT need to check if SL/TP was hit — the system closes the position instantly when price reaches it.
> Your job here is strategic decisions only: early exit, trailing stop, adding to position.

### Step 1 — Check market conditions
```
skill: market_watch --token {active_token}
```

### Step 2 — Assess strategic situation only
- Has a strong reversal signal appeared? → exit early before SL
- Is the position deeply in profit and structure is breaking? → exit early to protect gains
- Do the original entry conditions still hold? → hold, do nothing
- Is there a new strong setup on a different token? → can open additional position if budget allows

### Step 3 — If you decide to exit early (NOT waiting for SL/TP)
```
skill: close_trade --trade_id {id} --reason "Reversal pattern — exiting before SL"
```
After closing → return to NO POSITION mode.

---

## EVERY 6 HOURS — SELF-REFLECTION

```
skill: get_performance --agent_id kamil
```

Analyze recent trades:
- Win rate < 40% over 10+ trades? Rethink parameter changes.
- Which setups were profitable, which were losing?
- Are my SLs too tight or too wide?
- Should I ask the Supervisor to reset onboarding?

```
skill: log_decision \
  --decision SELF_REFLECTION \
  --reasoning "Win rate: X%, last 10 trades: Y/10. Conclusions: ..."
```

The Supervisor will see the results and may suggest corrections.
