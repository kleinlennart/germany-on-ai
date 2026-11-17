"""A polite, cached HTTP client shared by every source.

- Requests run one at a time, with a minimum interval between them.
- Transient failures (5xx, 429, network errors, cut-off JSON) are retried with back-off.
- Every parsed response is cached under data/raw. Live runs only write the cache;
  offline runs only read it, so a live run never serves a stale response. The one
  exception is an explicit resume, which reuses responses younger than a given age.
"""

import hashlib
import json
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}

Params = list[tuple[str, str]]


class FetchError(RuntimeError):
    pass


class Retryable(FetchError):
    pass


class Throttled(Retryable):
    pass


class CachedClient:
    def __init__(
        self,
        base_url: str,
        *,
        cache_dir: Path,
        headers: dict[str, str] | None = None,
        offline: bool = False,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 6,
        min_interval: float = 1.0,
        reuse_cache_younger_than: timedelta | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.cache_dir = cache_dir
        self.offline = offline
        self.max_attempts = max_attempts
        self.min_interval = min_interval
        self.reuse_age = reuse_cache_younger_than
        self.sleep = sleep
        self.clock = clock
        self._last_request = 0.0
        self.http = httpx.Client(
            base_url=base_url,
            headers=headers or {},
            timeout=httpx.Timeout(60.0),
            transport=transport,
        )

    def get(self, endpoint: str, params: Params | None = None) -> Any:
        params = sorted(params or [])
        path = self._cache_path(endpoint, params)
        if self.offline:
            if not path.exists():
                raise FetchError(f"not cached: {endpoint} {params}")
            return json.loads(path.read_text(encoding="utf-8"))
        if self.reuse_age and path.exists():
            age = self.clock() - path.stat().st_mtime
            if age < self.reuse_age.total_seconds():
                return json.loads(path.read_text(encoding="utf-8"))
        data = self._fetch(endpoint, params)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        return data

    def check(self, response: httpx.Response) -> None:
        """Source-specific signs of throttling; override where a source has them."""

    def _fetch(self, endpoint: str, params: Params) -> Any:
        url = f"/{endpoint}" if endpoint else ""
        for attempt in range(1, self.max_attempts + 1):
            wait = self._last_request + self.min_interval - self.clock()
            if wait > 0:
                self.sleep(wait)
            self._last_request = self.clock()
            try:
                response = self.http.get(url, params=tuple(params))
                self.check(response)
                if response.status_code in RETRY_STATUS:
                    raise Retryable(f"HTTP {response.status_code}")
                if response.status_code != 200:
                    raise FetchError(
                        f"{endpoint}: unexpected HTTP {response.status_code}"
                    )
                # A cut-off body fails to parse; retry it like a transient error.
                return response.json()
            except (httpx.TransportError, json.JSONDecodeError, Retryable) as error:
                if attempt == self.max_attempts:
                    raise FetchError(
                        f"{endpoint} failed after {attempt} attempts: {error}"
                    ) from error
                # Throttling lifts slowly; back off for minutes rather than seconds.
                self.sleep(30 * attempt if isinstance(error, Throttled) else 2**attempt)
        raise AssertionError("unreachable")

    def _cache_path(self, endpoint: str, params: Params) -> Path:
        key = hashlib.sha256(json.dumps([endpoint, params]).encode()).hexdigest()[:32]
        return self.cache_dir / (endpoint or "root") / f"{key}.json"
