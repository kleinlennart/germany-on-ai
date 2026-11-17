"""Compile Source records and the catalogue into DuckDB, and export Parquet.

The build starts from scratch on every run and uses one thread, so the same
commit always produces the same bytes.
"""

import json
from pathlib import Path

import duckdb

from germany_on_ai import catalogue, store

BUILD_DIR = Path("build")
RECORD_COLUMNS = {
    "id": "VARCHAR",
    "source_id": "VARCHAR",
    "entity": "VARCHAR",
    "source_url": "VARCHAR",
    "language": "VARCHAR",
    "retrieved_at": "TIMESTAMPTZ",
    "content_sha256": "VARCHAR",
    "data": "JSON",
}


def record_tables(records_dir: Path) -> dict[str, list[Path]]:
    """One table per source and entity, e.g. dip_vorgang -> its JSONL partitions."""
    tables = {}
    for entity_dir in sorted(p for p in records_dir.glob("*/*") if p.is_dir()):
        files = sorted(entity_dir.glob("*.jsonl"))
        if files:
            tables[f"{entity_dir.parent.name}_{entity_dir.name}"] = files
    return tables


def build(
    records_dir: Path = store.RECORDS_DIR,
    catalogue_path: Path = catalogue.CATALOGUE_PATH,
    out_dir: Path = BUILD_DIR,
) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "germany_on_ai.duckdb"
    db_path.unlink(missing_ok=True)
    exports = out_dir / "exports"
    exports.mkdir(exist_ok=True)

    catalogue_json = out_dir / "catalogue.json"
    catalogue.export(catalogue.load(catalogue_path), catalogue_json)
    events = sorted(catalogue.load_curated_events(), key=lambda e: (e.date, e.id))
    (out_dir / "curated_events.json").write_text(
        json.dumps(
            [e.model_dump(mode="json") for e in events], ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )

    counts = {}
    with duckdb.connect(db_path) as db:
        db.execute("SET threads = 1")
        db.execute("SET TimeZone = 'UTC'")
        db.execute(
            "CREATE TABLE sources AS SELECT * FROM read_json(?, format = 'array')",
            [str(catalogue_json)],
        )
        for table, files in record_tables(records_dir).items():
            db.execute(
                f"CREATE TABLE {table} AS SELECT * FROM read_json(?, "
                "format = 'newline_delimited', columns = ?) ORDER BY id",
                [[str(f) for f in files], RECORD_COLUMNS],
            )
        for (table,) in db.execute(
            "SELECT table_name FROM duckdb_tables() ORDER BY 1"
        ).fetchall():
            target = exports / f"{table}.parquet"
            query = f"SELECT * FROM {table} ORDER BY ALL"
            db.execute(f"COPY ({query}) TO '{target}' (FORMAT parquet)")
            counts[table] = len(db.execute(f"SELECT id FROM {table}").fetchall())
    return counts
