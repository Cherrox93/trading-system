"""
Test Knowledge Base -- uruchom po ingest.py
python test_kb.py
"""
import sys
import io
sys.path.insert(0, ".")

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from knowledge_base.query import search, get_strategies_summary

print(get_strategies_summary())
print("\n--- Test wyszukiwania ---")
results = search("strategia dla ranging market z mala zmiennoscia", n_results=3)
for r in results:
    print(f"- {r['id']} (distance: {r['distance']:.3f})")

print("\n--- Test wyszukiwania: momentum trend ---")
results2 = search("momentum trend following z EMA", n_results=3)
for r in results2:
    print(f"- {r['id']} (distance: {r['distance']:.3f})")

print("\n--- Test wyszukiwania: funding rate ---")
results3 = search("funding rate ekstremalny overcrowded", n_results=3)
for r in results3:
    print(f"- {r['id']} (distance: {r['distance']:.3f})")
