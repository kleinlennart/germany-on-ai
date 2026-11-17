"""A Source: a publisher or dataset the project draws on or points to."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# Plain strings keep URLs exactly as written; pydantic's URL types normalise them.
Url = Annotated[str, StringConstraints(pattern=r"^https?://\S+$")]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
LanguageCode = Annotated[str, StringConstraints(pattern=r"^[a-z]{2}$")]


class Kind(StrEnum):
    PRIMARY = "primary"
    TRACKER = "tracker"
    RESEARCH = "research"
    PRESS = "press"


class Arena(StrEnum):
    DOMESTIC = "domestic"
    EU = "eu"
    INTERNATIONAL = "international"


class Access(StrEnum):
    API = "api"
    DATASET = "dataset"
    SCRAPE = "scrape"
    MANUAL = "manual"
    NONE = "none"


class Status(StrEnum):
    PLANNED = "planned"
    INGESTED = "ingested"
    PARTIAL = "partial"
    REFERENCED = "referenced"
    UNAVAILABLE = "unavailable"


class UpdateFrequency(StrEnum):
    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    IRREGULAR = "irregular"
    STATIC = "static"


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)


class Coverage(Model):
    start: int | None = None
    end: int | None = None
    notes: str | None = None


class Terms(Model):
    licence: str | None = None
    url: Url | None = None
    verified: date | None = None
    notes: str | None = None


class Source(Model):
    id: Slug
    name: str
    name_original: str | None = None
    publisher: str
    url: Url
    description: str
    kind: Kind
    arenas: list[Arena] = Field(min_length=1)
    access: Access
    status: Status
    reason: str | None = None
    paywalled: bool = False
    languages: list[LanguageCode] = Field(min_length=1)
    coverage: Coverage | None = None
    update_frequency: UpdateFrequency | None = None
    terms: Terms = Terms()
    # None until decided; a decision needs verified terms.
    raw_publishable: bool | None = None
    pii_fields: list[str] = []
    docs: list[Url] = []

    @model_validator(mode="after")
    def _check(self) -> Self:
        not_ingested = self.status in (Status.REFERENCED, Status.UNAVAILABLE)
        if not_ingested and not self.reason:
            raise ValueError(f"status '{self.status}' needs a reason")
        if self.raw_publishable is not None and self.terms.verified is None:
            raise ValueError("raw_publishable is set but terms are not verified")
        return self
