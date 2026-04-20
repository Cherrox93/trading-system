"""
factory/spawn_agent.py

Tworzy nowego agenta tradingowego.
Kopiuje workspace z szablonu, rejestruje w bazie i uruchamia onboarding.

Użycie:
    # Z kodu:
    from factory.spawn_agent import spawn_agent, spawn_multiple
    result = await spawn_agent("trader_04", "aggressive", budget_usdt=500)

    # CLI:
    python factory/spawn_agent.py --id trader_04 --personality aggressive --budget 500
    python factory/spawn_agent.py --id trader_05 trader_06 --personality cautious neutral
"""
import asyncio
import logging
import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import create_agent, get_agent, set_agent_budget, log_activity
from agents.onboarding import run_onboarding

logger = logging.getLogger(__name__)

TEMPLATE_PATH = ROOT / "workspaces" / "trader_template"
WORKSPACES_DIR = ROOT / "workspaces"


def _prepare_workspace(agent_id: str) -> Path:
    """
    Skopiuj trader_template → workspaces/{agent_id}.
    Zastąp placeholder {AGENT_ID} w plikach .md.
    """
    workspace = WORKSPACES_DIR / agent_id

    if workspace.exists():
        raise FileExistsError(f"Workspace {agent_id} już istnieje: {workspace}")

    shutil.copytree(TEMPLATE_PATH, workspace)
    logger.info(f"Workspace skopiowany: {workspace}")

    # Zastąp {AGENT_ID} we wszystkich plikach .md
    for md_file in workspace.glob("**/*.md"):
        content = md_file.read_text(encoding="utf-8")
        if "{AGENT_ID}" in content:
            md_file.write_text(
                content.replace("{AGENT_ID}", agent_id),
                encoding="utf-8"
            )
            logger.debug(f"Zastąpiono {{AGENT_ID}} w {md_file.name}")

    return workspace


async def spawn_agent(
        agent_id: str,
        budget_usdt: float = 100.0,
        skip_onboarding: bool = False,
) -> dict:
    """
    Utwórz nowego agenta i uruchom onboarding.

    Kroki:
    1. Sprawdź czy agent już istnieje
    2. Skopiuj workspace z szablonu
    3. Zarejestruj w SQLite (status=pending)
    4. Ustaw budżet
    5. Uruchom onboarding (czyta KB, definiuje własny styl przez LLM)
    6. Po onboardingu agent ma status=active i jest gotowy do tradingu

    Args:
        agent_id:        np. 'trader_04'
        budget_usdt:     początkowy budżet w USDT
        skip_onboarding: True tylko do testów — pomiń wywołanie LLM
    """
    logger.info(f"Spawn: {agent_id} | budzet: ${budget_usdt}")

    # Sprawdź czy agent już istnieje
    existing = get_agent(agent_id)
    if existing:
        logger.warning(f"Agent {agent_id} już istnieje w bazie")
        return {
            "success":    False,
            "agent_id":   agent_id,
            "error":      f"Agent {agent_id} już istnieje",
            "agent":      existing,
        }

    # Przygotuj workspace
    try:
        workspace = _prepare_workspace(agent_id)
    except FileExistsError as e:
        return {"success": False, "agent_id": agent_id, "error": str(e)}
    except Exception as e:
        logger.error(f"Błąd kopiowania workspace: {e}")
        return {"success": False, "agent_id": agent_id, "error": f"Błąd workspace: {e}"}

    # Zarejestruj w bazie
    try:
        agent = create_agent(agent_id, str(workspace))
    except Exception as e:
        logger.error(f"Błąd rejestracji w bazie: {e}")
        shutil.rmtree(workspace, ignore_errors=True)
        return {"success": False, "agent_id": agent_id, "error": f"Błąd bazy: {e}"}

    # Ustaw budżet
    set_agent_budget(agent_id, budget_usdt)
    log_activity(agent_id, f"Agent spawned: budżet=${budget_usdt}", "info")

    # Onboarding
    if skip_onboarding:
        logger.warning(f"Onboarding pominięty (skip_onboarding=True) dla {agent_id}")
        onboarding_result = {"success": True, "agent_id": agent_id, "skipped": True}
    else:
        logger.info(f"Uruchamiam onboarding dla {agent_id}...")
        onboarding_result = await run_onboarding(agent_id)

        if not onboarding_result.get("success"):
            logger.error(f"Onboarding {agent_id} nieudany: {onboarding_result.get('error')}")
            return {
                "success":    False,
                "agent_id":   agent_id,
                "error":      f"Onboarding failed: {onboarding_result.get('error')}",
                "workspace":  str(workspace),
                "onboarding": onboarding_result,
            }

    identity = onboarding_result.get("self_identity", "autonomous")
    logger.info(f"Agent {agent_id} gotowy. Tożsamość: '{identity}'")

    return {
        "success":       True,
        "agent_id":      agent_id,
        "self_identity": identity,
        "budget_usdt":   budget_usdt,
        "workspace":     str(workspace),
        "onboarding":    onboarding_result,
    }


async def spawn_multiple(
        agents: list[dict],
        sequential: bool = False,
) -> list[dict]:
    """
    Stwórz wiele agentów naraz.

    Args:
        agents: lista słowników z kluczami: id, budget_usdt
        sequential: True = jeden po drugim (oszczędza tokeny LLM)
    """
    if sequential:
        results = []
        for cfg in agents:
            result = await spawn_agent(
                agent_id=cfg["id"],
                budget_usdt=cfg.get("budget_usdt", 100.0),
            )
            results.append(result)
            if not result["success"]:
                logger.error(f"Spawn {cfg['id']} nieudany: {result.get('error')}. Kontynuuję.")
        return results
    else:
        tasks = [
            spawn_agent(agent_id=cfg["id"], budget_usdt=cfg.get("budget_usdt", 100.0))
            for cfg in agents
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args():
    p = ArgumentParser(description="Utwórz nowego agenta tradingowego z onboardingiem")
    p.add_argument("--id", dest="ids", nargs="+", required=True, metavar="AGENT_ID")
    p.add_argument("--budget", type=float, default=100.0, help="Budżet w USDT (domyślnie 100)")
    p.add_argument("--skip-onboarding", action="store_true", help="Pomiń onboarding (tylko do testów)")
    p.add_argument("--sequential", action="store_true", help="Twórz agentów jeden po drugim")
    return p.parse_args()


async def _main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    args = _parse_args()

    agents_cfg = [{"id": aid, "budget_usdt": args.budget} for aid in args.ids]

    if len(agents_cfg) == 1:
        result = await spawn_agent(
            agent_id=agents_cfg[0]["id"],
            budget_usdt=agents_cfg[0]["budget_usdt"],
            skip_onboarding=args.skip_onboarding,
        )
        results = [result]
    else:
        results = await spawn_multiple(agents_cfg, sequential=args.sequential)

    ok  = [r for r in results if r.get("success")]
    err = [r for r in results if not r.get("success")]

    print(f"\n{'='*60}")
    print(f"Spawned: {len(ok)}/{len(results)} agentów")
    for r in ok:
        identity = r.get("self_identity") or r.get("onboarding", {}).get("self_identity", "?")
        model    = r.get("onboarding", {}).get("model_used", "?")
        print(f"  ✓ {r['agent_id']} | identity: {identity} | ${r.get('budget_usdt')} | model: {model}")
    for r in err:
        print(f"  ✗ {r['agent_id']}: {r.get('error')}")
    print(f"{'='*60}\n")

    if err:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(_main())
