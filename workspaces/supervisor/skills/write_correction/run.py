"""
Supervisor Skill: write_correction
Zapisz korektę dla agenta do bazy.
Agent odczyta ją w następnym cyklu przez read_corrections.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id",  required=True)
    parser.add_argument("--type",      required=True,
                        choices=["risk_reduction", "strategy_change", "pause",
                                 "resume", "budget_change", "note"])
    parser.add_argument("--new_value", required=True)
    parser.add_argument("--old_value", default=None)
    parser.add_argument("--reasoning", default="")
    args = parser.parse_args()

    try:
        from database.db import get_connection, log_activity, get_agent
        if not get_agent(args.agent_id):
            print(json.dumps({
                "success": False,
                "error":   f"Agent {args.agent_id} nie istnieje"
            }))
            return

        with get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO corrections
                    (agent_id, type, old_value, new_value, reasoning)
                VALUES (?, ?, ?, ?, ?)
            """, (args.agent_id, args.type,
                  args.old_value, args.new_value, args.reasoning))
            correction_id = cur.lastrowid

        log_activity(
            "supervisor",
            f"Korekta #{correction_id} dla {args.agent_id}: "
            f"{args.type} — {args.reasoning}",
            "info"
        )

        print(json.dumps({
            "success":       True,
            "correction_id": correction_id,
            "agent_id":      args.agent_id,
            "type":          args.type,
            "new_value":     args.new_value,
            "reasoning":     args.reasoning
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
