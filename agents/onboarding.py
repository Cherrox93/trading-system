"""
agents/onboarding.py

Jednorazowy onboarding każdego nowego agenta.
Agent czyta całą Knowledge Base i SAM definiuje swoją tożsamość tradingową.

Wywołanie:
    from agents.onboarding import run_onboarding
    result = await run_onboarding("trader_01")
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from database.db import (
    get_agent, update_agent, set_agent_strategies, log_activity
)

logger = logging.getLogger(__name__)



def _get_llm_client():
    """
    Zainicjalizuj klienta LLM do onboardingu.
    Primary:  Gemini 2.5 Flash Lite.
    Fallback: Groq Llama4 Scout.
    """
    from openai import OpenAI
    from config import settings

    gemini_key = settings.GEMINI_API_KEY
    if gemini_key:
        return OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=gemini_key,
        ), settings.GEMINI_FAST_MODEL

    groq_key = settings.GROQ_API_KEY
    if groq_key:
        logger.warning(
            "GEMINI_API_KEY nie ustawiony — "
            "uzywam Groq jako fallback"
        )
        return OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
        ), settings.GROQ_MODEL

    raise ValueError(
        "Brak kluczy LLM w .env.\n"
        "Dodaj GEMINI_API_KEY lub GROQ_API_KEY"
    )


_LENSES = [
    "As you read, pay special attention to orderbook microstructure, flow analysis, and volume delta — these tools reveal who is actually in control.",
    "As you read, pay special attention to trend-following and momentum strategies — riding strong moves rather than fighting them.",
    "As you read, pay special attention to mean reversion, range-bound setups, and liquidity sweeps — markets spend most time oscillating, not trending.",
    "As you read, pay special attention to macro structure, higher timeframe bias, and session-based patterns — context determines everything.",
    "As you read, pay special attention to risk management, position sizing, and ATR-based systems — edge comes from how you manage trades, not just when you enter.",
    "As you read, pay special attention to on-chain data, funding rates, and sentiment indicators — price follows money, and money leaves traces.",
    "As you read, pay special attention to scalping techniques, market microstructure, and fast 1m–5m setups — precision timing on short timeframes.",
]


def _build_onboarding_prompt(agent_id: str, all_strategies: list) -> str:
    """Zbuduj prompt onboardingu — agent sam definiuje kim jest jako trader."""
    import random
    lens = random.choice(_LENSES)

    docs_text = "\n\n".join(
        f"=== {s['id']} ===\n{s['text']}" for s in all_strategies
    )

    return f"""You are a new AI trading agent with ID: {agent_id}

You have no prescribed personality or style. You are a blank slate.

READING FOCUS: {lens}

PRIMARY GOAL:
Generate consistent positive returns.
- Win rate target: above 55% measured over your last 20 closed trades
- Risk/reward: minimum 1:1 on every trade — TP must be at least equal to the SL distance
  (use ATR-based stops as taught in the knowledge base — R:R adapts to volatility automatically)
- Monthly drawdown limit: never exceed -15% of starting budget
- Quality over frequency: a skipped trade costs nothing — a bad trade costs capital

YOUR TASK:
Read ALL {len(all_strategies)} knowledge documents below — market concepts, strategies,
risk management, and real-world patterns. This is your education.

After reading, decide for yourself who you are as a trader.
There are no right or wrong answers. Trust your own reading of this material.
What genuinely appeals to you? What feels natural? What would you actually do?

Define:
1. self_identity — what kind of trader you discovered yourself to be (1 sentence)
2. trading_philosophy — how you read markets and make decisions (max 100 words)
3. focus_areas — the setups and conditions you gravitate toward
4. avoid — what conflicts with how you think

KNOWLEDGE BASE ({len(all_strategies)} documents):
{docs_text}

Respond with valid JSON ONLY (zero markdown, zero introduction):
{{
  "self_identity": "I am a ... trader who ...",
  "trading_philosophy": "max 100 words, your genuine voice",
  "focus_areas": ["specific setup + timeframe", "..."],
  "avoid": ["condition or setup you reject, and why"]
}}

Rules:
- self_identity: 1 sentence, your own words
- focus_areas: 2–5 items, each max 15 words
- avoid: 1–4 items
- Do NOT copy phrases from the knowledge base — use your own language"""


async def run_onboarding(agent_id: str) -> dict:
    """
    Uruchom onboarding dla agenta.

    1. Pobierz całą KB (48+ dokumentów)
    2. Wyślij do LLM — agent czyta i definiuje siebie
    3. Zapisz tożsamość, filozofię i focus areas do SQLite
    4. Ustaw status na 'active'

    Zwraca:
    {
        "success": bool,
        "agent_id": str,
        "self_identity": str,
        "focus_areas": list[str],
        "avoid": list[str],
        "reasoning": str,
        "model_used": str
    }
    """
    log_activity(agent_id, "Onboarding rozpoczety", "info")
    logger.info(f"Onboarding: {agent_id}")

    # Sprawdź czy agent istnieje
    agent = get_agent(agent_id)
    if not agent:
        msg = f"Agent {agent_id} nie istnieje w bazie"
        logger.error(msg)
        return {"success": False, "error": msg}

    # Sprawdź czy onboarding już wykonany
    if agent.get("onboarding_done") and agent.get("strategies"):
        logger.info(f"Agent {agent_id} juz ma onboarding — pomijam")
        return {
            "success":      True,
            "agent_id":     agent_id,
            "focus_areas":  json.loads(agent["strategies"]),
            "reasoning":    agent.get("strategy_reasoning", ""),
            "model_used":   "cached",
            "already_done": True,
        }

    update_agent(agent_id, status="onboarding")
    log_activity(agent_id, "Czytam Knowledge Base...", "info")

    # Pobierz KB
    try:
        from knowledge_base.query import get_all_strategies
        all_strategies = get_all_strategies()
    except Exception as e:
        msg = f"Blad pobierania KB: {e}"
        logger.error(msg)
        update_agent(agent_id, status="error")
        return {"success": False, "error": msg}

    if not all_strategies:
        msg = "Knowledge Base jest pusta — uruchom ingest.py"
        logger.error(msg)
        update_agent(agent_id, status="error")
        return {"success": False, "error": msg}

    logger.info(f"Agent {agent_id}: czyta {len(all_strategies)} dokumentów z KB")
    log_activity(agent_id, f"Analizuje {len(all_strategies)} dokumentów z KB...", "info")

    # Wywołaj LLM
    try:
        client, model = _get_llm_client()
    except ValueError as e:
        logger.warning(f"Brak kluczy LLM: {e}. Fallback dla {agent_id}.")
        fallback_areas = ["momentum setups", "volume-based entries", "risk management"]
        set_agent_strategies(
            agent_id,
            fallback_areas,
            "Autonomous trader — no LLM available during onboarding.",
            strategy_notes={},
        )
        update_agent(agent_id, status="active")
        log_activity(agent_id, "Onboarding (fallback: brak LLM)", "info")
        return {
            "success":      True,
            "agent_id":     agent_id,
            "focus_areas":  fallback_areas,
            "reasoning":    "KB fallback — brak kluczy LLM.",
            "model_used":   "kb_fallback",
        }

    prompt = _build_onboarding_prompt(agent_id, all_strategies)

    log_activity(
        agent_id,
        f"Nauka {len(all_strategies)} strategii przez {model}...",
        "info",
    )

    try:
        def _sync_llm_call():
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8000,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        raw = await asyncio.get_event_loop().run_in_executor(
            None, _sync_llm_call
        )

    except Exception as e:
        msg = f"Blad LLM ({model}): {e}"
        logger.error(msg)
        update_agent(agent_id, status="error")
        return {"success": False, "error": msg}

    # Parsuj odpowiedź
    try:
        clean = raw.strip()
        # Wyczyść markdown jeśli LLM go dodał
        if "```" in clean:
            parts = clean.split("```")
            # Weź zawartość pierwszego bloku kodu
            for part in parts[1:]:
                stripped = part.lstrip("json").strip()
                if stripped.startswith("{"):
                    clean = stripped
                    break
        # Znajdź JSON w tekście jeśli jest otoczony innym tekstem
        if not clean.startswith("{"):
            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
        result = json.loads(clean)
    except json.JSONDecodeError as e:
        msg = f"LLM zwrocil niepoprawny JSON: {e}\nRaw: {raw[:300]}"
        logger.error(msg)
        update_agent(agent_id, status="error")
        return {"success": False, "error": msg}

    # Wyciągnij tożsamość i filozofię agenta
    self_identity = result.get("self_identity", "").strip()
    philosophy    = result.get("trading_philosophy", "").strip()
    focus_areas   = result.get("focus_areas", [])
    avoid         = result.get("avoid", [])

    if not philosophy:
        philosophy = "Autonomous trader — self-defined style, learning from market."
    if not self_identity:
        self_identity = "autonomous"
    if not focus_areas:
        focus_areas = ["momentum setups", "volume-based entries", "risk management"]

    focus_areas = [str(f)[:80] for f in focus_areas[:5]]
    avoid       = [str(a)[:80] for a in avoid[:4]]

    # Zapisz do SQLite
    # personality = self_identity zdefiniowana przez agenta
    # strategies  = focus_areas (kompatybilność z DB)
    # strategy_notes zawiera avoid
    set_agent_strategies(
        agent_id,
        focus_areas,
        philosophy,
        strategy_notes={"avoid": avoid},
    )
    update_agent(agent_id, personality=self_identity, status="active")

    log_activity(
        agent_id,
        f"Onboarding zakończony. Tożsamość: {self_identity} | "
        f"Focus: {', '.join(focus_areas)}",
        "info",
    )
    logger.info(f"Onboarding {agent_id}: identity='{self_identity}' | model: {model}")

    return {
        "success":       True,
        "agent_id":      agent_id,
        "self_identity": self_identity,
        "focus_areas":   focus_areas,
        "avoid":         avoid,
        "reasoning":     philosophy,
        "model_used":     model,
    }




async def reset_onboarding(agent_id: str) -> bool:
    """
    Zresetuj onboarding agenta — wymusi ponowny wybór strategii.
    Używane przez Supervisora gdy chce zmienić strategie słabego agenta.
    """
    agent = get_agent(agent_id)
    if not agent:
        return False

    update_agent(
        agent_id,
        onboarding_done=0,
        strategies=None,
        strategy_reasoning=None,
        strategy_notes=None,
        status="pending",
    )
    log_activity(
        agent_id,
        "Onboarding zresetowany przez Supervisora",
        "info"
    )
    logger.info(f"Onboarding {agent_id} zresetowany")
    return True
