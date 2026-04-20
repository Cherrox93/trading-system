"""Supervisor Skill: get_open_positions — pobierz wszystkie otwarte pozycje."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    try:
        from database.db import get_connection

        with get_connection() as conn:
            rows = conn.execute("""
                SELECT t.*, a.budget_usdt, a.personality
                FROM trades t
                LEFT JOIN agents a ON t.agent_id = a.id
                WHERE t.status = 'open'
                ORDER BY t.timestamp DESC
            """).fetchall()

        positions = [dict(r) for r in rows]

        total_exposure = sum(float(p.get("size_usdt") or 0) for p in positions)

        print(json.dumps({
            "success":        True,
            "count":          len(positions),
            "total_exposure": round(total_exposure, 4),
            "positions":      positions,
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
