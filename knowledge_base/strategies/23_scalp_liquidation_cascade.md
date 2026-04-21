# Scalp Liquidation Cascade — Riding the Liquidation Wave

## Opis
Na rynkach perpetual futures duże ruchy ceny wyzwalają kaskady likwidacji lewarowanych pozycji,
które jeszcze bardziej przyspieszają ruch. Scalper wchodzi w kierunku kaskady i wychodzi
zanim rynek się stabilizuje.

## Identyfikacja kaskady
- Nagły ruch ceny > 0.5% w < 2 minutach bez wyraźnego newsa
- Wolumen 1m spike > 5× średnia (likwidacje generują duży vol)
- RSI 5m wychodzi z zakresu 45-55 gwałtownie (>5 punktów w jednej świecy)
- Open interest spada przy ruchu (potwierdzenie likwidacji, nie nowe pozycje)

## Wejście
- Wejdź w kierunku ruchu NA POCZĄTKU kaskady (pierwsza lub druga świeca 1m)
- NIE gonij jeśli cena ruszyła już > 0.8% — kaskada może się odwrócić
- Najlepszy entry: pullback 0.1–0.2% po pierwszym impulsie

## Parametry pozycji (x100 leverage)
- SL: 0.15% (kaskady są gwałtowne — mały SL wystarczy)
- TP: 0.25–0.50% (kaskada może być długa, ale nie bądź chciwy)
- Max czas: 5 minut — kaskady się kończą szybko

## Sygnały końca kaskady (wyjdź)
- Wolumen zaczyna spadać przy kontynuacji ruchu
- Duża świeca z cieniem > 50% ciała (absorpcja przez market makerów)
- RSI 5m dotknął 80/20 (extreme — odwrócenie bliskie)

## Uwagi
- BTC ma największe kaskady likwidacji — największa płynność kontraktów
- SOL ma częste kaskady na niższych poziomach cenowych
- ETH — solidny, przewidywalny, dobry dla mniej doświadczonych
- Ryzyko: fałszywa kaskada = pułapka. Zawsze SL!
