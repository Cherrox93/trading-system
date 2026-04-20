# Skill: execute_trade

Otwiera pozycję na podstawie Twojej decyzji.
Wszystkie parametry ustalasz SAM na podstawie analizy.

## Wywołanie
```
python skills/execute_trade/run.py \
  --agent_id   trader_01 \
  --token      AVAX \
  --direction  long \
  --size_pct   0.008 \
  --sl_pct     0.004 \
  --tp_pct     0.014 \
  --leverage   3 \
  --strategy   pivot_mean_reversion \
  --confidence 0.82 \
  --reasoning  "RSI=31 przy S1 Pivot, wick rejection, FR neutralny, ATR maly"
```

## Parametry — ustalasz SAM

**size_pct** (0.001–0.05):
Ile % budżetu ryzykujesz. Mały setup = mały size. Pewny setup = większy.
Przykład: niepewny setup = 0.003, pewny = 0.015

**sl_pct** (0.001–0.05):
Gdzie SL. Zależy od ATR i struktury rynku.
Przykład: przy wąskim ATR = 0.003, przy szerokim = 0.015

**tp_pct** (0.001–0.10):
Gdzie TP. Zależy od celu (następny Pivot, strefa S/R).
Przykład: scalp = 0.005, swing = 0.03

**leverage** (1–10):
Dźwignia. Domyślnie 1 (bez dźwigni). Używaj ostrożnie.
Przykład: bez dźwigni = 1, umiarkowana = 3, agresywna = 5

**reasoning**:
Uzasadnij decyzję: co widzisz na rynku, która strategia, dlaczego teraz.
