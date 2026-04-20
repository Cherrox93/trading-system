"""Supervisor Skill: pause_agent — zatrzymaj agenta."""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True)
    parser.add_argument("--reason",   required=True)
    args = parser.parse_args()

    try:
        from database.db import get_agent, update_agent, log_activity, get_connection
        import asyncio
        from telegram.reporter import send_emergency_alert

        agent = get_agent(args.agent_id)
        if not agent:
            print(json.dumps({"success": False, "error": f"Agent {args.agent_id} nie istnieje"}))
            return

        if agent["status"] == "paused":
            print(json.dumps({"success": True, "message": f"{args.agent_id} już zatrzymany"}))
            return

        update_agent(args.agent_id, status="paused")

        with get_connection() as conn:
            conn.execute(
                "INSERT INTO corrections (agent_id, type, new_value, reasoning) VALUES (?,?,?,?)",
                (args.agent_id, "pause", '{"duration":"manual_review"}', args.reason),
            )

        log_activity("supervisor", f"PAUSE {args.agent_id}: {args.reason}", "warning")
        asyncio.run(send_emergency_alert(args.agent_id, args.reason))

        print(json.dumps({
            "success":  True,
            "agent_id": args.agent_id,
            "reason":   args.reason,
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
