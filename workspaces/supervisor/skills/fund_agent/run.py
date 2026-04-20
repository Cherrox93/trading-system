"""
Supervisor Skill: fund_agent
Przydziel lub zmień budżet agenta.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True)
    parser.add_argument("--amount",   type=float, required=True)
    args = parser.parse_args()

    try:
        from database.db import set_agent_budget, get_agent, log_activity

        if not get_agent(args.agent_id):
            print(json.dumps({
                "success": False,
                "error":   f"Agent {args.agent_id} nie istnieje"
            }))
            return

        result = set_agent_budget(args.agent_id, args.amount)
        agent  = get_agent(args.agent_id)

        log_activity(
            "supervisor",
            f"Budzet agenta {args.agent_id} ustawiony na ${args.amount}",
            "info"
        )

        print(json.dumps({
            "success":     True,
            "agent_id":    args.agent_id,
            "budget_usdt": agent["budget_usdt"],
            "used_usdt":   agent["used_usdt"],
            "message":     f"Budzet ${args.amount} przydzielony agentowi {args.agent_id}"
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
