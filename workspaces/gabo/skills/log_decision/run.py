"""
Skill: log_decision
Zaloguj decyzję agenta do bazy.
Każda decyzja (wejście, wyjście, brak setupu) powinna być zalogowana.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id",  required=True)
    parser.add_argument("--decision",  required=True)
    parser.add_argument("--reasoning", default="")
    args = parser.parse_args()

    try:
        from database.db import log_activity
        log_activity(
            args.agent_id,
            f"DECISION: {args.decision} | {args.reasoning}",
            "info",
            {"decision": args.decision, "reasoning": args.reasoning}
        )
        print(json.dumps({
            "success":   True,
            "agent_id":  args.agent_id,
            "decision":  args.decision,
            "reasoning": args.reasoning
        }))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
