"""
Test execution layer — paper broker + trade_executor.
python -X utf8 test_execution.py
"""
import sys
import io
sys.path.insert(0, ".")

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from database.db import init_db, create_agent, set_agent_budget, get_agent
from execution.trade_executor import execute_trade, close_trade

init_db()

# Wyczyść poprzedni test agent jeśli istnieje
from database.db import get_connection
with get_connection() as conn:
    conn.execute("DELETE FROM trades WHERE agent_id = 'test_agent'")
    conn.execute("DELETE FROM agents WHERE id = 'test_agent'")

# Utwórz testowego agenta
create_agent("test_agent", "./workspaces/test", "neutral")
set_agent_budget("test_agent", 100.0)

agent = get_agent("test_agent")
print(f"Agent: id={agent['id']}, budget={agent['budget_usdt']}, used={agent['used_usdt']}")

# --- Test 1: Otwórz pozycję ---
result = execute_trade({
    "agent_id":   "test_agent",
    "token":      "WLD",
    "direction":  "long",
    "size_usdt":  10.0,
    "sl_pct":     0.005,
    "tp_pct":     0.010,
    "strategy":   "pivot_mr",
    "reasoning":  "Test wejscia",
    "confidence": 0.75
})

print(f"\nExecute: {result}")
assert result["success"], f"Execute powinno sie udac: {result['message']}"
assert result["mode"] == "paper", "Powinien byc paper mode"
assert result["trade_id"] is not None
assert result["entry_price"] > 0
assert result["sl_price"] < result["entry_price"]   # long: SL poniżej entry
assert result["tp_price"] > result["entry_price"]   # long: TP powyżej entry

# Sprawdź że used_usdt się zaktualizował
agent_after = get_agent("test_agent")
assert agent_after["used_usdt"] == 10.0, f"used_usdt={agent_after['used_usdt']}, oczekiwano 10.0"
print(f"used_usdt po wejsciu: {agent_after['used_usdt']} (OK)")

# --- Test 2: Zamknij pozycję ---
close_result = close_trade(result["trade_id"], None, "test_close")
print(f"\nClose: {close_result}")
assert close_result["success"], f"Close powinno sie udac: {close_result.get('message')}"
assert "pnl_usdt" in close_result
assert close_result["mode"] == "paper"
assert close_result["exit_price"] > 0

# Sprawdź że used_usdt wrócił do 0
agent_final = get_agent("test_agent")
assert agent_final["used_usdt"] == 0.0, f"used_usdt={agent_final['used_usdt']}, oczekiwano 0.0"
print(f"used_usdt po zamknieciu: {agent_final['used_usdt']} (OK)")

# --- Test 3: Zbyt duży trade (brak budżetu) ---
bad_result = execute_trade({
    "agent_id":  "test_agent",
    "token":     "WLD",
    "direction": "long",
    "size_usdt": 999.0,   # za duzo
    "sl_pct":    0.005,
    "tp_pct":    0.010,
})
assert not bad_result["success"], "Powinno sie nie udac (brak budzetu)"
print(f"\nBrak budzetu (oczekiwany blad): {bad_result['message']}")

# --- Test 4: Nieznany agent ---
bad_agent = execute_trade({
    "agent_id":  "nieistniejacy",
    "token":     "WLD",
    "direction": "long",
    "size_usdt": 10.0,
    "sl_pct":    0.005,
    "tp_pct":    0.010,
})
assert not bad_agent["success"], "Powinno sie nie udac (brak agenta)"
print(f"Brak agenta (oczekiwany blad): {bad_agent['message']}")

print("\nOK: Execution Layer dziala poprawnie")
