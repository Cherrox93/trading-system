"""
JEDYNY plik który decyduje paper vs live.
Nie zmieniaj logiki — tylko dodawaj do paper_broker lub lighter_broker.
"""
from config import settings
from database.db import log_activity


def execute_trade(order: dict) -> dict:
    """
    Wykonaj zlecenie w odpowiednim trybie.

    order = {
        "agent_id": "trader_01",
        "token": "WLD",
        "direction": "long",    # long/short
        "size_usdt": 10.0,
        "sl_pct": 0.005,
        "tp_pct": 0.010,
        "strategy": "pivot_mr",
        "reasoning": "...",
        "confidence": 0.78
    }

    returns = {
        "success": True/False,
        "trade_id": int,
        "entry_price": float,
        "message": str,
        "mode": "paper"/"live"
    }
    """
    if settings.IS_PAPER:
        from execution.paper_broker import execute as paper_exec
        result = paper_exec(order)
    else:
        from execution.lighter_broker import execute as live_exec
        result = live_exec(order)

    log_activity(
        order["agent_id"],
        f"Trade {'wykonany' if result['success'] else 'BŁĄD'}: "
        f"{order['direction'].upper()} {order['token']} "
        f"${order['size_usdt']} [{result['mode']}]",
        "info" if result["success"] else "error"
    )

    return result


def close_trade(trade_id: int, exit_price: float, reason: str) -> dict:
    """Zamknij otwartą pozycję."""
    if settings.IS_PAPER:
        from execution.paper_broker import close as paper_close
        return paper_close(trade_id, exit_price, reason)
    else:
        from execution.lighter_broker import close as live_close
        return live_close(trade_id, exit_price, reason)
