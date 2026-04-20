"""
Skill: market_watch
Surowe dane jednego tokenu + stan pozycji.
Agent sam decyduje co robić.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    try:
        path     = ROOT / "data" / "market_snapshot.json"
        snapshot = json.loads(path.read_text())
        token    = next(
            (t for t in snapshot.get("tokens", [])
             if t["symbol"] == args.token.upper()),
            None
        )

        if not token:
            available = [t["symbol"] for t in snapshot.get("tokens", [])]
            print(json.dumps({
                "success":   False,
                "error":     f"Token {args.token} nie znaleziony",
                "available": available
            }))
            return

        # Pobierz aktywną pozycję na tym tokenie
        open_position = None
        try:
            from database.db import get_connection
            with get_connection() as conn:
                row = conn.execute("""
                    SELECT * FROM trades
                    WHERE token = ? AND status = 'open'
                    ORDER BY timestamp DESC LIMIT 1
                """, (args.token.upper(),)).fetchone()
            if row:
                open_position = dict(row)
        except Exception:
            pass

        print(json.dumps({
            "success":       True,
            "token":         token,
            "open_position": open_position
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
