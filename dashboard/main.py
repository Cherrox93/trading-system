"""
dashboard/main.py

FastAPI dashboard — punkt wejścia.
Uruchomienie: uvicorn dashboard.main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database.db import (
    get_all_agents, get_agent_performance,
    get_recent_logs, get_connection,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Trading System Dashboard", version="1.0.0")


def _get_price_with_fallback(token: str) -> float:
    """get_current_price z fallbackiem do price_cache (odświeżany async co 10s)."""
    from data.market_feed import get_current_price
    from dashboard.price_cache import get as cache_get
    price = get_current_price(token)
    if price and price > 0:
        return price
    return cache_get(token)


async def _price_refresh_loop():
    """Background task — odpytuje Lighter API co 15s, wypełnia price_cache."""
    import httpx
    from dashboard.price_cache import update as cache_update
    async with httpx.AsyncClient(timeout=8) as client:
        while True:
            try:
                r = await client.get(
                    "https://mainnet.zklighter.elliot.ai/api/v1/exchangeStats"
                )
                if r.status_code == 200:
                    prices = {
                        m["symbol"]: float(m["last_trade_price"])
                        for m in r.json().get("order_book_stats", [])
                        if m.get("last_trade_price") and float(m["last_trade_price"]) > 0
                    }
                    cache_update(prices)
            except Exception as e:
                logger.debug(f"price_cache refresh error: {e}")
            await asyncio.sleep(15)


@app.on_event("startup")
async def _startup():
    asyncio.create_task(_price_refresh_loop())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Zarejestruj routes
from dashboard.routes.agents   import router as agents_router
from dashboard.routes.trades   import router as trades_router
from dashboard.routes.control  import router as control_router
from dashboard.routes.knowledge import router as kb_router

app.include_router(agents_router)
app.include_router(trades_router)
app.include_router(control_router)
app.include_router(kb_router)


# ── WebSocket Manager ──────────────────────────────────────

class ConnectionManager:
    """Zarządza aktywnymi połączeniami WebSocket."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.debug(f"WS connected | active: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.debug(f"WS disconnected | active: {len(self.active)}")

    async def broadcast(self, data: dict):
        msg  = json.dumps(data, default=str)
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def _build_snapshot() -> dict:
    """Zbuduj pełny snapshot systemu do wysłania przez WS co 2 sekundy."""
    from dashboard.routes.agents import _get_open_position, _current_action
    agents      = get_all_agents()
    agents_data = []

    total_trades = 0
    for a in agents:
        perf     = get_agent_performance(a["id"])
        open_pos = _get_open_position(a["id"])
        total_trades += perf.get("trades", 0)
        agents_data.append({
            "id":            a["id"],
            "status":        a["status"],
            "personality":   a.get("personality", ""),
            "budget":        float(a["budget_usdt"] or 0),
            "used":          float(a["used_usdt"] or 0),
            "available":     float(a["budget_usdt"] or 0) - float(a["used_usdt"] or 0),
            "pnl":           float(a["pnl_usdt"] or 0),
            "trades":        perf.get("trades", 0),
            "wins":          perf.get("wins", 0),
            "win_rate":      perf.get("win_rate", 0),
            "open_position": open_pos,
            "current_action": _current_action(a["id"], a["status"], open_pos),
        })

    # Otwarte pozycje z unrealized PnL
    try:
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT t.*, a.personality
                FROM trades t
                JOIN agents a ON t.agent_id = a.id
                WHERE t.status = 'open'
                ORDER BY t.timestamp DESC
            """).fetchall()
        open_positions = []
        for row in rows:
            p = dict(row)
            try:
                price = _get_price_with_fallback(p["token"])
                ep    = float(p["entry_price"])
                size  = float(p["size_usdt"])
                lev   = int(p.get("leverage") or 1)
                if price and ep:
                    if p["direction"] == "long":
                        pnl_pct = (price - ep) / ep * 100
                    else:
                        pnl_pct = (ep - price) / ep * 100
                    p["current_price"]  = price
                    p["unrealized_pnl"] = round(size * pnl_pct / 100 * lev, 4)
                    p["pnl_pct"]        = round(pnl_pct * lev, 3)
                else:
                    p["current_price"]  = None
                    p["unrealized_pnl"] = None
                    p["pnl_pct"]        = None
            except Exception:
                p["current_price"]  = None
                p["unrealized_pnl"] = None
                p["pnl_pct"]        = None
            open_positions.append(p)
    except Exception:
        open_positions = []

    # Logi
    logs = get_recent_logs(limit=100)

    # Statystyki — scalper ma oddzielny PnL
    _SCALPER_IDS = {"scalper"}
    total_pnl    = sum(float(a["pnl_usdt"] or 0) for a in agents if a["id"] not in _SCALPER_IDS)
    scalper_pnl  = sum(float(a["pnl_usdt"] or 0) for a in agents if a["id"] in _SCALPER_IDS)
    active_count = sum(1 for a in agents if a["status"] == "active")

    # Market data (jeśli market_feed działa)
    try:
        from data.market_feed import get_all_tokens
        market = get_all_tokens()
    except Exception:
        market = []

    def _fmt_price(p: float) -> float:
        """Zaokrąglij cenę: 2 miejsca dla >10, 4 dla >1, 6 dla mniejszych."""
        if p >= 10:
            return round(p, 2)
        if p >= 1:
            return round(p, 4)
        return round(p, 6)

    market_mini = [
        {
            "symbol":     t["symbol"],
            "price":      _fmt_price(float(t.get("price") or 0)),
            "change_24h": round(float(t.get("change_24h") or 0), 2),
            "rsi":        t.get("indicators", {}).get("rsi_14", 0),
        }
        for t in market
    ]

    return {
        "type":           "snapshot",
        "mode":           settings.TRADING_MODE,
        "total_pnl":      round(total_pnl, 4),
        "scalper_pnl":    round(scalper_pnl, 4),
        "active_agents":  active_count,
        "total_agents":   len(agents),
        "total_trades":   total_trades,
        "open_positions": len(open_positions),
        "agents":         agents_data,
        "positions":      open_positions,
        "logs":           logs,
        "market":         market_mini,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint — pushuje snapshot co 2 sekundy."""
    await manager.connect(ws)
    try:
        while True:
            try:
                snapshot = _build_snapshot()
                await ws.send_text(json.dumps(snapshot, default=str))
            except Exception as e:
                logger.debug(f"WS snapshot error: {e}")
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.debug(f"WS error: {e}")
        manager.disconnect(ws)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect do głównego dashboardu."""
    return HTMLResponse(
        '<meta http-equiv="refresh" content="0; url=/static/index.html">'
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "trading_mode": settings.TRADING_MODE}


@app.get("/system/status")
async def system_status():
    """Status systemu."""
    agents = get_all_agents()
    return {
        "mode":          settings.TRADING_MODE,
        "active_agents": sum(1 for a in agents if a["status"] == "active"),
        "total_agents":  len(agents),
        "total_budget":  sum(float(a["budget_usdt"] or 0) for a in agents),
        "total_pnl":     sum(float(a["pnl_usdt"] or 0) for a in agents),
    }


@app.get("/system/logs")
async def system_logs(limit: int = 50, source: str = None):
    """Ostatnie logi aktywności."""
    logs = get_recent_logs(limit=limit, source=source)
    return {"logs": logs, "count": len(logs)}
