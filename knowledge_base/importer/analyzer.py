"""
Analizuje obrazy i PDF przez Groq Llama4 Scout (multimodal).
Darmowy tier Groq: wysoki limit requestów bez karty kredytowej.
"""
import base64
import logging
import os
from pathlib import Path
from datetime import datetime

from openai import OpenAI

logger = logging.getLogger(__name__)

STRATEGY_PROMPT = """You are a trading expert. Analyze this material.

For EACH trading strategy found, return a document
in exactly this Markdown format (nothing else, no introduction):

# [STRATEGY NAME]

## META
- Name: [full name]
- Category: [mean_reversion OR momentum OR breakout OR volume OR hybrid]
- Difficulty: [beginner OR intermediate OR advanced]
- Timeframes: [list e.g. 5m, 15m, 1h]
- Best Market: [trending OR ranging OR volatile OR any]
- Estimated Win Rate: [range e.g. 52-58%]
- Risk Reward: [ratio e.g. 1:2.0]
- Tokens: [any OR large_cap OR mid_cap OR volatile]
- Source: {source_type}
- Added: {timestamp}

## Description
[2-4 sentences describing the strategy]

## Entry Conditions
[Specific, measurable criteria — minimum 3 conditions]

## Exit Conditions
### Take Profit
[Where and when to take profit]
### Stop Loss
[Where to set stop loss]

## Confirming Signals
[Additional indicators that increase confidence]

## When NOT to Enter
[Exclusion conditions — minimum 3]

## Risk Management
[% of capital, maximum positions, rules]

## Setup Example
[A concrete setup example in the market]

## Configuration Parameters
[List of variables the trader can adjust]

If the material contains multiple strategies — separate them with:
===NEXT_STRATEGY===

If no trading strategies are found — write only:
NO_STRATEGY_FOUND

Write in English. Be specific and detailed.
Do not invent — describe only what you see in the material."""


def _get_groq_client() -> OpenAI:
    """Zainicjalizuj klienta Groq."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY nie ustawiony w .env\n"
            "Pobierz klucz: https://console.groq.com"
        )
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )


GROQ_VISION_MODEL = os.getenv(
    "GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)


def _parse_response(text: str) -> list:
    """Parsuj odpowiedź na listę dokumentów Markdown."""
    text = text.strip()
    if text == "NO_STRATEGY_FOUND":
        return []
    strategies = [
        s.strip()
        for s in text.split("===NEXT_STRATEGY===")
        if s.strip()
    ]
    logger.info(f"Groq wykrył {len(strategies)} strategii")
    return strategies


async def analyze_image(
        image_path: Path,
        media_type: str = "image/png"
) -> list:
    """
    Analizuj obraz przez Groq Llama4 Scout (multimodal/vision).
    Obsługuje PNG, JPG, WEBP.
    Zwraca listę dokumentów Markdown strategii.
    """
    import asyncio

    prompt_text = STRATEGY_PROMPT.format(
        source_type="image_upload",
        timestamp=datetime.utcnow().strftime("%Y-%m-%d")
    )

    image_data = base64.standard_b64encode(
        image_path.read_bytes()
    ).decode("utf-8")

    def _sync_call():
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        },
                    },
                    {"type": "text", "text": prompt_text},
                ],
            }],
            max_tokens=4096,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    try:
        text = await asyncio.get_event_loop().run_in_executor(
            None, _sync_call
        )
        return _parse_response(text)
    except Exception as e:
        logger.error(f"Groq Vision error: {e}")
        raise


async def analyze_pdf(pdf_path: Path) -> list:
    """
    Analizuj PDF przez Groq.
    Tekst wyciągany lokalnie przez PyMuPDF (zero API).
    Duże pliki dzielone na chunki po 30 000 znaków.
    """
    import asyncio

    text = _extract_pdf_text(pdf_path)
    if not text.strip():
        logger.warning(f"Brak tekstu w PDF: {pdf_path.name}")
        return []

    CHUNK_SIZE = 30_000
    chunks = [
        text[i:i + CHUNK_SIZE]
        for i in range(0, len(text), CHUNK_SIZE)
    ]
    logger.info(
        f"PDF {pdf_path.name}: {len(text)} znaków, "
        f"{len(chunks)} chunków do analizy"
    )

    all_strategies = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Analizuję chunk {i+1}/{len(chunks)}...")

        prompt_text = (
            STRATEGY_PROMPT.format(
                source_type="pdf_upload",
                timestamp=datetime.utcnow().strftime("%Y-%m-%d")
            )
            + f"\n\n=== TREŚĆ (część {i+1}/{len(chunks)}) ===\n{chunk}"
        )

        def _sync_chunk(p=prompt_text):
            client = _get_groq_client()
            response = client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=[{"role": "user", "content": p}],
                max_tokens=4096,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, _sync_chunk
            )
            strategies = _parse_response(result)
            all_strategies.extend(strategies)
            logger.info(
                f"Chunk {i+1}: znaleziono {len(strategies)} strategii"
            )
        except Exception as e:
            logger.warning(f"Blad chunk {i+1}: {e}")

        if i < len(chunks) - 1:
            await asyncio.sleep(2)  # krótka pauza między chunkami

    logger.info(
        f"PDF lacznie: {len(all_strategies)} strategii "
        f"z {len(chunks)} chunkow"
    )
    return all_strategies


def _extract_pdf_text(pdf_path: Path) -> str:
    """Wyciągnij tekst z PDF lokalnie przez PyMuPDF."""
    try:
        import fitz
        doc   = fitz.open(str(pdf_path))
        pages = [page.get_text() for page in doc]
        doc.close()
        result = "\n\n".join(pages)
        logger.info(
            f"PDF: {pdf_path.name} — "
            f"{len(pages)} stron, {len(result)} znakow"
        )
        return result
    except ImportError:
        logger.error(
            "PyMuPDF nie zainstalowane.\n"
            "Uruchom: pip install PyMuPDF --break-system-packages"
        )
        return ""
    except Exception as e:
        logger.error(f"Blad odczytu PDF {pdf_path.name}: {e}")
        return ""
