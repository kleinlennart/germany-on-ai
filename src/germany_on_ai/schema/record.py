"""A Source record (layer 1): one source item, kept as the source published it."""

import hashlib
import json
from datetime import datetime
from typing import Any

from germany_on_ai.schema.source import LanguageCode, Model, Url

# Fields a source rewrites without the content changing; left out of the content hash.
VOLATILE_FIELDS = frozenset({"aktualisiert"})


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(data: dict[str, Any]) -> str:
    stable = {k: v for k, v in data.items() if k not in VOLATILE_FIELDS}
    return hashlib.sha256(canonical_json(stable).encode()).hexdigest()


class SourceRecord(Model):
    id: str
    source_id: str
    entity: str
    source_url: Url
    language: LanguageCode
    retrieved_at: datetime
    content_sha256: str
    data: dict[str, Any]

    @classmethod
    def of(
        cls,
        *,
        source_id: str,
        entity: str,
        native_id: str,
        data: dict[str, Any],
        source_url: str,
        language: str,
        retrieved_at: datetime,
    ) -> SourceRecord:
        """Wrap one source item in the envelope; the hash ignores volatile fields."""
        return cls(
            id=f"{source_id}:{entity}:{native_id}",
            source_id=source_id,
            entity=entity,
            source_url=source_url,
            language=language,
            retrieved_at=retrieved_at,
            content_sha256=content_hash(data),
            data=data,
        )
