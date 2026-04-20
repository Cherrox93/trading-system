"""
Supervisor Skill: get_all_performance
Zwróć wyniki wszystkich agentów.
Używaj do przeglądu co 24 godziny.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    try:
        from database.db import get_all_agents, get_agent_performance, get_agent_trades

        agents = get_all_agents()
        result = []

        for agent in agents:
            perf   = get_agent_performance(agent["id"])
            recent = get_agent_trades(agent["id"], limit=5)
            result.append({
                "agent": {
                    "id":          agent["id"],
                    "status":      agent["status"],
                    "budget_usdt": agent["budget_usdt"],
                    "used_usdt":   agent["used_usdt"],
                    "pnl_usdt":    agent["pnl_usdt"],
                    "personality": agent["personality"],
                    "strategies":  agent.get("strategies"),
                },
                "performance":   perf,
                "recent_trades": recent
            })

        # Agregaty całego systemu
        total_pnl    = sum(a["agent"]["pnl_usdt"] for a in result)
        total_budget = sum(a["agent"]["budget_usdt"] for a in result)
        total_trades = sum(a["performance"].get("trades", 0) for a in result)

        print(json.dumps({
            "success":      True,
            "count":        len(result),
            "system_total": {
                "pnl_usdt":    round(total_pnl, 4),
                "budget_usdt": round(total_budget, 4),
                "trades":      total_trades,
            },
            "agents": result
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
