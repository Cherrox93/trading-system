"""
main.py

Punkt startowy systemu tradingowego.
Infrastruktura jako asyncio tasks:
  - market_feed     — dane rynkowe (WebSocket Lighter)
  - signal_scanner  — Layer 1 LLM (pre-filter sygnałów → market_signals.json)
  - dashboard       — FastAPI dashboard
  - telegram bot    — komendy właściciela (/status, /pause, /fund ...)
  - openclaw        — agenci (supervisor + trader_XX) przez CMDOP runtime

Agenci NIE są uruchamiani jako Python klasy.
Zarządza nimi OpenClaw przez CMDOP desktop (lokalnie na OPENCLAW_PORT).
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from config import settings
from database.db import init_db, log_activity

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


# ── Infrastruktura (niezmieniona) ──────────────────────────

async def _run_market_feed():
    from data.market_feed import run as feed_run
    logger.info("Market Feed: start")
    try:
        await feed_run()
    except Exception as e:
        logger.error(f"Market Feed error: {e}", exc_info=True)


async def _run_signal_scanner():
    from data.signal_scanner import SignalScanner
    logger.info("Signal Scanner: start")
    try:
        await SignalScanner().run()
    except Exception as e:
        logger.error(f"Signal Scanner error: {e}", exc_info=True)


async def _run_telegram():
    from telegram.commands import run_bot
    logger.info("Telegram Bot: start")
    try:
        await run_bot()
    except Exception as e:
        logger.error(f"Telegram Bot error: {e}", exc_info=True)


async def _run_dashboard():
    import uvicorn
    config = uvicorn.Config(
        "dashboard.main:app",
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(
        f"Dashboard: start — http://localhost:{settings.DASHBOARD_PORT}"
    )
    try:
        await server.serve()
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            logger.error(
                f"Dashboard: port {settings.DASHBOARD_PORT} zajęty. "
                f"Zmień DASHBOARD_PORT w .env lub zwolnij port."
            )
        else:
            logger.error(f"Dashboard error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)


# ── OpenClaw runtime ───────────────────────────────────────

async def _run_position_monitor():
    """
    Background task — monitoruje SL/TP bez LLM.
    Zamyka pozycje automatycznie gdy cena osiągnie SL lub TP.
    """
    from execution.position_monitor import run_position_monitor
    logger.info("PositionMonitor: start — monitoring SL/TP bez LLM")
    try:
        await run_position_monitor()
    except Exception as e:
        logger.error(f"PositionMonitor error: {e}", exc_info=True)


async def _run_openclaw():
    """
    Uruchamia wszystkich agentów przez OpenClaw (CMDOP) runtime.
    Supervisor + trader_XX jako autonomiczne agenty z SOUL.md / HEARTBEAT.md.
    Wymaga działającego CMDOP desktop na OPENCLAW_PORT.
    """
    from agents.openclaw_runner import run_openclaw
    logger.info("OpenClaw: start — agenci przez CMDOP runtime")
    try:
        await run_openclaw()
    except Exception as e:
        logger.error(f"OpenClaw error: {e}", exc_info=True)


# ── Main ───────────────────────────────────────────────────

async def main():
    logger.info("=" * 52)
    logger.info("  TRADING SYSTEM — START  [OpenClaw runtime]")
    logger.info("=" * 52)

    # 1. Walidacja konfiguracji
    try:
        settings.validate()
    except EnvironmentError as e:
        logger.error(f"Błąd konfiguracji:\n{e}")
        sys.exit(1)

    for k, v in settings.status().items():
        logger.info(f"  {k}: {v}")

    # 2. Inicjalizacja bazy danych
    init_db()
    log_activity(
        "system",
        f"System uruchomiony — tryb: {settings.TRADING_MODE} | runtime: OpenClaw",
        "info",
    )

    # 3. Ingest Knowledge Base (pomijaj jeśli aktualny)
    try:
        from knowledge_base.query import get_collection_count
        from knowledge_base.ingest import ingest
        from pathlib import Path as _Path
        strategy_files = len(list(
            _Path("knowledge_base/strategies").glob("*.md")
        ))
        kb_count = get_collection_count()
        if kb_count >= strategy_files > 0 and kb_count == strategy_files:
            logger.info(
                f"Knowledge Base: aktualny ({kb_count} dokumentów) — pomijam ingest"
            )
        else:
            logger.info(
                f"Knowledge Base: ingest "
                f"({kb_count} w KB / {strategy_files} plików)..."
            )
            ingest()
    except Exception as e:
        logger.warning(f"KB ingest warning (niekrytyczny): {e}")

    # 4. Uruchom wszystkie komponenty równolegle
    tasks = [
        asyncio.create_task(_run_market_feed(),       name="market_feed"),
        asyncio.create_task(_run_signal_scanner(),    name="signal_scanner"),
        asyncio.create_task(_run_dashboard(),         name="dashboard"),
        asyncio.create_task(_run_telegram(),          name="telegram"),
        asyncio.create_task(_run_position_monitor(),  name="position_monitor"),
        asyncio.create_task(_run_openclaw(),          name="openclaw"),
    ]

    # 5. Graceful shutdown (SIGTERM / SIGINT)
    loop = asyncio.get_running_loop()

    def _handle_signal(sig):
        logger.info(f"Sygnał {sig.name} — graceful shutdown...")
        for t in tasks:
            if not t.done():
                t.cancel()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _handle_signal, sig)
        except NotImplementedError:
            pass  # Windows

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Zatrzymuję wszystkie taski...")
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        log_activity("system", "System zatrzymany", "info")
        logger.info("System zatrzymany.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
