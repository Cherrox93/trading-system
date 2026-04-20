"""
Skill: execute_trade
Agent podaje wszystkie parametry — zero zewnętrznych ograniczeń poza
absolutnym minimalnym bezpieczeństwem konta.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id",   required=True)
    parser.add_argument("--token",      required=True)
    parser.add_argument("--direction",  required=True, choices=["long", "short"])
    parser.add_argument("--size_pct",   type=float, required=True)
    parser.add_argument("--sl_pct",     type=float, required=True)
    parser.add_argument("--tp_pct",     type=float, required=True)
    parser.add_argument("--leverage",   type=int, default=1)
    parser.add_argument("--strategy",   required=True)
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument("--reasoning",  type=str, default="")
    args = parser.parse_args()

    try:
        from database.db import get_agent
        agent = get_agent(args.agent_id)
        if not agent:
            print(json.dumps({
                "success": False,
                "error":   f"Agent {args.agent_id} nie istnieje"
            }))
            return

        # Jedyne absolutne minimum — SL musi być realny (nie zostanie trafiony przez spread)
        if args.sl_pct < 0.001:
            print(json.dumps({
                "success":    False,
                "hard_limit": True,
                "error":      f"sl_pct={args.sl_pct} zbyt maly — SL zostanie natychmiast trafiony przez spread. Minimum 0.1%.",
                "hint":       "Ustaw sl_pct >= 0.001"
            }))
            return

        # Sprawdź budżet
        available = agent["budget_usdt"] - agent["used_usdt"]
        size_usdt = agent["budget_usdt"] * args.size_pct

        if size_usdt > available:
            print(json.dumps({
                "success": False,
                "error":   (
                    f"Niewystarczajacy budzet: potrzeba ${size_usdt:.4f}, "
                    f"dostepne ${available:.4f}"
                )
            }))
            return

        # Przekaż do executora
        from execution.trade_executor import execute_trade
        result = execute_trade({
            "agent_id":   args.agent_id,
            "token":      args.token.upper(),
            "direction":  args.direction,
            "size_usdt":  round(size_usdt, 4),
            "sl_pct":     args.sl_pct,
            "tp_pct":     args.tp_pct,
            "leverage":   args.leverage,
            "strategy":   args.strategy,
            "reasoning":  args.reasoning[:300],
            "confidence": args.confidence
        })

        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
