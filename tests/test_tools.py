"""
Test wszystkich Tools
python -X utf8 tests/test_tools.py
"""
import sys
import io
import json
import subprocess
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def run(cmd: list, timeout: int = 60) -> dict:
    r = subprocess.run(
        ["python", "-X", "utf8"] + cmd,
        capture_output=True, text=True, cwd=ROOT,
        timeout=timeout, encoding="utf-8", errors="replace"
    )
    try:
        return json.loads(r.stdout)
    except Exception:
        return {
            "success": False,
            "raw": r.stdout[:200],
            "err": r.stderr[:300]
        }


def main():
    from database.db import init_db, create_agent, set_agent_budget, get_agent, get_connection
    init_db()

    # Reset test agent
    with get_connection() as conn:
        conn.execute("DELETE FROM trades   WHERE agent_id = 'test_agent'")
        conn.execute("DELETE FROM corrections WHERE agent_id = 'test_agent'")
        conn.execute("DELETE FROM agents   WHERE id = 'test_agent'")

    create_agent("test_agent", "./workspaces/test", "neutral")
    set_agent_budget("test_agent", 100.0)

    T = "workspaces/trader_template/skills"
    S = "workspaces/supervisor/skills"

    tests = [
        # Skanowanie — wszystkie tokeny, zero filtrów
        ([f"{T}/market_scan_all/run.py"],
         "market_scan_all"),

        # Szczegóły jednego tokenu
        ([f"{T}/market_watch/run.py", "--token", "SOL"],
         "market_watch (brak pozycji)"),

        # RAG
        ([f"{T}/rag_query/run.py",
          "--query", "pivot mean reversion oversold", "--n", "2"],
         "rag_query",
         120),   # dłuższy timeout — ładowanie modelu

        # Execute — agent sam ustala wszystkie parametry
        ([f"{T}/execute_trade/run.py",
          "--agent_id",   "test_agent",
          "--token",      "AVAX",
          "--direction",  "long",
          "--size_pct",   "0.008",
          "--sl_pct",     "0.004",
          "--tp_pct",     "0.014",
          "--leverage",   "1",
          "--strategy",   "pivot_mean_reversion",
          "--confidence", "0.82",
          "--reasoning",  "RSI=31, cena przy S1, FR neutralny"],
         "execute_trade (agent-defined params)"),

        # Execute z przekroczeniem hard limit
        ([f"{T}/execute_trade/run.py",
          "--agent_id",  "test_agent",
          "--token",     "BTC",
          "--direction", "long",
          "--size_pct",  "0.99",
          "--sl_pct",    "0.001",
          "--tp_pct",    "0.01",
          "--leverage",  "20",
          "--strategy",  "test",
          "--reasoning", "test"],
         "execute_trade (hard limit — powinien odrzucic)"),

        # Log
        ([f"{T}/log_decision/run.py",
          "--agent_id", "test_agent",
          "--decision", "SCAN_NO_SETUP",
          "--reasoning", "Brak setupu na 15 tokenach"],
         "log_decision"),

        # Performance
        ([f"{T}/get_performance/run.py", "--agent_id", "test_agent"],
         "get_performance"),

        # Korekty
        ([f"{S}/write_correction/run.py",
          "--agent_id", "test_agent",
          "--type",     "risk_reduction",
          "--new_value", '{"risk_per_trade": 0.004}',
          "--reasoning", "Win rate 35% — zmniejsz ryzyko"],
         "write_correction"),

        ([f"{T}/read_corrections/run.py", "--agent_id", "test_agent"],
         "read_corrections"),

        # Fund
        ([f"{S}/fund_agent/run.py",
          "--agent_id", "test_agent", "--amount", "50.0"],
         "fund_agent"),

        # All performance
        ([f"{S}/get_all_performance/run.py"],
         "get_all_performance"),
    ]

    passed = failed = 0
    trade_id = None

    for entry in tests:
        cmd      = entry[0]
        name     = entry[1]
        timeout  = entry[2] if len(entry) > 2 else 30

        r  = run(cmd, timeout=timeout)
        ok = r.get("success", False)

        # Hard limit — oczekujemy success=False z hard_limit=True
        if "hard limit" in name:
            ok = (not r.get("success", True)) and r.get("hard_limit", False)

        if name == "execute_trade (agent-defined params)" and r.get("success"):
            trade_id = r.get("trade_id")

        icon = "OK" if ok else "FAIL"
        print(f"[{icon}] {name}")

        if name == "market_scan_all" and ok:
            tokens = r.get("tokens", [])
            print(f"   {len(tokens)} tokenow, mode={r.get('mode')}")
            for t in tokens[:3]:
                print(f"   {t['symbol']}: ${t['price']} "
                      f"RSI={t.get('rsi','?')} "
                      f"FR={t.get('funding_rate','?')}")
            print(f"   ...")

        if name == "rag_query" and ok:
            results = r.get("results", [])
            for res in results:
                print(f"   {res['id']} (distance={res['distance']})")

        if not ok:
            print(f"   Error: {r.get('error', r.get('err', str(r)[:150]))}")
            failed += 1
        else:
            passed += 1

    # market_watch z pozycją
    if trade_id:
        r  = run([f"{T}/market_watch/run.py", "--token", "AVAX"])
        ok = r.get("success", False)
        has_pos = r.get("open_position") is not None
        print(f"{'[OK]' if ok else '[FAIL]'} market_watch "
              f"(z pozycja trade_id={trade_id}, "
              f"open_position={'tak' if has_pos else 'nie'})")
        passed += 1 if ok else 0
        failed += 0 if ok else 1

        # close_trade
        r  = run([f"{T}/close_trade/run.py",
                  "--trade_id", str(trade_id), "--reason", "test"])
        ok = r.get("success", False)
        print(f"{'[OK]' if ok else '[FAIL]'} close_trade "
              f"pnl={r.get('pnl_usdt', '?')}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1

    print(f"\n{'='*50}")
    print(f"Wynik: {passed} OK  |  {failed} FAIL")
    if failed == 0:
        print("OK: Wszystkie Tools dzialaja poprawnie")
    else:
        print("FAIL: Sprawdz bledy powyzej")
        sys.exit(1)


if __name__ == "__main__":
    main()
