from pathlib import Path

import pytest
from pydantic import ValidationError

from germany_on_ai import catalogue
from germany_on_ai.schema import Source

MINIMAL = {
    "id": "example",
    "name": "Example",
    "publisher": "Example publisher",
    "url": "https://example.org",
    "description": "An example source.",
    "kind": "primary",
    "arenas": ["domestic"],
    "access": "api",
    "status": "planned",
    "languages": ["de"],
}


def test_catalogue_is_valid():
    assert catalogue.load()


@pytest.mark.parametrize(
    "change",
    [
        {"status": "referenced"},  # needs a reason
        {"raw_publishable": True},  # needs verified terms
        {"id": "Not A Slug"},
        {"url": "example.org"},
        {"arenas": []},
        {"unknown_field": 1},
    ],
)
def test_rejects_invalid_source(change):
    with pytest.raises(ValidationError):
        Source.model_validate(MINIMAL | change)


def test_rejects_duplicate_ids(tmp_path: Path):
    path = tmp_path / "sources.yaml"
    path.write_text(
        "- &s {id: a, name: A, publisher: P, url: 'https://a.org', description: D,\n"
        "      kind: primary, arenas: [eu], access: api, status: planned,\n"
        "      languages: [en]}\n"
        "- *s\n"
    )
    with pytest.raises(ValueError, match="duplicate"):
        catalogue.load(path)


def test_open_questions_skip_referenced_sources():
    planned = Source.model_validate(MINIMAL)
    referenced = Source.model_validate(
        MINIMAL | {"id": "ref", "status": "referenced", "reason": "Linked."}
    )
    assert catalogue.open_questions([planned, referenced]) == [
        "example: terms not verified",
        "example: raw publishability not decided",
    ]


def test_export_is_deterministic(tmp_path: Path):
    sources = catalogue.load()
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    catalogue.export(sources, first)
    catalogue.export(list(reversed(sources)), second)
    assert first.read_bytes() == second.read_bytes()


EVENT = {
    "id": "example-summit",
    "date": "2026-02",
    "precision": "month",
    "level": "international",
    "kind": "Summit",
    "title": "An example summit",
    "source_url": "https://example.org/summit",
    "source_name": "Example host government",
    "ai_angle": "An official session on AI governance is on the programme.",
    "held": True,
}


def test_curated_events_file_is_valid():
    catalogue.load_curated_events()


@pytest.mark.parametrize(
    "change",
    [
        {"source_url": "not a url"},
        {"date": "2026-02-10"},  # day date with month precision
        {"level": "domestic"},  # levels are local … international
        {"ai_angle": None},  # every event must say where AI is on its agenda
    ],
)
def test_curated_event_rules(change):
    from germany_on_ai.schema import CuratedEvent

    with pytest.raises(ValidationError):
        CuratedEvent.model_validate(EVENT | change)
