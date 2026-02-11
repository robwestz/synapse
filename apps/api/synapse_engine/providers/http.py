from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class ProviderError(RuntimeError):
    pass


@dataclass
class RetryPolicy:
    retries: int = 2
    backoff_seconds: float = 0.8
    backoff_multiplier: float = 2.0
    timeout_seconds: float = 30.0


def _is_retryable(status_code: int) -> bool:
    return status_code in {408, 409, 425, 429, 500, 502, 503, 504}


class HttpClient:
    """Small wrapper around requests with retries.

    NOTE: This project stays intentionally lightweight (no httpx/tenacity dependency).
    """

    def __init__(self, retry: Optional[RetryPolicy] = None):
        self.retry = retry or RetryPolicy()

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Any = None,
        auth: Any = None,
    ) -> Dict[str, Any]:
        last_err: Optional[Exception] = None
        delay = self.retry.backoff_seconds

        for attempt in range(self.retry.retries + 1):
            try:
                r = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    auth=auth,
                    timeout=self.retry.timeout_seconds,
                )

                if r.status_code >= 400:
                    # Try to parse JSON error payload if any.
                    msg = None
                    try:
                        msg = r.json()
                    except Exception:
                        msg = r.text[:500]

                    if attempt < self.retry.retries and _is_retryable(r.status_code):
                        time.sleep(delay)
                        delay *= self.retry.backoff_multiplier
                        continue
                    raise ProviderError(f"HTTP {r.status_code} from {url}: {msg}")

                # Success
                if not r.text:
                    return {}
                try:
                    return r.json()
                except json.JSONDecodeError:
                    return {"raw": r.text}

            except Exception as e:
                last_err = e
                if attempt < self.retry.retries:
                    time.sleep(delay)
                    delay *= self.retry.backoff_multiplier
                    continue
                break

        raise ProviderError(f"Request failed: {method} {url}: {last_err}")
