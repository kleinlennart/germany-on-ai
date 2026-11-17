import json
from datetime import timedelta
from pathlib import Path

import httpx
import pytest

from germany_on_ai.ingest.dip.client import DipClient, DipError

PAGE = json.loads(Path("tests/fixtures/dip/vorgang_page.json").read_text())


def client_for(handler, tmp_path: Path, **kwargs) -> DipClient:
    return DipClient(
        "test-key",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
        min_interval=0,
        **kwargs,
    )


def paged(request: httpx.Request) -> httpx.Response:
    # An empty page repeating the cursor is DIP's end-of-results signal.
    if request.url.params.get("cursor") == "c1":
        return httpx.Response(
            200, json={"numFound": 2, "documents": [], "cursor": "c1"}
        )
    return httpx.Response(200, json=PAGE)


def test_query_follows_cursor_until_it_stops(tmp_path: Path):
    ids = [d["id"] for d in client_for(paged, tmp_path).query("vorgang", [])]
    assert ids == [d["id"] for d in PAGE["documents"]]


def test_query_fails_when_results_are_incomplete(tmp_path: Path):
    def short(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=PAGE | {"numFound": 3, "cursor": None})

    with pytest.raises(DipError, match="incomplete"):
        list(client_for(short, tmp_path).query("vorgang", []))


@pytest.mark.parametrize(
    "failure",
    [
        httpx.Response(503),
        httpx.Response(200, content=b'{"numFound": 2, "docu'),
        httpx.Response(303, headers={"location": "/.enodia/challenge?redirect=x"}),
    ],
    ids=["server-error", "truncated-body", "throttled"],
)
def test_transient_failures_are_retried(tmp_path: Path, failure: httpx.Response):
    responses = iter([failure, httpx.Response(200, json=PAGE)])
    client = client_for(lambda request: next(responses), tmp_path)
    assert client.get("vorgang")["numFound"] == 2


def test_gives_up_after_max_attempts(tmp_path: Path):
    client = client_for(lambda request: httpx.Response(503), tmp_path, max_attempts=2)
    with pytest.raises(DipError, match="after 2 attempts"):
        client.get("vorgang")


def test_offline_reads_only_what_a_live_run_cached(tmp_path: Path):
    client_for(paged, tmp_path).get("vorgang", [("f.titel", "KI")])
    offline = DipClient(None, cache_dir=tmp_path, offline=True)
    assert offline.get("vorgang", [("f.titel", "KI")]) == PAGE
    with pytest.raises(DipError, match="not cached"):
        offline.get("vorgang", [("f.titel", "other")])


def test_api_key_is_sent_as_header(tmp_path: Path):
    seen = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["Authorization"])
        return httpx.Response(200, json=PAGE)

    client_for(record, tmp_path).get("vorgang")
    assert seen == ["ApiKey test-key"]


def test_other_http_errors_fail_without_retry(tmp_path: Path):
    calls = []

    def not_found(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(404)

    with pytest.raises(DipError, match="HTTP 404"):
        client_for(not_found, tmp_path).get("vorgang")
    assert len(calls) == 1


def test_resume_reuses_recent_cache_only(tmp_path: Path):
    client_for(paged, tmp_path).get("vorgang")

    def offline(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should have used the cache")

    resumed = client_for(offline, tmp_path, reuse_cache_younger_than=timedelta(hours=1))
    assert resumed.get("vorgang") == PAGE
    stale = client_for(paged, tmp_path, reuse_cache_younger_than=timedelta(seconds=0))
    assert stale.get("vorgang") == PAGE
