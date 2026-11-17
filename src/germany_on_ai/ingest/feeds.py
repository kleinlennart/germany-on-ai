"""Feeds polled for the timeline: RSS (government press, Bundesrat events) and iCal
(Bundestag sitting weeks), as listed in data/fetch/feeds.yaml.

RSS items are stored with title, date, link and a short plain-text excerpt only: most
publishers state no reuse licence, so full texts stay on their sites. Feeds keep no
history; each run adds what is new and keeps what was stored before.
"""

import hashlib
import html
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, ConfigDict

from germany_on_ai import store
from germany_on_ai.ingest.http import CachedClient
from germany_on_ai.schema import SourceRecord

CONFIG_PATH = Path("data/fetch/feeds.yaml")
EXCERPT_CHARS = 300


class Feed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    entity: str
    format: Literal["rss", "ical"]
    urls: list[str]
    page: str | None = None  # public page to link calendar entries to


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int
    feeds: list[Feed]


def load_config(path: Path = CONFIG_PATH) -> Config:
    return Config.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def excerpt(markup: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup or ""))
    text = " ".join(text.split())
    return (
        text if len(text) <= EXCERPT_CHARS else text[: EXCERPT_CHARS - 1].rstrip() + "…"
    )


def parse_rss(text: str, feed_url: str) -> list[dict[str, Any]]:
    root = ET.fromstring(text)
    items = []
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        published = item.findtext("pubDate")
        items.append(
            {
                "id": hashlib.sha256(guid.encode()).hexdigest()[:16],
                "feed": feed_url,
                "title": " ".join((item.findtext("title") or "").split()),
                "link": link,
                "published": parsedate_to_datetime(published).isoformat()
                if published
                else None,
                "excerpt": excerpt(item.findtext("description") or ""),
            }
        )
    return items


def parse_ical(text: str) -> list[dict[str, Any]]:
    """All-day events: start, inclusive end, summary. Keyed on dates, not UIDs."""
    unfolded = re.sub(r"\r?\n[ \t]", "", text)  # iCal folds long lines
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", unfolded, flags=re.S):
        fields = {}
        for line in block.strip().splitlines():
            key, _, value = line.partition(":")
            fields[key.split(";")[0]] = value.strip()
        start = datetime.strptime(fields["DTSTART"][:8], "%Y%m%d").date()
        end = datetime.strptime(
            fields.get("DTEND", fields["DTSTART"])[:8], "%Y%m%d"
        ).date()
        if end > start:
            end -= timedelta(days=1)  # DTEND of an all-day event is exclusive
        events.append(
            {
                "id": start.isoformat(),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "summary": fields.get("SUMMARY", ""),
            }
        )
    return events


def client_for(url: str, *, offline: bool) -> tuple[CachedClient, str]:
    parts = urlsplit(url)
    client = CachedClient(
        f"{parts.scheme}://{parts.netloc}",
        cache_dir=Path("data/raw/feeds") / parts.netloc,
        offline=offline,
    )
    return client, parts.path.lstrip("/")


def run(*, offline: bool = False) -> dict[str, store.WriteStats]:
    now = datetime.now(UTC).replace(microsecond=0)
    stats: dict[str, store.WriteStats] = {}
    for feed in load_config().feeds:
        records: dict[str, SourceRecord] = {}
        for url in feed.urls:
            client, path = client_for(url, offline=offline)
            text = client.get_text(path)
            for data in (
                parse_rss(text, url) if feed.format == "rss" else parse_ical(text)
            ):
                records[data["id"]] = SourceRecord.of(
                    source_id=feed.source,
                    entity=feed.entity,
                    native_id=data["id"],
                    data=data,
                    source_url=data.get("link") or feed.page or url,
                    language="de",
                    retrieved_at=now,
                )
        stats[feed.source] = store.write(
            store.RECORDS_DIR
            / feed.source.replace("-", "_")
            / feed.entity.replace("-", "_"),
            records.values(),
            partition=lambda r: "all",
        )
    return stats
