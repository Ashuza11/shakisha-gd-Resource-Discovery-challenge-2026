from __future__ import annotations

from typing import Tuple

import requests


def check_url(url: str, timeout: int = 8) -> Tuple[str, int | None]:
    if not url or not isinstance(url, str):
        return "invalid", None
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        code = response.status_code
        if code < 400:
            return "available", code
        return "error", code
    except requests.RequestException:
        return "unreachable", None

