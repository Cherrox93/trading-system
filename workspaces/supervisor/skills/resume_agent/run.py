"""Supervisor Skill: resume_agent — wznów agenta."""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True)
    args = parser.parse_args()

    try:
        from database.db import get_agent, update_agent, log_activity

        agent = get_agent(args.agent_id)
        if not agent:
            print(json.dumps({"success": False, "error": f"Agent {args.agent_id} nie istnieje"}))
            return

        if agent["status"] == "active":
            print(json.dumps({"success": True, "message": f"{args.agent_id} już aktywny"}))
            return

        update_agent(args.agent_id, status="active")
        log_activity("supervisor", f"RESUME {args.agent_id}", "info")

        print(json.dumps({"success": True, "agent_id": args.agent_id}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
