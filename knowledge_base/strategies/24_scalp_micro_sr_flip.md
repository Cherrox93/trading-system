# Scalp Micro S/R Flip — Support/Resistance Level Flip

## Opis
Kluczowe poziomy S/R (round numbers, poprzednie high/low, pivot) po przebiciu zmieniają funkcję.
Opór staje się wsparciem i odwrotnie. Scalper wchodzi na retescie przebitego poziomu.

## Identyfikacja poziomów do scalpingu
- Round numbers: $100, $150, $200 itd. (szczególnie silne na BTC/ETH/SOL)
- 4h high/low z ostatnich 3 dni — poziomy gdzie rynek zawracał
- Pivot Daily PP, S1, R1 (podane przez scanner)
- Poprzedni ATH/ATL na krótszym TF (1h high/low)

## Scenariusz Flip (najbardziej wiarygodny setup)
1. Cena przebija poziom oporu z wolumenem > 1.5× średnia
2. Świeca 1m zamyka się powyżej (ważne — zamknięcie, nie wick)
3. Cena cofa się do przebitego poziomu (retest)
4. Na retescie: mała świeca z odrzuceniem (wick down, ciało zamknięte powyżej)
5. WEJŚCIE LONG na zamknięciu świecy retest

## Parametry pozycji (x100 leverage)
- SL: 0.15% poniżej przebitego poziomu (jeśli wraca przez poziom = setup nieważny)
- TP: 0.20–0.40% (następny poziom oporu)
- Max czas: 15 minut — retest albo działa natychmiast albo wcale

## To samo dla shorta (support → resistance flip)
- Przebit support z wolumenem
- Retest od dołu z odrzuceniem wick up
- Entry short, SL powyżej poziomu, TP następny support

## Uwagi
- Round numbers na BTC ($60k, $65k, $70k) = najsilniejsze poziomy
- SOL: $150, $180, $200 są historycznie ważne
- Nie wchodź na pierwszym dotknięciu bez retests — poczekaj na flip confirmation
