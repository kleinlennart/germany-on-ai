"""Source records on disk: one JSONL file per partition, sorted by id."""

from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from germany_on_ai.schema import SourceRecord, canonical_json

RECORDS_DIR = Path("data/records")


@dataclass
class WriteStats:
    added: int = 0
    changed: int = 0
    unchanged: int = 0
    removed: int = 0


def read(path: Path) -> list[SourceRecord]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [SourceRecord.model_validate_json(line) for line in lines if line]


def write(
    directory: Path,
    records: Iterable[SourceRecord],
    partition: Callable[[SourceRecord], str],
    sort_key: Callable[[SourceRecord], Any] = lambda r: r.id,
    replace: Callable[[SourceRecord], bool] | None = None,
) -> WriteStats:
    """Merge records into their partition files; a record whose content is unchanged
    keeps its stored version, so its retrieved_at and line stay as they were.

    Stored records matching `replace` are dropped unless the new records include them
    again, for sets that are regenerated as a whole."""
    stats = WriteStats()
    incoming: dict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        incoming[partition(record)].append(record)
    names = set(incoming)
    if replace:
        names |= {p.stem for p in directory.glob("*.jsonl")}

    for name in sorted(names):
        path = directory / f"{name}.jsonl"
        stored = {r.id: r for r in read(path)}
        merged = {i: r for i, r in stored.items() if not (replace and replace(r))}
        new_ids = {r.id for r in incoming[name]}
        stats.removed += sum(1 for i in stored if i not in merged and i not in new_ids)
        for record in incoming[name]:
            old = stored.get(record.id)
            if old is None:
                stats.added += 1
            elif old.content_sha256 == record.content_sha256:
                # Same content: keep retrieved_at and the stored payload, but take
                # envelope fields (e.g. a corrected source_url) from the new record.
                record = record.model_copy(
                    update={"retrieved_at": old.retrieved_at, "data": old.data}
                )
                if record == old:
                    stats.unchanged += 1
                    merged[record.id] = old
                    continue
                stats.changed += 1
            else:
                stats.changed += 1
            merged[record.id] = record
        _write_atomic(path, sorted(merged.values(), key=sort_key))
    return stats


def _write_atomic(path: Path, records: list[SourceRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = (canonical_json(r.model_dump(mode="json")) for r in records)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    tmp.replace(path)
