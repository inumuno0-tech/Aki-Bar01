"""共用 HTTP 請求與無伺服器記憶體快取。"""
from threading import Lock
from time import monotonic

import requests

TIMEOUT = 8
_cache = {}
_cache_lock = Lock()


class UpstreamError(Exception):
    """外部資料來源暫時無法提供可用資料。"""


def get_json(url, *, params=None, cache_seconds=300, headers=None):
    """取得 JSON；依網址與參數快取，快取僅存在目前執行個體記憶體。"""
    key = (url, tuple(sorted((params or {}).items())))
    now = monotonic()
    with _cache_lock:
        entry = _cache.get(key)
        if entry and entry[0] > now:
            return entry[1]
    request_headers = {"User-Agent": "WanderDesk-StudentProject/1.0 (contact@example.com)"}
    request_headers.update(headers or {})
    try:
        response = requests.get(url, params=params, headers=request_headers, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, (dict, list)):
            raise ValueError("回應格式不正確")
    except requests.Timeout as exc:
        raise UpstreamError("資料來源回應逾時，請稍後再試。") from exc
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "未知"
        raise UpstreamError(f"資料來源暫時無法使用（HTTP {status}），請稍後再試。") from exc
    except (requests.RequestException, ValueError) as exc:
        raise UpstreamError("目前無法取得資料，請檢查網路後稍後再試。") from exc
    with _cache_lock:
        _cache[key] = (now + cache_seconds, payload)
        if len(_cache) > 128:
            for old_key, value in list(_cache.items()):
                if value[0] <= now:
                    _cache.pop(old_key, None)
            while len(_cache) > 128:
                _cache.pop(next(iter(_cache)))
    return payload
