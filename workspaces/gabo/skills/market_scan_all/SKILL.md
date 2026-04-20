# Skill: market_scan_all

Zwraca aktualne dane rynkowe WSZYSTKICH monitorowanych tokenów.
Wywołuj co 30 sekund gdy nie masz otwartej pozycji.

## Wywołanie
```
python skills/market_scan_all/run.py
```

## Zwraca
Dane wszystkich tokenów: cena, RSI, MACD, Pivot S1/PP/R1,
funding_rate, open_interest, volume_24h, bid/ask/spread,
zmiana 24h.

## Twoja rola
Przeanalizuj dane każdego tokenu przez pryzmat
swoich strategii z Knowledge Base i zdecyduj:

- Czy widzę setup na którymś tokenie?
- Jeśli tak: który token? long czy short?
- Jaka wielkość pozycji (size_pct)?
- Gdzie SL (sl_pct)? Gdzie TP (tp_pct)? Jaka dźwignia?
- Dlaczego właśnie teraz?
