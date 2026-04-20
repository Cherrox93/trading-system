"""
dashboard/routes/control.py

FastAPI routes dla panelu sterowania.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.db import (
    get_agent, update_agent, set_agent_budget,
    log_activity, get_connection,
)

router = APIRouter(prefix="/control", tags=["control"])


# ── Request models ─────────────────────────────────────────

class FundRequest(BaseModel):
    agent_id: str
    amount:   float


class AgentRequest(BaseModel):
    agent_id: str


class SpawnRequest(BaseModel):
    agent_id: str
    budget:   float = 10.0


class ResetRequest(BaseModel):
    agent_id: str


# ── Endpoints ──────────────────────────────────────────────

@router.post("/fund")
async def fund_agent(req: FundRequest):
    """Przydziel / zmień budżet agenta."""
    agent = get_agent(req.agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {req.agent_id} nie istnieje")

    old = agent["budget_usdt"]
    set_agent_budget(req.agent_id, req.amount)
    log_activity(
        "dashboard",
        f"Budzet {req.agent_id}: ${old} -> ${req.amount}",
        "info",
    )
    return {
        "success":    True,
        "agent_id":   req.agent_id,
        "old_budget": old,
        "new_budget": req.amount,
    }


@router.post("/pause")
async def pause_agent(req: AgentRequest):
    """Zatrzymaj agenta (status → paused)."""
    agent = get_agent(req.agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {req.agent_id} nie istnieje")

    update_agent(req.agent_id, status="paused")
    log_activity(
        "dashboard",
        f"Agent {req.agent_id} zatrzymany przez dashboard",
        "info",
    )
    return {"success": True, "agent_id": req.agent_id, "status": "paused"}


@router.post("/resume")
async def resume_agent(req: AgentRequest):
    """Wznów agenta (status → active)."""
    agent = get_agent(req.agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {req.agent_id} nie istnieje")

    update_agent(req.agent_id, status="active")
    log_activity(
        "dashboard",
        f"Agent {req.agent_id} wznowiony przez dashboard",
        "info",
    )
    return {"success": True, "agent_id": req.agent_id, "status": "active"}


@router.post("/spawn")
async def spawn_new_agent(req: SpawnRequest):
    """Utwórz nowego agenta i uruchom onboarding."""
    existing = get_agent(req.agent_id)
    if existing:
        raise HTTPException(400, f"Agent {req.agent_id} juz istnieje")

    from factory.spawn_agent import spawn_agent
    result = await spawn_agent(agent_id=req.agent_id, budget_usdt=req.budget)
    return result


@router.post("/reset")
async def reset_agent(req: ResetRequest):
    """Zresetuj onboarding — agent wybierze nowe strategie."""
    agent = get_agent(req.agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {req.agent_id} nie istnieje")

    from agents.onboarding import reset_onboarding
    ok = await reset_onboarding(req.agent_id)
    if not ok:
        raise HTTPException(500, "Reset nieudany")

    log_activity(
        "dashboard",
        f"Reset onboardingu {req.agent_id} przez dashboard",
        "info",
    )
    return {
        "success":  True,
        "agent_id": req.agent_id,
        "message":  "Onboarding zresetowany — agent wybierze nowe strategie",
    }


@router.delete("/agent/{agent_id}")
async def delete_agent(agent_id: str):
    """Usuń agenta — baza, workspace i wszystkie powiązane dane."""
    if agent_id == "supervisor":
        raise HTTPException(400, "Nie można usunąć supervisora")

    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} nie istnieje")

    with get_connection() as conn:
        conn.execute("DELETE FROM trades      WHERE agent_id = ?", (agent_id,))
        conn.execute("DELETE FROM corrections WHERE agent_id = ?", (agent_id,))
        conn.execute("DELETE FROM activity_log WHERE source  = ?", (agent_id,))
        conn.execute("DELETE FROM agents       WHERE id      = ?", (agent_id,))
        conn.commit()

    # Usuń workspace jeśli istnieje
    import shutil
    ws_path = ROOT / "workspaces" / agent_id
    if ws_path.exists():
        shutil.rmtree(ws_path)

    log_activity(
        "dashboard",
        f"Agent {agent_id} usuniety przez dashboard",
        "info",
    )
    return {"success": True, "agent_id": agent_id, "message": f"Agent {agent_id} usunięty"}


@router.get("/corrections/{agent_id}")
async def get_corrections(agent_id: str):
    """Korekty Supervisora dla agenta."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM corrections
            WHERE agent_id = ?
            ORDER BY timestamp DESC LIMIT 20
        """, (agent_id,)).fetchall()
    return {"corrections": [dict(r) for r in rows]}
