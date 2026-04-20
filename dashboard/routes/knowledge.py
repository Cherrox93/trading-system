"""
FastAPI routes dla Knowledge Base Importera.
"""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/kb", tags=["knowledge-base"])
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "image/png":       ".png",
    "image/jpeg":      ".jpg",
    "image/webp":      ".webp",
    "application/pdf": ".pdf"
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.get("/strategies")
async def list_strategies():
    """Zwróć listę wszystkich strategii w KB."""
    try:
        from knowledge_base.query import get_all_strategies
        docs = get_all_strategies()
        return {
            "count": len(docs),
            "strategies": [
                {
                    "id":         d["id"],
                    "name":       d["metadata"].get("name", d["id"]),
                    "category":   d["metadata"].get("category", "unknown"),
                    "difficulty": d["metadata"].get("difficulty", "unknown"),
                    "win_rate":   d["metadata"].get("estimated_win_rate", "—"),
                    "source":     d["metadata"].get("source", "manual"),
                }
                for d in docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(
        file:        UploadFile = File(...),
        force_add:   bool       = Form(False),
        add_variant: bool       = Form(False),
):
    """
    Upload obrazka lub PDF.
    Analizuje przez Gemini Flash i dodaje do KB.
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Nieobslugiwany typ: {content_type}. "
                f"Dozwolone: PNG, JPG, WEBP, PDF"
            )
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Plik zbyt duzy (max {MAX_FILE_SIZE // 1024 // 1024} MB)"
        )

    suffix = ALLOWED_TYPES[content_type]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        from knowledge_base.importer.pipeline import process_file
        result = await process_file(
            tmp_path,
            force_add=force_add,
            add_similar_as_variant=add_variant
        )
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/search")
async def search_strategies(body: dict):
    """Wyszukaj strategie semantycznie."""
    query = body.get("query", "").strip()
    n     = min(int(body.get("n", 5)), 20)

    if not query:
        raise HTTPException(status_code=400, detail="Pole 'query' wymagane")

    try:
        from knowledge_base.query import search
        results = search(query, n_results=n)
        return {
            "query":   query,
            "count":   len(results),
            "results": [
                {
                    "id":         r["id"],
                    "name":       r["metadata"].get("name", r["id"]),
                    "category":   r["metadata"].get("category", "—"),
                    "similarity": round(1 - r.get("distance", 1), 3),
                    "summary":    r["text"][:300],
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategy/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """Usuń strategię z KB (ChromaDB + plik .md)."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        from config import settings

        client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        ef     = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        col = client.get_collection("trading_strategies", embedding_function=ef)
        col.delete(ids=[strategy_id])

        md_path = Path("knowledge_base/strategies") / f"{strategy_id}.md"
        if md_path.exists():
            md_path.unlink()

        return {"success": True, "deleted": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
