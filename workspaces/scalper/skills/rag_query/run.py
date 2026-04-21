"""
Skill: rag_query
Wyszukaj strategie w Knowledge Base.
Używaj podczas onboardingu i gdy chcesz przypomnieć sobie szczegóły strategii.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--n",     type=int, default=5)
    args = parser.parse_args()

    try:
        from knowledge_base.query import search
        results = search(args.query, n_results=args.n)

        # Wyczyść embeddingi z wyników (zbyt duże dla agenta)
        clean = []
        for r in results:
            clean.append({
                "id":       r["id"],
                "distance": round(r["distance"], 4),
                "metadata": r["metadata"],
                "text":     r["text"][:2000]  # limit tekstu
            })

        print(json.dumps({
            "success": True,
            "query":   args.query,
            "count":   len(clean),
            "results": clean
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
