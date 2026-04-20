"""
agents/kb_evolution.py

Ewolucja Knowledge Base — wywoływana przez Supervisora po każdym
pełnym przeglądzie (co 24h).

Trzy operacje:
  1. Dokumentuj wzorce najlepszego agenta → nowy plik .md w KB
  2. Korekty bazujące na porównaniu najlepszy vs najgorszy agent
  3. Oznacz nieskuteczne strategie ostrzeżeniem w .md
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import (
    get_agent_trades, get_connection, log_activity, get_strategy_performance
)

logger = logging.getLogger(__name__)

STRATEGIES_DIR = ROOT / "knowledge_base" / "strategies"
MAX_VALIDATED_PER_DAY = 2
MIN_TRADES_FOR_PATTERN = 10
MIN_AGENT_AGE_HOURS = 48


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _get_deep_client():
    from openai import OpenAI
    from config import settings
    key = settings.DEEPSEEK_API_KEY
    if key:
        return OpenAI(base_url="https://api.deepseek.com/v1", api_key=key), "deepseek-reasoner"
    groq_key = settings.GROQ_API_KEY
    if groq_key:
        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key), \
               settings.GROQ_MODEL
    raise ValueError("Brak DEEPSEEK_API_KEY ani GROQ_API_KEY")


def _get_fast_client():
    from openai import OpenAI
    from config import settings
    groq_key = settings.GROQ_API_KEY
    if groq_key:
        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key), \
               settings.GROQ_MODEL
    raise ValueError("Brak GROQ_API_KEY")


async def _llm_call(client, model: str, prompt: str, max_tokens: int = 800) -> str:
    def _sync():
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return r.choices[0].message.content.strip()

    return await asyncio.get_event_loop().run_in_executor(None, _sync)


def _parse_json(text: str) -> dict:
    clean = text.strip()
    if "```" in clean:
        for part in clean.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                try:
                    return json.loads(part)
                except Exception:
                    continue
    if not clean.startswith("{"):
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start >= 0 and end > start:
            clean = clean[start:end]
    try:
        return json.loads(clean)
    except Exception:
        return {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_trades(trades: list, limit: int = 20) -> str:
    closed = [t for t in trades if t.get("status") == "closed"][:limit]
    lines = []
    for t in closed:
        pnl   = float(t.get("pnl_usdt") or 0)
        sign  = "+" if pnl >= 0 else ""
        lines.append(
            f"  {t['token']} {(t.get('direction') or '').upper()} | "
            f"PnL={sign}{pnl:.4f}$ | "
            f"Strategy={t.get('strategy_used','?')} | "
            f"Confidence={t.get('confidence','?')}"
        )
    return "\n".join(lines) if lines else "  (brak zamknietych transakcji)"


def _count_validated_today() -> int:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return sum(1 for p in STRATEGIES_DIR.glob(f"validated_*_{today}.md"))


def _agent_age_hours(agent_id: str) -> float:
    """Zwraca wiek agenta w godzinach na podstawie pierwszej transakcji lub rejestracji."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT timestamp FROM trades WHERE agent_id = ? ORDER BY timestamp ASC LIMIT 1",
            (agent_id,),
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT created_at FROM agents WHERE id = ?",
                (agent_id,),
            ).fetchone()
        if not row:
            return 0.0

    ts_str = row[0]
    if not ts_str:
        return 0.0

    try:
        # SQLite zwraca "2026-04-15 12:34:56" lub z milisekundami
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                ts = datetime.strptime(ts_str[:19], fmt[:len(fmt)])
                break
            except ValueError:
                continue
        else:
            return 0.0
        now  = datetime.now()
        diff = now - ts
        return diff.total_seconds() / 3600
    except Exception:
        return 0.0


# ── OPERACJA 1: Dokumentuj wzorce najlepszego agenta ─────────────────────────

async def _op1_document_best_agent(agents_data: list) -> bool:
    """
    Jeśli jest agent z WR > 60% i >= 10 trades — dokumentuj wzorce w KB.
    Zwraca True jeśli dokument został stworzony.
    """
    # Sprawdź dzienny limit
    if _count_validated_today() >= MAX_VALIDATED_PER_DAY:
        logger.info("KB Evolution Op1: osiagniety dzienny limit validated dokumentow")
        return False

    # Znajdź najlepszego agenta
    best = None
    for a in agents_data:
        p = a.get("performance", {})
        wr = p.get("win_rate", 0)
        n  = p.get("trades", 0)
        if wr > 60 and n >= MIN_TRADES_FOR_PATTERN:
            if best is None or wr > best.get("performance", {}).get("win_rate", 0):
                best = a

    if not best:
        logger.info("KB Evolution Op1: brak agenta z WR>60% i min 10 trades")
        return False

    agent_id    = best["id"]
    personality = best.get("personality", "neutral")
    strategies  = best.get("strategies", [])
    p           = best["performance"]
    win_rate    = p.get("win_rate", 0)
    pnl         = p.get("pnl", 0)

    # Sprawdź wiek agenta
    age_h = _agent_age_hours(agent_id)
    if age_h < MIN_AGENT_AGE_HOURS:
        logger.info(
            f"KB Evolution Op1: agent {agent_id} za mlody "
            f"({age_h:.1f}h < {MIN_AGENT_AGE_HOURS}h)"
        )
        return False

    # Sprawdź czy dokument już nie istnieje
    today    = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_path = STRATEGIES_DIR / f"validated_{agent_id}_{today}.md"
    if out_path.exists():
        logger.info(f"KB Evolution Op1: dokument {out_path.name} juz istnieje")
        return False

    # Pobierz transakcje
    trades = get_agent_trades(agent_id, limit=30)
    closed = [t for t in trades if t.get("status") == "closed"][:20]
    if len(closed) < MIN_TRADES_FOR_PATTERN:
        logger.info(f"KB Evolution Op1: za malo zamknietych transakcji ({len(closed)})")
        return False

    trades_text = _format_trades(trades, limit=20)

    # Daty pierwszej i ostatniej transakcji
    timestamps = [t.get("timestamp", "") for t in closed if t.get("timestamp")]
    date_from  = min(timestamps)[:10] if timestamps else today
    date_to    = max(timestamps)[:10] if timestamps else today

    # Prompt do LLM
    prompt = f"""You are analyzing the results of the best AI trading agent.
Agent: {agent_id}
Personality: {personality}
Strategies: {', '.join(strategies)}
Win Rate: {win_rate}%
Total PnL: ${pnl}
RECENT TRADES (wins and losses):
{trades_text}

Identify concrete patterns that make this agent win.
Focus on:
- Which tokens, directions, timeframes work
- Which market conditions (RSI, ATR, funding rate) precede a profit
- Which conditions precede a loss
- What distinguishes winning setups from losing ones

Respond with JSON:
{{
  "pattern_name": "short pattern name",
  "description": "description in 2-3 sentences",
  "winning_conditions": ["condition 1", "condition 2"],
  "losing_conditions": ["condition 1", "condition 2"],
  "best_tokens": ["TOKEN1", "TOKEN2"],
  "best_timeframes": ["15m", "1h"],
  "avg_win_pct": 1.23,
  "avg_loss_pct": -0.45,
  "sample_size": 20,
  "confidence": "high/medium/low"
}}"""

    try:
        client, model = _get_deep_client()
        raw    = await _llm_call(client, model, prompt, max_tokens=600)
        result = _parse_json(raw)
    except Exception as e:
        logger.warning(f"KB Evolution Op1: LLM error: {e}")
        return False

    confidence   = result.get("confidence", "low")
    sample_size  = result.get("sample_size", 0)

    if confidence == "low" or sample_size < 5:
        logger.info(
            f"KB Evolution Op1: skip — confidence={confidence}, sample={sample_size}"
        )
        return False

    # Buduj dokument KB
    pattern_name       = result.get("pattern_name", f"Wzorzec {agent_id}")
    description        = result.get("description", "")
    winning_conditions = result.get("winning_conditions", [])
    losing_conditions  = result.get("losing_conditions", [])
    best_tokens        = result.get("best_tokens", ["any"])
    best_timeframes    = result.get("best_timeframes", ["15m", "1h"])
    avg_win_pct        = result.get("avg_win_pct", 0)
    avg_loss_pct       = result.get("avg_loss_pct", 0)

    winning_lines = "\n".join(f"- {c}" for c in winning_conditions) or "- (brak danych)"
    losing_lines  = "\n".join(f"- {c}" for c in losing_conditions)  or "- (brak danych)"

    doc = f"""# {pattern_name}

## META
- Name: {pattern_name} (Agent Validated)
- Category: hybrid
- Difficulty: intermediate
- Timeframes: {', '.join(best_timeframes)}
- Best Market: any
- Estimated Win Rate: {win_rate:.0f}%
- Risk Reward: 1:2.0
- Tokens: {', '.join(best_tokens)}
- Source: agent_validated
- Added: {today}

## Description
{description}

Strategy empirically validated by agent {agent_id} ({personality})
based on {sample_size} trades from the period {date_from} — {date_to}.
Win Rate: {win_rate:.1f}% | Total PnL: ${pnl:.4f}

## Entry Conditions
{winning_lines}

## Exit Conditions
### Take Profit
Target minimum 2x risk.
Average gain on winning trade: +{avg_win_pct:.2f}%.

### Stop Loss
Average losses closed at: {avg_loss_pct:.2f}%.
Set stop loss according to ATR or min 0.3% from entry.

## Confirming Signals
- Confirmation on higher timeframe
- Alignment with 4h trend
- Volume above average

## When NOT to Enter
{losing_lines}

## Risk Management
Agent decides position size and leverage autonomously within its allocated budget.
Strategy generated from empirical data — treat as
a supplement, not the sole signal source.

## Setup Example
Pattern confirmed on {sample_size} trades of agent {agent_id}.
Tokens with highest WR: {', '.join(best_tokens)}.
Preferred timeframes: {', '.join(best_timeframes)}.

## Configuration Parameters
- validated_agent: {agent_id}
- validated_date: {today}
- sample_size: {sample_size}
- confidence: {confidence}

## Annotation
Strategy empirically validated by {agent_id}
on {sample_size} trades, WR={win_rate:.1f}%,
period: {date_from} — {date_to}
"""

    out_path.write_text(doc, encoding="utf-8")
    logger.info(f"KB Evolution Op1: zapisano {out_path.name}")

    # Wgraj do ChromaDB
    try:
        from knowledge_base.ingest import ingest
        ingest()
        logger.info("KB Evolution Op1: ChromaDB zaktualizowana")
    except Exception as e:
        logger.warning(f"KB Evolution Op1: ingest error: {e}")

    log_activity(
        "supervisor",
        f"KB Evolution: nowy validated dokument — {out_path.name} "
        f"(WR={win_rate:.0f}%, n={sample_size})",
        "info",
    )
    return True


# ── OPERACJA 2: Korekty na podstawie porównania agentów ──────────────────────

async def _op2_compare_agents(agents_data: list):
    """
    Jeśli jest wyraźna różnica między najlepszym (WR>55%) a najgorszym (WR<40%)
    — generuj korekty dla gorszego na podstawie sukcesów lepszego.
    """
    # Filtruj agentów z min 10 trades i statusem active
    qualified = [
        a for a in agents_data
        if a.get("performance", {}).get("trades", 0) >= MIN_TRADES_FOR_PATTERN
        and a.get("status") == "active"
    ]
    if len(qualified) < 2:
        logger.info("KB Evolution Op2: za malo agentow z danymi do porownania")
        return

    best  = max(qualified, key=lambda a: a["performance"].get("win_rate", 0))
    worst = min(qualified, key=lambda a: a["performance"].get("win_rate", 0))

    best_wr  = best["performance"].get("win_rate", 0)
    worst_wr = worst["performance"].get("win_rate", 0)

    if best_wr <= 55 or worst_wr >= 40:
        logger.info(
            f"KB Evolution Op2: brak wyraznej roznicy "
            f"(best={best_wr:.0f}%, worst={worst_wr:.0f}%)"
        )
        return

    # Zbierz transakcje
    best_trades  = get_agent_trades(best["id"],  limit=30)
    worst_trades = get_agent_trades(worst["id"], limit=30)

    best_wins  = [
        t for t in best_trades
        if t.get("status") == "closed" and float(t.get("pnl_usdt") or 0) > 0
    ][:10]
    worst_losses = [
        t for t in worst_trades
        if t.get("status") == "closed" and float(t.get("pnl_usdt") or 0) < 0
    ][:10]

    best_wins_text  = _format_trades(best_wins,   limit=10)
    worst_loss_text = _format_trades(worst_losses, limit=10)

    best_strats  = best.get("strategies", [])
    worst_strats = worst.get("strategies", [])

    prompt = f"""Compare two AI traders and suggest what the worse one should
change based on the better one's successes.

BEST AGENT ({best['id']}, WR={best_wr:.0f}%):
Strategies: {', '.join(best_strats)}
Recent wins:
{best_wins_text}

WORST AGENT ({worst['id']}, WR={worst_wr:.0f}%):
Strategies: {', '.join(worst_strats)}
Recent losses:
{worst_loss_text}

Propose 1-2 specific, simple changes for the worse agent.
JSON:
{{
  "suggestions": [
    {{
      "type": "strategy_change/timing_change/note",
      "description": "specific change max 80 words"
    }}
  ]
}}"""

    try:
        client, model = _get_fast_client()
        raw     = await _llm_call(client, model, prompt, max_tokens=400)
        result  = _parse_json(raw)
    except Exception as e:
        logger.warning(f"KB Evolution Op2: LLM error: {e}")
        return

    suggestions = result.get("suggestions", [])
    if not suggestions:
        logger.info("KB Evolution Op2: LLM nie zwrocil sugestii")
        return

    # Zapisz korekty dla najgorszego agenta
    with get_connection() as conn:
        for s in suggestions[:2]:
            c_type      = s.get("type", "note")
            description = s.get("description", "")
            new_value   = {"action": c_type}

            conn.execute("""
                INSERT INTO corrections
                    (agent_id, type, new_value, reasoning, applied)
                VALUES (?, ?, ?, ?, 0)
            """, (
                worst["id"],
                c_type,
                json.dumps(new_value),
                f"KB Evolution (porownanie z {best['id']}): {description}",
            ))
            logger.info(
                f"KB Evolution Op2: korekta dla {worst['id']} — {c_type}: {description[:60]}"
            )

    log_activity(
        "supervisor",
        f"KB Evolution: korekty dla {worst['id']} "
        f"na podstawie wzorcow {best['id']} "
        f"(best WR={best_wr:.0f}%, worst WR={worst_wr:.0f}%)",
        "info",
    )


# ── OPERACJA 3: Oznacz nieskuteczne strategie ─────────────────────────────────

async def _op3_flag_weak_strategies():
    """
    Jeśli jakaś strategy_used ma WR < 35% przy min 15 użyciach —
    dodaj ostrzeżenie do pliku .md tej strategii.
    """
    try:
        perf_list = get_strategy_performance()
    except Exception as e:
        logger.warning(f"KB Evolution Op3: get_strategy_performance error: {e}")
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for perf in perf_list:
        strategy_name = perf.get("strategy_used", "")
        total         = perf.get("total", 0)
        win_rate      = perf.get("win_rate", 100)

        if not strategy_name or total < 15 or win_rate >= 35:
            continue

        # Znajdź plik .md dla tej strategii
        md_file = _find_strategy_file(strategy_name)
        if not md_file:
            logger.info(
                f"KB Evolution Op3: nie znaleziono pliku dla strategii '{strategy_name}'"
            )
            continue

        content = md_file.read_text(encoding="utf-8")

        # Nie dodawaj jeśli ostrzeżenie już jest
        if "SUPERVISOR WARNING" in content:
            continue

        warning = f"""

## SUPERVISOR WARNING
Date: {today}
Validated uses: {total} trades
Actual Win Rate: {win_rate:.1f}%
Status: PERFORMANCE BELOW THRESHOLD
Recommendation: use with caution, prioritize other strategies
"""
        md_file.write_text(content + warning, encoding="utf-8")
        logger.warning(
            f"KB Evolution Op3: oznaczono strategię '{strategy_name}' "
            f"(WR={win_rate:.0f}%, n={total})"
        )

        # Zaktualizuj ChromaDB
        try:
            from knowledge_base.ingest import ingest
            ingest()
        except Exception as e:
            logger.warning(f"KB Evolution Op3: ingest error: {e}")

        log_activity(
            "supervisor",
            f"KB Evolution: strategia '{strategy_name}' oznaczona jako slaba "
            f"(WR={win_rate:.0f}%, n={total})",
            "warning",
        )


def _find_strategy_file(strategy_name: str) -> Path | None:
    """
    Szuka pliku .md dla strategii.
    Sprawdza: dokładna nazwa w nazwie pliku, lub w sekcji META Name.
    """
    # Normalizuj: "trend_following" → szukaj pliku z "trend" w nazwie
    norm = strategy_name.lower().replace(" ", "_").replace("-", "_")

    for md in STRATEGIES_DIR.glob("*.md"):
        stem = md.stem.lower()
        # Sprawdź czy nazwa strategii jest częścią nazwy pliku
        if norm in stem or stem in norm:
            return md
        # Sprawdź META Name w treści pliku
        try:
            content = md.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("- Name:"):
                    name_val = line.split(":", 1)[1].strip().lower()
                    if norm in name_val or strategy_name.lower() in name_val:
                        return md
        except Exception:
            continue

    return None


# ── OPERACJA 4: Aktualizuj FIELD EXPERIENCE w plikach strategii ──────────────

async def _op4_update_strategy_experience():
    """
    Dla każdej strategii z >= 10 zamkniętych trade'ów aktualizuje sekcję
    ## FIELD EXPERIENCE w pliku .md — rzeczywisty WR, avg PnL, status.
    Dzięki temu kolejny onboarding agenta widzi empiryczne wyniki, nie tylko teorię.
    """
    try:
        perf_list = get_strategy_performance()
    except Exception as e:
        logger.warning(f"KB Evolution Op4: get_strategy_performance error: {e}")
        return

    if not perf_list:
        logger.info("KB Evolution Op4: brak danych o wydajności (za mało trade'ów)")
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = 0

    for perf in perf_list:
        strategy_name = perf.get("strategy_used", "")
        total = perf.get("total", 0)
        win_rate = perf.get("win_rate", 0)
        avg_pnl = perf.get("avg_pnl", 0)

        if total < 10 or not strategy_name:
            continue

        md_file = _find_strategy_file(strategy_name)
        if not md_file:
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"KB Evolution Op4: read error {md_file}: {e}")
            continue

        wins = int(round(total * win_rate / 100))
        losses = total - wins
        sign = "+" if avg_pnl >= 0 else ""

        if win_rate >= 55:
            status_line = "PERFORMING — above expected WR"
        elif win_rate >= 40:
            status_line = "NEUTRAL — within acceptable range"
        else:
            status_line = "UNDERPERFORMING — review before use"

        field_exp_section = (
            f"## FIELD EXPERIENCE\n"
            f"Last updated: {today}\n"
            f"Trades analyzed: {total} (wins: {wins}, losses: {losses})\n"
            f"Actual Win Rate: {win_rate:.1f}%\n"
            f"Average PnL per trade: {sign}{avg_pnl:.4f} USDT\n"
            f"Status: {status_line}\n"
        )

        if "## FIELD EXPERIENCE" in content:
            start = content.index("## FIELD EXPERIENCE")
            next_section = content.find("\n## ", start + 5)
            if next_section > 0:
                content = content[:start] + field_exp_section + content[next_section + 1:]
            else:
                content = content[:start] + field_exp_section.rstrip()
        else:
            content = content.rstrip() + "\n\n" + field_exp_section.rstrip()

        try:
            md_file.write_text(content, encoding="utf-8")
            updated += 1
        except Exception as e:
            logger.warning(f"KB Evolution Op4: write error {md_file}: {e}")
            continue

    if updated > 0:
        try:
            from knowledge_base.ingest import ingest
            ingest()
        except Exception as e:
            logger.warning(f"KB Evolution Op4: ingest error: {e}")

        logger.info(f"KB Evolution Op4: zaktualizowano FIELD EXPERIENCE w {updated} strategiach")
        log_activity(
            "supervisor",
            f"KB Evolution: FIELD EXPERIENCE zaktualizowany w {updated} strategiach",
            "info",
        )
    else:
        logger.info("KB Evolution Op4: żadna strategia nie spełnia progu min 10 trade'ów")


# ── Główna funkcja ────────────────────────────────────────────────────────────

async def evolve_knowledge_base(agents_data: list, review: dict):
    """
    Wywołana przez Supervisora po pełnym przeglądzie.
    Wykonuje trzy operacje ewolucji KB.
    Błędy poszczególnych operacji są izolowane i nie blokują siebie nawzajem.
    """
    logger.info("KB Evolution: start")

    # Op1: Dokumentuj wzorce najlepszego agenta
    try:
        created = await _op1_document_best_agent(agents_data)
        if created:
            logger.info("KB Evolution Op1: dokument stworzony")
        else:
            logger.info("KB Evolution Op1: skip (warunki nie spelnione)")
    except Exception as e:
        logger.warning(f"KB Evolution Op1 error: {e}", exc_info=True)

    # Op2: Korekty na podstawie porownania agentow
    try:
        await _op2_compare_agents(agents_data)
    except Exception as e:
        logger.warning(f"KB Evolution Op2 error: {e}", exc_info=True)

    # Op3: Oznacz nieskuteczne strategie
    try:
        await _op3_flag_weak_strategies()
    except Exception as e:
        logger.warning(f"KB Evolution Op3 error: {e}", exc_info=True)

    # Op4: Aktualizuj FIELD EXPERIENCE w plikach .md strategii
    try:
        await _op4_update_strategy_experience()
    except Exception as e:
        logger.warning(f"KB Evolution Op4 error: {e}", exc_info=True)

    logger.info("KB Evolution: zakonczona")
