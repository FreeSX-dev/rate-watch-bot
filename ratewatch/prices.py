"""Получение курсов с CoinGecko (без ключа, публичный API)."""

from __future__ import annotations

import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


class PriceFetchError(RuntimeError):
    pass


def get_price(coin_id: str, vs_currency: str = "usd", timeout: float = 10.0) -> float:
    """Возвращает текущую цену `coin_id` в `vs_currency`.

    Пример: get_price("bitcoin", "usd") -> 67230.12
    """
    try:
        response = requests.get(
            COINGECKO_URL,
            params={"ids": coin_id, "vs_currencies": vs_currency},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PriceFetchError(f"Не удалось получить курс {coin_id}: {exc}") from exc

    data = response.json()
    try:
        return float(data[coin_id][vs_currency])
    except (KeyError, TypeError, ValueError) as exc:
        raise PriceFetchError(f"Неожиданный ответ API для {coin_id}/{vs_currency}: {data}") from exc
