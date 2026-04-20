"""
Waliduje kompletność dokumentu strategii przed dodaniem do KB.
"""
import re
import logging

logger = logging.getLogger(__name__)

REQUIRED_SECTIONS = [
    "## META",
    "## Opis",
    "## Warunki Wejścia",
    "## Warunki Wyjścia",
    "### Take Profit",
    "### Stop Loss",
    "## Kiedy NIE wchodzić",
    "## Zarządzanie Ryzykiem",
]

REQUIRED_META_FIELDS = [
    "Name:",
    "Category:",
    "Difficulty:",
    "Timeframes:",
    "Best Market:",
    "Estimated Win Rate:",
]

VALID_CATEGORIES   = {"mean_reversion", "momentum", "breakout", "volume", "hybrid"}
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}


def validate(document: str) -> dict:
    """
    Sprawdź kompletność i poprawność dokumentu.

    Zwraca:
    {
        "valid":    bool,
        "score":    float,        # 0.0-1.0
        "errors":   list[str],
        "warnings": list[str],
        "name":     str
    }
    """
    errors   = []
    warnings = []

    # Sprawdź wymagane sekcje
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in document]
    if missing_sections:
        errors.append(f"Brakujace sekcje: {', '.join(missing_sections)}")

    # Sprawdź META pola
    missing_meta = [f for f in REQUIRED_META_FIELDS if f not in document]
    if missing_meta:
        errors.append(f"Brakujace pola META: {', '.join(missing_meta)}")

    # Sprawdź kategorię
    cat_match = re.search(r"- Category:\s*(\S+)", document, re.IGNORECASE)
    if cat_match:
        cat = cat_match.group(1).lower().rstrip(",.")
        if cat not in VALID_CATEGORIES:
            errors.append(
                f"Nieprawidlowa kategoria: '{cat}'. "
                f"Dozwolone: {VALID_CATEGORIES}"
            )
    else:
        errors.append("Brak pola Category w META")

    # Sprawdź trudność
    diff_match = re.search(r"- Difficulty:\s*(\S+)", document, re.IGNORECASE)
    if diff_match:
        diff = diff_match.group(1).lower().rstrip(",.")
        if diff not in VALID_DIFFICULTIES:
            warnings.append(
                f"Nieznana trudnosc: '{diff}'. "
                f"Zalecane: {VALID_DIFFICULTIES}"
            )

    # Minimum treści
    if len(document) < 400:
        errors.append("Dokument zbyt krotki (< 400 znakow)")

    # Ostrzeżenia opcjonalne
    if "## Przykład Setupu" not in document:
        warnings.append(
            "Brak 'Przyklad Setupu' — zalecane dla lepszego uczenia agentow"
        )
    if "## Parametry do Konfiguracji" not in document:
        warnings.append(
            "Brak 'Parametrow do Konfiguracji' — agenci nie wiedza co dostosowac"
        )

    # Wyciągnij nazwę
    name_match = re.search(r"^#\s+(.+)$", document, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else "Nieznana strategia"

    # Score
    total  = len(REQUIRED_SECTIONS) + len(REQUIRED_META_FIELDS)
    missed = len(missing_sections) + len(missing_meta)
    score  = max(0.0, (total - missed) / total)

    return {
        "valid":    len(errors) == 0,
        "score":    round(score, 2),
        "errors":   errors,
        "warnings": warnings,
        "name":     name,
    }
