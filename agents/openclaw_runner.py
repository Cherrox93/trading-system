"""
agents/openclaw_runner.py

Lokalny orchestrator agentów — bez CMDOP LLM.
LLM: Gemini 2.5 Flash Lite (primary) → Groq Llama4 Scout (fallback).
CMDOP nie jest używany — wszystko działa lokalnie na tym samym procesie.

Harmonogram:
  Supervisor — quick monitoring co 6h, full review co 24h
  Trader     — heartbeat co SCAN_INTERVAL s (30s bez pozycji, 60s z pozycją)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent

logger = logging.getLogger(__name__)

# ── Interwały ──────────────────────────────────────────────
TRADER_SCAN_INTERVAL     = 30
TRADER_POSITION_INTERVAL = 60
SUPERVISOR_QUICK         = 6 * 3600
SUPERVISOR_FULL          = 24 * 3600

# ── Timeouty LLM ──────────────────────────────────────────
TRADER_LLM_TIMEOUT   = 60   # s
SUPERVISOR_LLM_TIMEOUT = 120  # s


# ── LLM client ────────────────────────────────────────────

def _get_llm_client():
    """Gemini 2.5 Flash Lite → Groq Llama4 Scout fallback."""
    from openai import OpenAI
    from config import settings

    if settings.GEMINI_API_KEY:
        return OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=settings.GEMINI_API_KEY,
        ), settings.GEMINI_FAST_MODEL

    if settings.GROQ_API_KEY:
        return OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
        ), settings.GROQ_MODEL

    raise ValueError("Brak GEMINI_API_KEY ani GROQ_API_KEY w .env")


def _get_deep_llm_client():
    """DeepSeek R1 (direct) → Gemini 2.5 Flash Lite fallback dla głębokiej analizy."""
    from openai import OpenAI
    from config import settings

    if settings.DEEPSEEK_API_KEY:
        return OpenAI(
            base_url="https://api.deepseek.com/v1",
            api_key=settings.DEEPSEEK_API_KEY,
        ), "deepseek-reasoner"

    # Fallback: Gemini lub Groq
    return _get_llm_client()


async def _llm_call(prompt: str, max_tokens: int = 1000) -> str:
    """Async LLM call — uruchamia w executor żeby nie blokować pętli."""
    client, model = _get_llm_client()

    def _sync():
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()

    return await asyncio.get_event_loop().run_in_executor(None, _sync)


async def _deep_llm_call(prompt: str, max_tokens: int = 2000) -> str:
    """DeepSeek R1 async call — do głębokiej analizy supervisora."""
    client, model = _get_deep_llm_client()

    def _sync():
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return resp.choices[0].message.content.strip()

    return await asyncio.get_event_loop().run_in_executor(None, _sync)


def _parse_json(raw: str) -> dict:
    """Wyciągnij JSON z odpowiedzi LLM (toleruje markdown)."""
    clean = raw.strip()
    if "```" in clean:
        for part in clean.split("```")[1:]:
            stripped = part.lstrip("json").strip()
            if stripped.startswith("{"):
                clean = stripped
                break
    if not clean.startswith("{"):
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start >= 0 and end > start:
            clean = clean[start:end]
    return json.loads(clean)


# ── Dane rynkowe ───────────────────────────────────────────

def _load_signals() -> list:
    path = ROOT / "data" / "market_signals.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return data.get("signals", [])


def _build_conditions_text(signal: dict) -> str:
    """Buduje tekstowy opis warunków rynkowych do wyszukiwania semantycznego w dzienniku."""
    ind = signal.get("indicators", {})
    return (
        f"{signal.get('symbol','?')} {signal.get('direction','?').upper()} "
        f"signal={signal.get('signal_type','?')} conf={signal.get('confidence',0):.0%} | "
        f"RSI_15m={ind.get('rsi_14','?')} RSI_4h={ind.get('rsi_4h','?')} "
        f"ATR={ind.get('atr_14','?')} EMA9={ind.get('ema_9','?')} EMA21={ind.get('ema_21','?')} | "
        f"context: {signal.get('market_context','')[:100]}"
    )


async def _generate_reflection(agent_id: str, trade: dict, close_reasoning: str) -> str:
    """Generuje głęboką analizę po zamkniętym tradzie przez DeepSeek R1 — zapisywana do dziennika."""
    pnl     = float(trade.get("pnl_usdt") or 0)
    outcome = "WIN" if pnl > 0 else "LOSS"
    prompt = (
        f"You are AI trading agent '{agent_id}'. Analyse this closed trade deeply.\n\n"
        f"TRADE:\n"
        f"  Token:     {trade.get('token')} {(trade.get('direction') or '').upper()}\n"
        f"  Strategy:  {trade.get('strategy_used','?')}\n"
        f"  Entry:     ${trade.get('entry_price','?')} | Exit: ${trade.get('exit_price','?')}\n"
        f"  Size:      ${trade.get('size_usdt','?')} x{trade.get('leverage',1)} leverage\n"
        f"  PnL:       ${pnl:+.4f} ({outcome})\n"
        f"  Close reason: {close_reasoning[:120]}\n"
        f"  Entry reasoning: {(trade.get('reasoning') or '')[:200]}\n\n"
        f"ANALYSE:\n"
        f"1. Why did this trade {'win' if pnl > 0 else 'lose'}? Be specific.\n"
        f"2. What market condition made this {'work' if pnl > 0 else 'fail'}?\n"
        f"3. What is the ONE concrete rule to apply next time?\n\n"
        f"Respond in 3 short sentences max. Plain text only. No bullet points."
    )
    try:
        reflection = await asyncio.wait_for(_deep_llm_call(prompt, max_tokens=150), timeout=60)
        return reflection.strip()[:500]
    except Exception:
        return f"{outcome}: {trade.get('strategy_used','?')} on {trade.get('token','?')}"


def _format_journal_context(entries: list[dict]) -> str:
    """Formatuje wpisy z dziennika do wstawienia w prompt tradingowy."""
    if not entries:
        return ""
    lines = ["YOUR PAST EXPERIENCE (similar market conditions):"]
    for i, e in enumerate(entries, 1):
        pnl = e["pnl_usdt"]
        outcome_tag = f"[{e['outcome']} ${pnl:+.2f}]"
        doc = e["document"]
        reflection_part = ""
        if "reflection:" in doc:
            reflection_part = doc.split("reflection:", 1)[1].strip()[:120]
        lines.append(
            f"{i}. {outcome_tag} {e['token']} {e['direction'].upper()} "
            f"strategy={e['strategy']} | {reflection_part}"
        )
    return "\n".join(lines)


def _load_snapshot() -> dict:
    path = ROOT / "data" / "market_snapshot.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _get_token_snapshot(symbol: str) -> dict | None:
    snap = _load_snapshot()
    return next(
        (t for t in snap.get("tokens", []) if t["symbol"] == symbol.upper()),
        None,
    )


# ── Dane agenta ────────────────────────────────────────────

def _get_agent_data(agent_id: str) -> dict | None:
    from database.db import get_agent, get_agent_performance, get_agent_trades, get_connection
    agent = get_agent(agent_id)
    if not agent:
        return None
    perf   = get_agent_performance(agent_id)
    recent = get_agent_trades(agent_id, limit=5)

    with get_connection() as conn:
        corrections = conn.execute(
            "SELECT * FROM corrections WHERE agent_id=? AND applied=0 ORDER BY timestamp ASC",
            (agent_id,),
        ).fetchall()
        corrections = [dict(r) for r in corrections]
        if corrections:
            ids = ",".join(str(c["id"]) for c in corrections)
            conn.execute(f"UPDATE corrections SET applied=1 WHERE id IN ({ids})")

    open_trades = [t for t in (recent or []) if t.get("status") == "open"]

    return {
        "agent":       agent,
        "perf":        perf,
        "recent":      recent or [],
        "corrections": corrections,
        "open_trades": open_trades,
    }


# ── Trader heartbeat ───────────────────────────────────────

async def _write_journal_entry(agent_id: str, trade: dict, close_reasoning: str):
    """Generuje refleksję LLM i zapisuje trade do dziennika agenta w ChromaDB."""
    try:
        from knowledge_base.journal import write_trade_entry
        reflection = await _generate_reflection(agent_id, trade, close_reasoning)
        write_trade_entry(agent_id, trade, reflection)
        logger.debug(f"Journal: zapisano trade {trade.get('id')} dla {agent_id}")
    except Exception as e:
        logger.debug(f"Journal write task error ({agent_id}): {e}")


async def _trader_beat(agent_id: str) -> bool:
    """Jeden cykl heartbeat tradera — zbiera dane, pyta LLM, wykonuje akcję."""
    from database.db import log_activity, get_agent

    agent = get_agent(agent_id)
    if not agent:
        logger.warning(f"Trader {agent_id}: brak w bazie")
        return False
    if agent["status"] != "active":
        return True  # paused/killed — pętla obsługuje

    data = _get_agent_data(agent_id)
    if not data:
        return False

    focus_areas = json.loads(data["agent"].get("strategies") or "[]")
    philosophy  = data["agent"].get("strategy_reasoning") or ""
    personality = data["agent"].get("personality", "neutral")
    budget      = data["agent"]["budget_usdt"]
    used        = data["agent"]["used_usdt"]
    available   = budget - used
    open_trades = data["open_trades"]

    # Buduj kontekst
    corrections_txt = ""
    if data["corrections"]:
        corrections_txt = "\nSUPERVISOR CORRECTIONS (apply immediately):\n"
        for c in data["corrections"]:
            corrections_txt += f"  - [{c['type']}] {c.get('reasoning','')}\n"

    if not open_trades and data["agent"].get("notes") == "pending_pause":
        from database.db import update_agent
        update_agent(agent_id, status="paused", notes=None)
        log_activity(agent_id, "PAUSED: pending pause zastosowany po zamknięciu pozycji", "warning")
        logger.warning(f"Trader {agent_id}: pending pause zastosowany")
        return True

    if open_trades:
        # Ma otwartą pozycję — monitoruj
        trade = open_trades[0]
        token_snap = _get_token_snapshot(trade["token"])
        price_info = ""
        if token_snap:
            price_info = (
                f"Current price: ${token_snap['price']:.6f} | "
                f"Change 24h: {token_snap['change_24h']:.2f}%"
            )

        prompt = f"""You are trader agent {agent_id} ({personality} personality).
You have an OPEN POSITION:
  Token: {trade['token']} | Direction: {trade['direction']}
  Entry: ${trade.get('entry_price', '?')} | Size: ${trade.get('size_usdt', '?')}
  SL: {trade.get('sl_pct', '?')}% | TP: {trade.get('tp_pct', '?')}%
  Trade ID: {trade['id']}
{price_info}
{corrections_txt}
Budget: ${budget:.2f} | Available: ${available:.2f}

Analyze the current market conditions for {trade['token']} and decide: HOLD or CLOSE.
Close only if: strong reversal signal, SL likely to be hit soon, or better opportunity exists.

Respond with valid JSON only:
{{
  "decision": "hold" or "close",
  "reasoning": "max 60 words",
  "trade_id": {trade['id']}
}}"""

    else:
        # Brak pozycji — szukaj setupu
        signals = _load_signals()
        top_signals = signals[:8] if signals else []

        signals_txt = ""
        if top_signals:
            for s in top_signals:
                ind = s.get("indicators", {})
                pivots = (
                    f"PP={ind.get('pivot_pp','?')} "
                    f"S1={ind.get('pivot_s1','?')} S2={ind.get('pivot_s2','?')} "
                    f"R1={ind.get('pivot_r1','?')} R2={ind.get('pivot_r2','?')}"
                ) if ind else ""
                signals_txt += (
                    f"\n--- {s.get('symbol','?')} {(s.get('direction','?')).upper()} "
                    f"[{s.get('signal_type','?')}] conf={int(s.get('confidence',0)*100)}% ---\n"
                    f"  Price: ${s.get('price','?')}\n"
                    f"  RSI_15m={ind.get('rsi_14','?')} RSI_4h={ind.get('rsi_4h','?')} "
                    f"ATR={ind.get('atr_14','?')}\n"
                    f"  EMA9={ind.get('ema_9','?')} EMA21={ind.get('ema_21','?')}\n"
                    f"  {pivots}\n"
                    f"  Suggested SL={s.get('suggested_sl_pct','?')} "
                    f"TP={s.get('suggested_tp_pct','?')}\n"
                    f"  Context: {s.get('market_context','')[:120]}\n"
                )
        else:
            signals_txt = "  No signals available right now.\n"

        # Odpytaj dziennik agenta — doświadczenie z podobnych warunków
        journal_context = ""
        if top_signals:
            try:
                from knowledge_base.journal import query_similar, get_journal_count
                if get_journal_count(agent_id) >= 3:
                    conditions_text = _build_conditions_text(top_signals[0])
                    past_entries = query_similar(agent_id, conditions_text, n=3)
                    journal_context = _format_journal_context(past_entries)
            except Exception as _je:
                logger.debug(f"Journal query error: {_je}")

        focus_txt = ", ".join(focus_areas) if focus_areas else "open to any setup"
        philosophy_txt = philosophy[:200] if philosophy else ""

        prompt = f"""You are trader agent {agent_id} ({personality} personality).

YOUR TRADING IDENTITY:
{philosophy_txt}
Focus areas: {focus_txt}

Budget: ${budget:.2f} | Available: ${available:.2f}
{corrections_txt}
{journal_context}

MARKET SIGNALS (pre-analyzed by scanner):
{signals_txt}
You are free to use any approach that fits the market conditions — you are not locked to any strategy.
Use your trading identity and past experience to judge each signal.
If similar setups previously failed, lower confidence or skip.
Select ONE to enter, or skip if nothing fits.
You decide: leverage (1-50x), position size (% of budget), SL and TP.
Use the indicators (RSI, ATR, pivots) to set precise SL/TP levels.
IMPORTANT: always set sl_pct=0.004 (0.4%) and tp_pct=0.006 (0.6%) — fixed R:R learning phase.
Only enter if confidence >= 65%.

Respond with valid JSON only:
{{
  "decision": "enter" or "skip",
  "reasoning": "max 60 words",
  "token": "BTC",
  "direction": "long" or "short",
  "size_pct": 0.3,
  "leverage": 5,
  "sl_pct": 0.004,
  "tp_pct": 0.006,
  "strategy": "strategy_name",
  "confidence": 0.75
}}
Position sizing based on confidence:
  confidence < 0.70  → size_pct = 0.10  (10% of budget)
  confidence 0.70–0.79 → size_pct = 0.20  (20% of budget)
  confidence 0.80–0.89 → size_pct = 0.35  (35% of budget)
  confidence >= 0.90   → size_pct = 0.50  (50% of budget)
Do NOT enter if confidence < 0.65."""

    try:
        raw    = await asyncio.wait_for(_llm_call(prompt, max_tokens=400), timeout=TRADER_LLM_TIMEOUT)
        result = _parse_json(raw)
    except asyncio.TimeoutError:
        logger.warning(f"Trader {agent_id}: LLM timeout")
        return False
    except Exception as e:
        logger.warning(f"Trader {agent_id}: LLM error — {e}")
        return False

    decision = result.get("decision", "skip")
    reasoning = result.get("reasoning", "")

    if decision == "enter" and not open_trades:
        token     = result.get("token", "")
        direction = result.get("direction", "")
        size_pct  = float(result.get("size_pct", 0))
        leverage  = int(result.get("leverage", 1))
        sl_pct    = float(result.get("sl_pct", 0))
        tp_pct    = float(result.get("tp_pct", 0))
        strategy  = result.get("strategy", "unknown")
        confidence = float(result.get("confidence", 0.5))

        sl_pct = 0.004  # enforce SL 0.4%
        tp_pct = 0.006  # enforce TP 0.6% (R:R 1.5:1)
        if confidence >= 0.90:
            size_pct = 0.50
        elif confidence >= 0.80:
            size_pct = 0.35
        elif confidence >= 0.70:
            size_pct = 0.20
        else:
            size_pct = 0.10
        if token and direction and sl_pct >= 0.001:
            size_usdt = budget * size_pct
            if size_usdt <= available:
                from execution.trade_executor import execute_trade
                trade_result = execute_trade({
                    "agent_id":   agent_id,
                    "token":      token.upper(),
                    "direction":  direction,
                    "size_usdt":  round(size_usdt, 4),
                    "sl_pct":     sl_pct,
                    "tp_pct":     tp_pct,
                    "leverage":   max(1, min(50, leverage)),
                    "strategy":   strategy,
                    "reasoning":  reasoning[:300],
                    "confidence": confidence,
                })
                if trade_result.get("success"):
                    logger.info(f"Trader {agent_id}: ENTER {direction.upper()} {token} ${size_usdt:.2f} lev={leverage}x")
                    trade_data = {
                        "token":       token.upper(),
                        "direction":   direction,
                        "size_usdt":   size_usdt,
                        "strategy":    strategy,
                        "entry_price": trade_result.get("entry_price", "?"),
                        "sl_price":    trade_result.get("sl_price", "?"),
                        "tp_price":    trade_result.get("tp_price", "?"),
                        "leverage":    leverage,
                    }
                    try:
                        from telegram.reporter import send_trade_alert
                        await send_trade_alert(agent_id, trade_data, "open")
                    except Exception as _te:
                        logger.debug(f"Telegram trade alert error: {_te}")
                else:
                    logger.warning(f"Trader {agent_id}: trade FAIL — {trade_result.get('message')}")
            else:
                logger.info(f"Trader {agent_id}: za mały budżet na {token} (${size_usdt:.2f} > ${available:.2f})")

    elif decision == "close" and open_trades:
        trade_id = result.get("trade_id", open_trades[0]["id"])
        from execution.trade_executor import close_trade
        close_result = close_trade(trade_id, None, reasoning)
        if close_result.get("success"):
            logger.info(f"Trader {agent_id}: CLOSE trade {trade_id} — {reasoning[:60]}")
            orig = open_trades[0]
            closed_trade = {
                "token":       orig.get("token", "?"),
                "direction":   orig.get("direction", "?"),
                "pnl_usdt":    close_result.get("pnl_usdt", 0),
                "exit_price":  close_result.get("exit_price", "?"),
                "exit_reason": reasoning[:100],
            }
            try:
                from telegram.reporter import send_trade_alert
                await send_trade_alert(agent_id, closed_trade, "close")
            except Exception as _te:
                logger.debug(f"Telegram trade alert error: {_te}")

            # Zapisz do dziennika agenta (nieblokująco)
            journal_trade = {
                **dict(orig),
                "pnl_usdt":  close_result.get("pnl_usdt", 0),
                "exit_price": close_result.get("exit_price"),
                "status":    "closed",
            }
            asyncio.create_task(_write_journal_entry(agent_id, journal_trade, reasoning))
        else:
            logger.warning(f"Trader {agent_id}: close FAIL — {close_result.get('message')}")

    else:
        logger.info(f"Trader {agent_id}: {decision.upper()} — {reasoning[:80]}")

    log_activity(agent_id, f"DECISION: {decision} | {reasoning}", "info")
    return True


# ── Supervisor heartbeat ───────────────────────────────────

def _supervisor_pause_eligible(agent_data: dict) -> bool:
    """Zwraca True jeśli agent spełnia kryteria pauzy wg twardych reguł Python."""
    perf   = agent_data["perf"]
    trades = perf.get("trades", 0)
    wr     = perf.get("win_rate", 0)
    if wr < 30 and trades >= 10:
        return True
    recent = agent_data["recent"]
    closed = sorted(
        [t for t in recent if t.get("status") == "closed"],
        key=lambda x: x.get("timestamp", ""),
    )
    if len(closed) >= 5 and all((t.get("pnl_usdt") or 0) <= 0 for t in closed[-5:]):
        return True
    return False

async def _supervisor_quick() -> bool:
    """Supervisor quick check (co 6h): szuka problemów i pauzuje jeśli trzeba."""
    from database.db import get_all_agents, get_agent_performance, get_agent_trades, update_agent, get_connection, log_activity

    agents = get_all_agents()
    agents_data = []
    for a in agents:
        if a["status"] not in ("active", "paused"):
            continue
        perf   = get_agent_performance(a["id"])
        recent = get_agent_trades(a["id"], limit=20)
        agents_data.append({"agent": a, "perf": perf, "recent": recent or []})

    if not agents_data:
        logger.info("Supervisor quick: brak agentów do monitorowania")
        return True

    summary = ""
    for d in agents_data:
        a    = d["agent"]
        perf = d["perf"]
        wr   = perf.get("win_rate", 0)
        dd   = perf.get("max_drawdown", 0)
        trades = perf.get("trades", 0)
        summary += (
            f"  {a['id']} ({a['status']}) | WR={wr:.0f}% | "
            f"DD={dd:.1f}% | trades={trades} | PnL=${a['pnl_usdt']:.2f}\n"
        )

    prompt = f"""You are the Supervisor of a fleet of AI trading agents.
AGENT STATUS:
{summary}

Rules:
- PAUSE agent if: drawdown > 10% OR win_rate < 30% (with >= 10 trades) OR 5+ consecutive losses
- ALERT (send telegram) if any agent has drawdown > 15%
- Otherwise: monitor

Respond with valid JSON only:
{{
  "actions": [
    {{"type": "pause", "agent_id": "trader_XX", "reason": "..."}}
  ],
  "telegram": "alert message or empty string",
  "summary": "one sentence status"
}}
If no actions needed: {{"actions": [], "telegram": "", "summary": "All agents healthy"}}"""

    try:
        raw    = await asyncio.wait_for(_llm_call(prompt, max_tokens=500), timeout=SUPERVISOR_LLM_TIMEOUT)
        result = _parse_json(raw)
    except Exception as e:
        logger.warning(f"Supervisor quick: LLM error — {e}")
        return False

    agents_by_id = {d["agent"]["id"]: d for d in agents_data}

    for action in result.get("actions", []):
        if action.get("type") == "pause":
            aid    = action.get("agent_id")
            reason = action.get("reason", "Supervisor decision")

            agent_d = agents_by_id.get(aid)
            if not agent_d or not _supervisor_pause_eligible(agent_d):
                logger.info(f"Supervisor: PAUSE {aid} odrzucony — kryteria nie spełnione (za mało zamkniętych transakcji)")
                continue

            with get_connection() as conn:
                has_open = conn.execute(
                    "SELECT COUNT(*) FROM trades WHERE agent_id=? AND status='open'",
                    (aid,),
                ).fetchone()[0]

            if has_open:
                update_agent(aid, notes="pending_pause")
                log_activity("supervisor", f"PAUSE_DEFERRED {aid}: ma otwartą pozycję — pauza po zamknięciu. {reason}", "warning")
                logger.warning(f"Supervisor: PAUSE_DEFERRED {aid} — czeka na zamknięcie pozycji")
            else:
                update_agent(aid, status="paused")
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO corrections (agent_id, type, new_value, reasoning) VALUES (?,?,?,?)",
                        (aid, "pause", '{"duration":"manual_review"}', reason),
                    )
                log_activity("supervisor", f"PAUSE {aid}: {reason}", "warning")
                logger.warning(f"Supervisor: PAUSE {aid} — {reason}")

    alert = result.get("telegram", "")
    if alert:
        try:
            from telegram.reporter import send_emergency_alert
            await send_emergency_alert("supervisor", alert)
        except Exception as e:
            logger.warning(f"Supervisor: telegram error — {e}")

    logger.info(f"Supervisor quick: {result.get('summary', 'done')}")
    return True


async def _supervisor_full() -> bool:
    """Supervisor full review (co 24h): głęboka analiza + korekty + raport."""
    from database.db import get_all_agents, get_agent_performance, get_agent_trades, get_connection, log_activity

    agents = get_all_agents()
    agents_data = []
    for a in agents:
        perf   = get_agent_performance(a["id"])
        recent = get_agent_trades(a["id"], limit=20)
        strats = json.loads(a.get("strategies") or "[]")
        agents_data.append({
            "id":          a["id"],
            "status":      a["status"],
            "personality": a["personality"],
            "budget":      a["budget_usdt"],
            "pnl":         a["pnl_usdt"],
            "strategies":  strats,
            "perf":        perf,
            "recent":      recent or [],
        })

    if not agents_data:
        logger.info("Supervisor full: brak agentów")
        return True

    summary = json.dumps(
        [{"id": d["id"], "status": d["status"], "pnl": d["pnl"],
          "perf": d["perf"], "strategies": d["strategies"]}
         for d in agents_data],
        indent=2
    )

    prompt = f"""You are the Supervisor. Perform FULL 24h review of all trading agents.

AGENTS DATA:
{summary}

Your tasks:
1. Identify underperformers (WR < 40% with >= 10 trades) — suggest strategy_change correction
2. Identify outperformers (WR > 60%) — suggest budget increase
3. Write corrections for agents that need adjustment
4. Generate daily Telegram report

Respond with valid JSON only:
{{
  "corrections": [
    {{
      "agent_id": "trader_XX",
      "type": "strategy_change",
      "new_value": "description of change",
      "reasoning": "why this change"
    }}
  ],
  "budget_changes": [
    {{
      "agent_id": "trader_XX",
      "delta_usdt": 50,
      "reasoning": "outperformer reward"
    }}
  ],
  "telegram_report": "Daily report: system PnL $X, best agent: ..., issues: ...",
  "summary": "one sentence"
}}"""

    try:
        raw    = await asyncio.wait_for(_deep_llm_call(prompt, max_tokens=1500), timeout=SUPERVISOR_LLM_TIMEOUT * 2)
        result = _parse_json(raw)
    except Exception as e:
        logger.warning(f"Supervisor full: LLM error — {e}")
        return False

    # Zapisz korekty
    with get_connection() as conn:
        for c in result.get("corrections", []):
            conn.execute(
                "INSERT INTO corrections (agent_id, type, new_value, reasoning) VALUES (?,?,?,?)",
                (c.get("agent_id"), c.get("type", "note"),
                 c.get("new_value", ""), c.get("reasoning", "")),
            )
            logger.info(f"Supervisor: korekta dla {c.get('agent_id')} — {c.get('type')}")

    # Wyślij raport Telegram
    report = result.get("telegram_report", "")
    if report:
        try:
            from telegram.reporter import send_message
            await send_message(f"<b>RAPORT DZIENNY</b>\n\n{report}")
        except Exception as e:
            logger.warning(f"Supervisor: telegram report error — {e}")

    # Uruchom KB evolution
    try:
        from agents.kb_evolution import evolve_knowledge_base
        await evolve_knowledge_base(agents_data, result)
        logger.info("Supervisor: KB evolution zakończona")
    except Exception as e:
        logger.warning(f"Supervisor: KB evolution error — {e}")

    log_activity("supervisor", f"Full review: {result.get('summary', 'done')}", "info")
    logger.info(f"Supervisor full: {result.get('summary', 'done')}")
    return True


# ── OpenClawRunner ─────────────────────────────────────────

class OpenClawRunner:
    """
    Lokalny orchestrator agentów.
    CMDOP nie jest używany — wszystko działa w tym samym procesie Python.
    """

    def __init__(self):
        self.running    = False
        self.last_quick = 0.0
        self.last_full  = 0.0

    async def connect(self) -> bool:
        """Lokalny tryb — brak CMDOP. Zawsze zwraca True."""
        logger.info("OpenClaw: tryb lokalny — fast: Gemini 2.5 Flash Lite | deep: DeepSeek R1")
        try:
            from telegram.reporter import send_message
            from database.db import get_all_agents
            agents = get_all_agents()
            n = len([a for a in agents if a["status"] == "active"])
            await send_message(
                f"<b>CherroxLab — system uruchomiony</b>\n"
                f"Aktywnych agentow: {n}\n"
                f"LLM: Gemini Flash Lite (fast) | DeepSeek R1 (deep)\n"
                f"Tryb: paper"
            )
        except Exception:
            pass
        return True

    async def register_agent(self, agent_id: str) -> bool:
        """Sprawdź czy workspace istnieje."""
        workspace = ROOT / "workspaces" / agent_id
        if not workspace.exists():
            logger.error(f"OpenClaw: brak workspace dla {agent_id}: {workspace}")
            return False
        logger.info(f"OpenClaw: zarejestrowano {agent_id}")
        return True

    def _has_open_position(self, agent_id: str) -> bool:
        try:
            from database.db import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM trades WHERE agent_id=? AND status='open'",
                    (agent_id,),
                ).fetchone()
            return (row[0] or 0) > 0
        except Exception:
            return False

    async def _trader_loop(self, agent_id: str):
        logger.info(f"OpenClaw: trader loop start — {agent_id}")

        while self.running:
            try:
                from database.db import get_agent
                agent = get_agent(agent_id)
                if not agent:
                    logger.warning(f"OpenClaw: {agent_id} zniknął z bazy — stop")
                    break

                status = agent.get("status", "active")
                if status == "killed":
                    logger.info(f"OpenClaw: {agent_id} killed — stop")
                    break

                if status == "paused":
                    await asyncio.sleep(30)
                    continue

                success = await _trader_beat(agent_id)
                if success:
                    logger.info(f"OpenClaw heartbeat OK: {agent_id}")
                else:
                    logger.warning(f"OpenClaw heartbeat FAIL: {agent_id}")

                interval = (
                    TRADER_POSITION_INTERVAL
                    if self._has_open_position(agent_id)
                    else TRADER_SCAN_INTERVAL
                )
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trader loop error {agent_id}: {e}", exc_info=True)
                await asyncio.sleep(15)

        logger.info(f"OpenClaw: trader loop stop — {agent_id}")

    async def _supervisor_loop(self):
        logger.info("OpenClaw: supervisor loop start")

        # Full review przy starcie
        await _supervisor_full()
        self.last_full  = time.time()
        self.last_quick = time.time()

        while self.running:
            try:
                await asyncio.sleep(60)
                now = time.time()

                if now - self.last_full >= SUPERVISOR_FULL:
                    await _supervisor_full()
                    self.last_full  = time.time()
                    self.last_quick = time.time()
                elif now - self.last_quick >= SUPERVISOR_QUICK:
                    await _supervisor_quick()
                    self.last_quick = time.time()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Supervisor loop error: {e}", exc_info=True)
                await asyncio.sleep(60)

        logger.info("OpenClaw: supervisor loop stop")

    async def _spawn_trader_tasks(self) -> list[asyncio.Task]:
        from database.db import get_all_agents
        tasks = []
        for agent in get_all_agents():
            if agent["status"] == "active" and agent.get("onboarding_done") == 1:
                agent_id = agent["id"]
                if not (ROOT / "workspaces" / agent_id).exists():
                    logger.warning(f"OpenClaw: brak workspace {agent_id} — pomijam")
                    continue
                await self.register_agent(agent_id)
                task = asyncio.create_task(
                    self._trader_loop(agent_id),
                    name=f"oc_{agent_id}",
                )
                tasks.append(task)
                logger.info(f"OpenClaw: uruchomiono {agent_id}")
        return tasks

    async def _check_new_agents(self, tasks: list[asyncio.Task]):
        from database.db import get_all_agents
        running_ids = {t.get_name().removeprefix("oc_") for t in tasks if not t.done()}
        for agent in get_all_agents():
            agent_id = agent["id"]
            if (agent["status"] == "active"
                    and agent.get("onboarding_done") == 1
                    and agent_id not in running_ids
                    and agent_id != "supervisor"):
                if not (ROOT / "workspaces" / agent_id).exists():
                    continue
                await self.register_agent(agent_id)
                task = asyncio.create_task(
                    self._trader_loop(agent_id),
                    name=f"oc_{agent_id}",
                )
                tasks.append(task)
                logger.info(f"OpenClaw: nowy agent uruchomiony — {agent_id}")

    def stop(self):
        self.running = False

    async def run(self):
        connected = await self.connect()
        if not connected:
            logger.error("OpenClaw: brak połączenia")
            return

        self.running = True

        ok = await self.register_agent("supervisor")
        if not ok:
            logger.error("OpenClaw: nie można zainicjować workspace supervisora")
            self.running = False
            return

        from data.market_feed import wait_for_historical_ready
        logger.info("OpenClaw: czekam na market feed...")
        await wait_for_historical_ready()
        logger.info("OpenClaw: market feed gotowy")

        supervisor_task = asyncio.create_task(
            self._supervisor_loop(), name="oc_supervisor"
        )
        trader_tasks = await self._spawn_trader_tasks()
        all_tasks    = [supervisor_task] + trader_tasks

        try:
            while self.running:
                await asyncio.sleep(60)
                await self._check_new_agents(all_tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            for t in all_tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*all_tasks, return_exceptions=True)
            logger.info("OpenClaw: wszystkie agenty zatrzymane")


async def run_openclaw():
    runner = OpenClawRunner()
    await runner.run()
