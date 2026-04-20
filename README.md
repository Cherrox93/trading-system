# Trading System — Autonomous AI Trading Fleet

An autonomous multi-agent trading system for crypto perpetual futures on [Lighter DEX](https://lighter.xyz). A fleet of independently operating AI agents analyzes the market, queries a semantic knowledge base of 48+ trading strategies, and executes trades — all coordinated by a Supervisor agent and observed through a real-time WebSocket dashboard.

> **Status:** Paper trading fully functional. Live trading (Lighter broker) in progress.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         TRADING SYSTEM                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DATA LAYER                                              │    │
│  │  Lighter API (WebSocket + REST) → market_feed.py        │    │
│  │  RSI · EMA · MACD · ATR · Pivot Points (6 timeframes)   │    │
│  │  ↓                                                       │    │
│  │  signal_scanner.py → market_signals.json (Layer 1 LLM)  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  KNOWLEDGE BASE                                          │    │
│  │  48 strategy files (.md) → ChromaDB (sentence-transformers)  │
│  │  Semantic search · Idempotent ingest · 15min query cache │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AGENTS LAYER  (OpenClaw runtime)                        │    │
│  │  Supervisor (6h quick · 24h full review)                 │    │
│  │  TraderAgent × N  (heartbeat 30s no-pos · 60s in-pos)   │    │
│  │  LLM: Gemini Flash Lite (fast) · DeepSeek R1 (deep)     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  EXECUTION LAYER                                         │    │
│  │  trade_executor.py → paper_broker / lighter_broker       │    │
│  │  position_monitor.py  (SL/TP checks every 2s, no LLM)   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────┐    │
│  │  SQLite (5 tables)   │   │  Dashboard  FastAPI + WS      │    │
│  │  agents · trades     │   │  localhost:8000               │    │
│  │  corrections · logs  │   │  Overview · Agents · Positions│    │
│  │  market_snapshots    │   │  Market · Logs · Knowledge    │    │
│  └──────────────────────┘   └──────────────────────────────┘    │
│                                                                  │
│  Telegram Bot  (/status · /agents · /new · /pause · /resume)    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Multi-Agent Fleet
- Unlimited autonomous **TraderAgents** spawned on demand (API, Python, Telegram)
- Each agent has an isolated **workspace** (`SOUL.md` + `HEARTBEAT.md`) — its identity and operational rhythm
- Every agent reads the knowledge base through a randomized **lens** during onboarding, so no two agents think alike
- Agents perform **self-reflection** every 6 hours: review their own win rate, SL efficiency, and request strategy resets if needed

### Hybrid LLM Stack
| Role | Primary | Fallback |
|---|---|---|
| Fast analysis (setup scan) | Gemini 2.5 Flash Lite | Groq Llama 4 Scout |
| Deep thinking (entry decision) | DeepSeek R1 | Gemini |
| KB import (text + vision) | Groq Llama 4 Scout | — |

All three providers share the **OpenAI-compatible API interface** — only `base_url` and `api_key` differ.

### Semantic Knowledge Base
- **48 strategy documents** covering mean reversion, trend following, scalping, liquidity sweeps, funding rate reversals, and more
- Stored in **ChromaDB** with `sentence-transformers/all-MiniLM-L6-v2` embeddings
- Idempotent ingest: compares file count vs. collection size, skips if up to date
- Query results cached per `hash(query)` for 15 minutes to reduce embedding overhead

### Agent Onboarding (SAM — Self-Assessment Model)
```
1. Fetch all 48 strategies from Knowledge Base
2. Pick a random "lens" (7 perspectives: momentum, mean-reversion,
   scalping, macro structure, order flow, risk mgmt, on-chain data)
3. DeepSeek R1 call → agent defines its own trading identity:
   { self_identity, trading_philosophy, focus_areas, avoid }
4. Persist to SQLite: strategies[], reasoning, strategy_notes
```
Result: each agent develops a distinct personality and edge.

### Two-Layer Signal Pipeline
```
Layer 1 — Signal Scanner (Python, every 15s):
  price delta > 1.2%  |  volume spike > 3×  |  RSI extreme < 25 / > 75
  MACD crossover  |  pivot bounces  |  EMA crosses
  → dedup + cooldown → batch LLM pre-filter → market_signals.json

Layer 2 — Agent Decision (DeepSeek R1, per signal):
  Read signal + market context + own strategies
  → entry / skip  |  token · direction · size · SL · TP · leverage
```

### Zero-LLM Position Monitoring
A dedicated background task checks open positions **every 2 seconds** against current prices (snapshot → cache → API). SL/TP auto-close happens instantly — no LLM token cost, no latency.

### Paper / Live Switch
```python
# trade_executor.py — the only routing point
if settings.IS_PAPER:
    return paper_broker.execute(order)
else:
    return lighter_broker.execute(order)
```
Switch via `.env` only. No code changes required.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | OpenClaw |
| Fast LLM | Gemini 2.5 Flash Lite · Groq Llama 4 Scout (fallback) |
| Deep LLM | DeepSeek R1 via OpenRouter |
| KB importer | Groq Llama 4 Scout (text + vision) |
| Knowledge Base | ChromaDB + sentence-transformers |
| Technical indicators | pandas-ta (RSI, EMA, MACD, ATR, Pivot Points) |
| DEX | Lighter.xyz Python SDK |
| Web framework | FastAPI + uvicorn |
| Real-time UI | WebSocket (push every 2s) |
| Database | SQLite |
| Alerts & control | Telegram Bot (long polling) |
| Deployment | Docker Compose |

---

## Project Structure

```
trading-system/
├── main.py                     # Entry point — orchestrates all async tasks
├── config/
│   └── settings.py             # Single source of truth for all env vars
├── agents/
│   ├── trader.py               # Autonomous trader agent logic
│   ├── supervisor.py           # Fleet supervisor (6h/24h review cycles)
│   └── onboarding.py           # SAM: agent self-definition via KB + LLM
├── data/
│   ├── market_feed.py          # Lighter WebSocket + REST, indicators, snapshot
│   └── signal_scanner.py       # Layer 1 LLM: pre-filter market signals
├── execution/
│   ├── trade_executor.py       # Paper/live router (DO NOT MODIFY)
│   ├── paper_broker.py         # Full simulation (PnL, leverage, SL/TP)
│   ├── lighter_broker.py       # Live DEX execution (stub)
│   └── position_monitor.py     # Background SL/TP monitor (no LLM)
├── knowledge_base/
│   ├── ingest.py               # Load strategies into ChromaDB
│   ├── query.py                # Semantic search API
│   └── strategies/             # 48 strategy .md files
├── factory/
│   └── spawn_agent.py          # Create + onboard new agents
├── database/
│   ├── db.py                   # All SQLite access (single entry point)
│   └── schema.sql              # 5 tables: agents, trades, corrections, logs, snapshots
├── dashboard/
│   ├── main.py                 # FastAPI app + WebSocket broadcast
│   ├── routes/                 # REST endpoints: agents, trades, control, kb
│   └── static/index.html       # Dark-mode UI (6 tabs, real-time)
├── telegram/
│   ├── reporter.py             # Outbound reports (daily summary, trade alerts)
│   └── commands.py             # Inbound commands (/status, /new, /pause...)
├── workspaces/
│   ├── trader_template/        # SOUL.md + HEARTBEAT.md template
│   └── supervisor/             # Supervisor workspace
├── tests/                      # Unit tests (onboarding, trader, supervisor, telegram)
└── deploy/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── deploy.sh
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- API keys: Gemini (required) + Groq (required) + DeepSeek (optional, live mode)
- Optional: Telegram bot token, Lighter private key (live mode)

### Local Setup

```bash
# 1. Clone and install
git clone https://github.com/your-username/trading-system.git
cd trading-system
pip install -r deploy/requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in at minimum: GEMINI_API_KEY, GROQ_API_KEY

# 3. Load the knowledge base
python knowledge_base/ingest.py
# → "Knowledge Base ready — 48 strategies loaded"

# 4. Spawn your first agents
python factory/spawn_agent.py --id trader_01 trader_02 trader_03 --budget 1000 --sequential

# 5. Start the system
python main.py
# → Dashboard: http://localhost:8000
```

### Docker

```bash
# Build and start
docker compose -f deploy/docker-compose.yml up -d

# Logs
docker compose -f deploy/docker-compose.yml logs -f core

# Scale traders
docker compose -f deploy/docker-compose.yml up -d --scale trader=5
```

### Spawn Agents Dynamically

```bash
# REST API
curl -X POST http://localhost:8000/control/spawn \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "trader_04", "budget": 500}'

# Telegram
/new trader_04 500
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `TRADING_MODE` | `paper` or `live` | Yes |
| `GEMINI_API_KEY` | Gemini 2.5 Flash Lite — fast LLM | Yes |
| `GROQ_API_KEY` | Groq — fast LLM fallback + KB import | Yes |
| `OPENROUTER_API_KEY` | DeepSeek R1 free via OpenRouter | Onboarding |
| `DEEPSEEK_API_KEY` | DeepSeek direct — deep LLM | Live mode |
| `LIGHTER_PRIVATE_KEY` | Wallet private key | Live only |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Optional |
| `TELEGRAM_CHAT_ID` | Your chat ID from @userinfobot | Optional |
| `DASHBOARD_PORT` | Dashboard port (default: 8000) | Optional |
| `DATABASE_PATH` | SQLite path | Optional |
| `CHROMADB_PATH` | ChromaDB path | Optional |
| `MIN_VOLUME_USD` | Token discovery volume filter | Optional |

---

## Dashboard

Real-time WebSocket dashboard (push every 2 seconds):

| Tab | Content |
|---|---|
| **Overview** | Total PnL · active agents · open positions · mode badge (PAPER/LIVE) |
| **Agents** | Cards with budget · PnL · win rate · current action |
| **Positions** | Open trades: entry price · current price · unrealized PnL % |
| **Market** | Animated ticker: symbol · price · 24h change · RSI |
| **Logs** | Real-time activity stream (50 most recent events) |
| **Knowledge** | KB summary and semantic search |

---

## Telegram Commands

| Command | Action |
|---|---|
| `/status` | System overview (mode, agents, PnL, open positions) |
| `/agents` | Full agent list with performance metrics |
| `/agent {id}` | Single agent detail |
| `/trades {id}` | Recent trades for an agent |
| `/new {id} {budget}` | Spawn and onboard a new agent |
| `/pause {id}` | Pause an agent |
| `/resume {id}` | Resume a paused agent |

---

## Agent Lifecycle

```
spawn_agent()
    ↓
Copy workspace template → /workspaces/{agent_id}/
    ↓
Register in SQLite (status: pending)
    ↓
Onboarding: read all 48 strategies through random lens
    → DeepSeek R1: define self_identity + focus_areas
    → Persist strategies to SQLite
    ↓
Status: active
    ↓
Heartbeat loop:
    NO POSITION (every 30s):
        read_corrections() → market_scan_all() → LLM decision
        → execute_trade()  OR  log(SCAN_NO_SETUP)

    IN POSITION (every 60s):
        market_watch(token) → assess → early_exit?  OR  hold
        [SL/TP handled by position_monitor.py in background]

    EVERY 6 HOURS:
        self_reflection() → review win rate, SL efficiency
        → adjust strategy  OR  request supervisor review
```

---

## Strategy Knowledge Base

48 strategy documents organized into categories:

| Category | Examples |
|---|---|
| Mean Reversion | Pivot Point MR · RSI Divergence · VWAP Reversion · Bollinger Squeeze |
| Trend Following | EMA Crossover · Breakout Consolidation · MACD Momentum |
| Scalping | Wick Rejection · Fast Move Scalp · 1m–5m setups |
| Liquidity | Volume Profile · Liquidity Sweep · Order Flow Imbalance |
| On-chain / Crypto-specific | Funding Rate Reversal · Open Interest divergence |
| Price Action | Pin Bar · Inside Bar · Double Bottom/Top |

Each strategy file defines: entry conditions (LONG/SHORT), exit conditions (SL/TP/trailing), confirming signals, estimated win rate, preferred timeframes, and best market regime.

---

## Design Decisions

**Why `market_snapshot.json` as shared state?**
Multiple async processes (scanner, dashboard, broker) need current prices and indicators. A shared JSON file updated every 1–5 seconds is simpler and more resilient than a pub/sub bus for this use case.

**Why no LLM in position monitoring?**
SL/TP decisions are deterministic — no analysis required. Running a background Python loop every 2 seconds eliminates thousands of LLM calls per day and gives sub-second execution on stops.

**Why per-agent workspaces?**
OpenClaw runtime requires each agent to have its own `SOUL.md` (identity) and `HEARTBEAT.md` (operational loop). This also enables the Supervisor to inspect and patch individual agent instructions without touching code.

**Why randomized onboarding lenses?**
If every agent reads the same 48 strategies in the same order, they converge toward the same setups and cluster into correlated positions. Random lenses force behavioral diversity across the fleet.

---

## Current Status

| Component | Status |
|---|---|
| Market feed (WebSocket + REST) | ✅ Complete |
| Technical indicators (6 timeframes) | ✅ Complete |
| Knowledge Base (48 strategies) | ✅ Complete |
| Agent onboarding (SAM) | ✅ Complete |
| Paper broker (simulation) | ✅ Complete |
| Position monitor (SL/TP) | ✅ Complete |
| Real-time dashboard | ✅ Complete |
| Telegram bot | ✅ Complete |
| Signal scanner (Layer 1 LLM) | ⚠️ Partial |
| Supervisor logic | ⚠️ In progress |
| Live broker (Lighter SDK) | 🔲 Stub — next milestone |

---

## License

MIT
