"""
Centralne ustawienia systemu.
Wszystkie inne moduły importują stąd — nigdy nie czytają .env bezpośrednio.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

# ── Tryb tradingu ──────────────────────────────────────────
TRADING_MODE = os.getenv("TRADING_MODE", "paper")
IS_PAPER = TRADING_MODE == "paper"
IS_LIVE  = TRADING_MODE == "live"

# ── LLM ───────────────────────────────────────────────────
DEEPSEEK_API_KEY   = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL         = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_FAST_MODEL  = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash-lite-preview-06-17")

# ── DEX ───────────────────────────────────────────────────
LIGHTER_PRIVATE_KEY    = os.getenv("LIGHTER_PRIVATE_KEY", "")
LIGHTER_ACCOUNT_INDEX  = int(os.getenv("LIGHTER_ACCOUNT_INDEX", "0"))
LIGHTER_NETWORK        = os.getenv("LIGHTER_NETWORK", "testnet")

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Dashboard ─────────────────────────────────────────────
DASHBOARD_HOST   = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT   = int(os.getenv("DASHBOARD_PORT", "8000"))
DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET", "changeme")

# ── OpenClaw ──────────────────────────────────────────────
OPENCLAW_PORT = int(os.getenv("OPENCLAW_PORT", "18789"))
OPENCLAW_HOST = os.getenv("OPENCLAW_HOST", "127.0.0.1")

# ── Baza danych ───────────────────────────────────────────
DATABASE_PATH  = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "trading.db"))
CHROMADB_PATH  = os.getenv("CHROMADB_PATH", str(BASE_DIR / "database" / "chromadb"))

# ── Market feed ───────────────────────────────────────────
MIN_VOLUME_USD = float(os.getenv("MIN_VOLUME_USD", "200000"))

# ── System ────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TIMEZONE  = os.getenv("TIMEZONE", "Europe/Warsaw")

def validate():
    """Sprawdź czy wymagane klucze są ustawione."""
    errors = []

    if IS_LIVE:
        if not LIGHTER_PRIVATE_KEY:
            errors.append("LIGHTER_PRIVATE_KEY wymagany w trybie live")
        if not GROQ_API_KEY:
            errors.append("GROQ_API_KEY wymagany")
        if not DEEPSEEK_API_KEY:
            errors.append("DEEPSEEK_API_KEY wymagany")

    if TELEGRAM_BOT_TOKEN and not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID wymagany jeśli BOT_TOKEN ustawiony")

    if errors:
        raise EnvironmentError(
            "Błędy konfiguracji:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return True

def status():
    """Zwróć słownik z aktualnym stanem konfiguracji."""
    return {
        "trading_mode": TRADING_MODE,
        "llm_deep": "deepseek-reasoner (direct)" if DEEPSEEK_API_KEY else "BRAK KLUCZA",
        "llm_fast": (
            f"{GEMINI_FAST_MODEL} (gemini)" if GEMINI_API_KEY
            else (f"{GROQ_MODEL} (groq-fallback)" if GROQ_API_KEY else "BRAK KLUCZA")
        ),
        "dex": f"lighter-{LIGHTER_NETWORK}",
        "telegram": bool(TELEGRAM_BOT_TOKEN),
        "database": DATABASE_PATH,
    }
