"""
telegram/supervisor_chat.py

Swobodna rozmowa z Supervisorem przez Telegram.
Supervisor (DeepSeek) ma pełny wgląd w stan systemu i może:
  - odpowiadać na pytania o agentów, transakcje, PnL
  - wykonywać akcje: pause, resume, fund, correct, emergency_pause_all, reset_onboarding
"""
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

# Pamięć konwersacji — ostatnie N wymian (persystuje przez cały czas działania systemu)
_history: list[dict] = []
MAX_HISTORY_PAIRS = 8  # 8 par user/assistant = 16 wiadomości


# ── Kontekst systemowy ─────────────────────────────────────

def _get_system_context() -> str:
    """Pobierz aktualny stan systemu: agenci, pozycje, ostatnie transakcje."""
    from database.db import get_all_agents, get_agent_performance, get_connection
    lines = []

    # Agenci
    try:
        agents = get_all_agents()
        lines.append("=== AGENCI ===")
        for a in agents:
            p      = get_agent_performance(a["id"])
            pnl    = float(a["pnl_usdt"] or 0)
            budget = float(a["budget_usdt"] or 0)
            used   = float(a["used_usdt"] or 0)
            strats = json.loads(a.get("strategies") or "[]")
            lines.append(
                f"{a['id']} [{a.get('personality','?')}] "
                f"status={a['status']} "
                f"PnL={pnl:+.4f}$ "
                f"budget=${budget:.2f} "
                f"used=${used:.2f} "
                f"available=${budget - used:.2f} "
                f"WR={p.get('win_rate', 0):.0f}% "
                f"trades={p.get('trades', 0)} "
                f"strategies={','.join(strats) or 'brak'}"
            )
    except Exception as e:
        lines.append(f"=== AGENCI: błąd odczytu ({e}) ===")

    # Otwarte pozycje
    try:
        with get_connection() as conn:
            positions = [dict(r) for r in conn.execute("""
                SELECT agent_id, token, direction, size_usdt,
                       leverage, entry_price, sl_price, tp_price, timestamp
                FROM trades WHERE status = 'open'
                ORDER BY timestamp DESC
            """).fetchall()]
        if positions:
            lines.append("\n=== OTWARTE POZYCJE ===")
            for p in positions:
                lines.append(
                    f"{p['agent_id']}: {p['token']} {(p['direction'] or '').upper()} "
                    f"${float(p['size_usdt'] or 0):.2f} "
                    f"lev={p['leverage']}x "
                    f"entry={p['entry_price']} "
                    f"SL={p['sl_price']} TP={p['tp_price']}"
                )
        else:
            lines.append("\n=== OTWARTE POZYCJE: brak ===")
    except Exception as e:
        lines.append(f"\n=== OTWARTE POZYCJE: błąd odczytu ({e}) ===")

    # Ostatnie transakcje
    try:
        with get_connection() as conn:
            recent = [dict(r) for r in conn.execute("""
                SELECT agent_id, token, direction, pnl_usdt, status,
                       strategy_used AS strategy, timestamp
                FROM trades ORDER BY timestamp DESC LIMIT 8
            """).fetchall()]
        if recent:
            lines.append("\n=== OSTATNIE TRANSAKCJE ===")
            for t in recent:
                pnl_v = float(t["pnl_usdt"] or 0) if t["pnl_usdt"] is not None else None
                pnl_s = f"PnL={pnl_v:+.4f}$" if pnl_v is not None else "open"
                lines.append(
                    f"{t['agent_id']}: {t['token']} "
                    f"{(t['direction'] or '').upper()} "
                    f"{pnl_s} [{t['status']}] "
                    f"strategy={t.get('strategy','?')} "
                    f"{(t['timestamp'] or '')[:16]}"
                )
    except Exception as e:
        lines.append(f"\n=== OSTATNIE TRANSAKCJE: błąd odczytu ({e}) ===")

    return "\n".join(lines)


def _build_system_prompt(context: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""Jesteś Supervisorem autonomicznego systemu tradingowego AI (data: {now}).
Zarządzasz flotą agentów tradingowych na Lighter DEX (kryptowaluty, perpetual futures).

AKTUALNY STAN SYSTEMU:
{context}

MOŻLIWOŚCI — DOSTĘPNE AKCJE:
Aby wykonać akcję, umieść blok JSON w odpowiedzi (możesz użyć kilku bloków):

Zatrzymaj agenta:
```action
{{"action": "pause_agent", "agent_id": "trader_01", "reason": "powód"}}
```

Wznów agenta:
```action
{{"action": "resume_agent", "agent_id": "trader_01"}}
```

Zmień budżet agenta:
```action
{{"action": "fund_agent", "agent_id": "trader_01", "amount": 150.0}}
```

Wyślij korektę do agenta (agent zastosuje w następnym cyklu):
```action
{{"action": "write_correction", "agent_id": "trader_01", "type": "strategy_change", "new_value": "opis zmiany", "reasoning": "powód"}}
```
Dostępne typy korekt: strategy_change, note, parameter_change

Zatrzymaj wszystkich agentów awaryjnie:
```action
{{"action": "emergency_pause_all", "reason": "kryzys rynkowy"}}
```

Zresetuj strategie agenta (nowy onboarding z KB):
```action
{{"action": "reset_onboarding", "agent_id": "trader_01"}}
```

Stwórz nowego agenta:
```action
{{"action": "spawn_agent", "agent_id": "trader_04", "personality": "neutral", "budget_usdt": 10.0}}
```
Dostępne osobowości: cautious, aggressive, neutral, scalper, swing

STYL ODPOWIEDZI:
- Odpowiadaj po polsku, konkretnie i zwięźle
- Używaj HTML Telegrama: <b>pogrubienie</b>, <i>kursywa</i>, <code>kod</code>
- Jeśli wykonujesz akcję — krótko wyjaśnij dlaczego
- Jeśli pytasz o dane — bazuj na stanie systemu powyżej, nie wymyślaj
- Jeśli stan systemu jest nieaktualny lub brakuje danych — powiedz wprost
"""


# ── DeepSeek API ───────────────────────────────────────────

async def _call_deepseek(messages: list[dict]) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return "Brak DEEPSEEK_API_KEY w .env"

    try:
        import httpx
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model":      "deepseek-chat",   # V3 — szybki, do interaktywnego chatu
                    "messages":   messages,
                    "max_tokens": 1200,
                    "temperature": 0.3,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"] or ""
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return f"Błąd DeepSeek: {e}"


# ── Executor akcji ─────────────────────────────────────────

async def _execute_action(action: dict) -> str:
    act = action.get("action", "")
    try:
        if act == "pause_agent":
            from database.db import update_agent, log_activity
            aid    = action["agent_id"]
            reason = action.get("reason", "Polecenie Supervisora przez Telegram")
            update_agent(aid, status="paused")
            log_activity("supervisor_chat", f"Agent {aid} zatrzymany: {reason}", "warning")
            return f"Agent <code>{aid}</code> zatrzymany"

        elif act == "resume_agent":
            from database.db import update_agent, log_activity
            aid = action["agent_id"]
            update_agent(aid, status="active")
            log_activity("supervisor_chat", f"Agent {aid} wznowiony", "info")
            return f"Agent <code>{aid}</code> wznowiony"

        elif act == "fund_agent":
            from database.db import set_agent_budget, log_activity
            aid    = action["agent_id"]
            amount = float(action["amount"])
            set_agent_budget(aid, amount)
            log_activity("supervisor_chat", f"Budżet {aid} → ${amount}", "info")
            return f"Budżet <code>{aid}</code> → <b>${amount:.2f}</b>"

        elif act == "write_correction":
            from database.db import get_connection
            aid      = action["agent_id"]
            c_type   = action.get("type", "note")
            c_value  = str(action.get("new_value", ""))
            c_reason = action.get("reasoning", "")
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO corrections
                      (agent_id, type, new_value, reasoning, timestamp, applied)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (aid, c_type, c_value, c_reason,
                      datetime.now(timezone.utc).isoformat()))
            return f"Korekta → <code>{aid}</code>: {c_type} = {c_value}"

        elif act == "emergency_pause_all":
            from database.db import get_all_agents, update_agent, log_activity
            reason  = action.get("reason", "Awaryjne zatrzymanie")
            agents  = get_all_agents()
            paused  = []
            for a in agents:
                if a["status"] == "active":
                    update_agent(a["id"], status="paused")
                    paused.append(a["id"])
            log_activity("supervisor_chat", f"EMERGENCY PAUSE ALL: {reason}", "critical")
            ids = ", ".join(f"<code>{i}</code>" for i in paused)
            return f"Zatrzymano: {ids or 'brak aktywnych'}"

        elif act in ("spawn_agent", "create_agent", "new_agent"):
            from factory.spawn_agent import spawn_agent
            aid         = action["agent_id"]
            personality = action.get("personality", "neutral")
            budget      = float(action.get("budget_usdt", 10.0))
            result      = await spawn_agent(aid, personality, budget)
            if result["success"]:
                strats = result.get("onboarding", {}).get("strategies", [])
                return (
                    f"Agent <code>{aid}</code> utworzony!\n"
                    f"Osobowość: {personality} | Budżet: ${budget}\n"
                    f"Strategie: {', '.join(strats) or '—'}"
                )
            return f"Błąd tworzenia agenta <code>{aid}</code>: {result.get('error', '?')}"

        elif act == "reset_onboarding":
            from agents.onboarding import reset_onboarding, run_onboarding
            from database.db import get_agent
            aid   = action["agent_id"]
            agent = get_agent(aid)
            if not agent:
                return f"Agent {aid} nie istnieje"
            await reset_onboarding(aid)
            result = await run_onboarding(aid, agent.get("personality", "neutral"))
            if result["success"]:
                strats = result.get("strategies", [])
                return f"Onboarding <code>{aid}</code> zresetowany → {', '.join(strats) or '—'}"
            return f"Błąd onboardingu {aid}: {result.get('error', '?')}"

        else:
            return f"Nieznana akcja: <code>{act}</code>"

    except KeyError as e:
        return f"Brakujący parametr akcji {act}: {e}"
    except Exception as e:
        logger.error(f"Błąd wykonania akcji {act}: {e}", exc_info=True)
        return f"Błąd akcji {act}: {e}"


def _parse_actions(text: str) -> tuple[str, list[dict]]:
    """Wyciągnij bloki ```action``` z tekstu odpowiedzi."""
    actions = []
    pattern = r"```action\s*\n([\s\S]*?)\n```"
    for m in re.findall(pattern, text, re.DOTALL):
        try:
            actions.append(json.loads(m.strip()))
        except json.JSONDecodeError as e:
            logger.warning(f"Nie można sparsować akcji JSON: {e}\nTekst: {m}")
    clean = re.sub(pattern, "", text, flags=re.DOTALL).strip()
    return clean, actions


# ── Główna funkcja ─────────────────────────────────────────

async def handle_supervisor_message(text: str) -> str:
    """Przetworz wiadomość przez Supervisora (DeepSeek) i wykonaj akcje."""
    global _history

    context       = _get_system_context()
    system_prompt = _build_system_prompt(context)

    # Dodaj wiadomość użytkownika do historii
    _history.append({"role": "user", "content": text})

    # Ogranicz historię do ostatnich N par
    max_msgs = MAX_HISTORY_PAIRS * 2
    if len(_history) > max_msgs:
        _history = _history[-max_msgs:]

    messages      = [{"role": "system", "content": system_prompt}] + _history
    raw_response  = await _call_deepseek(messages)

    # Dodaj odpowiedź do historii
    _history.append({"role": "assistant", "content": raw_response})

    # Parsuj i wykonaj akcje
    clean_text, actions = _parse_actions(raw_response)

    action_results = []
    for action in actions:
        result = await _execute_action(action)
        action_results.append(result)

    # Złóż odpowiedź
    parts = []
    if clean_text:
        parts.append(clean_text)
    if action_results:
        lines = "\n".join(f"• {r}" for r in action_results)
        parts.append(f"\n<b>Wykonane akcje:</b>\n{lines}")

    return "\n".join(parts) or "Rozumiem."


def clear_history():
    """Wyczyść historię konwersacji."""
    global _history
    _history = []
