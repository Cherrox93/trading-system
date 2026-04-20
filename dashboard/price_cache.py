"""
Wspólny cache cen tokenów spoza market feedu.
Aktualizowany asynchronicznie co 10s przez background task w main.py.
Czytany synchronicznie przez _build_snapshot i _get_open_position.
"""
_prices: dict[str, float] = {}


def get(token: str) -> float:
    return _prices.get(token, 0.0)


def update(prices: dict[str, float]) -> None:
    _prices.clear()
    _prices.update(prices)
