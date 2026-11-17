import json
from datetime import UTC, datetime
from pathlib import Path

from germany_on_ai import build, store
from germany_on_ai.ingest.dip.ingest import to_record

PAGE = json.loads(Path("tests/fixtures/dip/vorgang_page.json").read_text())


def build_once(tmp_path: Path, name: str) -> dict[str, bytes]:
    records = tmp_path / "records"
    when = datetime(2026, 1, 1, tzinfo=UTC)
    store.write(
        records / "dip" / "vorgang",
        [to_record("vorgang", d, when) for d in PAGE["documents"]],
        partition=lambda r: "wp21",
    )
    out = tmp_path / name
    build.build(records_dir=records, out_dir=out)
    return {p.name: p.read_bytes() for p in sorted((out / "exports").glob("*.parquet"))}


def test_build_is_byte_identical(tmp_path: Path):
    first, second = build_once(tmp_path, "a"), build_once(tmp_path, "b")
    assert set(first) == {"dip_vorgang.parquet", "sources.parquet"}
    assert first == second
