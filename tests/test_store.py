import json
from datetime import UTC, datetime
from pathlib import Path

from germany_on_ai import store
from germany_on_ai.ingest.dip.ingest import to_record

PAGE = json.loads(Path("tests/fixtures/dip/vorgang_page.json").read_text())
FIRST, LATER = datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC)


def write(tmp_path: Path, documents, when: datetime, url: str | None = None):
    records = [to_record("vorgang", d, when) for d in documents]
    if url:
        records = [r.model_copy(update={"source_url": url}) for r in records]
    return store.write(tmp_path, records, partition=lambda r: "all")


def stored(tmp_path: Path):
    return {r.data["id"]: r for r in store.read(tmp_path / "all.jsonl")}


def test_unchanged_content_keeps_file_and_retrieved_at(tmp_path: Path):
    write(tmp_path, PAGE["documents"], FIRST)
    before = (tmp_path / "all.jsonl").read_bytes()
    bumped = [
        d | {"aktualisiert": "2026-02-01T00:00:00+01:00"} for d in PAGE["documents"]
    ]
    stats = write(tmp_path, bumped, LATER)
    assert stats.unchanged == 2
    assert (tmp_path / "all.jsonl").read_bytes() == before


def test_changed_content_is_rewritten(tmp_path: Path):
    write(tmp_path, PAGE["documents"], FIRST)
    edited = PAGE["documents"][0] | {"beratungsstand": "Erledigt"}
    stats = write(tmp_path, [edited], LATER)
    record = stored(tmp_path)[edited["id"]]
    assert (stats.changed, record.retrieved_at, record.data["beratungsstand"]) == (
        1,
        LATER,
        "Erledigt",
    )


def test_corrected_link_keeps_retrieval_date(tmp_path: Path):
    write(tmp_path, PAGE["documents"], FIRST)
    write(tmp_path, PAGE["documents"], LATER, url="https://example.org/fixed")
    record = next(iter(stored(tmp_path).values()))
    assert (record.source_url, record.retrieved_at) == (
        "https://example.org/fixed",
        FIRST,
    )


def test_records_are_sorted_by_id(tmp_path: Path):
    write(tmp_path, reversed(PAGE["documents"]), FIRST)
    ids = [r.id for r in store.read(tmp_path / "all.jsonl")]
    assert ids == sorted(ids)
