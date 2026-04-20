"""
Skill: market_scan_all
Zwraca sygnały rynkowe przygotowane przez Signal Scanner (Layer 1).
Każdy sygnał jest już przeanalizowany przez LLM i zawiera kierunek,
confidence, sugerowane SL/TP i kontekst rynkowy.
Agent (Layer 2) decyduje czy wejść w pozycję na podstawie swoich strategii.
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    try:
        signals_path = ROOT / "data" / "market_signals.json"

        if not signals_path.exists():
            print(json.dumps({
                "success": False,
                "error":   "market_signals.json nie istnieje — Signal Scanner nie uruchomiony",
            }))
            return

        data    = json.loads(signals_path.read_text())
        signals = data.get("signals", [])
        updated = data.get("updated_at", "unknown")

        # Sprawdź świeżość — sygnały starsze niż 2 minuty mogą być nieaktualne
        try:
            dt      = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            age_s   = (datetime.now(timezone.utc) - dt).total_seconds()
            stale   = age_s > 120
        except Exception:
            age_s = -1
            stale = False

        print(json.dumps({
            "success":    True,
            "count":      len(signals),
            "updated_at": updated,
            "age_seconds": round(age_s, 1),
            "stale":      stale,
            "signals":    signals,
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
