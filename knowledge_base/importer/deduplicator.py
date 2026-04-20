"""
Wykrywa duplikaty i podobne strategie w KB przez ChromaDB similarity.
"""
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

DUPLICATE_THRESHOLD = 0.85
SIMILAR_THRESHOLD   = 0.70


def check_duplicate(document: str) -> dict:
    """
    Sprawdź czy podobna strategia już istnieje.

    Zwraca:
    {
        "status":       "duplicate" | "similar" | "new",
        "similarity":   float,
        "matched_id":   str | None,
        "matched_name": str | None,
        "all_similar":  list[dict],
        "message":      str
    }
    """
    try:
        from knowledge_base.query import search

        query   = document[:500]
        results = search(query, n_results=5)

        if not results:
            return _new_result()

        best       = results[0]
        distance   = best.get("distance", 1.0)
        similarity = round(1.0 - distance, 3)

        all_similar = [
            {
                "id":         r["id"],
                "name":       r.get("metadata", {}).get("name", r["id"]),
                "similarity": round(1.0 - r.get("distance", 1.0), 3)
            }
            for r in results
            if (1.0 - r.get("distance", 1.0)) > SIMILAR_THRESHOLD
        ]

        if similarity >= DUPLICATE_THRESHOLD:
            name = best.get("metadata", {}).get("name", best["id"])
            return {
                "status":       "duplicate",
                "similarity":   similarity,
                "matched_id":   best["id"],
                "matched_name": name,
                "all_similar":  all_similar,
                "message": (
                    f"Strategia juz istnieje w bazie: "
                    f"'{name}' (podobienstwo: {similarity:.0%})"
                )
            }

        if similarity >= SIMILAR_THRESHOLD:
            name = best.get("metadata", {}).get("name", best["id"])
            return {
                "status":       "similar",
                "similarity":   similarity,
                "matched_id":   best["id"],
                "matched_name": name,
                "all_similar":  all_similar,
                "message": (
                    f"Znaleziono podobna strategie: "
                    f"'{name}' (podobienstwo: {similarity:.0%}). "
                    f"Czy dodac jako wariant?"
                )
            }

        return _new_result(all_similar)

    except Exception as e:
        logger.error(f"Blad deduplication: {e}")
        return _new_result()


def _new_result(all_similar: list = None) -> dict:
    return {
        "status":       "new",
        "similarity":   0.0,
        "matched_id":   None,
        "matched_name": None,
        "all_similar":  all_similar or [],
        "message":      "Nowa strategia — nie znaleziono podobnych w KB"
    }
