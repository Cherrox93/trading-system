"""
API do odpytywania Knowledge Base przez agentów.
Importowany przez onboarding i skills agentów.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.utils import embedding_functions
from config import settings

logger = logging.getLogger(__name__)
COLLECTION_NAME = "trading_strategies"

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=ef
        )
    return _collection


def search(query: str, n_results: int = 5) -> list[dict]:
    """
    Wyszukaj strategie pasujące do zapytania.
    Używane przez agentów podczas onboardingu.
    """
    try:
        col = _get_collection()
        results = col.query(
            query_texts=[query],
            n_results=min(n_results, col.count())
        )
        docs = []
        for i, doc_id in enumerate(results["ids"][0]):
            docs.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return docs
    except Exception as e:
        logger.error(f"Błąd query KB: {e}")
        return []


def get_all_strategies() -> list[dict]:
    """Zwróć wszystkie strategie — używane podczas onboardingu."""
    try:
        col = _get_collection()
        results = col.get()
        docs = []
        for i, doc_id in enumerate(results["ids"]):
            docs.append({
                "id": doc_id,
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        return docs
    except Exception as e:
        logger.error(f"Błąd get_all: {e}")
        return []


def get_strategy(strategy_id: str) -> dict | None:
    """Pobierz konkretną strategię po ID."""
    try:
        col = _get_collection()
        result = col.get(ids=[strategy_id])
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "text": result["documents"][0],
            "metadata": result["metadatas"][0]
        }
    except Exception as e:
        logger.error(f"Błąd get_strategy: {e}")
        return None


def get_collection_count() -> int:
    """Zwróć liczbę dokumentów w kolekcji (bez ładowania embeddingów)."""
    try:
        client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        col = client.get_collection(name=COLLECTION_NAME)
        return col.count()
    except Exception:
        return 0


def get_strategies_summary() -> str:
    """
    Zwróć krótkie podsumowanie wszystkich strategii.
    Używane w prompcie onboardingu agenta.
    """
    docs = get_all_strategies()
    if not docs:
        return "Brak strategii w Knowledge Base."

    lines = [f"Dostępnych strategii: {len(docs)}\n"]
    for doc in docs:
        meta = doc["metadata"]
        name = meta.get("name", doc["id"])
        category = meta.get("category", "—")
        difficulty = meta.get("difficulty", "—")
        win_rate = meta.get("estimated_win_rate", "—")
        lines.append(
            f"• [{doc['id']}] {name} | "
            f"Kategoria: {category} | "
            f"Trudność: {difficulty} | "
            f"Est. WR: {win_rate}"
        )
    return "\n".join(lines)
