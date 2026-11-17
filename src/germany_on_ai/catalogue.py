"""Load, check and export the Source catalogue."""

import json
from collections import Counter
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from germany_on_ai.schema import CuratedEvent, Source, Status

CATALOGUE_PATH = Path("data/catalogue/sources.yaml")
CURATED_EVENTS_PATH = Path("data/curated/events.yaml")

_sources = TypeAdapter(list[Source])
_events = TypeAdapter(list[CuratedEvent])


def load_curated_events(path: Path = CURATED_EVENTS_PATH) -> list[CuratedEvent]:
    events = _events.validate_python(
        yaml.safe_load(path.read_text(encoding="utf-8")) or []
    )
    duplicates = [i for i, n in Counter(e.id for e in events).items() if n > 1]
    if duplicates:
        raise ValueError(f"duplicate event ids: {', '.join(sorted(duplicates))}")
    return events


def load(path: Path = CATALOGUE_PATH) -> list[Source]:
    sources = _sources.validate_python(yaml.safe_load(path.read_text(encoding="utf-8")))
    duplicates = [id_ for id_, n in Counter(s.id for s in sources).items() if n > 1]
    if duplicates:
        raise ValueError(f"duplicate source ids: {', '.join(sorted(duplicates))}")
    return sources


def open_questions(sources: list[Source]) -> list[str]:
    """Gaps allowed for now that must be closed before a source is ingested."""
    questions = []
    for s in sources:
        if s.status in (Status.REFERENCED, Status.UNAVAILABLE):
            continue
        if s.terms.verified is None:
            questions.append(f"{s.id}: terms not verified")
        if s.raw_publishable is None:
            questions.append(f"{s.id}: raw publishability not decided")
    return questions


def export(sources: list[Source], path: Path) -> None:
    """Write the catalogue as JSON; same input, same bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [s.model_dump(mode="json") for s in sorted(sources, key=lambda s: s.id)]
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
