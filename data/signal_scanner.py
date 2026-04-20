"""
data/signal_scanner.py

Signal Scanner — centralny skaner rynku.
Zastępuje indywidualne skanowanie każdego agenta.

Architektura:
  Fast Scanner (co 15s): price delta + acceleration, volume spike 1m
  Slow Scanner (co 60s): RSI, EMA, MACD, Pivot

  → Hash dedup + cooldown per signal_type
  → KB query raz per signal_type (cache TTL 15min)
  → LLM Layer 1 (1 call): ocenia wszystkie sygnały naraz
  → Wyniki w data/market_signals.json
  → Agenci (trader.py) czytają sygnały, każdy wywołuje LLM Layer 2 osobno

Zmienne środowiskowe (.env):
  FAST_PRICE_DELTA_PCT    — próg delta ceny (domyślnie 0.012 = 1.2%)
  FAST_ACCELERATION_MULT  — mnożnik przyspieszenia (domyślnie 1.2 = 20% szybciej)
  FAST_VOLUME_SPIKE_MULT  — mnożnik volume spike (domyślnie 3.0 = 3× średnia)
  MAX_SIGNALS_PER_SCAN    — max sygnałów do Layer 1 (domyślnie 5)
"""
import asyncio
import hashlib
import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

SIGNALS_PATH = ROOT / "data" / "market_signals.json"

# ── Progi fast lane ────────────────────────────────────────
FAST_PRICE_DELTA_PCT   = float(os.getenv("FAST_PRICE_DELTA_PCT",   "0.012"))  # 1.2%
FAST_ACCELERATION_MULT = float(os.getenv("FAST_ACCELERATION_MULT", "1.2"))    # ruch 20% szybszy
FAST_VOLUME_SPIKE_MULT = float(os.getenv("FAST_VOLUME_SPIKE_MULT", "3.0"))    # 3× średni vol

# ── Progi slow lane ────────────────────────────────────────
MAX_SIGNALS_PER_SCAN = int(os.getenv("MAX_SIGNALS_PER_SCAN", "5"))

# ── Interwały ──────────────────────────────────────────────
FAST_SCAN_INTERVAL = 15   # sekund
SLOW_SCAN_INTERVAL = 60   # sekund

# ── Cooldown per signal_type (sekundy) ─────────────────────
COOLDOWNS: dict[str, int] = {
    "fast_move":      60,    # 1 min   — pump mija szybko
    "volume_spike":   90,    # 1.5 min
    "rsi_extreme":    300,   # 5 min
    "rsi_warning":    600,   # 10 min
    "pivot_bounce":   600,   # 10 min  — pivot to poziom, nie zdarzenie
    "ema_cross":      900,   # 15 min  — musi się potwierdzić na następnej świecy
    "macd_momentum":  600,   # 10 min
}

# ── KB cache ───────────────────────────────────────────────
KB_CACHE_TTL = 900  # 15 minut

# ── OpenRouter headers ─────────────────────────────────────
_OR_HEADERS = {
    "HTTP-Referer": "https://github.com/Cherrox93",
    "X-Title":      "CherroxLab Trading System",
}


def _get_llm_clients() -> list:
    """
    Klienci fast LLM (Layer 1) w kolejności priorytetu.
    Primary:  Gemini 2.5 Flash Lite.
    Fallback: Groq Llama4 Scout (auto-przełączenie gdy Gemini zawiedzie).
    Zwraca listę (client, model, provider_name).
    """
    from openai import OpenAI
    from config import settings

    clients = []

    gemini_key = settings.GEMINI_API_KEY
    if gemini_key:
        clients.append((
            OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=gemini_key,
            ),
            settings.GEMINI_FAST_MODEL,
            "gemini",
        ))

    groq_key = settings.GROQ_API_KEY
    if groq_key:
        clients.append((
            OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key),
            settings.GROQ_MODEL,
            "groq",
        ))

    if not clients:
        raise ValueError("Brak GEMINI_API_KEY ani GROQ_API_KEY w .env")

    return clients


async def _llm_call_with_fallback(
        clients: list, prompt: str, max_tokens: int = 800
) -> str:
    """Wywołaj fast LLM z automatycznym fallback gdy primary zawiedzie."""
    last_error = None
    for client, model, provider in clients:
        try:
            return await _llm_call(client, model, prompt, max_tokens)
        except Exception as e:
            logger.warning(
                f"Fast LLM Layer1 [{provider}/{model}] niedostepny: {e} "
                f"— próbuję fallback"
            )
            last_error = e
    raise last_error or ValueError("Brak działającego fast LLM klienta")


async def _llm_call(client, model: str, prompt: str, max_tokens: int = 800) -> str:
    def _sync():
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return r.choices[0].message.content.strip()

    return await asyncio.get_event_loop().run_in_executor(None, _sync)


def _parse_json(text: str) -> dict:
    clean = text.strip()
    if "```" in clean:
        for part in clean.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                try:
                    return json.loads(part)
                except Exception:
                    continue
    if not clean.startswith("{"):
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start >= 0 and end > start:
            clean = clean[start:end]
    try:
        return json.loads(clean)
    except Exception:
        return {}


# ── KB query map ───────────────────────────────────────────

_KB_QUERIES: dict[str, str] = {
    "fast_move":      "momentum breakout pump sudden price spike scalp",
    "volume_spike":   "volume spike breakout liquidity squeeze entry",
    "rsi_extreme":    "RSI oversold overbought extreme bounce reversal entry",
    "rsi_warning":    "RSI approaching extreme zone early entry strategy",
    "pivot_bounce":   "support resistance pivot point bounce entry setup",
    "ema_cross":      "EMA crossover momentum trend following entry signal",
    "macd_momentum":  "MACD histogram momentum continuation entry",
}


class SignalScanner:
    """
    Centralny skaner sygnałów rynkowych.

    Uruchamiaj jako asyncio task z main.py:
        asyncio.create_task(SignalScanner().run(), name="signal_scanner")
    """

    def __init__(self):
        # Bufor 3 ostatnich pomiarów ceny per token (dla acceleration detection)
        self.price_history: dict[str, deque] = {}

        # Dedup: signal_hash → timestamp ostatniego triggera
        self.active_hashes: dict[str, float] = {}

        # KB cache: signal_type → (timestamp, context_text)
        self.kb_cache: dict[str, tuple[float, str]] = {}

        # LLM clients — lista (client, model, provider) z fallback
        self.llm_clients: list = []

        # Timestamp ostatniego slow scan
        self.last_slow_scan = 0.0

    # ────────────────────────────────── inicjalizacja ──────

    def _init_llm(self):
        try:
            self.llm_clients = _get_llm_clients()
            providers = "/".join(p for _, _, p in self.llm_clients)
            logger.info(f"SignalScanner: LLM = {providers}")
        except ValueError as e:
            logger.warning(
                f"SignalScanner: brak LLM ({e}). "
                f"Layer 1 wyłączony — sygnały przechodzą z confidence=0.5."
            )

    # ────────────────────────────────── hash / dedup ───────

    @staticmethod
    def _direction(ind: dict, signal_type: str) -> str:
        """
        Określ kierunek sygnału na podstawie wskaźników.
        RSI < 50 → long, RSI > 50 → short.
        EMA9 vs EMA21 jako tiebreaker.
        """
        rsi  = ind.get("rsi_14")
        ema9 = ind.get("ema_9")
        ema21= ind.get("ema_21")

        if signal_type in ("rsi_extreme", "rsi_warning") and rsi is not None:
            return "long" if rsi < 50 else "short"

        if ema9 is not None and ema21 is not None:
            return "long" if ema9 > ema21 else "short"

        if rsi is not None:
            return "long" if rsi < 50 else "short"

        return "neutral"

    def _make_hash(
        self,
        token: str,
        signal_type: str,
        direction: str,
        rsi: float | None,
        atr: float | None,
        price: float,
    ) -> str:
        """
        Fingerprint sygnału.
        RSI buckety co 5 pkt → RSI 31→29 zmienia hash, 31.0→30.8 nie.
        Volatility bucket: high jeśli ATR > 2% ceny.
        """
        rsi_bucket = str(round(rsi / 5) * 5) if rsi is not None else "?"
        vol_bucket = "high" if (atr and price and atr > price * 0.02) else "low"
        raw = f"{token}:{signal_type}:{direction}:{rsi_bucket}:{vol_bucket}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _on_cooldown(self, sig_hash: str, signal_type: str) -> bool:
        last     = self.active_hashes.get(sig_hash, 0.0)
        cooldown = COOLDOWNS.get(signal_type, 300)
        return (time.time() - last) < cooldown

    def _mark(self, sig_hash: str):
        self.active_hashes[sig_hash] = time.time()

    # ────────────────────────────────── KB query ───────────

    async def _kb_query(self, signal_type: str) -> str:
        """
        Pobierz kontekst strategii z KB.
        Cache TTL = 15 minut — nie querujemy przy każdym sygnale.
        """
        cached = self.kb_cache.get(signal_type)
        if cached and (time.time() - cached[0]) < KB_CACHE_TTL:
            return cached[1]

        query = _KB_QUERIES.get(signal_type, signal_type)
        try:
            from knowledge_base.query import search
            results  = search(query, n_results=3)
            relevant = [
                r["text"][:500]
                for r in results
                if r.get("distance", 1.0) < 0.65   # tylko faktycznie pasujące
            ]
            context = "\n---\n".join(relevant) if relevant else "Brak pasujących strategii w KB."
        except Exception as e:
            logger.debug(f"KB query error ({signal_type}): {e}")
            context = "KB niedostępne."

        self.kb_cache[signal_type] = (time.time(), context)
        return context

    # ────────────────────────────────── fast lane ──────────

    def _update_price_history(self, token: str, price: float):
        if token not in self.price_history:
            self.price_history[token] = deque(maxlen=3)
        self.price_history[token].append((time.time(), price))

    def _check_fast(self, token: dict) -> list[dict]:
        """
        Fast lane signals:
          - fast_move:    delta ceny w ~15s > FAST_PRICE_DELTA_PCT,
                          opcjonalnie z acceleration (ruch przyspiesza)
          - volume_spike: ostatnia 1m świeca > N × średnia 20 poprzednich
        """
        symbol = token["symbol"]
        price  = float(token.get("price") or 0)
        if not price:
            return []

        self._update_price_history(symbol, price)
        hist = self.price_history.get(symbol, deque())
        ind  = token.get("indicators", {})
        out  = []

        # ── price delta + acceleration ─────────────────────
        if len(hist) >= 2:
            ts_prev, p_prev = hist[-2]
            age      = time.time() - ts_prev
            delta_new = (price - p_prev) / p_prev if p_prev else 0.0

            if abs(delta_new) >= FAST_PRICE_DELTA_PCT and age <= 30:
                is_acc = False
                if len(hist) >= 3:
                    _, p_old  = hist[-3]
                    delta_old = (p_prev - p_old) / p_old if p_old else 0.0
                    # ruch przyspiesza gdy nowy delta > stary * mnożnik
                    is_acc = abs(delta_new) > abs(delta_old) * FAST_ACCELERATION_MULT

                out.append({
                    "symbol":      symbol,
                    "signal_type": "fast_move",
                    "signal_kind": "fast",
                    "price":       price,
                    "indicators":  ind,
                    "score":       5.0 + (1.0 if is_acc else 0.0),
                    "meta": {
                        "delta_pct":    round(delta_new * 100, 3),
                        "accelerating": is_acc,
                        "age_s":        round(age, 1),
                    },
                })

        # ── volume spike ───────────────────────────────────
        candles_1m = token.get("candles", {}).get("1m", [])
        if len(candles_1m) >= 5:
            last_vol = float(candles_1m[-1].get("v", 0))
            prev_n   = candles_1m[-21:-1] if len(candles_1m) >= 21 else candles_1m[:-1]
            avg_vol  = (
                sum(float(c.get("v", 0)) for c in prev_n) / len(prev_n)
                if prev_n else 0.0
            )
            if avg_vol > 0 and last_vol > avg_vol * FAST_VOLUME_SPIKE_MULT:
                out.append({
                    "symbol":      symbol,
                    "signal_type": "volume_spike",
                    "signal_kind": "fast",
                    "price":       price,
                    "indicators":  ind,
                    "score":       4.0,
                    "meta": {
                        "vol_ratio": round(last_vol / avg_vol, 2),
                        "vol_1m":    round(last_vol, 2),
                    },
                })

        return out

    # ────────────────────────────────── slow lane ──────────

    def _check_slow(self, token: dict) -> list[dict]:
        """
        Slow lane signals: RSI extreme/warning, Pivot bounce, EMA cross, MACD momentum.
        Analog _prefilter_tokens z trader.py — przeniesiony tutaj i rozszerzony
        o typy sygnałów zamiast surowego score.
        """
        symbol = token["symbol"]
        price  = float(token.get("price") or 0)
        if not price:
            return []

        ind    = token.get("indicators", {})
        rsi    = ind.get("rsi_14")
        rsi5   = ind.get("rsi_5m")
        rsi4   = ind.get("rsi_4h")
        ema9   = ind.get("ema_9")
        ema9_5m = ind.get("ema_9_5m")
        ema21  = ind.get("ema_21")
        macd_h = ind.get("macd_hist")
        r1     = ind.get("pivot_r1")
        s1     = ind.get("pivot_s1")
        out    = []

        # RSI extreme (< 35 lub > 65)
        if rsi is not None and (rsi < 35 or rsi > 65):
            confirm_4h = rsi4 is not None and (rsi4 < 40 or rsi4 > 60)
            # 5m RSI w tym samym kierunku = szybsze potwierdzenie wejścia
            confirm_5m = rsi5 is not None and (
                (rsi < 35 and rsi5 < 40) or (rsi > 65 and rsi5 > 60)
            )
            score = 3.0 + (2.0 if confirm_4h else 0.0) + (1.0 if confirm_5m else 0.0)
            out.append({
                "symbol":      symbol,
                "signal_type": "rsi_extreme",
                "signal_kind": "slow",
                "price":       price,
                "indicators":  ind,
                "score":       score,
                "meta":        {"rsi_15m": rsi, "rsi_5m": rsi5, "rsi_4h": rsi4,
                                "4h_confirm": confirm_4h, "5m_confirm": confirm_5m},
            })

        # RSI warning (< 42 lub > 58) — tylko jeśli nie ma extreme
        elif rsi is not None and (rsi < 42 or rsi > 58):
            confirm_4h = rsi4 is not None and (rsi4 < 40 or rsi4 > 60)
            confirm_5m = rsi5 is not None and (
                (rsi < 42 and rsi5 < 45) or (rsi > 58 and rsi5 > 55)
            )
            score = 1.5 + (2.0 if confirm_4h else 0.0) + (0.5 if confirm_5m else 0.0)
            out.append({
                "symbol":      symbol,
                "signal_type": "rsi_warning",
                "signal_kind": "slow",
                "price":       price,
                "indicators":  ind,
                "score":       score,
                "meta":        {"rsi_15m": rsi, "rsi_5m": rsi5, "rsi_4h": rsi4,
                                "4h_confirm": confirm_4h, "5m_confirm": confirm_5m},
            })

        # Pivot bounce (cena ±0.8% od S1 lub R1)
        if s1 is not None and abs(price - s1) / price < 0.008:
            out.append({
                "symbol":      symbol,
                "signal_type": "pivot_bounce",
                "signal_kind": "slow",
                "price":       price,
                "indicators":  ind,
                "score":       2.5,
                "meta":        {"level": "S1", "pivot_s1": s1,
                                "dist_pct": round(abs(price - s1) / price * 100, 3)},
            })

        if r1 is not None and abs(price - r1) / price < 0.008:
            out.append({
                "symbol":      symbol,
                "signal_type": "pivot_bounce",
                "signal_kind": "slow",
                "price":       price,
                "indicators":  ind,
                "score":       2.5,
                "meta":        {"level": "R1", "pivot_r1": r1,
                                "dist_pct": round(abs(price - r1) / price * 100, 3)},
            })

        # EMA cross / momentum (gap EMA9-EMA21 > 0.1%)
        if ema9 is not None and ema21 is not None and ema21 > 0:
            gap_pct = abs(ema9 - ema21) / ema21
            if gap_pct > 0.001:
                # 5m EMA9 aligned = wejście z trendem na niższym TF
                aligned_5m = ema9_5m is not None and (
                    (ema9 > ema21 and ema9_5m > ema9) or
                    (ema9 < ema21 and ema9_5m < ema9)
                )
                out.append({
                    "symbol":      symbol,
                    "signal_type": "ema_cross",
                    "signal_kind": "slow",
                    "price":       price,
                    "indicators":  ind,
                    "score":       1.5 + (0.5 if aligned_5m else 0.0),
                    "meta":        {"gap_pct": round(gap_pct * 100, 3),
                                    "ema9": ema9, "ema21": ema21,
                                    "ema9_5m": ema9_5m, "5m_aligned": aligned_5m},
                })

        # MACD momentum (histogram > 0.05% ceny)
        if macd_h is not None and price > 0 and abs(macd_h) / price > 0.0005:
            out.append({
                "symbol":      symbol,
                "signal_type": "macd_momentum",
                "signal_kind": "slow",
                "price":       price,
                "indicators":  ind,
                "score":       1.0,
                "meta":        {"macd_hist": macd_h,
                                "hist_pct": round(abs(macd_h) / price * 100, 4)},
            })

        return out

    # ────────────────────────────────── dedup + cooldown ───

    def _filter_new(self, candidates: list[dict]) -> list[dict]:
        """
        Przepuść kandydatów przez hash dedup i cooldown per signal_type.
        Dodaje pola: direction, hash.
        """
        new = []
        for sig in candidates:
            ind = sig.get("indicators", {})

            direction = self._direction(ind, sig["signal_type"])
            sig["direction"] = direction

            sig_hash = self._make_hash(
                token       = sig["symbol"],
                signal_type = sig["signal_type"],
                direction   = direction,
                rsi         = ind.get("rsi_14"),
                atr         = ind.get("atr_14"),
                price       = sig["price"],
            )
            sig["hash"] = sig_hash

            if self._on_cooldown(sig_hash, sig["signal_type"]):
                logger.debug(
                    f"SKIP (cooldown {COOLDOWNS.get(sig['signal_type'],300)}s): "
                    f"{sig['symbol']} {sig['signal_type']}"
                )
                continue

            new.append(sig)
            self._mark(sig_hash)

        return new

    # ────────────────────────────────── Layer 1 LLM ────────

    async def _layer1(self, signals: list[dict]) -> list[dict]:
        """
        LLM Layer 1 — jeden call dla wszystkich sygnałów.

        Zbiera KB context (cache) dla każdego signal_type.
        Pyta LLM: które sygnały są technicznie valid?
        Zwraca sygnały z polami: valid, confidence, market_context,
        suggested_sl_pct, suggested_tp_pct.
        """
        if not self.llm_clients:
            # Brak LLM — przepuszcza wszystkie z confidence=0.5
            for sig in signals:
                sig["valid"]            = True
                sig["confidence"]       = 0.5
                sig["market_context"]   = "Layer 1 niedostępny (brak LLM)."
                sig["suggested_sl_pct"] = 0.015
                sig["suggested_tp_pct"] = 0.030
            return signals

        # KB query per signal_type (cache)
        signal_types = list({s["signal_type"] for s in signals})
        kb_contexts  = {st: await self._kb_query(st) for st in signal_types}

        # Zbuduj opis każdego sygnału
        lines = []
        for i, sig in enumerate(signals):
            ind = sig.get("indicators", {})
            kb  = kb_contexts.get(sig["signal_type"], "")
            lines.append(
                f"[{i}] {sig['symbol']} | {sig['signal_type']} ({sig['signal_kind']}) "
                f"| dir={sig['direction']} score={sig['score']} price={sig['price']}\n"
                f"  RSI15m={ind.get('rsi_14','?')} RSI4h={ind.get('rsi_4h','?')} "
                f"EMA9={ind.get('ema_9','?')} EMA21={ind.get('ema_21','?')} "
                f"MACD_hist={ind.get('macd_hist','?')} ATR={ind.get('atr_14','?')}\n"
                f"  PivotS1={ind.get('pivot_s1','?')} PivotR1={ind.get('pivot_r1','?')}\n"
                f"  meta={json.dumps(sig.get('meta', {}))}\n"
                f"  KB: {kb[:400]}"
            )

        prompt = f"""Jestes analizatorem sygnałów tradingowych (Layer 1 — pre-filtr przed agentami).

SYGNAŁY DO OCENY ({len(signals)}):
{chr(10).join(lines)}

Dla KAŻDEGO sygnału oceń:
1. Czy setup jest technicznie valid I wart dalszej analizy WZGLĘDEM JEGO KIERUNKU (dir)?
   - dir=long:  oceń czy wskaźniki wspierają ruch w górę
   - dir=short: oceń czy wskaźniki wspierają ruch w dół — NIE odrzucaj shorta tylko dlatego że trend ogólny jest wzrostowy
2. Jaki jest krótki market context (max 50 słów)?
3. Sugerowane SL% i TP% jako ułamek dziesiętny (np. 0.015 = 1.5%)
   Bierz pod uwagę ATR i volatility przy dobieraniu SL/TP.

Bądź konserwatywny — valid=true TYLKO gdy setup jest czytelny w danym kierunku.
Oceniaj każdy sygnał niezależnie — nie odrzucaj wszystkich shortów gdy rynek jest szeroko overbought.

Odpowiedz WYŁĄCZNIE JSON:
{{
  "results": [
    {{
      "index": 0,
      "valid": true,
      "confidence": 0.80,
      "market_context": "opis setupu max 50 słów",
      "suggested_sl_pct": 0.015,
      "suggested_tp_pct": 0.030
    }}
  ],
  "market_summary": "ogólny stan rynku max 30 słów"
}}"""

        try:
            raw    = await _llm_call_with_fallback(self.llm_clients, prompt, max_tokens=700)
            parsed = _parse_json(raw)
        except Exception as e:
            logger.warning(f"Layer 1 LLM error (wszystkie providery zawiodly): {e}")
            parsed = {}

        result_map     = {r["index"]: r for r in parsed.get("results", [])}
        market_summary = parsed.get("market_summary", "")

        valid = []
        for i, sig in enumerate(signals):
            r = result_map.get(i, {})
            sig["valid"]            = r.get("valid", False)
            sig["confidence"]       = float(r.get("confidence", 0.0))
            sig["market_context"]   = r.get("market_context", "")
            sig["suggested_sl_pct"] = float(r.get("suggested_sl_pct", 0.015))
            sig["suggested_tp_pct"] = float(r.get("suggested_tp_pct", 0.030))
            sig["market_summary"]   = market_summary

            if sig["valid"]:
                valid.append(sig)
                logger.info(
                    f"Layer 1 VALID: {sig['symbol']} {sig['signal_type']} "
                    f"conf={sig['confidence']:.0%} dir={sig['direction']}"
                )
            else:
                logger.info(
                    f"Layer 1 REJECT: {sig['symbol']} {sig['signal_type']}"
                )

        return valid

    # ────────────────────────────────── zapis ──────────────

    def _write(self, signals: list[dict]):
        n_fast = sum(1 for s in signals if s["signal_kind"] == "fast")
        n_slow = sum(1 for s in signals if s["signal_kind"] == "slow")
        output = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "count":      len(signals),
            "signals":    signals,
        }
        SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SIGNALS_PATH.write_text(json.dumps(output, default=str))
        logger.info(f"Signals zapisane: {len(signals)} ({n_fast} fast, {n_slow} slow)")

    def _clear(self):
        output = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "count":      0,
            "signals":    [],
        }
        SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SIGNALS_PATH.write_text(json.dumps(output))

    # ────────────────────────────────── główna pętla ───────

    async def run(self):
        """
        Główna pętla scannera.
        Fast scan co 15s, slow scan co 60s.
        Uruchamiaj jako asyncio task.
        """
        logger.info("SignalScanner: start")
        self._init_llm()

        no_signal_ticks = 0

        while True:
            try:
                now = time.time()

                from data.market_feed import get_all_tokens
                tokens = get_all_tokens()

                if not tokens:
                    await asyncio.sleep(FAST_SCAN_INTERVAL)
                    continue

                candidates: list[dict] = []

                # Fast lane — każdy tick
                for token in tokens:
                    candidates.extend(self._check_fast(token))

                # Slow lane — co SLOW_SCAN_INTERVAL
                if now - self.last_slow_scan >= SLOW_SCAN_INTERVAL:
                    for token in tokens:
                        candidates.extend(self._check_slow(token))
                    self.last_slow_scan = now

                if not candidates:
                    no_signal_ticks += 1
                    if no_signal_ticks % 4 == 0:
                        logger.debug(
                            f"Scanner: brak kandydatów "
                            f"({no_signal_ticks * FAST_SCAN_INTERVAL}s)"
                        )
                    await asyncio.sleep(FAST_SCAN_INTERVAL)
                    continue

                no_signal_ticks = 0

                # Dedup + cooldown
                new_signals = self._filter_new(candidates)

                if not new_signals:
                    logger.debug(
                        f"Scanner: {len(candidates)} kandydatów, "
                        f"wszystkie na cooldown/dedup"
                    )
                    await asyncio.sleep(FAST_SCAN_INTERVAL)
                    continue

                logger.info(
                    f"Scanner: {len(new_signals)} nowych sygnałów "
                    f"(z {len(candidates)} kandydatów, {len(tokens)} tokenów)"
                )

                # Ogranicz do MAX_SIGNALS_PER_SCAN — najpierw fast, potem wg score
                new_signals.sort(
                    key=lambda s: (s["signal_kind"] == "fast", s["score"]),
                    reverse=True,
                )
                new_signals = new_signals[:MAX_SIGNALS_PER_SCAN]

                # Layer 1 LLM — 1 call dla wszystkich
                valid_signals = await self._layer1(new_signals)

                if valid_signals:
                    self._write(valid_signals)
                else:
                    logger.info("Scanner: Layer 1 odrzucił wszystkie — brak sygnałów")
                    self._clear()

            except asyncio.CancelledError:
                logger.info("SignalScanner: zatrzymany")
                break
            except Exception as e:
                logger.error(f"SignalScanner error: {e}", exc_info=True)

            await asyncio.sleep(FAST_SCAN_INTERVAL)
