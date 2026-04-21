"""
Wszystkie operacje na bazie danych.
Jeden punkt dostępu do SQLite dla całego systemu.
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from config import settings

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicjalizuj bazę danych ze schematu."""
    schema_path = Path(__file__).parent / "schema.sql"
    with get_connection() as conn:
        conn.executescript(schema_path.read_text())
        # Migracja — dodaj kolumny jeśli nie istnieją (dla istniejących baz)
        for migration in [
            "ALTER TABLE agents ADD COLUMN strategy_notes TEXT",
            "ALTER TABLE agents ADD COLUMN personal_notes TEXT",
            "ALTER TABLE trades ADD COLUMN leverage INTEGER DEFAULT 1",
            (
                "CREATE TABLE IF NOT EXISTS journal_queue ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "timestamp TEXT DEFAULT (datetime('now')), "
                "agent_id TEXT NOT NULL, "
                "trade_json TEXT NOT NULL, "
                "close_reason TEXT NOT NULL, "
                "status TEXT DEFAULT 'pending', "
                "attempts INTEGER DEFAULT 0, "
                "last_error TEXT)"
            ),
            "CREATE INDEX IF NOT EXISTS idx_jq_status ON journal_queue(status)",
        ]:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass  # kolumna już istnieje
    logger.info(f"Baza danych zainicjalizowana: {settings.DATABASE_PATH}")


# ── Agenci ────────────────────────────────────────────────

def create_agent(agent_id: str, workspace_path: str, personality: str = "neutral") -> dict:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO agents (id, status, personality, workspace_path)
            VALUES (?, 'pending', ?, ?)
        """, (agent_id, personality, workspace_path))
    return get_agent(agent_id)


def get_agent(agent_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
    return dict(row) if row else None


def get_all_agents(status: str = None) -> list[dict]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM agents WHERE status = ?", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM agents").fetchall()
    return [dict(r) for r in rows]


def update_agent(agent_id: str, **kwargs) -> bool:
    if not kwargs:
        return False
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [agent_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE agents SET {sets} WHERE id = ?", vals)
    return True


def set_agent_strategies(
        agent_id: str,
        strategies: list,
        reasoning: str,
        strategy_notes: dict = None,
):
    kwargs = dict(
        strategies=json.dumps(strategies),
        strategy_reasoning=reasoning,
        onboarding_done=1,
        status="active",
    )
    if strategy_notes is not None:
        kwargs["strategy_notes"] = json.dumps(strategy_notes)
    update_agent(agent_id, **kwargs)


def set_agent_budget(agent_id: str, amount: float) -> bool:
    agent = get_agent(agent_id)
    if not agent:
        return False
    update_agent(agent_id, budget_usdt=amount)
    log_activity("system", f"Budżet agenta {agent_id} ustawiony na ${amount}", "info")
    return True


# ── Transakcje ────────────────────────────────────────────

def log_trade_open(agent_id: str, token: str, direction: str,
                   size_usdt: float, entry_price: float,
                   sl_price: float, tp_price: float,
                   strategy: str, reasoning: str,
                   confidence: float, leverage: int = 1) -> int:
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO trades
            (agent_id, token, direction, size_usdt, entry_price,
             sl_price, tp_price, strategy_used, reasoning, confidence, mode, leverage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, token, direction, size_usdt, entry_price,
              sl_price, tp_price, strategy, reasoning, confidence,
              settings.TRADING_MODE, leverage))
        trade_id = cur.lastrowid
    update_agent(agent_id, used_usdt=get_agent(agent_id)["used_usdt"] + size_usdt)
    return trade_id


def modify_trade_levels(trade_id: int, sl_price: float = None, tp_price: float = None):
    """Zmień SL i/lub TP otwartej pozycji."""
    with get_connection() as conn:
        if sl_price is not None and tp_price is not None:
            conn.execute(
                "UPDATE trades SET sl_price=?, tp_price=? WHERE id=? AND status='open'",
                (sl_price, tp_price, trade_id),
            )
        elif sl_price is not None:
            conn.execute(
                "UPDATE trades SET sl_price=? WHERE id=? AND status='open'",
                (sl_price, trade_id),
            )
        elif tp_price is not None:
            conn.execute(
                "UPDATE trades SET tp_price=? WHERE id=? AND status='open'",
                (tp_price, trade_id),
            )


def log_trade_close(trade_id: int, exit_price: float, pnl_usdt: float):
    with get_connection() as conn:
        trade = conn.execute(
            "SELECT * FROM trades WHERE id = ?", (trade_id,)
        ).fetchone()
        if not trade:
            return
        conn.execute("""
            UPDATE trades
            SET exit_price = ?, pnl_usdt = ?, status = 'closed'
            WHERE id = ?
        """, (exit_price, pnl_usdt, trade_id))
    agent = get_agent(dict(trade)["agent_id"])
    update_agent(
        agent["id"],
        used_usdt=max(0, agent["used_usdt"] - dict(trade)["size_usdt"]),
        pnl_usdt=agent["pnl_usdt"] + pnl_usdt,
        budget_usdt=round(agent["budget_usdt"] + pnl_usdt, 4),
    )


def get_agent_trades(agent_id: str, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM trades WHERE agent_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (agent_id, limit)).fetchall()
    return [dict(r) for r in rows]


def get_agent_performance(agent_id: str) -> dict:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM trades
            WHERE agent_id = ? AND status = 'closed'
        """, (agent_id,)).fetchall()
    trades = [dict(r) for r in rows]
    if not trades:
        return {"trades": 0, "win_rate": 0, "pnl": 0, "avg_profit": 0}
    wins = [t for t in trades if t["pnl_usdt"] > 0]
    return {
        "trades":     len(trades),
        "wins":       len(wins),
        "win_rate":   round(len(wins) / len(trades) * 100, 1),
        "pnl":        round(sum(t["pnl_usdt"] for t in trades), 2),
        "avg_profit": round(sum(t["pnl_usdt"] for t in trades) / len(trades), 4),
    }


# ── Logi ──────────────────────────────────────────────────

def log_activity(source: str, message: str,
                 level: str = "info", metadata: dict = None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO activity_log (source, level, message, metadata)
            VALUES (?, ?, ?, ?)
        """, (source, level, message, json.dumps(metadata) if metadata else None))


def save_personal_note(agent_id: str, note: str):
    """
    Zapisz notatkę agenta o własnym tradingu.
    Maksymalnie 50 ostatnich notatek — usuwa starsze.
    """
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO agents (id) VALUES (?)",
            (agent_id,)
        )
        row = conn.execute(
            "SELECT personal_notes FROM agents WHERE id = ?",
            (agent_id,)
        ).fetchone()

        notes = json.loads(
            row["personal_notes"] or "[]"
        ) if row and row["personal_notes"] else []

        notes.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": note[:300],
        })

        notes = notes[-50:]

        conn.execute(
            "UPDATE agents SET personal_notes = ? WHERE id = ?",
            (json.dumps(notes), agent_id)
        )


def get_personal_notes(agent_id: str, limit: int = 10) -> list[str]:
    """Pobierz ostatnie N notatek agenta."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT personal_notes FROM agents WHERE id = ?",
            (agent_id,)
        ).fetchone()
    if not row or not row["personal_notes"]:
        return []
    notes = json.loads(row["personal_notes"])
    return [n["note"] for n in notes[-limit:]]


def get_strategy_performance() -> list[dict]:
    """Zwraca WR i liczbę użyć dla każdej strategy_used (globalnie)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                strategy_used,
                COUNT(*) as total,
                SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(pnl_usdt), 4) as avg_pnl,
                ROUND(
                    100.0 * SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 1
                ) as win_rate
            FROM trades
            WHERE status = 'closed'
              AND strategy_used IS NOT NULL
            GROUP BY strategy_used
            HAVING COUNT(*) >= 5
            ORDER BY win_rate DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_agent_strategy_breakdown(agent_id: str) -> list[dict]:
    """Per-agent: WR i avg PnL dla każdej strategii (min. 3 trade'y)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                strategy_used,
                COUNT(*) as total,
                SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(pnl_usdt), 4) as avg_pnl,
                ROUND(
                    100.0 * SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 1
                ) as win_rate
            FROM trades
            WHERE agent_id = ? AND status = 'closed' AND strategy_used IS NOT NULL
            GROUP BY strategy_used
            HAVING COUNT(*) >= 3
            ORDER BY win_rate DESC
        """, (agent_id,)).fetchall()
    return [dict(r) for r in rows]


def get_agent_token_breakdown(agent_id: str) -> list[dict]:
    """Per-agent: WR i avg PnL dla każdego tokenu (min. 3 trade'y)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                token,
                COUNT(*) as total,
                SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(pnl_usdt), 4) as avg_pnl,
                ROUND(
                    100.0 * SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 1
                ) as win_rate
            FROM trades
            WHERE agent_id = ? AND status = 'closed'
            GROUP BY token
            HAVING COUNT(*) >= 3
            ORDER BY win_rate DESC
        """, (agent_id,)).fetchall()
    return [dict(r) for r in rows]


# ── Journal Queue ─────────────────────────────────────────

def push_journal_queue(agent_id: str, trade: dict, close_reason: str) -> int:
    """Dodaj trade do kolejki przetwarzania dziennika (restart-safe)."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO journal_queue (agent_id, trade_json, close_reason) VALUES (?, ?, ?)",
            (agent_id, json.dumps(trade), close_reason[:500]),
        )
        return cur.lastrowid


def pop_journal_queue_batch(limit: int = 5) -> list[dict]:
    """Pobierz pending wpisy i oznacz jako 'processing'."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM journal_queue WHERE status='pending' ORDER BY timestamp ASC LIMIT ?",
            (limit,),
        ).fetchall()
        if rows:
            ids = ",".join(str(r["id"]) for r in rows)
            conn.execute(
                f"UPDATE journal_queue SET status='processing', attempts=attempts+1 WHERE id IN ({ids})"
            )
        return [dict(r) for r in rows]


def mark_journal_done(queue_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE journal_queue SET status='done' WHERE id=?", (queue_id,))


def mark_journal_failed(queue_id: int, error: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE journal_queue SET status='failed', last_error=? WHERE id=?",
            (error[:300], queue_id),
        )


def reset_processing_journal_entries():
    """Na starcie: przywróć 'processing' → 'pending' (przerwane przez restart)."""
    with get_connection() as conn:
        n = conn.execute(
            "UPDATE journal_queue SET status='pending' WHERE status='processing'"
        ).rowcount
    if n:
        logger.info(f"Journal queue: przywrócono {n} przerwaną analizę po restarcie")


def get_recent_logs(limit: int = 100, source: str = None) -> list[dict]:
    with get_connection() as conn:
        if source:
            rows = conn.execute("""
                SELECT * FROM activity_log WHERE source = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (source, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM activity_log
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]
