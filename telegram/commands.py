"""
telegram/commands.py

Bot odbierający komendy od właściciela systemu.
Używa long polling — nie wymaga publicznego URL (działa za NAT/VPN).

Uruchomienie:
    python telegram/commands.py
Lub jako asyncio.create_task w main.py.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram.reporter import send_message

logger = logging.getLogger(__name__)

POLL_TIMEOUT = 30  # long polling timeout w sekundach


def _get_config() -> tuple[str, str]:
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def _is_authorized(message: dict) -> bool:
    """Sprawdź czy wiadomość pochodzi od właściciela."""
    _, allowed = _get_config()
    incoming   = str(message.get("chat", {}).get("id", ""))
    return bool(allowed) and incoming == allowed


# ── Handlery komend ────────────────────────────────────────

async def cmd_status() -> str:
    """Status systemu."""
    from database.db import get_all_agents, get_connection
    from config import settings

    agents    = get_all_agents()
    active    = sum(1 for a in agents if a["status"] == "active")
    paused    = sum(1 for a in agents if a["status"] == "paused")
    total_pnl = sum(float(a["pnl_usdt"] or 0) for a in agents)

    with get_connection() as conn:
        open_pos = conn.execute(
            "SELECT COUNT(*) FROM trades WHERE status='open'"
        ).fetchone()[0]

    mode = "PAPER" if settings.TRADING_MODE == "paper" else "LIVE"

    return (
        f"<b>STATUS SYSTEMU</b>\n\n"
        f"Tryb: <b>{mode}</b>\n\n"
        f"Agenci lacznie:  {len(agents)}\n"
        f"Aktywnych:       {active}\n"
        f"Zatrzymanych:    {paused}\n"
        f"Otwarte pozycje: {open_pos}\n\n"
        f"Laczny PnL: <b>"
        f"{'+' if total_pnl >= 0 else ''}{total_pnl:.4f} USDT</b>"
    )


async def cmd_agents() -> str:
    """Lista wszystkich agentów."""
    from database.db import get_all_agents, get_agent_performance

    agents = get_all_agents()
    if not agents:
        return "Brak agentow w systemie.\nUzyj /new aby stworzyc."

    lines = ["<b>AGENCI</b>\n"]
    for a in agents:
        p     = get_agent_performance(a["id"])
        pnl   = float(a["pnl_usdt"] or 0)
        emoji = ("+" if a["status"] == "active" else
                 "~" if a["status"] == "paused" else "?")
        lines.append(
            f"{emoji} <b>{a['id']}</b> [{a.get('personality', '?')}]\n"
            f"   PnL: {'+' if pnl >= 0 else ''}{pnl:.4f}$ | "
            f"WR: {p.get('win_rate', 0):.0f}% | "
            f"Trades: {p.get('trades', 0)} | "
            f"Budzet: ${float(a['budget_usdt'] or 0):.2f}"
        )
    return "\n".join(lines)


async def cmd_agent(agent_id: str) -> str:
    """Szczegóły jednego agenta."""
    from database.db import get_agent, get_agent_performance, get_agent_trades

    agent = get_agent(agent_id)
    if not agent:
        return f"Agent <code>{agent_id}</code> nie istnieje."

    p      = get_agent_performance(agent_id)
    trades = get_agent_trades(agent_id, limit=5)
    strats = json.loads(agent.get("strategies") or "[]")
    pnl    = float(agent["pnl_usdt"] or 0)
    budget = float(agent["budget_usdt"] or 0)
    used   = float(agent["used_usdt"] or 0)

    last_lines = []
    for t in trades:
        if t["status"] == "closed":
            tp    = float(t.get("pnl_usdt") or 0)
            label = "+" if tp >= 0 else "-"
            last_lines.append(
                f"  {label} {t['token']} {(t['direction'] or '').upper()} "
                f"PnL={'+' if tp >= 0 else ''}{tp:.4f}$"
            )

    msg = (
        f"<b>{agent_id}</b>\n\n"
        f"Status:     {agent['status']}\n"
        f"Osobowosc:  {agent.get('personality', '?')}\n"
        f"Strategie:  {', '.join(strats) or '—'}\n"
        f"Budzet:     ${budget:.2f}\n"
        f"Dostepne:   ${budget - used:.2f}\n"
        f"PnL:        {'+' if pnl >= 0 else ''}{pnl:.4f} USDT\n"
        f"Win Rate:   {p.get('win_rate', 0):.1f}%\n"
        f"Trades:     {p.get('trades', 0)}\n"
    )
    if last_lines:
        msg += "\n<b>Ostatnie transakcje:</b>\n" + "\n".join(last_lines)

    return msg


async def cmd_trades() -> str:
    """Ostatnie 10 transakcji."""
    from database.db import get_connection

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM trades
            ORDER BY timestamp DESC LIMIT 10
        """).fetchall()

    if not rows:
        return "Brak transakcji w historii."

    lines = ["<b>OSTATNIE TRANSAKCJE</b>\n"]
    for t in [dict(r) for r in rows]:
        pnl   = t.get("pnl_usdt")
        if pnl is not None:
            pnl   = float(pnl)
            label = "+" if pnl >= 0 else "-"
            pnl_t = f"{'+' if pnl >= 0 else ''}{pnl:.4f}$"
        else:
            label = "o"
            pnl_t = "open"
        lines.append(
            f"{label} {t['agent_id']} | "
            f"<b>{t['token']}</b> {(t['direction'] or '').upper()} | "
            f"{pnl_t}"
        )
    return "\n".join(lines)


async def cmd_pnl() -> str:
    """Łączny PnL systemu."""
    from database.db import get_all_agents, get_connection

    agents    = get_all_agents()
    total_pnl = sum(float(a["pnl_usdt"] or 0) for a in agents)
    total_bud = sum(float(a["budget_usdt"] or 0) for a in agents)

    # Dzisiaj — trades zamknięte dziś (kolumna timestamp)
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(pnl_usdt), 0)
            FROM trades
            WHERE status = 'closed'
            AND date(timestamp) = date('now')
        """).fetchone()
    today = float(row[0] or 0)

    dir_label = "PnL" if total_pnl >= 0 else "STRATA"
    return (
        f"<b>{dir_label} SYSTEMU</b>\n\n"
        f"Laczny PnL:  <b>"
        f"{'+' if total_pnl >= 0 else ''}{total_pnl:.4f} USDT</b>\n"
        f"Dzisiaj:     "
        f"{'+' if today >= 0 else ''}{today:.4f} USDT\n\n"
        f"Agenci:       {len(agents)}\n"
        f"Laczny budzet: ${total_bud:.2f}"
    )


async def cmd_pause(agent_id: str) -> str:
    """Zatrzymaj agenta."""
    from database.db import get_agent, update_agent, log_activity

    agent = get_agent(agent_id)
    if not agent:
        return f"Agent <code>{agent_id}</code> nie istnieje."
    if agent["status"] == "paused":
        return f"Agent <code>{agent_id}</code> jest juz zatrzymany."

    update_agent(agent_id, status="paused")
    log_activity("telegram", f"Agent {agent_id} zatrzymany przez Telegram", "info")
    return f"Agent <code>{agent_id}</code> zatrzymany."


async def cmd_resume(agent_id: str) -> str:
    """Wznów agenta."""
    from database.db import get_agent, update_agent, log_activity

    agent = get_agent(agent_id)
    if not agent:
        return f"Agent <code>{agent_id}</code> nie istnieje."
    if agent["status"] == "active":
        return f"Agent <code>{agent_id}</code> juz dziala."

    update_agent(agent_id, status="active")
    log_activity("telegram", f"Agent {agent_id} wznowiony przez Telegram", "info")
    return f"Agent <code>{agent_id}</code> wznowiony."


async def cmd_fund(agent_id: str, amount: float) -> str:
    """Przydziel budżet agentowi."""
    from database.db import get_agent, set_agent_budget, log_activity

    agent = get_agent(agent_id)
    if not agent:
        return f"Agent <code>{agent_id}</code> nie istnieje."

    old = float(agent["budget_usdt"] or 0)
    set_agent_budget(agent_id, amount)
    log_activity(
        "telegram",
        f"Budzet {agent_id}: ${old} -> ${amount} przez Telegram",
        "info",
    )
    return (
        f"Budzet <code>{agent_id}</code> zaktualizowany:\n"
        f"${old:.2f} -> <b>${amount:.2f} USDT</b>"
    )


async def cmd_new(agent_id: str, budget: float) -> str:
    """Stwórz nowego agenta z onboardingiem."""
    from database.db import get_agent

    if get_agent(agent_id):
        return f"Agent <code>{agent_id}</code> juz istnieje."

    await send_message(
        f"Tworze agenta <code>{agent_id}</code>...\n"
        f"Budzet: ${budget}\n"
        f"Onboarding (agent definiuje wlasny styl) — ~30 sekund."
    )

    try:
        from factory.spawn_agent import spawn_agent
        result = await spawn_agent(agent_id, budget)
        if result["success"]:
            identity = result.get("self_identity") or result.get("onboarding", {}).get("self_identity", "?")
            model    = result.get("onboarding", {}).get("model_used", "?")
            return (
                f"Agent <code>{agent_id}</code> gotowy!\n\n"
                f"Tozsamosc: {identity}\n"
                f"Budzet:    ${budget}\n"
                f"Model:     {model}"
            )
        else:
            return f"Blad tworzenia agenta:\n{result.get('error', '?')}"
    except Exception as e:
        logger.error(f"cmd_new error: {e}")
        return f"Blad: {e}"


async def cmd_reset(agent_id: str) -> str:
    """Zresetuj onboarding agenta."""
    from database.db import get_agent

    agent = get_agent(agent_id)
    if not agent:
        return f"Agent <code>{agent_id}</code> nie istnieje."

    await send_message(
        f"Resetuje onboarding <code>{agent_id}</code>...\n"
        f"Agent wybierze nowe strategie z KB."
    )

    try:
        from agents.onboarding import reset_onboarding, run_onboarding
        await reset_onboarding(agent_id)
        result = await run_onboarding(
            agent_id,
            agent.get("personality", "neutral"),
        )
        if result["success"]:
            strats = result.get("strategies", [])
            return (
                f"Reset onboardingu <code>{agent_id}</code> gotowy!\n"
                f"Nowe strategie: {', '.join(strats) or '—'}\n"
                f"Uzasadnienie: {result.get('reasoning', '')[:150]}"
            )
        else:
            return f"Blad onboardingu: {result.get('error', '?')}"
    except Exception as e:
        logger.error(f"cmd_reset error: {e}")
        return f"Blad: {e}"


async def cmd_clear() -> str:
    """Wyczyść historię rozmowy z Supervisorem."""
    from telegram.supervisor_chat import clear_history
    clear_history()
    return "Historia rozmowy z Supervisorem wyczyszczona."


async def cmd_help() -> str:
    """Lista dostępnych komend."""
    return (
        "<b>TRADING SYSTEM — KOMENDY</b>\n\n"
        "<b>Info:</b>\n"
        "/status          - status systemu\n"
        "/agents          - lista agentow\n"
        "/agent ID        - szczegoly agenta\n"
        "/trades          - ostatnie 10 transakcji\n"
        "/pnl             - laczny PnL\n\n"
        "<b>Sterowanie:</b>\n"
        "/pause ID        - zatrzymaj agenta\n"
        "/resume ID       - wznow agenta\n"
        "/fund ID kwota   - przydziel budzet ($)\n"
        "/reset ID        - reset strategii agenta\n\n"
        "<b>Tworzenie:</b>\n"
        "/new ID budzet\n"
        "  np: /new trader_04 100\n"
        "  Agent sam definiuje swoj styl podczas onboardingu\n\n"
        "<b>Supervisor AI:</b>\n"
        "Napisz dowolna wiadomosc (bez /) aby porozmawiac\n"
        "z Supervisorem — odpowie i moze podjac akcje.\n"
        "/clear           - wyczysc historie rozmowy\n\n"
        "/help            - ta wiadomosc"
    )


# ── Parser komend ──────────────────────────────────────────

async def handle_command(text: str) -> str | None:
    """Parsuj tekst i wywołaj właściwy handler. Zwraca odpowiedź lub None."""
    parts = text.strip().split()
    if not parts:
        return None

    cmd = parts[0].lower().lstrip("/").split("@")[0]  # usuń @botname jeśli jest

    try:
        if cmd == "status":
            return await cmd_status()

        elif cmd == "agents":
            return await cmd_agents()

        elif cmd == "agent":
            if len(parts) < 2:
                return "Uzycie: /agent AGENT_ID"
            return await cmd_agent(parts[1])

        elif cmd == "trades":
            return await cmd_trades()

        elif cmd == "pnl":
            return await cmd_pnl()

        elif cmd == "pause":
            if len(parts) < 2:
                return "Uzycie: /pause AGENT_ID"
            return await cmd_pause(parts[1])

        elif cmd == "resume":
            if len(parts) < 2:
                return "Uzycie: /resume AGENT_ID"
            return await cmd_resume(parts[1])

        elif cmd == "fund":
            if len(parts) < 3:
                return "Uzycie: /fund AGENT_ID KWOTA"
            try:
                amount = float(parts[2])
            except ValueError:
                return "Kwota musi byc liczba. Np: /fund trader_01 15"
            return await cmd_fund(parts[1], amount)

        elif cmd == "new":
            if len(parts) < 3:
                return "Uzycie: /new AGENT_ID BUDZET\nNp: /new trader_04 100"
            try:
                budget = float(parts[2])
            except ValueError:
                return "Budzet musi byc liczba. Np: /new trader_04 100"
            return await cmd_new(parts[1], budget)

        elif cmd == "reset":
            if len(parts) < 2:
                return "Uzycie: /reset AGENT_ID"
            return await cmd_reset(parts[1])

        elif cmd == "clear":
            return await cmd_clear()

        elif cmd in ("help", "start"):
            return await cmd_help()

        else:
            return (
                f"Nieznana komenda: <code>{cmd}</code>\n"
                f"Uzyj /help aby zobaczyc dostepne komendy."
            )

    except Exception as e:
        logger.error(f"Blad komendy {cmd}: {e}", exc_info=True)
        return f"Blad wykonania komendy: {e}"


# ── Long Polling Loop ──────────────────────────────────────

async def run_bot():
    """
    Główna pętla bota — long polling.
    Nie wymaga publicznego URL ani webhooków.
    Działa za NAT i VPN.
    """
    token, chat_id = _get_config()

    if not token or not chat_id:
        logger.warning(
            "Telegram bot nie skonfigurowany.\n"
            "Dodaj TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID do .env"
        )
        return

    logger.info("Telegram bot uruchomiony (long polling)...")

    import httpx
    offset = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            async with httpx.AsyncClient(timeout=POLL_TIMEOUT + 5) as client:
                r    = await client.get(url, params={
                    "offset":          offset,
                    "timeout":         POLL_TIMEOUT,
                    "allowed_updates": ["message"],
                })
                data = r.json()

            if not data.get("ok"):
                logger.warning(f"Telegram API error: {data}")
                await asyncio.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                msg = update.get("message", {})
                if not msg:
                    continue

                # Autoryzacja — tylko właściciel
                if not _is_authorized(msg):
                    logger.warning(
                        f"Nieautoryzowany: "
                        f"chat_id={msg.get('chat', {}).get('id')}"
                    )
                    continue

                text = msg.get("text", "").strip()
                if not text:
                    continue

                if text.startswith("/"):
                    logger.info(f"Komenda Telegram: {text}")
                    response = await handle_command(text)
                else:
                    logger.info(f"Wiadomosc do Supervisora: {text[:60]}")
                    from telegram.supervisor_chat import handle_supervisor_message
                    response = await handle_supervisor_message(text)

                if response:
                    await send_message(response)

        except asyncio.CancelledError:
            logger.info("Telegram bot zatrzymany")
            break
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    asyncio.run(run_bot())
