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
TRADER_POSITION_INTERVAL = 15
SUPERVISOR_QUICK         = 6 * 3600
SUPERVISOR_FULL          = 24 * 3600

# ── Scalper config ─────────────────────────────────────────
SCALPER_AGENTS   = {"scalper"}
SCALPER_TOKENS   = {"SOL", "ETH", "BTC"}
SCALPER_LEVERAGE = 100
SCALPER_SCAN_INTERVAL     = 10
SCALPER_POSITION_INTERVAL = 5

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
            temperature=0.5,
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
        reflection = await asyncio.wait_for(_deep_llm_call(prompt, max_tokens=350), timeout=60)
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


async def _scalper_beat(agent_id: str) -> bool:
    """Heartbeat scalpera — tylko SOL/ETH/BTC, x100 leverage, bardzo ciasne SL/TP."""
    from database.db import log_activity, get_agent

    agent = get_agent(agent_id)
    if not agent or agent["status"] != "active":
        return True

    data = _get_agent_data(agent_id)
    if not data:
        return False

    budget     = data["agent"]["budget_usdt"]
    used       = data["agent"]["used_usdt"]
    available  = budget - used
    open_trades = data["open_trades"]

    if open_trades:
        trade     = open_trades[0]
        token_snap = _get_token_snapshot(trade["token"])
        cur_price  = float(token_snap.get("price") or 0) if token_snap else 0.0

        from datetime import datetime, timezone as _tz
        time_in_pos = "?"
        try:
            ts  = datetime.fromisoformat(str(trade.get("timestamp","")).replace("Z","+00:00"))
            if ts.tzinfo is None: ts = ts.replace(tzinfo=_tz.utc)
            mins = int((datetime.now(_tz.utc) - ts).total_seconds() / 60)
            time_in_pos = f"{mins}m"
        except Exception:
            mins = 0

        unrealized = ""
        if cur_price and trade.get("entry_price"):
            ep  = float(trade["entry_price"])
            sz  = float(trade.get("size_usdt") or 0)
            upnl = ((cur_price - ep) / ep if trade["direction"] == "long" else (ep - cur_price) / ep) * sz * SCALPER_LEVERAGE
            unrealized = f"Unrealized PnL: {upnl:+.4f}$"

        sl_hit = cur_price and (
            (trade["direction"] == "long"  and cur_price <= float(trade.get("sl_price") or 0)) or
            (trade["direction"] == "short" and cur_price >= float(trade.get("sl_price") or 0))
        )
        tp_hit = cur_price and (
            (trade["direction"] == "long"  and cur_price >= float(trade.get("tp_price") or 0)) or
            (trade["direction"] == "short" and cur_price <= float(trade.get("tp_price") or 0))
        )
        alert = ""
        if sl_hit:   alert = "\n!! SL BREACHED — close immediately !!"
        elif tp_hit: alert = "\n!! TP REACHED — take profit now !!"
        time_alert = "\n!! POSITION > 15min — consider closing, scalps should be fast !!" if mins >= 15 else ""

        prompt = f"""You are SCALPER, an ultra-fast trading agent. You trade ONLY BTC, ETH, SOL with x100 leverage.

OPEN POSITION:
  Token: {trade["token"]} | Direction: {trade["direction"].upper()} | Leverage: x{SCALPER_LEVERAGE}
  Entry: ${trade.get("entry_price","?")} | Size: ${trade.get("size_usdt","?")}
  SL: ${trade.get("sl_price","?")} | TP: ${trade.get("tp_price","?")}
  Current price: ${cur_price or "?"} | {unrealized}
  Time in position: {time_in_pos}
{alert}{time_alert}

SCALPER RULES:
- x100 leverage means 0.10% against you = 10% loss. BE STRICT with SL.
- Max position time: 15 minutes. Scalps don't last longer.
- ALWAYS close if SL or TP is hit.
- Close early if: momentum reversed, OR time > 15min with < 0.10% profit.
- Adjust SL to breakeven after 0.10% profit (protect capital).

Respond with valid JSON only:
{{
  "decision": "hold" | "close" | "adjust_sl" | "adjust_tp",
  "new_sl_price": 0.0,
  "new_tp_price": 0.0,
  "reasoning": "max 40 words",
  "trade_id": {trade["id"]}
}}"""

    else:
        # Brak pozycji — szukaj setupu tylko na SOL/ETH/BTC
        signals = [s for s in _load_signals() if s.get("symbol","").upper() in SCALPER_TOKENS]
        if not signals:
            logger.debug(f"Scalper: brak sygnałów na SOL/ETH/BTC")
            return True

        signals_txt = ""
        for s in signals[:5]:
            ind = s.get("indicators", {})
            signals_txt += (
                f"\n--- {s['symbol']} {s.get('direction','?').upper()} "
                f"[{s.get('signal_type','?')}] conf={int(s.get('confidence',0)*100)}% ---\n"
                f"  Price: ${s.get('price','?')}\n"
                f"  RSI_5m={ind.get('rsi_5m','?')} RSI_15m={ind.get('rsi_14','?')} "
                f"ATR={ind.get('atr_14','?')}\n"
                f"  EMA9_5m={ind.get('ema_9_5m','?')} EMA9={ind.get('ema_9','?')} EMA21={ind.get('ema_21','?')}\n"
                f"  PP={ind.get('pivot_pp','?')} S1={ind.get('pivot_s1','?')} R1={ind.get('pivot_r1','?')}\n"
                f"  Suggested SL={s.get('suggested_sl_pct','?')} TP={s.get('suggested_tp_pct','?')}\n"
                f"  Context: {s.get('market_context','')[:100]}\n"
            )

        prompt = f"""You are SCALPER, an ultra-fast trading agent specializing in BTC, ETH, SOL only.
Leverage is ALWAYS x100. You trade fast: in and out in 2-15 minutes.

Budget: ${budget:.2f} | Available: ${available:.2f}

MARKET SIGNALS (BTC/ETH/SOL only):
{signals_txt}

SCALPER ENTRY RULES:
- ONLY enter BTC, ETH, or SOL — never other tokens
- Leverage is FIXED at x100 — do NOT suggest other values
- SL: 0.10–0.20% maximum (x100 means tight SL is essential)
- TP: 0.15–0.35% (R:R minimum 1.5:1)
- size_pct: 0.20–0.40 (20-40% of budget — manage risk with small size on x100)
- Confidence >= 0.65 required (scalping is high-precision, skip weak setups)
- Best setups: volume spike + momentum alignment, S/R flip retest, VWAP deviation

Respond with valid JSON only:
{{
  "decision": "enter" or "skip",
  "reasoning": "max 40 words",
  "token": "BTC" | "ETH" | "SOL",
  "direction": "long" or "short",
  "size_pct": 0.30,
  "leverage": 100,
  "sl_pct": 0.0015,
  "tp_pct": 0.0025,
  "strategy": "scalp_strategy_name",
  "confidence": 0.72
}}
Only enter if confidence >= 0.65 and token is BTC, ETH, or SOL."""

    try:
        raw    = await asyncio.wait_for(_llm_call(prompt, max_tokens=300), timeout=TRADER_LLM_TIMEOUT)
        result = _parse_json(raw)
    except asyncio.TimeoutError:
        logger.warning(f"Scalper: LLM timeout")
        return False
    except Exception as e:
        logger.warning(f"Scalper: LLM error — {e}")
        return False

    decision  = result.get("decision", "skip")
    reasoning = result.get("reasoning", "")

    if decision == "enter" and not open_trades:
        token = (result.get("token") or "").upper()
        if token not in SCALPER_TOKENS:
            logger.info(f"Scalper: odrzucono {token} — tylko BTC/ETH/SOL")
            return True

        direction  = result.get("direction", "")
        size_pct   = float(result.get("size_pct", 0.3))
        sl_pct     = max(float(result.get("sl_pct", 0.0015)), 0.001)
        tp_pct     = max(float(result.get("tp_pct", 0.002)), 0.0015)
        strategy   = result.get("strategy", "scalp")
        confidence = float(result.get("confidence", 0.5))

        if confidence < 0.65:
            logger.info(f"Scalper: SKIP {token} — conf={int(confidence*100)}% < 65%")
            return True

        size_usdt = min(budget * size_pct, available)
        if size_usdt < 0.5:
            logger.info(f"Scalper: za mały budżet")
            return True

        from execution.trade_executor import execute_trade
        trade_result = execute_trade({
            "agent_id":   agent_id,
            "token":      token,
            "direction":  direction,
            "size_usdt":  round(size_usdt, 4),
            "sl_pct":     sl_pct,
            "tp_pct":     tp_pct,
            "leverage":   SCALPER_LEVERAGE,
            "strategy":   strategy,
            "reasoning":  reasoning[:300],
            "confidence": confidence,
        })
        if trade_result.get("success"):
            logger.info(f"Scalper: ENTER {direction.upper()} {token} ${size_usdt:.2f} x{SCALPER_LEVERAGE}")
        else:
            logger.warning(f"Scalper: trade FAIL — {trade_result.get('message')}")

    elif decision == "close" and open_trades:
        orig = open_trades[0]
        from execution.trade_executor import close_trade
        close_result = close_trade(orig["id"], None, reasoning)
        if close_result.get("success"):
            logger.info(f"Scalper: CLOSE {orig['token']} PnL={close_result.get('pnl_usdt',0):+.4f}$")
            from database.db import push_journal_queue
            push_journal_queue(agent_id, {
                **dict(orig),
                "pnl_usdt":   close_result.get("pnl_usdt", 0),
                "exit_price": close_result.get("exit_price"),
                "status":     "closed",
            }, reasoning)

    elif decision == "adjust_sl" and open_trades:
        new_sl = float(result.get("new_sl_price") or 0)
        if new_sl > 0:
            from execution.trade_executor import modify_trade
            modify_trade(open_trades[0]["id"], sl_price=new_sl)
            logger.info(f"Scalper: ADJUST_SL → {new_sl:.6f}")

    elif decision == "adjust_tp" and open_trades:
        new_tp = float(result.get("new_tp_price") or 0)
        if new_tp > 0:
            from execution.trade_executor import modify_trade
            modify_trade(open_trades[0]["id"], tp_price=new_tp)
            logger.info(f"Scalper: ADJUST_TP → {new_tp:.6f}")

    else:
        logger.info(f"Scalper: {decision.upper()} — {reasoning[:80]}")

    log_activity(agent_id, f"SCALPER {decision} | {reasoning}", "info")
    return True


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
        corrections_txt = "\nSUPERVISOR CORRECTIONS (apply immediately — these override your defaults):\n"
        for c in data["corrections"]:
            instruction = c.get("new_value") or c.get("reasoning") or ""
            corrections_txt += f"  - {instruction[:300]}\n"

    if not open_trades and data["agent"].get("notes") == "pending_pause":
        from database.db import update_agent
        update_agent(agent_id, status="paused", notes=None)
        log_activity(agent_id, "PAUSED: pending pause zastosowany po zamknięciu pozycji", "warning")
        logger.warning(f"Trader {agent_id}: pending pause zastosowany")
        return True

    if open_trades:
        # Ma otwartą pozycję — monitoruj
        trade      = open_trades[0]
        token_snap = _get_token_snapshot(trade["token"])

        # Czas w pozycji i unrealized PnL
        from datetime import datetime, timezone as _tz
        time_in_pos = ""
        unrealized  = ""
        try:
            ts_str = trade.get("timestamp", "")
            if ts_str:
                ts   = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=_tz.utc)
                mins = int((datetime.now(_tz.utc) - ts).total_seconds() / 60)
                time_in_pos = f"{mins//60}h {mins%60}m" if mins >= 60 else f"{mins}m"
        except Exception:
            pass

        cur_price = 0.0
        if token_snap:
            cur_price = float(token_snap.get("price") or 0)
        if cur_price and trade.get("entry_price"):
            ep  = float(trade["entry_price"])
            lev = float(trade.get("leverage") or 1)
            sz  = float(trade.get("size_usdt") or 0)
            if trade["direction"] == "long":
                upnl = (cur_price - ep) / ep * sz * lev
            else:
                upnl = (ep - cur_price) / ep * sz * lev
            unrealized = f"Unrealized PnL: {'+' if upnl >= 0 else ''}{upnl:.4f}$"

        # Top sygnały dostępne (dla oceny czy warto wyjść wcześniej)
        alt_signals = _load_signals()[:3]
        alt_txt = ""
        for s in alt_signals:
            if s.get("symbol") != trade["token"]:
                alt_txt += (
                    f"\n  {s['symbol']} {s.get('direction','?').upper()} "
                    f"[{s.get('signal_type','?')}] conf={int(s.get('confidence',0)*100)}%"
                )
        alt_section = f"\nAVAILABLE SIGNALS (other opportunities):{alt_txt}" if alt_txt else ""

        sl_hit = cur_price and (
            (trade['direction'] == 'long'  and cur_price <= float(trade.get('sl_price') or 0)) or
            (trade['direction'] == 'short' and cur_price >= float(trade.get('sl_price') or 0))
        )
        tp_hit = cur_price and (
            (trade['direction'] == 'long'  and cur_price >= float(trade.get('tp_price') or 0)) or
            (trade['direction'] == 'short' and cur_price <= float(trade.get('tp_price') or 0))
        )
        alert = ""
        if sl_hit:
            alert = "\n!! SL BREACHED — close immediately to limit losses !!"
        elif tp_hit:
            alert = "\n!! TP REACHED — take profit now !!"

        prompt = f"""You are trader agent {agent_id} ({personality} personality).

OPEN POSITION:
  Token: {trade['token']} | Direction: {trade['direction'].upper()}
  Entry: ${trade.get('entry_price','?')} | Size: ${trade.get('size_usdt','?')} x{trade.get('leverage',1)}
  SL: ${trade.get('sl_price','?')} | TP: ${trade.get('tp_price','?')}
  Current price: ${cur_price or '?'} | {unrealized}
  Time in position: {time_in_pos or '?'}
  Trade ID: {trade['id']}
{alert}{corrections_txt}{alt_section}

YOU control this position — there is no automatic SL/TP. You must close it yourself.

DECISIONS AVAILABLE:
- "hold"          — stay, nothing to do
- "close"         — exit now at market price
- "adjust_sl"     — move SL (only tighten toward entry / breakeven, never widen)
- "adjust_tp"     — extend TP further in profit direction when momentum is strong
- "close_partial" — close 50% now to lock partial profit, keep 50% running

Rules:
- ALWAYS close if current price has reached or passed SL or TP
- Close early: position > 2h with < 0.1% move, OR strong reversal, OR better signal conf >= 10% higher
- Partial close: in profit but uncertain — locks gains while staying exposed
- Adjust SL: after solid move in your favour, trail to breakeven
- Adjust TP: momentum accelerating — let winners run

Respond with valid JSON only:
{{
  "decision": "hold" | "close" | "adjust_sl" | "adjust_tp" | "close_partial",
  "new_sl_price": 0.0,
  "new_tp_price": 0.0,
  "close_pct": 0.5,
  "reasoning": "max 60 words",
  "trade_id": {trade['id']}
}}
(include only relevant fields)"""

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

POSITION RULES:
- Position size (size_pct = fraction of budget):
    confidence 0.55–0.64 → size_pct 0.20–0.30  (20–30% of budget)
    confidence 0.65–0.74 → size_pct 0.30–0.50  (30–50% of budget)
    confidence 0.75–0.84 → size_pct 0.50–0.70  (50–70% of budget)
    confidence >= 0.85   → size_pct 0.70–1.00  (70–100% of budget)
- Leverage — MUST follow this table, no exceptions:
    confidence 0.55–0.64 → leverage x1–x3
    confidence 0.65–0.74 → leverage x5–x10
    confidence 0.75–0.84 → leverage x10–x20
    confidence >= 0.85   → leverage x20–x50
- You decide SL and TP: use ATR and pivot points (S1/R1) to place them at natural levels.
  Minimum SL: 0.3%, minimum TP: 0.5%
- Only enter if confidence >= 55%.

Respond with valid JSON only:
{{
  "decision": "enter" or "skip",
  "reasoning": "max 60 words",
  "token": "BTC",
  "direction": "long" or "short",
  "size_pct": 0.50,
  "leverage": 15,
  "sl_pct": 0.008,
  "tp_pct": 0.015,
  "strategy": "strategy_name",
  "confidence": 0.78
}}
Do NOT enter if confidence < 0.55."""

    try:
        raw    = await asyncio.wait_for(_llm_call(prompt, max_tokens=400), timeout=TRADER_LLM_TIMEOUT)
        result = _parse_json(raw)
    except asyncio.TimeoutError:
        logger.warning(f"Trader {agent_id}: LLM timeout")
        return False
    except Exception as e:
        logger.warning(f"Trader {agent_id}: LLM error — {e}")
        return False

    # Two-pass: jeśli Gemini chce wejść z niską pewnością → DeepSeek potwierdza lub odrzuca
    if (not open_trades
            and result.get("decision") == "enter"
            and float(result.get("confidence", 1.0)) < 0.70):
        conf_pct = int(float(result.get("confidence", 0)) * 100)
        logger.debug(f"Trader {agent_id}: conf={conf_pct}% < 70% — DeepSeek second opinion")
        deep_prompt = (
            f"You are a senior trading analyst reviewing a junior trader's decision.\n\n"
            f"PROPOSED TRADE:\n"
            f"  Token: {result.get('token')} {(result.get('direction') or '').upper()}\n"
            f"  Strategy: {result.get('strategy')} | Confidence: {conf_pct}%\n"
            f"  Leverage: x{result.get('leverage',1)} | SL: {result.get('sl_pct',0):.1%} "
            f"TP: {result.get('tp_pct',0):.1%}\n"
            f"  Reasoning: {result.get('reasoning','')}\n\n"
            f"MARKET DATA:\n{prompt[prompt.find('MARKET SIGNALS'):prompt.find('POSITION RULES')]}\n\n"
            f"Does this trade make sense? Is the reasoning sound? "
            f"Can you find a fatal flaw? Be critical.\n"
            f"If the setup is genuinely valid, confirm it and suggest adjusted confidence. "
            f"If it is weak or risky, reject it.\n\n"
            f"Respond with valid JSON only:\n"
            f'{{"verdict": "confirm" or "reject", "confidence": 0.72, "reasoning": "max 60 words"}}'
        )
        try:
            deep_raw    = await asyncio.wait_for(
                _deep_llm_call(deep_prompt, max_tokens=250), timeout=45
            )
            deep_result = _parse_json(deep_raw)
            if deep_result.get("verdict") == "reject":
                logger.info(
                    f"Trader {agent_id}: DeepSeek ODRZUCIŁ {result.get('token')} — "
                    f"{deep_result.get('reasoning','')[:80]}"
                )
                result["decision"]   = "skip"
                result["reasoning"]  = f"[DeepSeek] {deep_result.get('reasoning','rejected')}"
            else:
                result["confidence"] = float(deep_result.get("confidence", result.get("confidence", 0.65)))
                logger.debug(
                    f"Trader {agent_id}: DeepSeek POTWIERDZIŁ {result.get('token')} "
                    f"conf={int(result['confidence']*100)}%"
                )
        except Exception as _de:
            logger.debug(f"Trader {agent_id}: DeepSeek second opinion error — {_de}")

    decision  = result.get("decision", "skip")
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

        sl_pct = max(sl_pct, 0.003)   # minimum SL 0.3%
        tp_pct = max(tp_pct, 0.005)   # minimum TP 0.5%
        if token and direction and confidence >= 0.55 and sl_pct >= 0.003:
            # Blokada: 1 token = max 1 agent
            from database.db import get_connection as _gc
            with _gc() as _conn:
                _tok_busy = _conn.execute(
                    "SELECT COUNT(*) FROM trades WHERE token=? AND status='open' AND agent_id!=?",
                    (token.upper(), agent_id),
                ).fetchone()[0]
            if _tok_busy:
                logger.info(f"Trader {agent_id}: {token} zajęty przez innego agenta — skip")
                log_activity(agent_id, f"SKIP: {token} zajęty przez innego agenta", "info")
                return True

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
        orig     = open_trades[0]
        trade_id = result.get("trade_id", orig["id"])
        from execution.trade_executor import close_trade
        close_result = close_trade(trade_id, None, reasoning)
        if close_result.get("success"):
            logger.info(f"Trader {agent_id}: CLOSE {trade_id} — {reasoning[:60]}")
            try:
                from telegram.reporter import send_trade_alert
                await send_trade_alert(agent_id, {
                    "token":       orig.get("token", "?"),
                    "direction":   orig.get("direction", "?"),
                    "pnl_usdt":    close_result.get("pnl_usdt", 0),
                    "exit_price":  close_result.get("exit_price", "?"),
                    "exit_reason": reasoning[:100],
                }, "close")
            except Exception as _te:
                logger.debug(f"Telegram trade alert error: {_te}")
            from database.db import push_journal_queue
            push_journal_queue(agent_id, {
                **dict(orig),
                "pnl_usdt":   close_result.get("pnl_usdt", 0),
                "exit_price": close_result.get("exit_price"),
                "status":     "closed",
            }, reasoning)
        else:
            logger.warning(f"Trader {agent_id}: close FAIL — {close_result.get('message')}")

    elif decision == "adjust_sl" and open_trades:
        new_sl = float(result.get("new_sl_price") or 0)
        if new_sl > 0:
            from execution.trade_executor import modify_trade
            r = modify_trade(open_trades[0]["id"], sl_price=new_sl)
            if r.get("success"):
                logger.info(f"Trader {agent_id}: ADJUST_SL → {new_sl:.6f} | {reasoning[:60]}")
                log_activity(agent_id, f"ADJUST_SL: {new_sl:.6f} | {reasoning}", "info")
            else:
                logger.warning(f"Trader {agent_id}: adjust_sl FAIL — {r.get('message')}")

    elif decision == "adjust_tp" and open_trades:
        new_tp = float(result.get("new_tp_price") or 0)
        if new_tp > 0:
            from execution.trade_executor import modify_trade
            r = modify_trade(open_trades[0]["id"], tp_price=new_tp)
            if r.get("success"):
                logger.info(f"Trader {agent_id}: ADJUST_TP → {new_tp:.6f} | {reasoning[:60]}")
                log_activity(agent_id, f"ADJUST_TP: {new_tp:.6f} | {reasoning}", "info")
            else:
                logger.warning(f"Trader {agent_id}: adjust_tp FAIL — {r.get('message')}")

    elif decision == "close_partial" and open_trades:
        orig      = open_trades[0]
        close_pct = float(result.get("close_pct") or 0.5)
        from execution.trade_executor import partial_close_trade
        pc_result = partial_close_trade(orig["id"], close_pct, None, reasoning)
        if pc_result.get("success"):
            logger.info(
                f"Trader {agent_id}: PARTIAL_CLOSE {int(close_pct*100)}% "
                f"PnL={pc_result.get('pnl_usdt',0):+.4f}$ — {reasoning[:50]}"
            )
            log_activity(
                agent_id,
                f"PARTIAL_CLOSE {int(close_pct*100)}%: PnL={pc_result.get('pnl_usdt',0):+.4f}$ "
                f"| pozostało ${pc_result.get('remaining_size',0):.4f} | {reasoning}",
                "info",
            )
        else:
            logger.warning(f"Trader {agent_id}: partial_close FAIL — {pc_result.get('message')}")

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
    from database.db import (
        get_all_agents, get_agent_performance, get_agent_trades, get_connection,
        log_activity, get_agent_strategy_breakdown, get_agent_token_breakdown,
    )

    agents = get_all_agents()
    agents_data = []
    for a in agents:
        perf            = get_agent_performance(a["id"])
        recent          = get_agent_trades(a["id"], limit=10)
        strats          = json.loads(a.get("strategies") or "[]")
        strat_breakdown = get_agent_strategy_breakdown(a["id"])
        token_breakdown = get_agent_token_breakdown(a["id"])
        agents_data.append({
            "id":             a["id"],
            "status":         a["status"],
            "personality":    a["personality"],
            "budget":         a["budget_usdt"],
            "pnl":            a["pnl_usdt"],
            "strategies":     strats,
            "perf":           perf,
            "recent":         recent or [],
            "strat_breakdown": strat_breakdown,
            "token_breakdown": token_breakdown,
        })

    if not agents_data:
        logger.info("Supervisor full: brak agentów")
        return True

    # Buduj czytelny blok per agent — nie surowy JSON żeby LLM lepiej rozumiał
    agents_blocks = []
    for d in agents_data:
        recent_lines = ""
        for t in d["recent"]:
            if t.get("status") == "closed":
                pnl_s = f"{t.get('pnl_usdt', 0):+.4f}$"
                recent_lines += (
                    f"    {t.get('token','?')} {(t.get('direction','?')).upper()} "
                    f"{t.get('strategy_used','?')} {pnl_s} "
                    f"conf={int((t.get('confidence') or 0)*100)}%\n"
                )

        strat_lines = ""
        for s in d["strat_breakdown"]:
            strat_lines += (
                f"    {s['strategy_used']}: WR={s['win_rate']:.0f}% "
                f"trades={s['total']} avg={s['avg_pnl']:+.4f}$\n"
            )

        token_lines = ""
        for t in d["token_breakdown"]:
            token_lines += (
                f"    {t['token']}: WR={t['win_rate']:.0f}% "
                f"trades={t['total']} avg={t['avg_pnl']:+.4f}$\n"
            )

        perf = d["perf"]
        agents_blocks.append(
            f"=== {d['id']} ({d['status']}, {d['personality']}) ===\n"
            f"  Budget: ${d['budget']:.2f} | PnL: ${d['pnl']:+.2f} | "
            f"WR: {perf.get('win_rate',0):.0f}% | Trades: {perf.get('trades',0)}\n"
            f"  Strategies assigned: {', '.join(d['strategies']) or 'none'}\n"
            f"  Strategy breakdown (min 3 trades):\n{strat_lines or '    (insufficient data)\n'}"
            f"  Token breakdown (min 3 trades):\n{token_lines or '    (insufficient data)\n'}"
            f"  Recent closed trades:\n{recent_lines or '    (none)\n'}"
        )

    agents_summary = "\n".join(agents_blocks)

    prompt = f"""You are the Supervisor of a fleet of AI trading agents. Perform FULL 24h review.

AGENT PERFORMANCE DATA:
{agents_summary}

YOUR TASKS:
1. For each agent with >= 5 closed trades: analyse which strategies and tokens work best FOR THAT AGENT specifically.
2. Write a targeted, personalised correction for agents that need focus adjustment.
   - Good correction: "Your ema_cross on BTC/SOL has 78% WR — prioritise these setups. Avoid pivot_mr (25% WR, 8 trades — not working for you)."
   - Bad correction: "consider adjusting risk" (too generic — do not write this)
3. Agents with WR > 60% and >= 10 trades: suggest budget increase (+$5 to +$20)
4. Agents with 5+ consecutive losses or WR < 30% (>= 10 trades): suggest pause
5. Generate a daily Telegram report (plain text, no HTML, max 5 lines)

RULES:
- Only write corrections where you have real data to back them up
- Corrections must be specific: name the exact strategy or token
- If an agent has < 5 closed trades, write correction only if there is a clear problem pattern
- Corrections are read by the agent at next heartbeat and influence its next trade decision

Respond with valid JSON only:
{{
  "corrections": [
    {{
      "agent_id": "trader_XX",
      "type": "strategy_focus",
      "new_value": "Specific actionable instruction with strategy/token names and their WR",
      "reasoning": "Data-backed explanation: strategy X has Y% WR over Z trades"
    }}
  ],
  "budget_changes": [
    {{
      "agent_id": "trader_XX",
      "delta_usdt": 10,
      "reasoning": "WR X% over Y trades — outperformer reward"
    }}
  ],
  "pause_agents": ["trader_XX"],
  "telegram_report": "Daily report: ...",
  "summary": "one sentence"
}}
If nothing to correct: {{"corrections": [], "budget_changes": [], "pause_agents": [], "telegram_report": "...", "summary": "All agents reviewed, no major issues"}}"""

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
                (c.get("agent_id"), c.get("type", "strategy_focus"),
                 c.get("new_value", ""), c.get("reasoning", "")),
            )
            logger.info(
                f"Supervisor: korekta dla {c.get('agent_id')} — "
                f"{c.get('new_value','')[:80]}"
            )

    # Pauzy zalecone przez supervisora
    from database.db import update_agent
    for aid in result.get("pause_agents", []):
        from database.db import get_connection as _gc2
        with _gc2() as conn2:
            has_open = conn2.execute(
                "SELECT COUNT(*) FROM trades WHERE agent_id=? AND status='open'", (aid,)
            ).fetchone()[0]
        if has_open:
            update_agent(aid, notes="pending_pause")
            log_activity("supervisor", f"PAUSE_DEFERRED {aid} — pauza po zamknięciu pozycji", "warning")
        else:
            update_agent(aid, status="paused")
            log_activity("supervisor", f"PAUSE {aid} — zalecone przez full review", "warning")
            logger.warning(f"Supervisor: PAUSE {aid}")

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

                if agent_id in SCALPER_AGENTS:
                    success = await _scalper_beat(agent_id)
                    interval = (
                        SCALPER_POSITION_INTERVAL
                        if self._has_open_position(agent_id)
                        else SCALPER_SCAN_INTERVAL
                    )
                else:
                    success = await _trader_beat(agent_id)
                    interval = (
                        TRADER_POSITION_INTERVAL
                        if self._has_open_position(agent_id)
                        else TRADER_SCAN_INTERVAL
                    )

                if success:
                    logger.info(f"OpenClaw heartbeat OK: {agent_id}")
                else:
                    logger.warning(f"OpenClaw heartbeat FAIL: {agent_id}")
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

    async def _journal_processor_loop(self):
        """Przetwarza journal_queue: DeepSeek reflection + zapis do ChromaDB.
        Restart-safe — wpisy w DB przeżywają restart procesu."""
        from database.db import (
            pop_journal_queue_batch, mark_journal_done,
            mark_journal_failed, reset_processing_journal_entries,
        )
        reset_processing_journal_entries()
        logger.info("OpenClaw: journal processor start")

        while self.running:
            try:
                entries = pop_journal_queue_batch(limit=3)
                for entry in entries:
                    queue_id     = entry["id"]
                    agent_id     = entry["agent_id"]
                    try:
                        trade        = json.loads(entry["trade_json"])
                        close_reason = entry["close_reason"]
                        await _write_journal_entry(agent_id, trade, close_reason)
                        mark_journal_done(queue_id)
                        logger.debug(f"Journal: queue_id={queue_id} agent={agent_id} zapisano")
                    except Exception as e:
                        mark_journal_failed(queue_id, str(e))
                        logger.warning(f"Journal: queue_id={queue_id} błąd — {e}")

                await asyncio.sleep(30 if entries else 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Journal processor error: {e}", exc_info=True)
                await asyncio.sleep(60)

        logger.info("OpenClaw: journal processor stop")

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
        journal_task = asyncio.create_task(
            self._journal_processor_loop(), name="oc_journal"
        )
        trader_tasks = await self._spawn_trader_tasks()
        all_tasks    = [supervisor_task, journal_task] + trader_tasks

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
