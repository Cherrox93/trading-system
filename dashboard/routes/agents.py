"""
dashboard/routes/agents.py

FastAPI routes dla agentów.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, HTTPException

from database.db import (
    get_all_agents, get_agent,
    get_agent_performance, get_agent_trades,
    get_connection,
)

def _get_price_fallback(token: str) -> float:
    """Cena z price_cache (aktualizowanego async co 10s przez main.py)."""
    from dashboard.price_cache import get as cache_get
    return cache_get(token)


def _get_open_position(agent_id: str) -> dict | None:
    """Zwraca otwartą pozycję agenta z unrealized PnL lub None."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT token, direction, entry_price, sl_price, tp_price,
                      size_usdt, leverage
               FROM trades WHERE agent_id=? AND status='open' LIMIT 1""",
            (agent_id,),
        ).fetchone()

    if not row:
        return None

    pos = {
        "token":       row[0],
        "direction":   row[1],
        "entry_price": float(row[2]),
        "sl_price":    float(row[3]),
        "tp_price":    float(row[4]),
        "size_usdt":   float(row[5]),
        "leverage":    int(row[6] or 1),
        "current_price":   None,
        "unrealized_pnl":  None,
        "pnl_pct":         None,
    }

    try:
        from data.market_feed import get_current_price, SNAPSHOT_PATH
        price = get_current_price(pos["token"])
        if not price:
            import json
            snap = json.loads(SNAPSHOT_PATH.read_text())
            for t in snap.get("tokens", []):
                if t.get("symbol") == pos["token"]:
                    price = float(t.get("price") or 0)
                    break
        if not price:
            price = _get_price_fallback(pos["token"])
        ep   = pos["entry_price"]
        size = pos["size_usdt"]
        if price and price > 0 and ep:
            if pos["direction"] == "long":
                pnl_pct = (price - ep) / ep * 100
            else:
                pnl_pct = (ep - price) / ep * 100
            pos["current_price"]  = price
            pos["unrealized_pnl"] = round(size * pnl_pct / 100 * pos["leverage"], 4)
            pos["pnl_pct"]        = round(pnl_pct * pos["leverage"], 3)
    except Exception:
        pass

    return pos


def _current_action(agent_id: str, status: str, open_pos: dict | None) -> str:
    """Zwraca krótki opis co agent robi w tej chwili."""
    if status == "onboarding":
        return "📚 Reading knowledge base..."
    if status == "pending":
        return "⏳ Waiting to start"
    if status == "paused":
        return "⏸ Paused by supervisor"
    if status == "killed":
        return "🛑 Stopped"
    if status == "error":
        return "⚠️ Error — needs attention"

    if open_pos:
        token     = open_pos["token"]
        direction = open_pos["direction"].upper()
        arrow     = "↑" if direction == "LONG" else "↓"
        return f"👁 Monitoring {token} {arrow} {direction}"

    with get_connection() as conn:
        row = conn.execute(
            "SELECT message FROM activity_log WHERE source=? ORDER BY timestamp DESC LIMIT 1",
            (agent_id,),
        ).fetchone()

    if not row:
        return "🔍 Scanning market..."

    msg = row[0].lower()
    if "enter" in msg:
        return "✅ Entered position"
    if "close" in msg or "closed" in msg:
        return "🔒 Just closed trade"
    if "skip" in msg:
        return "🔍 Scanning — no setup yet"
    if "hold" in msg:
        return "👁 Holding position"
    if "onboarding" in msg or "knowledge" in msg:
        return "📚 Completed onboarding"
    if "timeout" in msg or "error" in msg:
        return "⚡ LLM retry..."
    return "🔍 Scanning market..."


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def list_agents():
    """Lista wszystkich agentów z wynikami."""
    agents = get_all_agents()
    result = []
    for a in agents:
        perf     = get_agent_performance(a["id"])
        open_pos = _get_open_position(a["id"])
        result.append({
            "id":              a["id"],
            "status":          a["status"],
            "personality":     a.get("personality", ""),
            "strategies":      json.loads(a.get("strategies") or "[]"),
            "budget":          a["budget_usdt"],
            "used":            a["used_usdt"],
            "available":       a["budget_usdt"] - a["used_usdt"],
            "pnl":             a["pnl_usdt"],
            "risk_per_trade":  a.get("risk_per_trade", 0.007),
            "onboarding_done": a.get("onboarding_done", 0),
            "performance":     perf,
            "open_position":   open_pos,
            "current_action":  _current_action(a["id"], a["status"], open_pos),
        })
    return {"agents": result, "count": len(result)}


@router.get("/{agent_id}")
async def get_agent_detail(agent_id: str):
    """Szczegóły jednego agenta z historią i korektami."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=404, detail=f"Agent {agent_id} nie istnieje"
        )

    perf   = get_agent_performance(agent_id)
    trades = get_agent_trades(agent_id, limit=20)

    with get_connection() as conn:
        corrections = [dict(r) for r in conn.execute("""
            SELECT * FROM corrections
            WHERE agent_id = ?
            ORDER BY timestamp DESC LIMIT 10
        """, (agent_id,)).fetchall()]

    return {
        "agent":         dict(agent),
        "performance":   perf,
        "recent_trades": trades,
        "corrections":   corrections,
    }
