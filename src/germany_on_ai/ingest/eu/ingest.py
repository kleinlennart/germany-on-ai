"""EU sources for the timeline: European Parliament procedures (Open Data API v2) and
the legal dates of adopted acts (Publications Office, Cellar SPARQL).

Both follow data/fetch/eu.yaml. Items are stored as the source published them.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml
from pydantic import BaseModel, ConfigDict

from germany_on_ai import store
from germany_on_ai.ingest.http import CachedClient, FetchError
from germany_on_ai.schema import SourceRecord

FETCH_FILTER_PATH = Path("data/fetch/eu.yaml")
EP_SOURCE = "european-parliament-open-data"
CELLAR_SOURCE = "eu-cellar"
EP_API = "https://data.europarl.europa.eu/api/v2"
CELLAR_SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"


class Procedure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str  # e.g. 2021/0106(COD)
    short: str

    @property
    def api_id(self) -> str:
        """2021/0106(COD) -> 2021-0106, the id the EP API uses."""
        return self.reference.split("(")[0].replace("/", "-")


class Act(BaseModel):
    model_config = ConfigDict(extra="forbid")
    celex: str
    short: str
    amended_by: str | None = None  # CELEX of a later act that changes its dates


class FetchFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int
    procedures: list[Procedure]
    acts: list[Act]


def load_fetch_filter(path: Path = FETCH_FILTER_PATH) -> FetchFilter:
    return FetchFilter.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def oeil_url(reference: str) -> str:
    return f"https://oeil.secure.europarl.europa.eu/oeil/en/procedure-file?reference={quote(reference)}"


def eurlex_url(celex: str) -> str:
    return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"


def ep_client(**kwargs: Any) -> CachedClient:
    return CachedClient(
        EP_API,
        cache_dir=Path("data/raw/ep"),
        headers={"Accept": "application/ld+json"},
        **kwargs,
    )


def cellar_client(**kwargs: Any) -> CachedClient:
    return CachedClient(
        CELLAR_SPARQL,
        cache_dir=Path("data/raw/cellar"),
        headers={"Accept": "application/sparql-results+json"},
        **kwargs,
    )


def fetch_procedure(client: CachedClient, procedure: Procedure) -> dict[str, Any]:
    response = client.get(
        f"procedures/{procedure.api_id}", [("format", "application/ld+json")]
    )
    items = response.get("data") or []
    if len(items) != 1 or items[0].get("label") != procedure.reference:
        raise FetchError(f"unexpected response for procedure {procedure.reference}")
    return items[0]


ACT_DATES_QUERY = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex ?date_document ?date_signature ?date_entry_into_force WHERE {{
  ?work cdm:resource_legal_id_celex ?celex .
  FILTER(STR(?celex) IN ({celex_list}))
  OPTIONAL {{ ?work cdm:work_date_document ?date_document }}
  OPTIONAL {{ ?work cdm:resource_legal_date_signature ?date_signature }}
  OPTIONAL {{ ?work cdm:resource_legal_date_entry-into-force ?date_entry_into_force }}
}}"""


def fetch_act_dates(client: CachedClient, acts: list[Act]) -> dict[str, dict[str, Any]]:
    """Legal dates per act. Cellar lists staged application dates as several
    entry-into-force values, so those come back as a sorted list."""
    celex_list = ", ".join(f'"{a.celex}"' for a in sorted(acts, key=lambda a: a.celex))
    response = client.get(
        "", [("query", ACT_DATES_QUERY.format(celex_list=celex_list))]
    )
    found: dict[str, dict[str, set[str]]] = {}
    for row in response["results"]["bindings"]:
        celex = row["celex"]["value"]
        dates = found.setdefault(celex, {})
        for field in ("date_document", "date_signature", "date_entry_into_force"):
            if field in row:
                dates.setdefault(field, set()).add(row[field]["value"])
    missing = {a.celex for a in acts} - set(found)
    if missing:
        raise FetchError(f"no Cellar data for {sorted(missing)}")
    return {
        celex: {
            "celex": celex,
            **{field: sorted(values) for field, values in d.items()},
        }
        for celex, d in found.items()
    }


def run(*, offline: bool = False) -> dict[str, store.WriteStats]:
    now = datetime.now(UTC).replace(microsecond=0)
    fetch_filter = load_fetch_filter()

    ep = ep_client(offline=offline)
    procedures = [
        SourceRecord.of(
            source_id=EP_SOURCE,
            entity="procedure",
            native_id=p.api_id,
            data=fetch_procedure(ep, p),
            source_url=oeil_url(p.reference),
            language="en",
            retrieved_at=now,
        )
        for p in fetch_filter.procedures
    ]
    cellar = cellar_client(offline=offline)
    acts = [
        SourceRecord.of(
            source_id=CELLAR_SOURCE,
            entity="act",
            native_id=celex,
            data=data,
            source_url=eurlex_url(celex),
            language="en",
            retrieved_at=now,
        )
        for celex, data in fetch_act_dates(cellar, fetch_filter.acts).items()
    ]
    return {
        "procedure": store.write(
            store.RECORDS_DIR / "ep" / "procedure", procedures, lambda r: "all"
        ),
        "act": store.write(store.RECORDS_DIR / "cellar" / "act", acts, lambda r: "all"),
    }
