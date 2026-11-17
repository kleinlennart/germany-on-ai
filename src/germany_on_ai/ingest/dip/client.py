"""DIP API client, following the rules in DIP's API documentation:

- requests run one at a time, at most one every two seconds (DIP asks for at most 25
  concurrent requests, and its bot protection throttles fast clients);
- list endpoints page with a cursor until the cursor stops changing;
- the full set is checked against numFound.

Caching, retries and pacing come from the shared client (ingest/http.py).
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx

from germany_on_ai.ingest.http import CachedClient, FetchError, Params, Throttled

BASE_URL = "https://search.dip.bundestag.de/api/v1"
CACHE_DIR = Path("data/raw/dip")
MIN_INTERVAL = 2.0
# When throttled, DIP redirects to a bot-protection challenge instead of answering.
CHALLENGE_PATH = "/.enodia/"

DipError = FetchError

__all__ = ["DipClient", "DipError", "Params"]


class DipClient(CachedClient):
    def __init__(
        self,
        api_key: str | None,
        *,
        cache_dir: Path = CACHE_DIR,
        offline: bool = False,
        min_interval: float = MIN_INTERVAL,
        **kwargs: Any,
    ) -> None:
        if not offline and not api_key:
            raise DipError("DIP_API_KEY is not set")
        super().__init__(
            BASE_URL,
            cache_dir=cache_dir,
            headers={"Authorization": f"ApiKey {api_key}"} if api_key else {},
            offline=offline,
            min_interval=min_interval,
            **kwargs,
        )

    def check(self, response: httpx.Response) -> None:
        if CHALLENGE_PATH in response.headers.get("location", ""):
            raise Throttled("throttled by DIP's bot protection")

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
