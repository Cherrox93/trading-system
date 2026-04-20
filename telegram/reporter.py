"""
telegram/reporter.py

Wysyłanie wiadomości i raportów przez Telegram Bot API.
Używany przez Supervisora i inne moduły systemu.
"""
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)


def _get_config() -> tuple[str, str]:
    """Pobierz token i chat_id z env."""
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    return token, chat_id


async def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """
    Wyślij wiadomość tekstową przez Bot API.
    Zwraca True jeśli wysłano, False jeśli błąd lub brak konfiguracji.
    """
    token, chat_id = _get_config()
    if not token or not chat_id:
        logger.debug("Telegram nie skonfigurowany — pomijam")
        return False

    # Telegram limit: 4096 znaków per wiadomość
    if len(text) > 4000:
        text = text[:3900] + "\n\n... [skrocono]"

    try:
        import httpx
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json={
                "chat_id":    chat_id,
                "text":       text,
                "parse_mode": parse_mode,
            })
            r.raise_for_status()
        logger.info("Telegram: wiadomosc wyslana")
        return True
    except Exception as e:
        logger.warning(f"Telegram send error: {e}")
        return False


async def send_daily_report(agents_data: list, review: dict):
    """Wyślij dzienny raport Supervisora."""
    now       = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_pnl = sum(a.get("pnl", 0) for a in agents_data)
    health    = review.get("system_health", "unknown")
    h_label   = {"good": "OK", "warning": "UWAGA", "critical": "KRYTYCZNY"}.get(
        health, "RAPORT"
    )

    # Ranking agentów po PnL
    sorted_a = sorted(agents_data, key=lambda x: x.get("pnl", 0), reverse=True)
    ranking  = []
    for i, a in enumerate(sorted_a, 1):
        p   = a.get("performance", {})
        pnl = a.get("pnl", 0)
        ranking.append(
            f"{i}. <b>{a['id']}</b>: "
            f"{'+' if pnl >= 0 else ''}{pnl:.2f}$ | "
            f"WR={p.get('win_rate', 0):.0f}% | "
            f"{p.get('trades', 0)}tr"
        )

    # Korekty z akcją
    corrections = [
        c for c in review.get("corrections", [])
        if c.get("action", "none") != "none"
    ]
    corr_text = ""
    if corrections:
        lines = [
            f"- {c['agent_id']}: <i>{c['action']}</i> - "
            f"{c.get('reasoning', '')[:60]}"
            for c in corrections
        ]
        corr_text = "\n\nKOREKTY:\n" + "\n".join(lines)

    n_active = sum(1 for a in agents_data if a.get("status") == "active")

    msg = (
        f"[{h_label}] <b>RAPORT DZIENNY</b>\n"
        f"{now}\n\n"
        f"<b>LACZNY PnL: "
        f"{'+' if total_pnl >= 0 else ''}{total_pnl:.4f} USDT</b>\n"
        f"Agenci: {len(agents_data)} | Aktywnych: {n_active}\n\n"
        f"<b>RANKING:</b>\n"
        f"{chr(10).join(ranking)}"
        f"{corr_text}\n\n"
        f"{review.get('overall_assessment', '')}\n\n"
        f"Zalecenia: {review.get('recommendations', '')}"
    )
    await send_message(msg)


async def send_emergency_alert(agent_id: str, reason: str):
    """Alert o krytycznej sytuacji — natychmiastowy pause."""
    msg = (
        f"[EMERGENCY] <b>ALERT SUPERVISORA</b>\n\n"
        f"Agent: <code>{agent_id}</code>\n"
        f"Powod: {reason}\n"
        f"Akcja: Agent zatrzymany automatycznie\n"
        f"Czas: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    )
    await send_message(msg)


async def send_trade_alert(agent_id: str, trade: dict, action: str):
    """
    Alert o transakcji (opcjonalny — dla dużych tradów).
    action: "open" lub "close"
    """
    if action == "open":
        dir_label = "LONG" if trade.get("direction") == "long" else "SHORT"
        msg = (
            f"[TRADE OPEN]\n"
            f"Agent: <code>{agent_id}</code>\n"
            f"Token: <b>{trade['token']}</b> {dir_label}\n"
            f"Wejscie: ${trade.get('entry_price', '?')}\n"
            f"SL: ${trade.get('sl_price', '?')} | "
            f"TP: ${trade.get('tp_price', '?')}\n"
            f"Rozmiar: ${trade.get('size_usdt', '?')} USDT\n"
            f"Strategia: {trade.get('strategy', '?')}"
        )
    else:
        pnl   = float(trade.get("pnl_usdt", 0) or 0)
        sign  = "+" if pnl >= 0 else ""
        label = "ZYSK" if pnl >= 0 else "STRATA"
        msg = (
            f"[TRADE CLOSE] {label}\n"
            f"Agent: <code>{agent_id}</code>\n"
            f"Token: <b>{trade.get('token', '?')}</b> "
            f"{(trade.get('direction') or '').upper()}\n"
            f"Exit: ${trade.get('exit_price', '?')}\n"
            f"PnL: <b>{sign}{pnl:.4f} USDT</b>\n"
            f"Powod: {trade.get('exit_reason', '?')}"
        )
    await send_message(msg)
