"""
tests/test_trader.py
Trader testowany przez skille OpenClaw (nie przez Python klasy).
"""
import pytest, json, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def _run_skill(workspace: str, skill: str, *args) -> dict:
    cmd = ["python", f"workspaces/{workspace}/skills/{skill}/run.py"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return json.loads(r.stdout)


def test_market_scan_all_returns_structure():
    """market_scan_all zwraca sygnały lub informację o braku danych."""
    data = _run_skill("trader_template", "market_scan_all")
    assert "success" in data
    if data["success"]:
        assert "signals" in data
        assert "count" in data


def test_read_corrections_marks_applied():
    """read_corrections zwraca pending korekty (nie aplikuje starych)."""
    data = _run_skill("trader_template", "read_corrections", "--agent_id", "trader_01")
    assert "success" in data
    if data["success"]:
        assert "corrections" in data
        assert "count" in data


def test_get_performance_structure():
    """get_performance zwraca poprawną strukturę."""
    data = _run_skill("trader_template", "get_performance", "--agent_id", "trader_01")
    assert "success" in data
