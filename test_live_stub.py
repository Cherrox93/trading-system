"""
Test 3 — live mode powinien zwrócić błąd gracefully.
python -X utf8 test_live_stub.py
"""
import sys
sys.path.insert(0, ".")

from execution.lighter_broker import execute

result = execute({
    "agent_id":  "x",
    "token":     "WLD",
    "direction": "long",
    "size_usdt": 10,
    "sl_pct":    0.005,
    "tp_pct":    0.01
})
print(result)
assert result["success"] == False
assert "nie zaimplementowany" in result["message"]
print("OK: Live mode gracefully zwraca blad bez crashowania")
