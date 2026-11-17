from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import httpx

from germany_on_ai import store
from germany_on_ai.ingest.dip import transcripts
from germany_on_ai.ingest.dip.client import DipClient
from germany_on_ai.ingest.dip.ingest import (
    by_position_in_transcript,
    load_fetch_filter,
    to_record,
)

PROTOKOLL: dict[str, Any] = {
    "id": "5749",
    "dokumentnummer": "21/41",
    "datum": "2025-11-14",
    "wahlperiode": 21,
    "herausgeber": "BT",
    "fundstelle": {"pdf_url": "https://dserver.bundestag.de/btp/21/21041.pdf"},
}
TEXT = (
    "Tagesordnungspunkt 29:\n\n"
    "KI-Sicherheit stärken – Risiken leistungsfähiger KI-Systeme wirksam begrenzen\n"
    "Das Wort hat die Kollegin.\n"
    "Wir brauchen klare Regeln für künstliche Intelligenz.\n"
)


def passages(text: str = TEXT):
    patterns = load_fetch_filter().passage_patterns()
    return transcripts.extract_passages(PROTOKOLL, text, patterns)


def test_passages_are_verbatim_slices_of_the_full_text():
    found = passages()
    assert [p["text"] for p in found] == [
        "KI-Sicherheit stärken – Risiken leistungsfähiger KI-Systeme wirksam begrenzen",
        "Wir brauchen klare Regeln für künstliche Intelligenz.",
    ]
    for p in found:
        assert TEXT[p["start"] : p["end"]] == p["text"]
        assert p["fulltext_sha256"] == transcripts.text_sha256(TEXT)


def test_terms_do_not_match_inside_other_words():
    assert passages("Die KIta öffnet um acht.\nSKI-Verband tagt.\n") == []


def test_a_changed_transcript_replaces_its_passages(tmp_path: Path):
    when = datetime(2026, 1, 1, tzinfo=UTC)

    def save(found):
        return store.write(
            tmp_path,
            [to_record("passage", p, when) for p in found],
            partition=lambda r: "wp21",
            sort_key=by_position_in_transcript,
            replace=lambda r: r.data["plenarprotokoll_id"] == PROTOKOLL["id"],
        )

    save(passages())
    stats = save(passages("Neue Einleitung.\n" + TEXT))
    kept = store.read(tmp_path / "wp21.jsonl")
    assert (stats.added, stats.removed, len(kept)) == (2, 2, 2)


def test_fulltext_export_is_byte_identical_and_hashed(tmp_path: Path):
    def serve(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": PROTOKOLL["id"], "text": TEXT})

    live = DipClient(
        "key",
        cache_dir=tmp_path / "cache",
        transport=httpx.MockTransport(serve),
        min_interval=0,
    )
    transcripts.fetch_text(live, PROTOKOLL["id"])
    offline = DipClient(None, cache_dir=tmp_path / "cache", offline=True)

    first, second = tmp_path / "a.parquet", tmp_path / "b.parquet"
    assert transcripts.export_fulltext(offline, [PROTOKOLL], first) == 1
    transcripts.export_fulltext(offline, [PROTOKOLL], second)
    assert first.read_bytes() == second.read_bytes()
    query = f"SELECT text, text_sha256 FROM '{first}'"
    stored = duckdb.connect().execute(query).fetchall()[0]
    assert stored == (TEXT, transcripts.text_sha256(TEXT))
