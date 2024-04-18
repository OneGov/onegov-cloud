from pydantic import BaseModel
from pydantic import Field
from typing import Literal


class ProgressSchema(BaseModel):
    counted: int
    total: int


class TitleSchema(BaseModel):
    de_CH: str | None = None
    fr_CH: str | None = None
    it_CH: str | None = None
    rm_CH: str | None = None


class VoteResultsSchema(BaseModel):
    answer: str | None = None
    nays_percentage: float | None = None
    yeas_percentage: float | None = None


class BallotTotalResultSchema(BaseModel):
    counted: bool
    accepted: bool | None
    eligible_voters: int
    invalid: int
    cast_ballots: int
    turnout: float
    empty: int
    yeas: int
    nays: int
    yeas_percentage: float
    nays_percentage: float


class BallotEntityResultSchema(BallotTotalResultSchema):
    id: int
    name: str
    district: str


class BallotResultSchema(BaseModel):
    total: BallotTotalResultSchema
    entities: list[BallotEntityResultSchema]


class BallotSchema(BaseModel):
    type: Literal['proposal', 'counter-proposal', 'tie-breaker']
    title: TitleSchema
    progress: ProgressSchema
    results: BallotResultSchema


class DataSchema(BaseModel):
    json_: str = Field(..., alias='json', serialization_alias='json')
    csv: str


class VoteSchema(BaseModel):
    completed: bool
    date: str
    domain: Literal[
        'federation',
        'canton',
        'region',
        'district',
        'municipality',
        'none',
    ]
    last_modified: str
    progress: ProgressSchema
    related_link: str | None = None
    title: TitleSchema
    type: Literal['vote']
    results: VoteResultsSchema
    ballots: list[BallotSchema]
    url: str
    embed: dict | None = None  # type:ignore[type-arg]
    media: dict | None = None  # type:ignore[type-arg]
    data: DataSchema
