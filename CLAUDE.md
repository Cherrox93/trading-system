# TRADING SYSTEM — INSTRUKCJE DLA CLAUDE CODE

## Opis projektu

Autonomiczny system tradingowy AI złożony z floty agentów (TraderAgent)
zarządzanych przez Supervisora. Agenci analizują rynek na Lighter DEX,
podejmują decyzje tradingowe przez LLM (Groq fast + DeepSeek deep)
i uczą się strategii z Knowledge Base (ChromaDB). Dashboard FastAPI
w czasie rzeczywistym przez WebSocket.

## Struktura plików

```
trading-system/
├── main.py                    # punkt startowy systemu
├── .env                       # konfiguracja (nie commituj!)
├── .env.example               # szablon zmiennych
├── config/
│   └── settings.py            # wszystkie ustawienia — jedyne źródło prawdy
├── agents/
│   ├── trader.py              # autonomiczny agent tradingowy
│   ├── supervisor.py          # nadzorca floty agentów
│   └── onboarding.py          # nauka strategii z KB przy starcie
├── data/
│   └── market_feed.py         # dane rynkowe (Lighter REST + WebSocket)
├── execution/
│   ├── trade_executor.py      # wybór brokera paper/live
│   ├── paper_broker.py        # symulacja transakcji
│   └── lighter_broker.py      # live DEX
├── knowledge_base/
│   ├── ingest.py              # ładowanie strategii do ChromaDB
│   ├── query.py               # odpytywanie KB
│   └── strategies/            # pliki .md ze strategiami
├── factory/
│   └── spawn_agent.py         # tworzenie nowego agenta
├── database/
│   ├── db.py                  # dostęp do SQLite
│   └── schema.sql             # schemat tabel
├── dashboard/
│   ├── main.py                # FastAPI app + WebSocket
│   ├── routes/                # REST API endpoints
│   └── static/index.html      # frontend (5 tabs)
├── telegram/
│   ├── reporter.py            # wysyłanie raportów
│   └── commands.py            # long polling bot
├── workspaces/
│   ├── trader_template/       # szablon workspace nowego agenta
│   └── supervisor/            # workspace Supervisora
├── tests/                     # testy jednostkowe
└── deploy/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── deploy.sh
```

## Uruchomienie lokalne (bez Docker)

```bash
# 1. Zainstaluj zależności
pip install -r deploy/requirements.txt

# 2. Skonfiguruj środowisko
cp .env.example .env
# uzupełnij co najmniej GROQ_API_KEY

# 3. Uruchom system
python main.py

# Dashboard dostępny na: http://localhost:8000
```

## Uruchomienie z Docker

```bash
# Build + start
docker compose -f deploy/docker-compose.yml up -d

# Logi
docker compose -f deploy/docker-compose.yml logs -f core

# Skalowanie traderów
docker compose -f deploy/docker-compose.yml up -d --scale trader=5

# Stop
docker compose -f deploy/docker-compose.yml down
```

## Jak dodać nowego agenta

```bash
# Przez API (zalecane)
curl -X POST http://localhost:8000/control/spawn \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "trader_04", "personality": "neutral", "budget": 100}'

# Przez Python
from factory.spawn_agent import spawn_agent
await spawn_agent("trader_04", personality="cautious", budget_usdt=100)

# Przez Telegram
/new trader_04 neutral 100
```

Każdy nowy agent automatycznie przechodzi onboarding (nauka strategii z KB).

## Jak przełączyć na live mode

1. Uzupełnij `.env`:
   ```
   TRADING_MODE=live
   LIGHTER_PRIVATE_KEY=0x...
   LIGHTER_NETWORK=mainnet
   DEEPSEEK_API_KEY=...
   GROQ_API_KEY=...
   ```
2. Przetestuj jeden agent z małym budżetem ($10)
3. Obserwuj logi i Telegram

## Ważne zasady

- **Nie zmieniaj logiki LLM** — prompty w `_build_*_prompt()` są skalibrowane
- **Nie dodawaj filtrów sygnałów** — agenci sami oceniają jakość setupu
- **Przełącznik paper/live TYLKO przez `.env`** — nigdy w kodzie
- **Nowy agent zawsze przez `spawn_agent.py`** — nie twórz workspace ręcznie
- **Pliki których nie ruszasz bez pytania:**
  - `database/schema.sql`
  - `config/settings.py`
  - `execution/trade_executor.py`
  - `agents/onboarding.py`

## Stack technologiczny

| Komponent       | Technologia                          |
|-----------------|--------------------------------------|
| Agent framework | OpenClaw                             |
| LLM głęboki     | DeepSeek R1 (via OpenRouter, darmowy)|
| LLM szybki      | Gemini 2.5 Flash Lite (primary) + Groq Llama4 Scout (fallback) |
| KB Importer     | Groq Llama4 Scout (text + vision)    |
| Knowledge Base  | ChromaDB + sentence-transformers     |
| DEX             | Lighter.xyz Python SDK               |
| Baza danych     | SQLite (database/db.py)              |
| Dashboard       | FastAPI + WebSocket                  |
| Alerty          | Telegram Bot (long polling)          |
| Deploy          | Docker Compose                       |

## Zmienne środowiskowe

| Zmienna               | Opis                              | Wymagana     |
|-----------------------|-----------------------------------|--------------|
| `TRADING_MODE`        | `paper` lub `live`                | tak          |
| `GEMINI_API_KEY`      | Gemini 2.5 Flash Lite — fast LLM (primary) | tak   |
| `GROQ_API_KEY`        | Groq — fast LLM fallback + KB importer     | tak   |
| `OPENROUTER_API_KEY`  | OpenRouter — DeepSeek R1 free     | onboarding   |
| `DEEPSEEK_API_KEY`    | DeepSeek direct — deep LLM        | live mode    |
| `LIGHTER_PRIVATE_KEY` | Klucz prywatny wallet             | tylko live   |
| `TELEGRAM_BOT_TOKEN`  | Token bota (@BotFather)           | opcjonalna   |
| `TELEGRAM_CHAT_ID`    | Twoje chat ID (@userinfobot)      | opcjonalna   |
| `DASHBOARD_PORT`      | Port dashboardu (domyślnie 8000)  | opcjonalna   |
| `DATABASE_PATH`       | Ścieżka do SQLite                 | opcjonalna   |
| `CHROMADB_PATH`       | Ścieżka do ChromaDB               | opcjonalna   |
