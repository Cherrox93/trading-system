"""
Lighter DEX Broker — STUB dla live tradingu.
Implementuj gdy TRADING_MODE=live.

Dokumentacja Lighter API: https://apidocs.lighter.xyz
Python SDK: pip install lighter-sdk
"""
import logging
from config import settings

logger = logging.getLogger(__name__)


def _get_client():
    """
    Zainicjalizuj klienta Lighter SDK.
    TODO: Uzupelnij gdy przechodzimy na live.
    """
    if not settings.LIGHTER_PRIVATE_KEY:
        raise ValueError(
            "LIGHTER_PRIVATE_KEY nie ustawiony w .env. "
            "Uzupelnij przed uruchomieniem w trybie live."
        )
    # TODO: from lighter_sdk import LighterClient
    # return LighterClient(
    #     private_key=settings.LIGHTER_PRIVATE_KEY,
    #     account_index=settings.LIGHTER_ACCOUNT_INDEX,
    #     network=settings.LIGHTER_NETWORK
    # )
    raise NotImplementedError("Lighter client nie zaimplementowany")


def execute(order: dict) -> dict:
    """
    Otwórz pozycję na Lighter DEX.

    order = {
        "agent_id": str,
        "token": str,        # np. "WLD"
        "direction": str,    # "long" / "short"
        "size_usdt": float,
        "sl_pct": float,
        "tp_pct": float,
        "strategy": str,
        "reasoning": str,
        "confidence": float
    }
    """
    try:
        client = _get_client()

        # TODO: Implementacja po przejsciu na live
        # market = f"{order['token']}-PERP"
        # side = "BUY" if order["direction"] == "long" else "SELL"
        # size = order["size_usdt"] / current_price
        #
        # result = client.place_order(
        #     market=market,
        #     side=side,
        #     order_type="MARKET",
        #     size=size
        # )
        # entry_price = result.avg_fill_price
        # trade_id = log_trade_open(...)
        # return {"success": True, "trade_id": trade_id, ...}

        raise NotImplementedError

    except (NotImplementedError, ValueError):
        return {
            "success": False,
            "message": "Lighter broker nie zaimplementowany. Uzyj TRADING_MODE=paper",
            "mode": "live"
        }
    except Exception as e:
        logger.error(f"Lighter execute error: {e}")
        return {
            "success": False,
            "message": str(e),
            "mode": "live"
        }


def close(trade_id: int, exit_price: float, reason: str) -> dict:
    """
    Zamknij pozycję na Lighter DEX.
    TODO: Implementuj po przejsciu na live.
    """
    try:
        client = _get_client()
        # TODO: Implementacja
        raise NotImplementedError
    except (NotImplementedError, ValueError):
        return {
            "success": False,
            "message": "Lighter broker nie zaimplementowany",
            "mode": "live"
        }
    except Exception as e:
        logger.error(f"Lighter close error: {e}")
        return {"success": False, "message": str(e), "mode": "live"}


def get_balance() -> float:
    """
    Pobierz saldo konta z Lighter.
    TODO: Implementuj po przejsciu na live.
    """
    try:
        client = _get_client()
        # TODO: return client.get_account_value()
        raise NotImplementedError
    except Exception:
        return 0.0


def get_open_positions() -> list:
    """
    Pobierz otwarte pozycje z Lighter.
    TODO: Implementuj po przejsciu na live.
    """
    try:
        client = _get_client()
        # TODO: return client.get_positions()
        raise NotImplementedError
    except Exception:
        return []
