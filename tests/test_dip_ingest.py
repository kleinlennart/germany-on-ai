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


def test_interpellation_papers_pair_questions_with_answers():
    from germany_on_ai.ingest.dip.ingest import interpellation_papers

    def step(vorgang, position, typ="Kleine Anfrage", doc="Drucksache", id_="1"):
        return {
            "vorgang_id": vorgang,
            "vorgangsposition": position,
            "vorgangstyp": typ,
            "fundstelle": {"dokumentart": doc, "id": id_},
        }

    positions = [
        step("a", "Antwort", id_="20"),
        step("a", "Kleine Anfrage", id_="10"),  # the questions, not the answer
        step("b", "Antwort", id_="30"),  # earlier term
        step("c", "Antwort", typ="Antrag", id_="40"),  # not an interpellation
        step("d", "Große Anfrage", typ="Große Anfrage", id_="4"),
        step("d", "Ergänzende Antwort", typ="Große Anfrage", id_="5"),
        step("d", "Ergänzende Antwort", typ="Große Anfrage", id_="5"),  # duplicate
        step("e", "Antwort", id_="60"),  # no question paper on record
    ]
    wp_of = {"a": 21, "b": 20, "c": 21, "d": 21, "e": 21}
    assert interpellation_papers(positions, wp_of, [21]) == [("4", "5"), ("10", "20")]
