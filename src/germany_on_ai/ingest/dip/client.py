"""DIP API client, following the rules in DIP's API documentation:

- requests run one at a time, at most one every two seconds (DIP asks for at most 25
  concurrent requests, and its bot protection throttles fast clients);
- list endpoints page with a cursor until the cursor stops changing;
- the full set is checked against numFound.

Every parsed response is cached under data/raw. Live runs only write the cache;
offline runs only read it, so a live run never serves a stale page. The one
exception is an explicit resume, which reuses responses younger than a given age.
"""

import hashlib
import json
import time
from collections.abc import Callable, Iterator
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://search.dip.bundestag.de/api/v1"
CACHE_DIR = Path("data/raw/dip")
RETRY_STATUS = {429, 500, 502, 503, 504}
MIN_INTERVAL = 2.0
# When throttled, DIP redirects to a bot-protection challenge instead of answering.
CHALLENGE_PATH = "/.enodia/"

Params = list[tuple[str, str]]


class DipError(RuntimeError):
    pass


class Retryable(DipError):
    pass


class Throttled(Retryable):
    pass


class DipClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        cache_dir: Path = CACHE_DIR,
        offline: bool = False,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 6,
        min_interval: float = MIN_INTERVAL,
        reuse_cache_younger_than: timedelta | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not offline and not api_key:
            raise DipError("DIP_API_KEY is not set")
        self.cache_dir = cache_dir
        self.offline = offline
        self.max_attempts = max_attempts
        self.min_interval = min_interval
        self.reuse_age = reuse_cache_younger_than
        self.sleep = sleep
        self.clock = clock
        self._last_request = 0.0
        self.http = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"ApiKey {api_key}"} if api_key else {},
            timeout=httpx.Timeout(60.0),
            transport=transport,
        )

    def get(self, endpoint: str, params: Params | None = None) -> dict[str, Any]:
        params = sorted(params or [])
        path = self._cache_path(endpoint, params)
        if self.offline:
            if not path.exists():
                raise DipError(f"not cached: {endpoint} {params}")
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

    def query(self, endpoint: str, params: Params) -> Iterator[dict[str, Any]]:
        """Yield every matching entity, then check the total against numFound."""
        seen: set[str] = set()
        cursor: str | None = None
        num_found = 0
        while True:
            page_params = params + ([("cursor", cursor)] if cursor else [])
            page = self.get(endpoint, page_params)
            num_found = page["numFound"]
            for document in page["documents"]:
                if document["id"] not in seen:
                    seen.add(document["id"])
                    yield document
            next_cursor = page.get("cursor")
            if not page["documents"] or next_cursor == cursor:
                break
            cursor = next_cursor
        if len(seen) != num_found:
            raise DipError(
                f"incomplete result for {endpoint} {params}: "
                f"{len(seen)} unique of {num_found} found"
            )

    def _fetch(self, endpoint: str, params: Params) -> dict[str, Any]:
        for attempt in range(1, self.max_attempts + 1):
            wait = self._last_request + self.min_interval - self.clock()
            if wait > 0:
                self.sleep(wait)
            self._last_request = self.clock()
            try:
                response = self.http.get(f"/{endpoint}", params=tuple(params))
                if CHALLENGE_PATH in response.headers.get("location", ""):
                    raise Throttled("throttled by DIP's bot protection")
                if response.status_code in RETRY_STATUS:
                    raise Retryable(f"HTTP {response.status_code}")
                if response.status_code != 200:
                    raise DipError(
                        f"{endpoint}: unexpected HTTP {response.status_code}"
                    )
                # A cut-off body fails to parse; retry it like a transient error.
                return response.json()
            except (httpx.TransportError, json.JSONDecodeError, Retryable) as error:
                if attempt == self.max_attempts:
                    raise DipError(
                        f"{endpoint} failed after {attempt} attempts: {error}"
                    ) from error
                # Throttling lifts slowly; back off for minutes rather than seconds.
                self.sleep(30 * attempt if isinstance(error, Throttled) else 2**attempt)
        raise AssertionError("unreachable")

    def _cache_path(self, endpoint: str, params: Params) -> Path:
        key = hashlib.sha256(json.dumps([endpoint, params]).encode()).hexdigest()[:32]
        return self.cache_dir / endpoint / f"{key}.json"
