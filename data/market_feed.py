"""
data/market_feed.py

Prawdziwy feed danych rynkowych z Lighter API.
Paper mode i live mode — identyczne dane rynkowe.
Tylko execution różni się między trybami.

Dostarcza:
- Świece OHLCV: 1m/5m/15m/1h/4h/1d  (REST polling)
- Order Book top 10                   (WebSocket realtime)
- Funding Rate                        (REST polling co 30m)
- Wskaźniki: RSI, EMA, MACD, ATR, Pivot Points

API Lighter:
  REST: https://mainnet.zklighter.elliot.ai/api/v1/...
  WS:   wss://mainnet.zklighter.elliot.ai/stream
    Kanał order book:  order_book/{market_id}
    Wiadomości: subscribed/order_book, update/order_book
    (brak kanału candlestick — świece przez REST polling)

Format świec z REST:
  {"code":200,"r":"1m","c":[{"t":ms,"o":f,"h":f,"l":f,"c":f,"v":f,"V":f,"i":i}]}
"""
import asyncio
import contextlib
import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Optional

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import httpx
import websockets
import pandas as pd

try:
    import pandas_ta as ta
    HAS_TA = True
except ImportError:
    HAS_TA = False
    logging.warning(
        "pandas_ta nie zainstalowane — wskazniki beda puste. "
        "Uruchom: pip install pandas-ta>=0.3.14b"
    )

from config import settings

logger = logging.getLogger(__name__)

# Event ustawiany gdy dane historyczne są w pełni załadowane.
# Supervisor czeka na ten sygnał zanim odpali agentów.
_historical_ready: asyncio.Event = asyncio.Event()


def is_historical_ready() -> bool:
    """Czy dane historyczne (świece + wskaźniki) są gotowe?"""
    return _historical_ready.is_set()


async def wait_for_historical_ready():
    """Poczekaj aż dane historyczne będą gotowe."""
    await _historical_ready.wait()


# ── Konfiguracja ───────────────────────────────────────────

SNAPSHOT_PATH = Path("./data/market_snapshot.json")
API_BASE      = "https://mainnet.zklighter.elliot.ai"
WS_URL        = "wss://mainnet.zklighter.elliot.ai/stream"

# Lista tokenów jest budowana dynamicznie przy starcie z exchangeStats.
# Filtr: daily_quote_token_volume >= settings.MIN_VOLUME_USD
# TOKENS i LIGHTER_SYMBOL są wypełniane przez discover_markets() w run().
TOKENS: list[str] = []          # symbol → używany w całym systemie
LIGHTER_SYMBOL: dict[str, str]= {}  # symbol → symbol na Lighter (gdy różny)

# Tokeny do pominięcia — instrumenty tradfi, commodities, zduplikowane lub błędne symbole
TOKEN_BLACKLIST: set[str] = {
    "SPY",       # S&P 500 ETF tracker
    "XAG",       # srebro (silver)
    "XAU",       # złoto (gold)
    "XCU",       # miedź (copper)
    "XPT",       # platyna (platinum)
    "WTI",       # ropa WTI (crude oil)
    "BRENTOIL",  # ropa Brent (crude oil)
    "AI16Z",     # token AI memów, niska jakość sygnałów
    "LIT/USDC",  # błędny symbol ze slashem
    "ETH/USDC",  # spot/swap — duplikat ETH, nie perpetual
}

# Timeframy: klucz wewnętrzny → parametr API
# Lighter używa: 1m, 5m, 15m, 30m, 1h, 4h, 1d
RESOLUTIONS: list[str] = ["1m", "5m", "15m", "4h", "1d"]

# Ile świec pobieramy historycznie dla każdego TF
CANDLE_LIMIT = {
    "1m":  200,
    "5m":  200,
    "15m": 200,
    "1h":  200,
    "4h":  200,
    "1d":  365,
}

# Jak daleko wstecz sięga każdy TF (w ms)
CANDLE_LOOKBACK_MS = {
    "1m":    200 * 60 * 1000,
    "5m":    200 * 5  * 60 * 1000,
    "15m":   200 * 15 * 60 * 1000,
    "1h":    200 * 60 * 60 * 1000,
    "4h":    200 * 4  * 60 * 60 * 1000,
    "1d":    400 * 24 * 60 * 60 * 1000,
}

# Co ile sekund odświeżać świece przez REST polling
CANDLE_POLL_INTERVAL = {
    "1m":  60,
    "5m":  300,
    "15m": 900,
    "1h":  3600,
    "4h":  14400,
    "1d":  86400,
}


# ── Stan wewnętrzny ────────────────────────────────────────

class MarketState:
    """
    Trzyma w pamięci wszystkie dane rynkowe.
    Aktualizowany przez WebSocket + REST polling.
    Odczytywany przez write_snapshot co 1 sekundę.
    """

    def __init__(self):
        self.markets: dict    = {}  # symbol → {market_id, lighter_symbol}
        self.candles: dict    = {}  # symbol → {res → deque[candle]}
        self.orderbooks: dict = {}  # symbol → {bids, asks}
        self.funding: dict    = {}  # symbol → {rate}
        self.last_price: dict = {}  # symbol → float
        self.stats: dict      = {}  # symbol → {change_24h, volume_24h}

    def init_token(self, symbol: str, market_id: int, lighter_symbol: str):
        self.candles[symbol] = {
            res: deque(maxlen=CANDLE_LIMIT[res])
            for res in RESOLUTIONS
        }
        self.orderbooks[symbol] = {"bids": [], "asks": []}
        self.funding[symbol]    = {"rate": 0.0}
        self.last_price[symbol] = 0.0
        self.stats[symbol]      = {"change_24h": 0.0, "volume_24h": 0.0}
        self.markets[symbol]    = {
            "market_id":     market_id,
            "lighter_symbol": lighter_symbol
        }
        logger.debug(f"Token zainicjalizowany: {symbol} "
                     f"(market_id={market_id}, lighter={lighter_symbol})")

    def add_candle(self, symbol: str, res: str, candle: dict):
        """Dodaj lub zaktualizuj świecę. Jeśli ten sam timestamp — nadpisz."""
        if symbol not in self.candles or res not in self.candles[symbol]:
            return
        buf = self.candles[symbol][res]
        if buf and buf[-1]["t"] == candle["t"]:
            buf[-1] = candle  # aktualizacja bieżącej świecy
        else:
            buf.append(candle)
        # Aktualizuj last_price z każdej świecy 1m
        if res == "1m":
            self.last_price[symbol] = candle["c"]

    def update_orderbook_snapshot(self, symbol: str,
                                   bids: list, asks: list):
        """Pełne zastąpienie order book (po subscribed)."""
        self.orderbooks[symbol] = {
            "bids": sorted(bids,  key=lambda x: x[0], reverse=True),
            "asks": sorted(asks,  key=lambda x: x[0])
        }
        # Aktualizuj last_price z mid-price
        if bids and asks:
            mid = (float(bids[0][0]) + float(asks[0][0])) / 2
            self.last_price[symbol] = mid

    def apply_orderbook_update(self, symbol: str, bids: list, asks: list):
        """Incrementalny update order book (delta)."""
        ob = self.orderbooks.get(symbol, {"bids": [], "asks": []})
        ob["bids"] = _merge_ob_side(ob["bids"], bids, reverse=True)
        ob["asks"] = _merge_ob_side(ob["asks"], asks, reverse=False)
        self.orderbooks[symbol] = ob
        # Aktualizuj last_price
        if ob["bids"] and ob["asks"]:
            mid = (ob["bids"][0][0] + ob["asks"][0][0]) / 2
            self.last_price[symbol] = mid

    def update_funding(self, symbol: str, rate: float):
        self.funding[symbol] = {"rate": rate}

    def update_stats(self, symbol: str, change_24h: float, volume_24h: float):
        self.stats[symbol] = {
            "change_24h": change_24h,
            "volume_24h": volume_24h,
        }


def _merge_ob_side(existing: list, updates: list, reverse: bool) -> list:
    """Zastosuj delta update do jednej strony order booka."""
    price_map = {entry[0]: entry[1] for entry in existing}
    for price, size in updates:
        if float(size) == 0.0:
            price_map.pop(price, None)
        else:
            price_map[price] = size
    result = [[p, s] for p, s in price_map.items()]
    return sorted(result, key=lambda x: x[0], reverse=reverse)


state = MarketState()


# ── REST — pobieranie danych wstępnych ─────────────────────

async def discover_markets() -> dict:
    """
    Odkryj wszystkie pary na Lighter z wolumenem >= MIN_VOLUME_USD.

    Łączy dane z dwóch endpointów:
      /api/v1/orderBooks   → market_id dla każdego symbolu
      /api/v1/exchangeStats → wolumen 24h dla każdego symbolu

    Wypełnia globalne TOKENS i LIGHTER_SYMBOL.
    Zwraca: {symbol → market_id}  (symbol = klucz wewnętrzny)
    """
    global TOKENS, LIGHTER_SYMBOL

    min_vol = settings.MIN_VOLUME_USD

    async with httpx.AsyncClient(timeout=15) as client:
        r_ob, r_st = await asyncio.gather(
            client.get(f"{API_BASE}/api/v1/orderBooks"),
            client.get(f"{API_BASE}/api/v1/exchangeStats"),
        )
        r_ob.raise_for_status()
        r_st.raise_for_status()

    ob_data  = r_ob.json()
    st_data  = r_st.json()

    # lighter_symbol → market_id
    sym_to_id: dict[str, int] = {}
    for ob in ob_data.get("order_books", []):
        sym = ob.get("symbol", "")
        mid = ob.get("market_id")
        if sym and mid is not None:
            sym_to_id[sym] = int(mid)

    # lighter_symbol → volume_24h
    sym_to_vol: dict[str, float] = {}
    for s in st_data.get("order_book_stats", []):
        sym = s.get("symbol", "")
        vol = float(s.get("daily_quote_token_volume", 0))
        if sym:
            sym_to_vol[sym] = vol

    # Filtruj po wolumenie i zbuduj mapę
    market_ids: dict[str, int] = {}
    new_lighter: dict[str, str] = {}

    for lighter_sym, mid in sym_to_id.items():
        vol = sym_to_vol.get(lighter_sym, 0.0)
        if vol < min_vol:
            continue

        # Klucz wewnętrzny: strip prefix "1000" dla czytelności (1000PEPE → PEPE)
        if lighter_sym.startswith("1000"):
            internal = lighter_sym[4:]
            new_lighter[internal] = lighter_sym
        else:
            internal = lighter_sym

        # Pomiń tokeny z czarnej listy
        if internal in TOKEN_BLACKLIST or lighter_sym in TOKEN_BLACKLIST:
            logger.info(f"  SKIP {internal} — na czarnej liście")
            continue

        market_ids[internal] = mid

    # Aktualizuj globalne listy (sortuj po wolumenie malejąco)
    TOKENS = sorted(
        market_ids.keys(),
        key=lambda s: sym_to_vol.get(LIGHTER_SYMBOL.get(s, s), 0),
        reverse=True,
    )
    LIGHTER_SYMBOL = new_lighter

    logger.info(
        f"Odkryto {len(market_ids)} par z vol >= ${min_vol:,.0f} "
        f"(spośród {len(sym_to_id)} wszystkich)"
    )
    for sym in TOKENS:
        lighter_sym = LIGHTER_SYMBOL.get(sym, sym)
        vol = sym_to_vol.get(lighter_sym, 0.0)
        logger.info(
            f"  {sym:<14} market_id={market_ids[sym]:<4}  "
            f"vol24h=${vol/1e6:.1f}M"
        )

    return market_ids


def _parse_candles_response(raw: dict, symbol: str, res: str) -> int:
    """
    Parsuj odpowiedź REST /api/v1/candles.
    Format: {"code":200,"r":"1m","c":[{"t":ms,"o":f,"h":f,"l":f,"c":f,"v":f}]}
    Zwraca liczbę dodanych świec.
    """
    candles = raw.get("c", [])
    for c in candles:
        state.add_candle(symbol, res, {
            "t": int(c["t"]),
            "o": float(c["o"]),
            "h": float(c["h"]),
            "l": float(c["l"]),
            "c": float(c["c"]),
            "v": float(c.get("v", 0)),
        })
    return len(candles)


async def fetch_historical_candles(
        symbol: str,
        market_id: int,
        resolution: str,
        _retries: int = 3,
        client: httpx.AsyncClient | None = None,
        _backoff_base: float = 5.0,
) -> int:
    """
    Pobierz historyczne świece przez REST.
    Wywoływane raz przy starcie, potem co CANDLE_POLL_INTERVAL[res].
    Zwraca liczbę załadowanych świec. Ponawia przy 429 (max 3 razy).
    Przyjmuje opcjonalny współdzielony client (szybsze połączenia keepalive).
    """
    limit = CANDLE_LIMIT[resolution]
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - CANDLE_LOOKBACK_MS[resolution]
    _own_client = client is None

    for attempt in range(_retries):
        try:
            if _own_client:
                client = httpx.AsyncClient(timeout=15)
            async with (client if _own_client else contextlib.nullcontext(client)) as c:
                resp = await c.get(
                    f"{API_BASE}/api/v1/candles",
                    params={
                        "market_id":       market_id,
                        "resolution":      resolution,
                        "start_timestamp": start_ms,
                        "end_timestamp":   now_ms,
                        "count_back":      limit,
                    }
                )
                if resp.status_code == 429:
                    wait = _backoff_base * (2 ** attempt)
                    logger.debug(f"429 {symbol}/{resolution} — retry za {wait}s")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return _parse_candles_response(resp.json(), symbol, resolution)

        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.warning(f"Blad historycznych swiec {symbol}/{resolution}: {e}")
            return 0

    logger.warning(
        f"Blad historycznych swiec {symbol}/{resolution}: "
        f"wyczerpano {_retries} prob (429)"
    )
    return 0


async def fetch_exchange_stats() -> None:
    """
    Pobierz statystyki giełdowe (ceny, zmiana 24h, wolumen).
    Wywołuj co ~30 sekund.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{API_BASE}/api/v1/exchangeStats")
            resp.raise_for_status()
            data = resp.json()

        # Zbuduj mapę lighter_symbol → stats
        stats_map: dict = {}
        for s in data.get("order_book_stats", []):
            stats_map[s["symbol"]] = s

        for our_sym in list(state.markets.keys()):
            lighter_sym = LIGHTER_SYMBOL.get(our_sym, our_sym)
            s = stats_map.get(lighter_sym)
            if not s:
                continue

            price = float(s.get("last_trade_price", 0))
            if price > 0:
                state.last_price[our_sym] = price

            state.update_stats(
                our_sym,
                change_24h=float(s.get("daily_price_change", 0)),
                volume_24h=float(s.get("daily_quote_token_volume", 0)),
            )

    except Exception as e:
        logger.debug(f"exchange_stats error: {e}")


async def fetch_funding_rate(symbol: str, market_id: int) -> None:
    """
    Pobierz ostatnią stawkę funding dla jednego tokenu.
    Wywołuj co 30 minut.
    """
    now_ms = int(time.time() * 1000)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{API_BASE}/api/v1/fundings",
                params={
                    "market_id":       market_id,
                    "resolution":      "1h",
                    "start_timestamp": now_ms - 2 * 3600 * 1000,
                    "end_timestamp":   now_ms,
                    "count_back":      3,
                }
            )
            if resp.status_code != 200:
                return
            data = resp.json()

        fundings = data.get("fundings", [])
        if fundings:
            latest = fundings[-1]
            state.update_funding(symbol, rate=float(latest.get("rate", 0)))

    except Exception as e:
        logger.debug(f"funding_rate {symbol}: {e}")


# ── Wskaźniki techniczne ───────────────────────────────────

def _calc_pivot_points(candles_buf: deque) -> dict:
    """
    Classic Pivot Points z poprzedniej zamkniętej świecy.
    Używamy 4h jako głównego timeframu dla Pivotów.
    """
    if len(candles_buf) < 2:
        return {}
    prev = candles_buf[-2]
    h, l, c = prev["h"], prev["l"], prev["c"]
    pp = (h + l + c) / 3
    return {
        "pivot_pp": round(pp,             6),
        "pivot_s1": round(2 * pp - h,     6),
        "pivot_s2": round(pp - (h - l),   6),
        "pivot_r1": round(2 * pp - l,     6),
        "pivot_r2": round(pp + (h - l),   6),
    }


def calc_indicators(symbol: str) -> dict:
    """
    Oblicz wskaźniki techniczne z buforów świec.

    Z 5m:  RSI(14), EMA(9) — szybki entry timing
    Z 15m: RSI(14), EMA(9), EMA(21), MACD, ATR(14)
    Z 4h:  EMA(21), RSI(14), ATR(14)
    Z 1d:  EMA(21), EMA(50), RSI(14)
    Pivot: z 4h
    """
    result: dict = {}

    if not HAS_TA:
        return result

    # ── Wskaźniki z 5m ────────────────────────────────────
    candles_5m = list(state.candles[symbol]["5m"])
    if len(candles_5m) >= 15:
        try:
            closes_5m = pd.Series([c["c"] for c in candles_5m])

            rsi_5m = ta.rsi(closes_5m, length=14)
            if rsi_5m is not None and not rsi_5m.empty:
                v = rsi_5m.iloc[-1]
                if pd.notna(v):
                    result["rsi_5m"] = round(float(v), 2)

            ema9_5m = ta.ema(closes_5m, length=9)
            if ema9_5m is not None and not ema9_5m.empty:
                v = ema9_5m.iloc[-1]
                if pd.notna(v):
                    result["ema_9_5m"] = round(float(v), 6)

        except Exception as e:
            logger.debug(f"Wskazniki 5m {symbol}: {e}")

    # ── Wskaźniki z 15m ───────────────────────────────────
    candles_15m = list(state.candles[symbol]["15m"])
    if len(candles_15m) >= 20:
        try:
            closes = pd.Series([c["c"] for c in candles_15m])
            highs  = pd.Series([c["h"] for c in candles_15m])
            lows   = pd.Series([c["l"] for c in candles_15m])

            rsi = ta.rsi(closes, length=14)
            if rsi is not None and not rsi.empty:
                v = rsi.iloc[-1]
                if pd.notna(v):
                    result["rsi_14"] = round(float(v), 2)

            ema9 = ta.ema(closes, length=9)
            if ema9 is not None and not ema9.empty:
                v = ema9.iloc[-1]
                if pd.notna(v):
                    result["ema_9"] = round(float(v), 6)

            ema21 = ta.ema(closes, length=21)
            if ema21 is not None and not ema21.empty:
                v = ema21.iloc[-1]
                if pd.notna(v):
                    result["ema_21"] = round(float(v), 6)

            macd_df = ta.macd(closes)
            if macd_df is not None and not macd_df.empty:
                row = macd_df.iloc[-1]
                if pd.notna(row.iloc[0]):
                    result["macd"]        = round(float(row.iloc[0]), 6)
                    result["macd_signal"] = round(float(row.iloc[2]), 6)
                    result["macd_hist"]   = round(float(row.iloc[1]), 6)

            atr = ta.atr(highs, lows, closes, length=14)
            if atr is not None and not atr.empty:
                v = atr.iloc[-1]
                if pd.notna(v):
                    result["atr_14"] = round(float(v), 6)

        except Exception as e:
            logger.debug(f"Wskazniki 15m {symbol}: {e}")

    # ── Wskaźniki z 4h ────────────────────────────────────
    candles_4h = list(state.candles[symbol]["4h"])
    if len(candles_4h) >= 21:
        try:
            closes_4h = pd.Series([c["c"] for c in candles_4h])
            highs_4h  = pd.Series([c["h"] for c in candles_4h])
            lows_4h   = pd.Series([c["l"] for c in candles_4h])

            ema21_4h = ta.ema(closes_4h, length=21)
            if ema21_4h is not None and not ema21_4h.empty:
                v = ema21_4h.iloc[-1]
                if pd.notna(v):
                    result["ema_21_4h"] = round(float(v), 6)

            rsi_4h = ta.rsi(closes_4h, length=14)
            if rsi_4h is not None and not rsi_4h.empty:
                v = rsi_4h.iloc[-1]
                if pd.notna(v):
                    result["rsi_4h"] = round(float(v), 2)

            atr_4h = ta.atr(highs_4h, lows_4h, closes_4h, length=14)
            if atr_4h is not None and not atr_4h.empty:
                v = atr_4h.iloc[-1]
                if pd.notna(v):
                    result["atr_4h"] = round(float(v), 6)

        except Exception as e:
            logger.debug(f"Wskazniki 4h {symbol}: {e}")

    # ── Wskaźniki z 1d ────────────────────────────────────
    candles_1d = list(state.candles[symbol]["1d"])
    if len(candles_1d) >= 21:
        try:
            closes_1d = pd.Series([c["c"] for c in candles_1d])

            ema21_1d = ta.ema(closes_1d, length=21)
            if ema21_1d is not None and not ema21_1d.empty:
                v = ema21_1d.iloc[-1]
                if pd.notna(v):
                    result["ema_21_1d"] = round(float(v), 6)

            ema50_1d = ta.ema(closes_1d, length=50)
            if ema50_1d is not None and not ema50_1d.empty:
                v = ema50_1d.iloc[-1]
                if pd.notna(v):
                    result["ema_50_1d"] = round(float(v), 6)

            rsi_1d = ta.rsi(closes_1d, length=14)
            if rsi_1d is not None and not rsi_1d.empty:
                v = rsi_1d.iloc[-1]
                if pd.notna(v):
                    result["rsi_1d"] = round(float(v), 2)

        except Exception as e:
            logger.debug(f"Wskazniki 1d {symbol}: {e}")

    # ── Pivot Points z 4h ─────────────────────────────────
    result.update(_calc_pivot_points(state.candles[symbol]["4h"]))

    return result


# ── Zapis snapshotu ────────────────────────────────────────

def write_snapshot():
    """
    Zapisz pełny stan rynku do market_snapshot.json.
    Wywoływane co 1 sekundę przez główną pętlę.
    """
    tokens_data = []

    for symbol in list(state.markets.keys()):
        if symbol in TOKEN_BLACKLIST:
            continue
        if symbol not in state.last_price:
            continue
        price = state.last_price[symbol]
        if price == 0.0:
            continue

        ob       = state.orderbooks.get(symbol, {"bids": [], "asks": []})
        fund     = state.funding.get(symbol,   {"rate": 0.0})
        inds     = calc_indicators(symbol)
        st       = state.stats.get(symbol,     {"change_24h": 0.0, "volume_24h": 0.0})

        # Spread z order book
        best_bid = ob["bids"][0][0] if ob["bids"] else price * 0.9995
        best_ask = ob["asks"][0][0] if ob["asks"] else price * 1.0005
        spread   = round((best_ask - best_bid) / price * 100, 4) \
                   if price > 0 else 0.0

        # Zmiana 24h liczona z otwarciem bieżącej świecy dziennej (1d)
        # API Lighter zwraca daily_price_change w nieznanym formacie — ignorujemy
        change_24h = 0.0
        candles_1d = list(state.candles[symbol].get("1d", []))
        if candles_1d and price > 0:
            open_1d = float(candles_1d[-1]["o"])
            if open_1d > 0:
                change_24h = round((price - open_1d) / open_1d * 100, 2)

        tokens_data.append({
            "symbol":    symbol,
            "market_id": state.markets.get(symbol, {}).get("market_id", 0),

            # Cena i zmiana
            "price":      price,
            "change_24h": change_24h,
            "volume_24h": st["volume_24h"],

            # Order book
            "bid":        round(best_bid, 8),
            "ask":        round(best_ask, 8),
            "spread_pct": spread,
            "order_book": {
                "bids": [[e[0], e[1]] for e in ob["bids"][:10]],
                "asks": [[e[0], e[1]] for e in ob["asks"][:10]],
            },

            # Funding
            "funding_rate": fund["rate"],

            # Tylko ostatnie 25 świec 1m (potrzebne przez signal_scanner do volume spike)
            "candles": {
                "1m": list(state.candles[symbol]["1m"])[-25:],
            },

            # Wskaźniki wyliczone lokalnie
            "indicators": inds,
        })

    snapshot = {
        "updated_at":  datetime.now(timezone.utc).isoformat(),
        "mode":        settings.TRADING_MODE,
        "tokens":      tokens_data,
        "token_count": len(tokens_data),
    }

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot))


# ── WebSocket — parsowanie wiadomości ──────────────────────

async def handle_ws_message(msg: str, market_id_to_symbol: dict):
    """
    Parsuj wiadomość z WebSocket i aktualizuj MarketState.
    Obsługuje: subscribed/order_book, update/order_book.

    Format kanału: "order_book:{market_id}" (kolon, nie slash).
    """
    try:
        data     = json.loads(msg)
        msg_type = data.get("type", "")

        if msg_type == "ping":
            return  # pong obsługuje biblioteka websockets przez ping_interval

        channel = data.get("channel", "")
        # channel = "order_book:1" → market_id = 1
        if not channel.startswith("order_book:"):
            return

        market_id_str = channel.split(":", 1)[1]
        market_id     = int(market_id_str)
        symbol        = market_id_to_symbol.get(market_id)
        if not symbol:
            return

        ob = data.get("order_book", {})
        if not ob:
            return

        raw_bids = [[float(b["price"]), float(b["size"])]
                    for b in ob.get("bids", [])]
        raw_asks = [[float(a["price"]), float(a["size"])]
                    for a in ob.get("asks", [])]

        if msg_type == "subscribed/order_book":
            # Pełny snapshot — zastąp całkowicie
            state.update_orderbook_snapshot(symbol, raw_bids, raw_asks)

        elif msg_type == "update/order_book":
            # Delta update — scal z istniejącym
            state.apply_orderbook_update(symbol, raw_bids, raw_asks)

    except json.JSONDecodeError:
        pass
    except Exception as e:
        logger.debug(f"handle_ws_message error: {e}")


# ── REST polling — świece i statystyki ────────────────────

async def candle_poll_loop(market_ids: dict):
    """
    Odświeżaj świece przez REST polling.
    Każdy timeframe odświeżany co swój CANDLE_POLL_INTERVAL.
    Polling: 1 retry, backoff 1s, semaphore 4 — nie blokuje event loop.
    """
    last_poll = {res: 0.0 for res in RESOLUTIONS}
    _sem = asyncio.Semaphore(4)

    async def _poll_one(sym: str, mid: int, res: str, client: httpx.AsyncClient):
        async with _sem:
            try:
                await fetch_historical_candles(
                    sym, mid, res,
                    _retries=1, _backoff_base=1.0, client=client,
                )
            except Exception:
                pass

    async with httpx.AsyncClient(
        timeout=12,
        limits=httpx.Limits(max_connections=6, max_keepalive_connections=4),
    ) as shared_client:
        while True:
            now = time.time()
            for res in RESOLUTIONS:
                if now - last_poll[res] >= CANDLE_POLL_INTERVAL[res]:
                    tasks = [
                        _poll_one(sym, mid, res, shared_client)
                        for sym, mid in market_ids.items()
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    last_poll[res] = time.time()
                    logger.debug(f"Swiec odswiezono: {res} ({len(tasks)} tokenow)")
            await asyncio.sleep(5)


async def snapshot_writer_loop():
    """Zapisuj snapshot co 5 sekund — w osobnym wątku, nie blokuje event loop."""
    loop = asyncio.get_event_loop()
    while True:
        await asyncio.sleep(5)
        try:
            await loop.run_in_executor(None, write_snapshot)
        except Exception:
            pass


async def stats_poll_loop(market_ids: dict):
    """
    Odświeżaj statystyki giełdowe (ceny, zmiana, wolumen) co 30s.
    Odświeżaj funding co 30 minut.
    """
    last_stats   = 0.0
    last_funding = 0.0

    while True:
        now = time.time()

        if now - last_stats >= 30:
            await fetch_exchange_stats()
            last_stats = now

        if now - last_funding >= 1800:
            for symbol, market_id in market_ids.items():
                await fetch_funding_rate(symbol, market_id)
                await asyncio.sleep(0.1)  # rate limit
            last_funding = now

        await asyncio.sleep(5)


# ── WebSocket — główna pętla z auto-reconnect ──────────────

async def websocket_loop(market_ids: dict):
    """
    Połącz z Lighter WebSocket, subskrybuj order book dla wszystkich tokenów.
    Automatyczny reconnect przy rozłączeniu.
    """
    market_id_to_symbol = {v: k for k, v in market_ids.items()}

    while True:
        try:
            logger.info(f"Lacze z WebSocket: {WS_URL}")
            async with websockets.connect(
                WS_URL,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=10 * 1024 * 1024
            ) as ws:
                # Poczekaj na potwierdzenie połączenia
                connected_msg = await asyncio.wait_for(ws.recv(), timeout=10)
                connected = json.loads(connected_msg)
                if connected.get("type") != "connected":
                    logger.warning(f"Nieoczekiwana wiadomosc powitalna: {connected}")
                else:
                    logger.info(
                        f"WebSocket polaczony "
                        f"(session_id={connected.get('session_id', '?')[:8]}...)"
                    )

                # Subskrybuj order book dla każdego tokenu
                sub_count = 0
                for symbol, market_id in market_ids.items():
                    await ws.send(json.dumps({
                        "type":    "subscribe",
                        "channel": f"order_book/{market_id}"
                    }))
                    sub_count += 1
                    await asyncio.sleep(0.05)  # małe opóźnienie między sub

                logger.info(
                    f"Subskrypcje wyslane: {sub_count} order_book "
                    f"({len(market_ids)} tokenow)"
                )

                # Pętla odbioru wiadomości + snapshot co 1s
                last_snapshot = 0.0
                async for message in ws:
                    await handle_ws_message(message, market_id_to_symbol)

                    now = time.time()
                    if now - last_snapshot >= 1.0:
                        write_snapshot()
                        last_snapshot = now

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WS rozlaczony ({e}) — reconnect za 5s")
            await asyncio.sleep(5)
        except OSError as e:
            logger.error(f"WS blad sieciowy ({e}) — reconnect za 10s")
            await asyncio.sleep(10)
        except asyncio.TimeoutError:
            logger.warning("WS timeout — reconnect za 5s")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"WS nieoczekiwany blad ({e}) — reconnect za 15s")
            await asyncio.sleep(15)


# ── Publiczne API dla innych modułów ──────────────────────


def get_token_data(token: str) -> Optional[dict]:
    """Synchroniczny dostęp do pełnych danych tokenu."""
    try:
        snap = json.loads(SNAPSHOT_PATH.read_text())
        return next(
            (t for t in snap.get("tokens", [])
             if t["symbol"] == token.upper()),
            None
        )
    except Exception:
        return None


def get_all_tokens() -> list:
    """Synchroniczny dostęp do wszystkich tokenów — z state jeśli załadowany, fallback plik."""
    if state.markets:
        tokens = []
        for symbol in list(state.markets.keys()):
            if symbol in TOKEN_BLACKLIST:
                continue
            price = state.last_price.get(symbol, 0.0)
            if price == 0.0:
                continue
            inds = calc_indicators(symbol)
            st   = state.stats.get(symbol, {"change_24h": 0.0, "volume_24h": 0.0})
            # Licz change_24h z 1d candle (jak write_snapshot)
            change_24h = st.get("change_24h", 0.0)
            candles_1d = list(state.candles[symbol].get("1d", []))
            if candles_1d and price > 0:
                open_1d = float(candles_1d[-1]["o"])
                if open_1d > 0:
                    change_24h = round((price - open_1d) / open_1d * 100, 2)
            tokens.append({
                "symbol":     symbol,
                "price":      price,
                "change_24h": change_24h,
                "volume_24h": st.get("volume_24h", 0.0),
                "indicators": inds,
            })
        return tokens
    try:
        snap = json.loads(SNAPSHOT_PATH.read_text())
        return snap.get("tokens", [])
    except Exception:
        return []


def get_current_price(token: str) -> float:
    """Synchroniczny dostęp do aktualnej ceny — state → snapshot → 0."""
    sym = token.upper()
    price = state.last_price.get(sym, 0.0)
    if price > 0:
        return price
    # Fallback: snapshot (obsługuje tokeny poniżej progu wolumenu)
    try:
        snap = json.loads(SNAPSHOT_PATH.read_text())
        for t in snap.get("tokens", []):
            if t.get("symbol") == sym:
                p = float(t.get("price") or 0)
                if p > 0:
                    return p
    except Exception:
        pass
    return 0.0


# ── Punkt wejścia ──────────────────────────────────────────

async def run():
    """Uruchom market feed — punkt wejścia z main.py."""
    logger.info("=" * 50)
    logger.info("MARKET FEED — start")
    logger.info(f"Tryb:       {settings.TRADING_MODE}")
    logger.info(f"Min vol:    ${settings.MIN_VOLUME_USD:,.0f}")
    logger.info(f"TF:         {RESOLUTIONS}")
    logger.info("=" * 50)

    # 1. Odkryj wszystkie pary z wystarczającym wolumenem
    market_ids = await discover_markets()
    if not market_ids:
        raise RuntimeError(
            "Nie mozna pobrac market IDs z Lighter API.\n"
            "Sprawdz polaczenie z internetem i dostepnosc:\n"
            f"  {API_BASE}/api/v1/orderBooks"
        )

    # 2. Inicjalizuj stan dla każdego tokenu
    for our_sym, market_id in market_ids.items():
        lighter_sym = LIGHTER_SYMBOL.get(our_sym, our_sym)
        state.init_token(our_sym, market_id, lighter_sym)

    # 3. Załaduj dane historyczne (REST) — sekwencyjnie, 0.3s między requestami
    n_req = len(market_ids) * len(RESOLUTIONS)
    logger.info(f"Laduje dane historyczne przez REST ({n_req} zapytan, sekwencyjnie)...")
    all_tasks = [
        (symbol, mid, res)
        for symbol, mid in market_ids.items()
        for res in RESOLUTIONS
    ]
    REQUEST_TIMEOUT = 15
    counts: list[int] = []
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        limits=httpx.Limits(max_connections=5, max_keepalive_connections=3),
    ) as shared_client:
        for idx, (sym, mid, res) in enumerate(all_tasks):
            try:
                n = await asyncio.wait_for(
                    fetch_historical_candles(sym, mid, res, client=shared_client),
                    timeout=REQUEST_TIMEOUT + 5,
                )
                counts.append(n)
            except Exception:
                counts.append(0)
            if idx < len(all_tasks) - 1:
                await asyncio.sleep(0.3)

    total = sum(counts)
    logger.info(
        f"Dane historyczne zaladowane: {total} swiec "
        f"({len(market_ids)} tokenow x {len(RESOLUTIONS)} TF)"
    )
    _historical_ready.set()  # sygnał dla Supervisora: dane gotowe

    # 4. Pobierz statystyki wstępne (ceny, zmiana 24h, wolumen)
    await fetch_exchange_stats()

    # 5. Inicjalizuj last_price z 1m candles jeśli brakuje
    for symbol in market_ids:
        if state.last_price[symbol] == 0.0:
            buf = state.candles[symbol]["1m"]
            if buf:
                state.last_price[symbol] = buf[-1]["c"]

    # 6. Pierwszy snapshot (przed WebSocket)
    write_snapshot()
    logger.info(f"Snapshot zapisany: {SNAPSHOT_PATH}")

    # Sprawdź ile tokenów ma ceny
    with_prices = sum(
        1 for sym in market_ids if state.last_price.get(sym, 0) > 0
    )
    logger.info(f"Tokeny z cenami: {with_prices}/{len(market_ids)}")

    # 7. Uruchom równolegle: WebSocket + REST polling
    logger.info("Uruchamiam WebSocket + polling loops...")
    await asyncio.gather(
        websocket_loop(market_ids),
        candle_poll_loop(market_ids),
        stats_poll_loop(market_ids),
        snapshot_writer_loop(),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    asyncio.run(run())
