# Scalp VWAP Deviation — Mean Reversion from VWAP

## Opis
VWAP (Volume Weighted Average Price) to punkt równowagi rynku w danej sesji.
Cena ma tendencję do powrotu do VWAP po ekstremach. Scalper wchodzi gdy cena
odchyla się za daleko i wraca.

## Warunki wejścia (Long — cena poniżej VWAP)
- Cena jest > 0.3% poniżej VWAP
- RSI 5m < 40 (oversold na krótkim TF)
- Wolumen na świecy spadkowej spada (brak dalszej presji sprzedaży)
- Pojawia się świeca z dolnym cieniem > 60% zasięgu (absorpcja)
- Entry: na zamknięciu tej świecy absorpcji

## Warunki wejścia (Short — cena powyżej VWAP)
- Cena jest > 0.3% powyżej VWAP
- RSI 5m > 60
- Wolumen na świecy wzrostowej spada
- Świeca z górnym cieniem > 60% zasięgu
- Entry: short na zamknięciu

## Parametry pozycji (x100 leverage)
- SL: 0.12–0.15% (poza zakresem wicks)
- TP: powrót do VWAP (zwykle 0.20–0.35%)
- Max czas: 12 minut — jeśli cena nie wraca do VWAP, setup się zmienił

## Silne odchylenia VWAP (wysokie conviction)
- > 0.5% odchylenie = bardzo silny mean reversion setup
- Połączenie z round number lub pivot level = ultra high conviction
- W takim przypadku można zwiększyć size

## Uwagi
- Strategia działa najlepiej w środku sesji (nie na otwieraniu/zamykaniu)
- Na BTC VWAP jest bardzo respektowany przez market makerów
- Nie używaj gdy trending market silnie odrywa się od VWAP (momentum > mean reversion)
- Najlepszy timeframe na scalpowanie VWAP: pierwsze 2h po otwieraniu sesji azjatyckiej/europejskiej
