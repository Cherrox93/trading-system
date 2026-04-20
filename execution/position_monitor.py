"""
execution/position_monitor.py

Background task — monitorowanie SL/TP bez LLM.
Sprawdza ceny co CHECK_INTERVAL sekund, zamyka pozycje gdy cena
osiągnie SL lub TP. Agent (LLM) dostaje powiadomienie przy następnym
heartbeat przez get_performance — widzi że pozycja jest zamknięta.

Korzyść: zero tokenów LLM na rutynowy monitoring SL/TP.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
logger = logging.getLogger(__name__)

CHECK_INTERVAL = 2   # sekundy między sprawdzeniami cen

def _get_exchange_stats() -> dict[str, float]:
    """Pobierz last_trade_price dla wszystkich tokenów z price_cache dashboardu."""
    try:
        from dashboard.price_cache import _prices
        return dict(_prices)
    except Exception:
        return {}


def _get_open_positions() -> list[dict]:
    """Pobierz wszystkie otwarte pozycje z SQLite."""
    try:
        from database.db import get_connection
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT id, agent_id, token, direction,
                       entry_price, sl_price, tp_price, size_usdt, leverage
                FROM trades
                WHERE status = 'open'
            """).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"PositionMonitor: błąd pobierania pozycji: {e}")
        return []


def _get_current_price(token: str, snapshot: dict) -> float | None:
    """Pobierz aktualną cenę tokenu — z state jeśli załadowany, fallback snapshot, fallback API."""
    try:
        from data.market_feed import get_current_price
        price = get_current_price(token)
        if price and price > 0:
            return price
    except Exception:
        pass
    for t in snapshot.get("tokens", []):
        if t.get("symbol", "").upper() == token.upper():
            return float(t.get("price") or t.get("last_price") or 0) or None
    # Fallback: Lighter API dla tokenów które wypadły z feedu (np. wolumen < próg)
    stats = _get_exchange_stats()
    price = stats.get(token, 0.0)
    if price > 0:
        logger.debug(f"PositionMonitor: {token} nie w feedzie — cena z API cache: {price}")
        return price
    return None


def _check_sl_tp(position: dict, current_price: float) -> str | None:
    """
    Sprawdź czy cena przekroczyła SL lub TP.
    Zwraca 'sl', 'tp' lub None.
    """
    direction  = (position.get("direction") or "long").lower()
    sl_price   = position.get("sl_price")
    tp_price   = position.get("tp_price")

    if sl_price is None or tp_price is None:
        return None

    sl = float(sl_price)
    tp = float(tp_price)

    if direction == "long":
        if current_price <= sl:
            return "sl"
        if current_price >= tp:
            return "tp"
    else:  # short
        if current_price >= sl:
            return "sl"
        if current_price <= tp:
            return "tp"

    return None


async def _close_position(position: dict, reason_type: str, current_price: float):
    """Zamknij pozycję i zaloguj."""
    trade_id = position["id"]
    agent_id = position["agent_id"]
    token    = position["token"]
    reason   = (
        f"SL trafiony @ {current_price:.6f}"
        if reason_type == "sl"
        else f"TP osiągnięty @ {current_price:.6f}"
    )

    try:
        from execution.trade_executor import close_trade
        result = close_trade(trade_id, current_price, reason)

        level = "info" if reason_type == "tp" else "warning"
        label = "TP" if reason_type == "tp" else "SL"
        pnl   = result.get("pnl_usdt", 0) or 0

        from database.db import log_activity
        log_activity(
            agent_id,
            f"[PositionMonitor] {token} {label} → zamknięto @ {current_price:.6f} "
            f"| PnL={pnl:+.4f}$",
            level,
        )

        logger.info(
            f"PositionMonitor: {agent_id} {token} {label} "
            f"@ {current_price:.6f} | PnL={pnl:+.4f}$"
        )

        try:
            from telegram.reporter import send_trade_alert
            await send_trade_alert(agent_id, {
                "token":       token,
                "direction":   position.get("direction", ""),
                "exit_price":  current_price,
                "pnl_usdt":    pnl,
                "exit_reason": reason,
            }, "close")
        except Exception as _te:
            logger.debug(f"PositionMonitor: telegram error: {_te}")

    except Exception as e:
        logger.error(
            f"PositionMonitor: błąd zamykania trade_id={trade_id} "
            f"({agent_id} {token}): {e}"
        )


async def run_position_monitor():
    """
    Główna pętla monitora pozycji.
    Uruchamiać jako asyncio.create_task w main.py.
    """
    snapshot_path = ROOT / "data" / "market_snapshot.json"
    logger.info("PositionMonitor: start")

    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL)

            # Załaduj snapshot — plik aktualizowany przez market_feed co ~1s
            if not snapshot_path.exists():
                continue

            snapshot = json.loads(snapshot_path.read_text())
            positions = _get_open_positions()

            if not positions:
                continue

            for pos in positions:
                token = pos.get("token", "")
                if not token:
                    continue

                price = _get_current_price(token, snapshot)
                if price is None or price <= 0:
                    continue

                hit = _check_sl_tp(pos, price)
                if hit:
                    await _close_position(pos, hit, price)

        except asyncio.CancelledError:
            logger.info("PositionMonitor: zatrzymany")
            break
        except Exception as e:
            logger.error(f"PositionMonitor: nieoczekiwany błąd: {e}", exc_info=True)
            await asyncio.sleep(5)
