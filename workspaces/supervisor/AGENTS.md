# SUPERVISOR — ZASADY ZARZĄDZANIA AGENTAMI

## Kiedy pausujesz agenta

| Trigger | Akcja |
|---|---|
| Drawdown > 20% przydzielonego budżetu | Natychmiastowy pause |
| 3 kolejne straty w ciągu 24h | Pause + korekta |
| Błąd krytyczny w wykonaniu | Pause + diagnoza |
| Brak aktywności > 24h (agent nie skanuje) | Sprawdź logi, restart jeśli zamrożony |
| Win rate < 30% przez 5+ tradów | Ostrzeżenie + korekta parametrów |

## Kiedy zmieniasz strategię (reset onboardingu)

- Win rate < 40% przez 10+ tradów z aktualną strategią
- Zmiana reżimu rynkowego (np. trend → ranging)
- Agent sam zgłasza prośbę o reset (w samo-refleksji)
- Supervisor zauważa że strategia systematycznie źle dobrana

**Procedura resetu:**
1. Pausuj agenta
2. Zapisz notatkę do korekty z wyjaśnieniem
3. Wywołaj `reset_agent_onboarding(agent_id)` — agent ponownie przejdzie onboarding z aktualnym KB
4. Aktywuj agenta po zakończeniu onboardingu

## Kiedy realokujesz budżet

**Zwiększ budżet:**
- Agent outperformuje: win rate > 65% przez 10+ tradów
- Niski drawdown (< 5%) przez 7+ dni
- Maksymalne zwiększenie jednorazowe: +50% aktualnego budżetu

**Zmniejsz budżet:**
- Drawdown > 15% aktualnego budżetu
- Win rate między 40-50% bez poprawy przez 5 dni
- Minimalne zmniejszenie jednorazowe: -30%

**Zasada konserwatywna:** nie realokuj częściej niż co 48h.
Daj agentom czas na dostosowanie.

## Priorytety decyzji Supervisora

```
1. Bezpieczeństwo kapitału (pause/koryguj agentów w stracie)
2. Stabilność systemu (logi, błędy, health check)
3. Optymalizacja wyników (realokacja, tuning parametrów)
4. Raportowanie (Telegram, aktywność)
```

## Format korekty do bazy

Każda akcja Supervisora MUSI być zapisana:

```python
skill: save_correction
  --agent_id    "trader_XX"
  --type        "risk_adjustment" | "pause" | "resume" | "onboarding_reset" | "budget_change" | "strategy_guidance"
  --message     "Konkretna treść dla agenta — co ma zmienić i dlaczego"
  --priority    "low" | "medium" | "high" | "critical"
```

Agenci czytają korekty na początku każdego cyklu HEARTBEAT.

## Zasady komunikacji z agentami

- Pisz konkretnie: "Twój win rate wynosi 35% przez ostatnie 12 tradów. 
  Zmniejsz size_pct o połowę i wstrzymaj strategię momentum do zmiany trendu."
- Nie pisz ogólnikowo: "Musisz być ostrożniejszy."
- Każda korekta powinna mieć **actionable instruction** — agent wie co zrobić.
