# Skill: market_watch

Zwraca aktualne dane jednego tokenu.
Wywołuj co 5 sekund gdy masz otwartą pozycję.

## Wywołanie
```
python skills/market_watch/run.py --token AVAX
```

## Zwraca
Aktualne dane tokenu + aktywna pozycja z bazy (jeśli istnieje).

## Twoja rola
Oceń czy trzymać pozycję czy zamknąć.
Weź pod uwagę:

- Czy cena osiągnęła Twój TP/SL?
- Czy warunki które skłoniły Cię do wejścia nadal istnieją?
- Czy funding rate się nie zmienił ekstremalnie?
- Czy widzisz sygnały odwrócenia?
