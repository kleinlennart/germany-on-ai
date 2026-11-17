import httpx
import pytest

from germany_on_ai.ingest.eu.ingest import (
    Act,
    Procedure,
    cellar_client,
    ep_client,
    fetch_act_dates,
    fetch_procedure,
    load_fetch_filter,
)
from germany_on_ai.ingest.http import FetchError


def client(factory, handler, tmp_path):
    c = factory(
        transport=httpx.MockTransport(handler), min_interval=0, sleep=lambda _: None
    )
    c.cache_dir = tmp_path
    return c


def binding(celex, **dates):
    row = {"celex": {"value": celex}}
    row.update({k: {"value": v} for k, v in dates.items()})
    return row


def test_procedure_reference_maps_to_api_id():
    assert Procedure(reference="2021/0106(COD)", short="AI Act").api_id == "2021-0106"


def test_fetch_filter_loads():
    assert load_fetch_filter().procedures


def test_wrong_procedure_in_response_is_rejected(tmp_path):
    def handler(request):
        return httpx.Response(200, json={"data": [{"label": "2025/0360(COD)"}]})

    procedure = Procedure(reference="2025/0359(COD)", short="Digital Omnibus on AI")
    with pytest.raises(FetchError, match="unexpected response"):
        fetch_procedure(client(ep_client, handler, tmp_path), procedure)


def test_act_dates_are_grouped_sorted_and_deduplicated(tmp_path):
    rows = [
        binding(
            "32024R1689",
            date_signature="2024-06-13",
            date_entry_into_force="2026-08-02",
        ),
        binding(
            "32024R1689",
            date_signature="2024-06-13",
            date_entry_into_force="2024-08-01",
        ),
    ]

    def handler(request):
        return httpx.Response(200, json={"results": {"bindings": rows}})

    dates = fetch_act_dates(
        client(cellar_client, handler, tmp_path),
        [Act(celex="32024R1689", short="AI Act")],
    )
    assert dates["32024R1689"] == {
        "celex": "32024R1689",
        "date_signature": ["2024-06-13"],
        "date_entry_into_force": ["2024-08-01", "2026-08-02"],
    }


def test_unknown_act_fails_loudly(tmp_path):
    def handler(request):
        return httpx.Response(200, json={"results": {"bindings": []}})

    with pytest.raises(FetchError, match="no Cellar data"):
        fetch_act_dates(
            client(cellar_client, handler, tmp_path),
            [Act(celex="32099R9999", short="x")],
        )
