"""Frankfurter 幣別清單與匯率換算。"""
from decimal import Decimal, InvalidOperation
import re

from .common import UpstreamError, get_json

CURRENCY_URL = "https://api.frankfurter.dev/v2/currencies"
RATES_URL = "https://api.frankfurter.dev/v2/rates"
POPULAR = ["TWD", "USD", "EUR", "JPY", "GBP", "KRW", "AUD", "HKD", "SGD", "CAD", "CHF", "CNY", "THB", "NZD"]


class CurrencyError(Exception):
    pass


def get_currencies():
    """讀取來源清單；來源暫時失效時使用常見幣別供表單操作。"""
    try:
        data = get_json(CURRENCY_URL, cache_seconds=86400)
        return sorted(data.keys()) if isinstance(data, dict) else POPULAR
    except UpstreamError:
        return POPULAR


def convert_currency(raw_amount, source, target):
    try:
        if not re.fullmatch(r"\d{1,10}(?:\.\d{1,2})?", raw_amount or ""):
            raise CurrencyError("請輸入大於 0 且最多兩位小數的金額。")
        amount = Decimal(raw_amount)
        if amount <= 0:
            raise CurrencyError("金額必須大於 0。")
        currencies = get_currencies()
        if source not in currencies or target not in currencies:
            raise CurrencyError("目前匯率來源不支援所選幣別，請改選常見幣別後再試。")
        if source == target:
            rate, date = Decimal("1"), "同幣別"
        else:
            data = get_json(RATES_URL, params={"base": source, "quotes": target}, cache_seconds=1800)
            if isinstance(data, list):
                row = next(item for item in data if item.get("quote") == target)
                rate, date = Decimal(str(row["rate"])), row.get("date", "")
            else:
                row = data.get("rates", {}).get(target)
                rate, date = Decimal(str(row)), data.get("date", "")
        return {"amount": amount, "source": source, "target": target,
                "rate": rate, "converted": (amount * rate).quantize(Decimal("0.01")), "date": date}
    except CurrencyError:
        raise
    except UpstreamError as exc:
        raise CurrencyError(str(exc) + " TWD 或部分冷門幣別可能暫無資料。") from exc
    except (InvalidOperation, KeyError, TypeError, StopIteration) as exc:
        raise CurrencyError("目前無法取得這組幣別的匯率，請稍後再試。") from exc
