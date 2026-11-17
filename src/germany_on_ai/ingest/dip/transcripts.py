"""Plenary transcripts: metadata, full text, and passages that mention the fetch terms.

Full texts are large and stay out of git; they are cached and published as a release
asset. Passages are copied verbatim with character offsets into the full text and its
sha256, so anyone can check a passage against the published text.
"""

import hashlib
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb

from germany_on_ai.ingest.dip.client import DipClient

HOUSES = ("BT", "BR")


def fetch_protokolle(
    client: DipClient, wahlperioden: list[int], since_param: tuple[str, str] | None
) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for house in HOUSES:  # f.zuordnung takes a single value
        params = [("f.wahlperiode", str(wp)) for wp in wahlperioden]
        params += [("f.zuordnung", house), *([since_param] if since_param else [])]
        for document in client.query("plenarprotokoll", params):
            found[document["id"]] = document
    return list(found.values())


def fetch_text(client: DipClient, protokoll_id: str) -> str:
    # One transcript per request: lists of several full texts can arrive cut off.
    return client.get(f"plenarprotokoll-text/{protokoll_id}")["text"]


def export_fulltext(
    client: DipClient, protokolle: list[dict[str, Any]], target: Path
) -> int:
    """Write every transcript's full text to one Parquet file, for a release asset.
    Reads the offline cache, so it never calls DIP."""
    rows = []
    for p in sorted(protokolle, key=lambda p: int(p["id"])):
        text = fetch_text(client, p["id"])
        rows.append(
            (
                p["id"],
                p["dokumentnummer"],
                p["datum"],
                p["wahlperiode"],
                p["herausgeber"],
                p["fundstelle"]["pdf_url"],
                text,
                text_sha256(text),
            )
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect() as db:
        db.execute("SET threads = 1")
        db.execute(
            "CREATE TABLE fulltext (id VARCHAR, dokumentnummer VARCHAR, datum DATE, "
            "wahlperiode INTEGER, herausgeber VARCHAR, pdf_url VARCHAR, text VARCHAR, "
            "text_sha256 VARCHAR)"
        )
        db.executemany("INSERT INTO fulltext VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        db.execute(f"COPY fulltext TO '{target}' (FORMAT parquet)")
    return len(rows)


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def paragraphs(text: str) -> Iterator[tuple[int, int]]:
    """(start, end) character offsets of each non-empty line; DIP's text puts one
    paragraph per line."""
    for match in re.finditer(r"[^\n]+", text):
        if match.group().strip():
            yield match.start(), match.end()


def extract_passages(
    protokoll: dict[str, Any], text: str, terms: list[re.Pattern[str]]
) -> list[dict[str, Any]]:
    digest = text_sha256(text)
    passages = []
    for start, end in paragraphs(text):
        paragraph = text[start:end]
        matched = sorted({t.pattern for t in terms if t.search(paragraph)})
        if matched:
            passages.append(
                {
                    "id": f"{protokoll['id']}-{start}",
                    "plenarprotokoll_id": protokoll["id"],
                    "dokumentnummer": protokoll["dokumentnummer"],
                    "datum": protokoll["datum"],
                    "wahlperiode": protokoll["wahlperiode"],
                    "herausgeber": protokoll["herausgeber"],
                    "pdf_url": protokoll["fundstelle"]["pdf_url"],
                    "start": start,
                    "end": end,
                    "text": paragraph,
                    "terms": matched,
                    "fulltext_sha256": digest,
                }
            )
    return passages
