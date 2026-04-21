# Scalp Order Book Delta — Bid/Ask Imbalance Entry

## Opis
Wejście w kierunku dominującej presji kupna/sprzedaży na podstawie dysproporcji wolumenu bid vs ask.
Gdy jedna strona książki zleceń jest znacznie większa, cena będzie podążać za popytem.

## Warunki wejścia
- Volume delta (buy vol - sell vol) na ostatnich 3 świecach 1m silnie jednostronny (> +60% lub < -60% z całości)
- Order book: bid stack > 2× ask stack → long; ask stack > 2× bid stack → short
- Cena porusza się w kierunku dominującej strony (momentum confirmation)
- Spread < 0.05% — wejście musi być efektywne kosztowo

## Parametry pozycji (x100 leverage)
- SL: 0.12–0.18% (za poziomem odwrócenia imbalance)
- TP: 0.20–0.30% (kolejny poziom S/R lub wyczerpanie imbalance)
- Max czas: 8 minut

## Kiedy NIE wchodzić
- Tuż przed/po dużych newsach (imbalance fałszywy)
- Gdy spread > 0.1% (koszty zjadają zysk przy x100)
- Gdy price action choppowy (bez kierunkowego ruchu ostatnie 5 świec 1m)

## Uwagi
- Najlepszy na ETH i SOL (duży order book, manipulacja mniej powszechna)
- Imbalance > 80% jest bardzo silnym sygnałem — traktuj jako high conviction
- Kombinacja z 1m momentum = najsilniejszy setup scalperski
