"""
Wgrywa dokumenty strategii do ChromaDB.
Uruchom: python knowledge_base/ingest.py
Idempotentny — bezpieczne wielokrotne uruchamianie.
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.utils import embedding_functions
from config import settings

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("ingest")

STRATEGIES_DIR = Path(__file__).parent / "strategies"
COLLECTION_NAME = "trading_strategies"


def get_collection():
    client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"description": "Trading strategies knowledge base"}
    )


def parse_document(path: Path) -> dict:
    """Parsuje dokument Markdown i wyciąga metadane z nagłówka."""
    text = path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")

    metadata = {
        "filename": path.name,
        "category": path.parent.name,
    }

    # Wyciągnij metadane z sekcji ## META
    if "## META" in text:
        meta_start = text.index("## META") + len("## META")
        meta_end = text.index("\n##", meta_start) if "\n##" in text[meta_start:] else len(text)
        meta_block = text[meta_start:meta_end]
        for line in meta_block.strip().split("\n"):
            if ":" in line and line.startswith("-"):
                key, _, val = line[1:].partition(":")
                metadata[key.strip().lower().replace(" ", "_")] = val.strip()

    return {
        "id": path.stem,
        "text": text,
        "metadata": metadata
    }


def ingest():
    logger.info(f"Ładuję dokumenty z: {STRATEGIES_DIR}")
    docs = list(STRATEGIES_DIR.glob("**/*.md"))

    if not docs:
        logger.error("Brak dokumentów w knowledge_base/strategies/")
        return 0

    collection = get_collection()
    existing = set(collection.get()["ids"])

    added = updated = skipped = 0

    for path in docs:
        doc = parse_document(path)
        doc_id = doc["id"]

        if doc_id in existing:
            collection.update(
                ids=[doc_id],
                documents=[doc["text"]],
                metadatas=[doc["metadata"]]
            )
            updated += 1
        else:
            collection.add(
                ids=[doc_id],
                documents=[doc["text"]],
                metadatas=[doc["metadata"]]
            )
            added += 1

    logger.info(f"Zakończono: {added} dodano, {updated} zaktualizowano, {skipped} pominięto")
    logger.info(f"Łącznie w kolekcji: {collection.count()} dokumentów")
    return collection.count()


if __name__ == "__main__":
    count = ingest()
    if count > 0:
        print(f"\nOK: Knowledge Base gotowa -- {count} strategii zaladowanych")
    else:
        print("\nBLAD: sprawdz logi")
