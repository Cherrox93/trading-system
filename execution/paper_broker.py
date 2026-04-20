"""
Paper Trading Broker — symuluje wykonanie bez prawdziwych zleceń.
Używany gdy TRADING_MODE=paper.

Ceny pobierane z data/market_snapshot.json (aktualizowany przez market_feed).
PnL obliczany na podstawie symulowanego ruchu ceny.
"""
import json
import logging
import random
from pathlib import Path
from datetime import datetime

from config import settings
from database.db import (
    log_trade_open, log_trade_close,
    get_agent, update_agent, log_activity,
    get_connection
)

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = Path("./data/market_snapshot.json")


def _get_price(token: str) -> float:
    """Pobierz aktualną cenę z snapshotu, z fallbackiem do Lighter API."""
    try:
        data = json.loads(SNAPSHOT_PATH.read_text())
        for t in data.get("tokens", []):
            if t["symbol"] == token:
                return float(t["price"])
    except Exception as e:
        logger.warning(f"Nie mogę odczytać ceny {token} z snapshotu: {e}")
    # Fallback — zapytaj Lighter API bezpośrednio
    try:
        import httpx
        r = httpx.get(
            "https://mainnet.zklighter.elliot.ai/api/v1/exchangeStats",
            timeout=5,
        )
        for m in r.json().get("order_book_stats", []):
            if m.get("symbol") == token:
                price = float(m["last_trade_price"])
                logger.warning(f"_get_price: {token} z Lighter API fallback @ {price}")
                return price
    except Exception as e:
        logger.error(f"_get_price: Lighter API fallback nieudany dla {token}: {e}")
    raise ValueError(f"Nie można pobrać ceny dla {token} — brak danych w snapshot i API")


def _get_snapshot_data(token: str) -> dict:
    """Pobierz pełne dane tokenu z snapshotu."""
    try:
        data = json.loads(SNAPSHOT_PATH.read_text())
        for t in data.get("tokens", []):
            if t["symbol"] == token:
                return t
    except Exception:
        pass
    return {"symbol": token, "price": _get_price(token), "rsi": 50.0}


def execute(order: dict) -> dict:
    """
    Symuluj otwarcie pozycji.

    Waliduje budżet agenta, oblicza poziomy SL/TP,
    zapisuje trade do SQLite.
    """
    agent_id = order["agent_id"]
    agent = get_agent(agent_id)

    if not agent:
        return {
            "success": False,
            "message": f"Agent {agent_id} nie istnieje",
            "mode": "paper"
        }

    # Sprawdź budżet
    available = agent["budget_usdt"] - agent["used_usdt"]
    if order["size_usdt"] > available:
        return {
            "success": False,
            "message": (
                f"Niewystarczajacy budzet: potrzeba ${order['size_usdt']:.2f}, "
                f"dostepne ${available:.2f}"
            ),
            "mode": "paper"
        }

    # Pobierz cenę wejścia
    entry_price = _get_price(order["token"])
    direction   = order["direction"]  # long/short
    sl_pct      = order.get("sl_pct", 0.005)
    tp_pct      = order.get("tp_pct", 0.010)

    # Oblicz SL i TP
    if direction == "long":
        sl_price = round(entry_price * (1 - sl_pct), 6)
        tp_price = round(entry_price * (1 + tp_pct), 6)
    else:
        sl_price = round(entry_price * (1 + sl_pct), 6)
        tp_price = round(entry_price * (1 - tp_pct), 6)

    # Zapisz trade do bazy
    trade_id = log_trade_open(
        agent_id    = agent_id,
        token       = order["token"],
        direction   = direction,
        size_usdt   = order["size_usdt"],
        entry_price = entry_price,
        sl_price    = sl_price,
        tp_price    = tp_price,
        strategy    = order.get("strategy", "unknown"),
        reasoning   = order.get("reasoning", ""),
        confidence  = order.get("confidence", 0.5),
        leverage    = int(order.get("leverage", 1)),
    )

    log_activity(
        agent_id,
        f"PAPER {direction.upper()} {order['token']} "
        f"@${entry_price} | SL:${sl_price} TP:${tp_price} "
        f"| Rozmiar: ${order['size_usdt']}",
        "info"
    )

    return {
        "success":     True,
        "trade_id":    trade_id,
        "entry_price": entry_price,
        "sl_price":    sl_price,
        "tp_price":    tp_price,
        "message":     (
            f"PAPER {direction.upper()} {order['token']} "
            f"@${entry_price:.4f}"
        ),
        "mode": "paper"
    }


def close(trade_id: int, exit_price: float | None, reason: str) -> dict:
    """
    Zamknij pozycję paper.
    Jeśli exit_price=None, pobierz aktualną cenę z snapshotu.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM trades WHERE id = ?", (trade_id,)
        ).fetchone()

    if not row:
        return {"success": False, "message": f"Trade {trade_id} nie istnieje"}

    trade = dict(row)

    if trade["status"] != "open":
        return {"success": False, "message": f"Trade {trade_id} juz zamkniety"}

    if exit_price is None:
        try:
            exit_price = _get_price(trade["token"])
        except ValueError as e:
            logger.error(f"close: {e}")
            return {"success": False, "message": str(e)}

    # Oblicz PnL — size_usdt to margin, leverage mnoży ekspozycję
    leverage = float(trade.get("leverage") or 1)
    if trade["direction"] == "long":
        pnl = (exit_price - trade["entry_price"]) \
              / trade["entry_price"] * trade["size_usdt"] * leverage
    else:
        pnl = (trade["entry_price"] - exit_price) \
              / trade["entry_price"] * trade["size_usdt"] * leverage

    pnl = round(pnl, 4)
    log_trade_close(trade_id, exit_price, pnl)

    sign = "+" if pnl > 0 else ""
    log_activity(
        trade["agent_id"],
        f"PAPER CLOSE {trade['token']} @${exit_price:.4f} "
        f"| PnL: {sign}{pnl} USDT "
        f"| Powod: {reason}",
        "info"
    )

    return {
        "success":    True,
        "trade_id":   trade_id,
        "pnl_usdt":   pnl,
        "exit_price": exit_price,
        "reason":     reason,
        "mode":       "paper"
    }


def simulate_price_move(trade_id: int) -> dict | None:
    """
    Sprawdź czy otwarta pozycja paper osiągnęła SL lub TP.
    Wywoływana co N sekund przez market_feed.
    Zwraca wynik close jeśli pozycja zamknięta, None jeśli nadal otwarta.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM trades WHERE id = ? AND status = 'open'",
            (trade_id,)
        ).fetchone()

    if not row:
        return None

    trade     = dict(row)
    current   = _get_price(trade["token"])
    direction = trade["direction"]
    sl_price  = trade["sl_price"]
    tp_price  = trade["tp_price"]

    # Sprawdź czy osiągnięto SL lub TP
    if direction == "long":
        if current <= sl_price:
            return close(trade_id, sl_price, "stop_loss")
        if current >= tp_price:
            return close(trade_id, tp_price, "take_profit")
    else:
        if current >= sl_price:
            return close(trade_id, sl_price, "stop_loss")
        if current <= tp_price:
            return close(trade_id, tp_price, "take_profit")

    return None  # pozycja nadal otwarta
