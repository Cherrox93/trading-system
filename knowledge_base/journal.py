"""
knowledge_base/journal.py

Osobisty dziennik transakcji każdego agenta — przechowywany w ChromaDB.
Wyszukiwanie semantyczne: "znajdź moje przeszłe trade'y w podobnych warunkach".

Każdy agent ma osobną kolekcję: journal_{agent_id}
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.utils import embedding_functions
from config import settings

logger = logging.getLogger(__name__)

_collections: dict = {}


def _get_agent_collection(agent_id: str):
    global _collections
    if agent_id not in _collections:
        client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        col_name = f"journal_{agent_id.replace('-', '_')}"
        _collections[agent_id] = client.get_or_create_collection(
            name=col_name,
            embedding_function=ef,
            metadata={"description": f"Trade journal for {agent_id}"},
        )
    return _collections[agent_id]


def write_trade_entry(agent_id: str, trade: dict, reflection: str) -> bool:
    """
    Zapisz zamknięty trade do dziennika agenta.

    trade: dict z tabeli trades (po close) z polami:
      id, token, direction, strategy_used, reasoning, confidence,
      entry_price, exit_price, pnl_usdt, timestamp
    reflection: max 200 znaków — wniosek LLM (co zadziałało / co nie)
    """
    try:
        col = _get_agent_collection(agent_id)

        pnl = float(trade.get("pnl_usdt") or 0)
        outcome = "WIN" if pnl > 0 else "LOSS"
        token = trade.get("token", "?")
        direction = (trade.get("direction") or "?").upper()
        strategy = trade.get("strategy_used", "?")
        reasoning = (trade.get("reasoning") or "")[:200]
        confidence = float(trade.get("confidence") or 0)
        timestamp = trade.get("timestamp", "")
        trade_id = str(trade.get("id", ""))

        doc = (
            f"{token} {direction} | strategy: {strategy} | "
            f"confidence: {confidence:.0%} | "
            f"entry_reasoning: {reasoning} | "
            f"outcome: {outcome} ${pnl:+.2f} | "
            f"reflection: {reflection}"
        )

        metadata = {
            "token": token,
            "direction": direction.lower(),
            "strategy": strategy,
            "outcome": outcome,
            "pnl_usdt": round(pnl, 4),
            "confidence": confidence,
            "timestamp": timestamp,
        }

        doc_id = f"{agent_id}_trade_{trade_id}"
        existing = col.get(ids=[doc_id])
        if existing["ids"]:
            col.update(ids=[doc_id], documents=[doc], metadatas=[metadata])
        else:
            col.add(ids=[doc_id], documents=[doc], metadatas=[metadata])

        return True
    except Exception as e:
        logger.warning(f"Journal write error ({agent_id}): {e}")
        return False


def query_similar(agent_id: str, conditions_text: str, n: int = 3) -> list[dict]:
    """
    Znajdź semantycznie podobne przeszłe trade'y.

    conditions_text: opis bieżących warunków rynkowych (token, kierunek, wskaźniki)
    Zwraca: [{outcome, pnl_usdt, strategy, token, direction, document, distance}]
    """
    try:
        col = _get_agent_collection(agent_id)
        count = col.count()
        if count == 0:
            return []

        results = col.query(
            query_texts=[conditions_text],
            n_results=min(n, count),
        )

        entries = []
        for i, _ in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            entries.append({
                "outcome":    meta.get("outcome", "?"),
                "pnl_usdt":   meta.get("pnl_usdt", 0),
                "strategy":   meta.get("strategy", "?"),
                "token":      meta.get("token", "?"),
                "direction":  meta.get("direction", "?"),
                "document":   results["documents"][0][i],
                "distance":   results["distances"][0][i],
            })

        return entries
    except Exception as e:
        logger.warning(f"Journal query error ({agent_id}): {e}")
        return []


def get_journal_count(agent_id: str) -> int:
    try:
        return _get_agent_collection(agent_id).count()
    except Exception:
        return 0
