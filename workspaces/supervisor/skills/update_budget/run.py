"""Supervisor Skill: update_budget — zmień budżet agenta."""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True)
    parser.add_argument("--budget",   type=float, required=True)
    parser.add_argument("--reason",   default="Supervisor decision")
    args = parser.parse_args()

    try:
        from database.db import get_agent, set_agent_budget, log_activity

        agent = get_agent(args.agent_id)
        if not agent:
            print(json.dumps({"success": False, "error": f"Agent {args.agent_id} nie istnieje"}))
            return

        old = float(agent["budget_usdt"] or 0)
        set_agent_budget(args.agent_id, args.budget)
        log_activity(
            "supervisor",
            f"Budżet {args.agent_id}: ${old:.2f} → ${args.budget:.2f} | {args.reason}",
            "info",
        )

        print(json.dumps({
            "success":    True,
            "agent_id":   args.agent_id,
            "old_budget": old,
            "new_budget": args.budget,
            "reason":     args.reason,
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
