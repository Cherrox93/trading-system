"""Supervisor Skill: kb_evolve — ewolucja Knowledge Base na podstawie wyników agentów."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    try:
        import asyncio
        from database.db import get_all_agents, get_agent_performance
        from agents.kb_evolution import evolve_knowledge_base

        agents = get_all_agents()
        agents_data = []
        for a in agents:
            p = get_agent_performance(a["id"])
            agents_data.append({
                "id":          a["id"],
                "status":      a["status"],
                "personality": a.get("personality", "neutral"),
                "pnl":         float(a["pnl_usdt"] or 0),
                "budget":      float(a["budget_usdt"] or 0),
                "performance": p,
                "rating":      "good" if p.get("win_rate", 0) >= 60 else "warning",
            })

        review = {
            "system_health": "good",
            "corrections":   [],
        }

        asyncio.run(evolve_knowledge_base(agents_data, review))

        print(json.dumps({"success": True, "agents_analyzed": len(agents_data)}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
