# SUPERVISOR — HARMONOGRAM DZIAŁANIA

---

## CO 24 GODZINY — PEŁNY PRZEGLĄD

### Krok 1 — Pobierz wyniki wszystkich agentów
```
python skills/get_all_performance/run.py
```

### Krok 2 — Oceń każdego agenta przez DeepSeek R1

Dla każdego agenta przeanalizuj:
- Win rate z ostatnich 7 dni
- PnL całkowity i dzienny
- Max drawdown
- Liczba transakcji (czy agent jest aktywny?)
- Które strategie przynosiły zyski, które straty

### Krok 3 — Podejmij decyzje korygujące

**Underperformer** (win rate < 40% przez 10+ tradów lub drawdown > 20%):
```
python skills/pause_agent/run.py --agent_id trader_XX --reason "Win rate 32% przez 15 tradów"
python skills/write_correction/run.py \
  --agent_id trader_XX \
  --type strategy_change \
  --new_value '{"action":"reset_and_relearn"}' \
  --reasoning "Rozważ zmianę strategii. Aktualne setupy nie działają w tym reżimie rynkowym."
```

**Outperformer** (win rate > 65% przez 10+ tradów):
```
python skills/update_budget/run.py --agent_id trader_XX --budget 200 --reason "WR 70% przez 15 tradów"
```

**Agent z nieaktualną strategią**:
```
python skills/reset_onboarding/run.py --agent_id trader_XX
```

### Krok 4 — Ewolucja Knowledge Base
```
python skills/kb_evolve/run.py
```

### Krok 5 — Raport Telegram
```
python skills/send_telegram/run.py --type daily_report
```

---

## CO 6 GODZIN — MONITORING RYZYKA

### Krok 1 — Sprawdź otwarte pozycje
```
python skills/get_open_positions/run.py
```

Oceń:
- Czy któryś agent ma zbyt duże otwarte pozycje?
- Czy funding rate nie pożera zysku?
- Czy drawdown > 10% bez zbliżającego się TP?

### Krok 2 — Sprawdź wyniki agentów
```
python skills/get_all_performance/run.py
```

Jeśli drawdown > 10% lub 5+ strat z rzędu:
```
python skills/pause_agent/run.py --agent_id trader_XX --reason "Drawdown 12% — zatrzymanie prewencyjne"
```

Jeśli sytuacja krytyczna (wszystkie agenci tracą):
```
python skills/emergency_pause_all/run.py --reason "Rynek w kryzysie — zatrzymuję wszystkich"
python skills/send_telegram/run.py --message "ALERT: Wszystkie agenty zatrzymane. Powód: [opis]"
```

---

## NA ALARM — REAGUJ NATYCHMIAST

Alarmy przychodzą przez activity_log z `level=critical`.

| Alarm | Akcja |
|---|---|
| Flash crash > 10% | `python skills/emergency_pause_all/run.py --reason "Flash crash"` |
| Agent otworzył pozycję > 2x budżet | Audit + korekta przez write_correction |
| LLM error rate > 50% | `python skills/send_telegram/run.py --message "ALERT: LLM errors"` |

---

## SKILLE DOSTĘPNE

| Skill | Wywołanie |
|---|---|
| get_all_performance | `python skills/get_all_performance/run.py` |
| get_open_positions | `python skills/get_open_positions/run.py` |
| write_correction | `python skills/write_correction/run.py --agent_id X --type T --new_value V --reasoning R` |
| pause_agent | `python skills/pause_agent/run.py --agent_id X --reason R` |
| resume_agent | `python skills/resume_agent/run.py --agent_id X` |
| emergency_pause_all | `python skills/emergency_pause_all/run.py --reason R` |
| update_budget | `python skills/update_budget/run.py --agent_id X --budget N --reason R` |
| reset_onboarding | `python skills/reset_onboarding/run.py --agent_id X` |
| fund_agent | `python skills/fund_agent/run.py --agent_id X --amount N` |
| kb_evolve | `python skills/kb_evolve/run.py` |
| send_telegram | `python skills/send_telegram/run.py --message "tekst"` lub `--type daily_report` |
