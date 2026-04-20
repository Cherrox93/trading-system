"""Supervisor Skill: reset_onboarding — resetuj strategie agenta i uruchom ponowny onboarding."""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True)
    args = parser.parse_args()

    try:
        import asyncio
        from database.db import get_agent, log_activity
        from agents.onboarding import reset_onboarding, run_onboarding

        agent = get_agent(args.agent_id)
        if not agent:
            print(json.dumps({"success": False, "error": f"Agent {args.agent_id} nie istnieje"}))
            return

        async def _do():
            await reset_onboarding(args.agent_id)
            return await run_onboarding(
                args.agent_id,
                agent.get("personality", "neutral"),
            )

        result = asyncio.run(_do())
        log_activity(
            "supervisor",
            f"Reset onboardingu {args.agent_id}: {result.get('success')}",
            "info",
        )
        print(json.dumps({
            "success":    result.get("success", False),
            "agent_id":   args.agent_id,
            "strategies": result.get("strategies", []),
            "error":      result.get("error"),
        }))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
