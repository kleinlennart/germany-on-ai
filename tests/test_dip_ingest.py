import json
from datetime import UTC, datetime

from germany_on_ai.ingest.dip.ingest import load_fetch_filter, vorgang_queries
from germany_on_ai.ingest.dip.spec import LOCK_PATH, documented_parameters


def test_every_query_covers_all_electoral_terms():
    fetch_filter = load_fetch_filter()
    for params in vorgang_queries(fetch_filter, since=None):
        terms = [v for k, v in params if k == "f.wahlperiode"]
        assert terms == [str(wp) for wp in fetch_filter.wahlperioden]


def test_incremental_start_is_sent_in_german_time():
    since = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
    params = vorgang_queries(load_fetch_filter(), since)[0]
    assert ("f.aktualisiert.start", "2026-07-01T12:00:00") in params


def test_queries_use_only_locked_parameters():
    lock = json.loads(LOCK_PATH.read_text())
    used = {
        k
        for params in vorgang_queries(load_fetch_filter(), datetime.now(UTC))
        for k, _ in params
    }
    assert used | {"cursor"} <= set(lock["parameters_used"]["/vorgang"])


def test_documented_parameters_resolves_refs():
    spec = {
        "components": {"parameters": {"Titel": {"name": "f.titel"}}},
        "paths": {
            "/vorgang": {
                "get": {"parameters": [{"$ref": "#/x/Titel"}, {"name": "cursor"}]}
            }
        },
    }
    assert documented_parameters(spec) == {"/vorgang": {"f.titel", "cursor"}}
