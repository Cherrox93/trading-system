"""
tests/test_supervisor.py
Supervisor testowany przez skille OpenClaw (nie przez Python klasy).
"""
import pytest, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def test_get_all_performance_skill():
    """Skill get_all_performance zwraca poprawną strukturę."""
    import subprocess, json
    result = subprocess.run(
        ["python", "workspaces/supervisor/skills/get_all_performance/run.py"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert "agents" in data
    assert "system_total" in data


def test_get_open_positions_skill():
    """Skill get_open_positions zwraca poprawną strukturę."""
    import subprocess, json
    result = subprocess.run(
        ["python", "workspaces/supervisor/skills/get_open_positions/run.py"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert "positions" in data
    assert "count" in data


def test_pause_agent_nonexistent():
    """Skill pause_agent poprawnie obsługuje nieistniejącego agenta."""
    import subprocess, json
    result = subprocess.run(
        ["python", "workspaces/supervisor/skills/pause_agent/run.py",
         "--agent_id", "trader_nonexistent", "--reason", "test"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    data = json.loads(result.stdout)
    assert data["success"] is False
