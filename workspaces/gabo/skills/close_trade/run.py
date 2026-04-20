"""
Skill: close_trade
Zamknij otwartą pozycję.
Agent decyduje kiedy i dlaczego zamknąć.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trade_id", type=int, required=True)
    parser.add_argument("--reason",   type=str, required=True)
    args = parser.parse_args()

    try:
        from execution.trade_executor import close_trade
        result = close_trade(args.trade_id, None, args.reason)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
