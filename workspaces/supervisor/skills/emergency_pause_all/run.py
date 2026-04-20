"""Supervisor Skill: emergency_pause_all — natychmiastowy pause wszystkich agentów."""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    try:
        from database.db import get_all_agents, update_agent, log_activity
        import asyncio
        from telegram.reporter import send_message

        agents  = get_all_agents()
        paused  = []

        for a in agents:
            if a["status"] == "active":
                update_agent(a["id"], status="paused")
                paused.append(a["id"])

        log_activity("supervisor", f"EMERGENCY PAUSE ALL: {args.reason}", "warning")

        if paused:
            msg = (
                f"[EMERGENCY] Zatrzymano {len(paused)} agentów\n"
                f"Powód: {args.reason}\n"
                f"Agenci: {', '.join(paused)}"
            )
            asyncio.run(send_message(msg))

        print(json.dumps({"success": True, "paused": paused, "reason": args.reason}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
