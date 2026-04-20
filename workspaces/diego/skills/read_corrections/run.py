"""
Skill: read_corrections
Odczytaj i oznacz jako zastosowane korekty od Supervisora.
Wywołuj na początku każdego cyklu heartbeat.
"""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True)
    args = parser.parse_args()

    try:
        from database.db import get_connection

        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM corrections
                WHERE agent_id = ? AND applied = 0
                ORDER BY timestamp ASC
            """, (args.agent_id,)).fetchall()

            corrections = [dict(r) for r in rows]

            if corrections:
                ids = ",".join(str(c["id"]) for c in corrections)
                conn.execute(
                    f"UPDATE corrections SET applied = 1 WHERE id IN ({ids})"
                )

        print(json.dumps({
            "success":     True,
            "agent_id":    args.agent_id,
            "count":       len(corrections),
            "corrections": corrections,
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
