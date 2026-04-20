"""Supervisor Skill: send_telegram — wyślij wiadomość lub dzienny raport."""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="")
    parser.add_argument("--type",    default="message",
                        choices=["message", "daily_report"])
    args = parser.parse_args()

    try:
        import asyncio
        from telegram.reporter import send_message, send_daily_report
        from database.db import get_all_agents, get_agent_performance

        if args.type == "daily_report":
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
                })
            review = {
                "overall_assessment": "Raport dzienny wygenerowany przez Supervisor (OpenClaw)",
                "system_health":      "good",
                "corrections":        [],
                "recommendations":    "Sprawdź dashboard po szczegóły.",
            }
            asyncio.run(send_daily_report(agents_data, review))
            print(json.dumps({"success": True, "type": "daily_report"}))

        else:
            if not args.message:
                print(json.dumps({"success": False, "error": "Brak --message"}))
                return
            ok = asyncio.run(send_message(args.message))
            print(json.dumps({"success": ok}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
