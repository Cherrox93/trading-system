"""
Skill: get_performance
Zwróć wyniki agenta z bazy danych.
Używaj co 6 godzin do samo-refleksji.
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
    args = parser.parse_args()

    try:
        from database.db import get_agent, get_agent_performance, get_agent_trades
        agent = get_agent(args.agent_id)
        if not agent:
            print(json.dumps({
                "success": False,
                "error":   f"Agent {args.agent_id} nie istnieje"
            }))
            return

        perf   = get_agent_performance(args.agent_id)
        recent = get_agent_trades(args.agent_id, limit=10)

        print(json.dumps({
            "success": True,
            "agent": {
                "id":          agent["id"],
                "status":      agent["status"],
                "budget_usdt": agent["budget_usdt"],
                "used_usdt":   agent["used_usdt"],
                "pnl_usdt":    agent["pnl_usdt"],
                "personality": agent["personality"],
                "strategies":  agent.get("strategies"),
            },
            "performance":    perf,
            "recent_trades":  recent
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
