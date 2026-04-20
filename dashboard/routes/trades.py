"""
dashboard/routes/trades.py

FastAPI routes dla transakcji.
"""
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import APIRouter

from database.db import get_connection

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/open")
async def open_positions():
    """Wszystkie otwarte pozycje z unrealized PnL."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.*, a.personality, a.budget_usdt
            FROM trades t
            JOIN agents a ON t.agent_id = a.id
            WHERE t.status = 'open'
            ORDER BY t.timestamp DESC
        """).fetchall()

    positions = []
    for row in rows:
        p = dict(row)
        try:
            from data.market_feed import get_current_price
            price  = get_current_price(p["token"])
            ep     = float(p["entry_price"])
            size   = float(p["size_usdt"])
            if p["direction"] == "long":
                pnl_pct = (price - ep) / ep * 100
            else:
                pnl_pct = (ep - price) / ep * 100
            p["current_price"]   = price
            p["unrealized_pnl"]  = round(size * pnl_pct / 100, 4)
            p["pnl_pct"]         = round(pnl_pct, 3)
        except Exception:
            p["current_price"]  = None
            p["unrealized_pnl"] = None
            p["pnl_pct"]        = None
        positions.append(p)

    return {"positions": positions, "count": len(positions)}


@router.get("")
async def list_trades(
        limit:    int             = 50,
        agent_id: Optional[str]  = None,
        status:   Optional[str]  = None,
):
    """Historia transakcji z opcjonalnymi filtrami."""
    query  = "SELECT * FROM trades WHERE 1=1"
    params = []

    if agent_id:
        query += " AND agent_id = ?"
        params.append(agent_id)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    trades = [dict(r) for r in rows]

    closed   = [t for t in trades if t["status"] == "closed"]
    wins     = [t for t in closed if (t.get("pnl_usdt") or 0) > 0]
    total_pnl = sum(t.get("pnl_usdt") or 0 for t in closed)

    return {
        "trades": trades,
        "count":  len(trades),
        "stats": {
            "closed":    len(closed),
            "wins":      len(wins),
            "win_rate":  round(len(wins) / len(closed) * 100, 1)
                         if closed else 0,
            "total_pnl": round(total_pnl, 4),
        },
    }
