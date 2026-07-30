from __future__ import annotations

import random
import time
from collections.abc import Mapping
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.6,
        status_forcelist=(408, 425, 429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    value = requests.Session()
    value.mount("https://", adapter)
    value.mount("http://", adapter)
    value.headers.update(
        {
            "User-Agent": "A-SCOPE/0.2 (+https://github.com/BullbaseGuy/a-scope-reearch)",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
        }
    )
    return value


def get_json(
    value: requests.Session,
    url: str,
    *,
    params: Mapping[str, object] | None = None,
    attempts: int = 2,
    timeout: tuple[int, int] = (10, 35),
) -> Any:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = value.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < attempts:
                time.sleep(min(4.0, 0.7 * (2 ** (attempt - 1))) + random.random() * 0.2)
    raise RuntimeError(f"GET failed: {url}: {last}") from last
