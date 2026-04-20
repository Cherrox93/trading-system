"""
Pełny pipeline importowania strategii.
Łączy: analyzer → validator → deduplicator → zapis → ingest.
"""
import logging
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from knowledge_base.importer.validator    import validate
from knowledge_base.importer.deduplicator import check_duplicate

logger = logging.getLogger(__name__)

STRATEGIES_DIR = ROOT / "knowledge_base" / "strategies"


def _generate_filename(document: str) -> str:
    """Generuj bezpieczną nazwę pliku z tytułu dokumentu."""
    match = re.search(r"^#\s+(.+)$", document, re.MULTILINE)
    name  = match.group(1).strip() if match else "unknown_strategy"

    replacements = {
        "a":"a","e":"e","s":"s","z":"z","z":"z",
        "c":"c","o":"o","n":"n","l":"l",
        "ą":"a","ę":"e","ś":"s","ź":"z","ż":"z",
        "ć":"c","ó":"o","ń":"n","ł":"l"
    }
    name_lower = name.lower()
    for pl, en in replacements.items():
        name_lower = name_lower.replace(pl, en)

    name_safe = re.sub(r"[^a-z0-9]+", "_", name_lower).strip("_")
    return f"{name_safe}.md"


def _make_variant_filename(base_filename: str) -> str:
    stem = Path(base_filename).stem
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M")
    return f"{stem}_variant_{ts}.md"


async def process_file(
        file_path: Path,
        force_add: bool = False,
        add_similar_as_variant: bool = False
) -> dict:
    """
    Pełny pipeline dla jednego pliku (obrazek lub PDF).

    Zwraca:
    {
        "success":           bool,
        "strategies_found":  int,
        "strategies_added":  int,
        "results":           list[dict]
    }
    """
    suffix = file_path.suffix.lower()

    # Analiza przez Gemini
    logger.info(f"Analizuje plik: {file_path.name} ({suffix})")
    try:
        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            from knowledge_base.importer.analyzer import analyze_image
            media_types = {
                ".png":  "image/png",
                ".jpg":  "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp"
            }
            documents = await analyze_image(file_path, media_types[suffix])

        elif suffix == ".pdf":
            from knowledge_base.importer.analyzer import analyze_pdf
            documents = await analyze_pdf(file_path)

        else:
            return {
                "success": False,
                "error":   f"Nieobslugiwany format: {suffix}. "
                           f"Dozwolone: PNG, JPG, WEBP, PDF",
                "strategies_found": 0,
                "strategies_added": 0,
                "results": []
            }

    except ValueError as e:
        return {
            "success": False,
            "error":   str(e),
            "strategies_found": 0,
            "strategies_added": 0,
            "results": []
        }
    except Exception as e:
        logger.error(f"Blad analizy {file_path.name}: {e}")
        return {
            "success": False,
            "error":   f"Blad analizy: {str(e)}",
            "strategies_found": 0,
            "strategies_added": 0,
            "results": []
        }

    if not documents:
        return {
            "success":          True,
            "strategies_found": 0,
            "strategies_added": 0,
            "results": [{
                "status":  "no_strategy",
                "message": "Brak strategii tradingowych w materiale"
            }]
        }

    # Procesuj każdą strategię
    results = []
    added   = 0

    for doc in documents:
        result = await _process_single(doc, force_add, add_similar_as_variant)
        results.append(result)
        if result.get("added"):
            added += 1

    return {
        "success":           True,
        "strategies_found":  len(documents),
        "strategies_added":  added,
        "results":           results
    }


async def _process_single(
        document: str,
        force_add: bool,
        add_similar_as_variant: bool
) -> dict:
    """Jeden dokument przez validator → deduplicator → zapis → ChromaDB."""

    # Walidacja
    validation = validate(document)
    if not validation["valid"] and not force_add:
        return {
            "added":    False,
            "status":   "invalid",
            "name":     validation["name"],
            "errors":   validation["errors"],
            "warnings": validation["warnings"],
            "message":  f"Dokument niekompletny: {'; '.join(validation['errors'])}"
        }

    # Deduplikacja
    dup = check_duplicate(document)

    if dup["status"] == "duplicate" and not force_add:
        return {
            "added":        False,
            "status":       "duplicate",
            "name":         validation["name"],
            "matched_id":   dup["matched_id"],
            "matched_name": dup["matched_name"],
            "similarity":   dup["similarity"],
            "all_similar":  dup["all_similar"],
            "message":      dup["message"],
            "validation":   validation
        }

    if dup["status"] == "similar" and not add_similar_as_variant:
        return {
            "added":         False,
            "status":        "similar",
            "name":          validation["name"],
            "matched_id":    dup["matched_id"],
            "matched_name":  dup["matched_name"],
            "similarity":    dup["similarity"],
            "all_similar":   dup["all_similar"],
            "message":       dup["message"],
            "validation":    validation,
            "action_needed": True
        }

    # Zapisz plik .md
    base_fn = _generate_filename(document)
    if dup["status"] == "similar" and add_similar_as_variant:
        filename = _make_variant_filename(base_fn)
    else:
        filename = base_fn

    file_path = STRATEGIES_DIR / filename
    counter = 1
    while file_path.exists() and not force_add:
        stem      = Path(base_fn).stem
        file_path = STRATEGIES_DIR / f"{stem}_{counter}.md"
        counter  += 1

    STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
    file_path.write_text(document, encoding="utf-8")
    logger.info(f"Zapisano: {file_path.name}")

    # Zaktualizuj ChromaDB
    chromadb_ok = False
    try:
        from knowledge_base.ingest import ingest
        ingest()
        chromadb_ok = True
        logger.info("ChromaDB zaktualizowana")
    except Exception as e:
        logger.error(f"Blad ChromaDB update: {e}")

    return {
        "added":       True,
        "status":      "added",
        "name":        validation["name"],
        "filename":    file_path.name,
        "similarity":  dup["similarity"],
        "is_variant":  dup["status"] == "similar",
        "validation":  validation,
        "chromadb_ok": chromadb_ok,
        "message":     f"Dodano: '{validation['name']}' -> {file_path.name}"
    }
