"""Fetch DIP entities selected by the fetch filter and store them as Source records."""

import json
import re
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, ConfigDict

from germany_on_ai import store
from germany_on_ai.ingest.dip import answers, transcripts
from germany_on_ai.ingest.dip.client import DipClient, Params
from germany_on_ai.schema import SourceRecord

SOURCE_ID = "dip"
FETCH_FILTER_PATH = Path("data/fetch/dip.yaml")
RECORDS_DIR = store.RECORDS_DIR / SOURCE_ID
STATE_PATH = RECORDS_DIR / "_state.json"
# DIP needs about 15 minutes before a change shows up in the API.
UPDATE_OVERLAP = timedelta(minutes=30)
# DIP's timestamps are German local time.
DIP_TZ = ZoneInfo("Europe/Berlin")


class VorgangFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deskriptor: list[str]
    titel: list[str]


class PassageFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    terms: list[str]


class FetchFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int
    wahlperioden: list[int]
    fulltext_wahlperioden: list[int]
    vorgang: VorgangFilter
    passages: PassageFilter

    def passage_patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(term) for term in self.passages.terms]


def load_fetch_filter(path: Path = FETCH_FILTER_PATH) -> FetchFilter:
    return FetchFilter.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def web_url(entity: str, id_: str) -> str:
    # DIP's web UI needs a slug segment but ignores its value (checked 17 Nov 2026).
    return f"https://dip.bundestag.de/{entity}/-/{id_}"


def source_url(entity: str, data: dict[str, Any]) -> str:
    """Public link: the PDF (at the page) where DIP gives one, else a DIP web page."""
    pdf = data.get("pdf_url") or (data.get("fundstelle") or {}).get("pdf_url")
    if pdf and entity != "vorgang":
        return pdf
    if entity == "vorgangsposition":
        return web_url("vorgang", data["vorgang_id"])
    if entity == "aktivitaet" and data.get("vorgangsbezug"):
        return web_url("vorgang", data["vorgangsbezug"][0]["id"])
    return web_url(entity, data["id"])


def to_record(
    entity: str, data: dict[str, Any], retrieved_at: datetime
) -> SourceRecord:
    return SourceRecord.of(
        source_id=SOURCE_ID,
        entity=entity,
        native_id=data["id"],
        data=data,
        source_url=source_url(entity, data),
        language="de",
        retrieved_at=retrieved_at,
    )


def since_param(since: datetime | None) -> tuple[str, str] | None:
    if since is None:
        return None
    local = since.astimezone(DIP_TZ)
    return ("f.aktualisiert.start", local.strftime("%Y-%m-%dT%H:%M:%S"))


def vorgang_queries(fetch_filter: FetchFilter, since: datetime | None) -> list[Params]:
    base: Params = [("f.wahlperiode", str(wp)) for wp in fetch_filter.wahlperioden]
    if param := since_param(since):
        base.append(param)
    terms = [("f.deskriptor", d) for d in fetch_filter.vorgang.deskriptor]
    terms += [("f.titel", t) for t in fetch_filter.vorgang.titel]
    return [[*base, term] for term in terms]


def fetch_vorgaenge(
    client: DipClient, fetch_filter: FetchFilter, since: datetime | None
) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for params in vorgang_queries(fetch_filter, since):
        for document in client.query("vorgang", params):
            found[document["id"]] = document
    return list(found.values())


def fetch_by_ids(
    client: DipClient, endpoint: str, filter_name: str, ids: Iterable[str], batch: int
) -> list[dict[str, Any]]:
    """Fetch entities linked to ids; batch > 1 only for OR-repeatable filters."""
    ordered = sorted(set(ids), key=int)
    found: dict[str, dict[str, Any]] = {}
    for start in range(0, len(ordered), batch):
        params = [(filter_name, id_) for id_ in ordered[start : start + batch]]
        for document in client.query(endpoint, params):
            found[document["id"]] = document
    return list(found.values())


def fundstelle_ids(positions: Iterable[dict[str, Any]], dokumentart: str) -> set[str]:
    return {
        str(p["fundstelle"]["id"])
        for p in positions
        if (p.get("fundstelle") or {}).get("dokumentart") == dokumentart
    }


INTERPELLATIONS = ("Kleine Anfrage", "Große Anfrage")
ANSWERS = ("Antwort", "Ergänzende Antwort")


def interpellation_papers(
    positions: Iterable[dict[str, Any]], wp_of: dict[str, int], terms: list[int]
) -> list[tuple[str, str]]:
    """(question paper id, answer paper id) for each answered interpellation in these
    terms. A supplementary answer pairs with the same question paper."""
    questions, answered = {}, []
    for p in positions:
        fundstelle = p.get("fundstelle") or {}
        if (
            p.get("vorgangstyp") not in INTERPELLATIONS
            or fundstelle.get("dokumentart") != "Drucksache"
            or wp_of.get(p["vorgang_id"]) not in terms
        ):
            continue
        if p.get("vorgangsposition") in INTERPELLATIONS:
            questions[p["vorgang_id"]] = str(fundstelle["id"])
        elif p.get("vorgangsposition") in ANSWERS:
            answered.append((p["vorgang_id"], str(fundstelle["id"])))
    return sorted(
        {(questions[v], a) for v, a in answered if v in questions},
        key=lambda pair: int(pair[1]),
    )


def by_wahlperiode(record: SourceRecord) -> str:
    return f"wp{record.data['wahlperiode']}"


def by_numeric_id(record: SourceRecord) -> int:
    return int(record.data["id"])


def by_position_in_transcript(record: SourceRecord) -> tuple[int, int]:
    return int(record.data["plenarprotokoll_id"]), record.data["start"]


def by_question(record: SourceRecord) -> tuple[int, int]:
    return int(record.data["drucksache_id"]), record.data["number"]


def store_records(
    entity: str,
    documents: Iterable[dict[str, Any]],
    now: datetime,
    partition: Callable[[SourceRecord], str] = by_wahlperiode,
    sort_key: Callable[[SourceRecord], Any] = by_numeric_id,
    replace: Callable[[SourceRecord], bool] | None = None,
) -> store.WriteStats:
    records = [to_record(entity, d, now) for d in documents]
    return store.write(RECORDS_DIR / entity, records, partition, sort_key, replace)


def read_state() -> dict[str, str]:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}


def write_state(state: dict[str, str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def run(client: DipClient, *, full: bool) -> dict[str, store.WriteStats]:
    """Proceedings matching the fetch filter, then everything linked to them (their
    steps, the printed papers and activities of those steps, the persons behind the
    activities), then all plenary transcripts with their matching passages.

    Each entity is stored as soon as it is fetched, so a failure late in the run keeps
    what came before. The run state only advances once everything succeeded."""
    started = datetime.now(UTC).replace(microsecond=0)
    fetch_filter = load_fetch_filter()
    state = read_state()
    last = state.get("vorgang")
    since = None if full or not last else datetime.fromisoformat(last) - UPDATE_OVERLAP
    stats: dict[str, store.WriteStats] = {}

    vorgaenge = fetch_vorgaenge(client, fetch_filter, since)
    stats["vorgang"] = store_records("vorgang", vorgaenge, started)
    wp_of = {v["id"]: v["wahlperiode"] for v in vorgaenge}

    positions = fetch_by_ids(client, "vorgangsposition", "f.vorgang", wp_of, batch=1)
    stats["vorgangsposition"] = store_records(
        "vorgangsposition",
        positions,
        started,
        partition=lambda r: f"wp{wp_of[r.data['vorgang_id']]}",
    )

    position_ids = [p["id"] for p in positions]
    aktivitaeten = fetch_by_ids(
        client, "aktivitaet", "f.vorgangsposition_id", position_ids, batch=50
    )
    stats["aktivitaet"] = store_records("aktivitaet", aktivitaeten, started)

    drucksache_ids = fundstelle_ids(positions, "Drucksache")
    drucksachen = fetch_by_ids(client, "drucksache", "f.id", drucksache_ids, batch=50)
    stats["drucksache"] = store_records("drucksache", drucksachen, started)

    person_ids = {str(a["person_id"]) for a in aktivitaeten if a.get("person_id")}
    personen = fetch_by_ids(client, "person", "f.id", person_ids, batch=50)
    stats["person"] = store_records(
        "person", personen, started, partition=lambda r: "all"
    )

    protokolle = transcripts.fetch_protokolle(
        client, fetch_filter.fulltext_wahlperioden, since_param(since)
    )
    stats["plenarprotokoll"] = store_records("plenarprotokoll", protokolle, started)

    patterns = fetch_filter.passage_patterns()
    passages = []
    for protokoll in protokolle:
        text = transcripts.fetch_text(client, protokoll["id"])
        passages += transcripts.extract_passages(protokoll, text, patterns)
    refreshed = {p["id"] for p in protokolle}
    stats["passage"] = store_records(
        "passage",
        passages,
        started,
        sort_key=by_position_in_transcript,
        # A transcript's passages are replaced as a set; offsets move with its text.
        replace=lambda r: r.data["plenarprotokoll_id"] in refreshed,
    )

    # Government answers to this term's interpellations, split into question-answer
    # pairs with the help of the question paper. Answers DIP has no text for yet are
    # picked up by a later run.
    pairs, answered = [], set()
    for question_id, answer_id in interpellation_papers(
        positions, wp_of, fetch_filter.fulltext_wahlperioden
    ):
        answer = client.get(f"drucksache-text/{answer_id}")
        if not answer.get("text"):
            continue
        question = client.get(f"drucksache-text/{question_id}")
        pairs += answers.answer_pairs(answer, question.get("text"))
        answered.add(answer_id)
    stats["answer_pair"] = store_records(
        "answer_pair",
        pairs,
        started,
        sort_key=by_question,
        # An answer's pairs are replaced as a set, like a transcript's passages.
        replace=lambda r: r.data["drucksache_id"] in answered,
    )

    if not client.offline:
        write_state(state | {"vorgang": started.isoformat()})
    return stats
