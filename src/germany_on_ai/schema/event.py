"""A curated event: a dated item no feed provides (summits, treaty sessions,
declarations), entered by hand. Each must cite an official source."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from germany_on_ai.schema.source import Model, Slug, Url

# YYYY, YYYY-MM or YYYY-MM-DD; the precision says which.
PartialDate = Annotated[str, StringConstraints(pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")]


class Level(StrEnum):
    LOCAL = "local"
    SUBNATIONAL = "subnational"
    NATIONAL = "national"
    EU = "eu"
    INTERNATIONAL = "international"


class Precision(StrEnum):
    DAY = "day"
    MONTH = "month"
    SEASON = "season"
    YEAR = "year"


class CuratedEvent(Model):
    id: Slug
    date: PartialDate
    precision: Precision
    level: Level
    kind: str
    title: str
    source_url: Url
    source_name: str
    held: bool  # coarse dates cannot tell past from future, so each event says

    @model_validator(mode="after")
    def _date_matches_precision(self) -> Self:
        parts = len(self.date.split("-"))
        expected = {"day": 3, "month": 2, "season": 2, "year": 1}[self.precision]
        if parts != expected:
            raise ValueError(
                f"date {self.date!r} does not match precision {self.precision!r}"
            )
        return self
