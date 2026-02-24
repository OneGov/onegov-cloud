from __future__ import annotations

from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSONObject
    from typing import TypedDict
    from typing import TypeAlias

    class EntityPercentage(TypedDict):
        counted: bool
        votes: int
        percentage: float

    class DistrictPercentage(TypedDict):
        entities: list[int]
        counted: bool
        votes: int
        percentage: float

    class ProgressJson(TypedDict):
        counted: int
        total: int

    class TitleJson(TypedDict, total=False):
        de_CH: str
        fr_CH: str
        it_CH: str
        rm_CH: str

    class VoteResultsJson(TypedDict):
        answer: str | None
        nays_percentage: float | None
        yeas_percentage: float | None

    class BallotTotalResultJson(TypedDict):
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

    class BallotEntityResultJson(BallotTotalResultJson):
        id: int
        name: str
        district: str

    class BallotResultJson(TypedDict):
        total: BallotTotalResultJson
        entities: list[BallotEntityResultJson]

    class BallotJson(TypedDict):
        type: BallotType
        title: TitleJson
        progress: ProgressJson
        results: BallotResultJson

    class DataJson(TypedDict):
        json: str
        csv: str

    class VoteJson(TypedDict):
        completed: bool
        date: str
        domain: DomainOfInfluence
        last_modified: str
        progress: ProgressJson
        related_link: str | None
        title: TitleJson
        short_title: TitleJson
        type: Literal['vote']
        results: VoteResultsJson
        ballots: list[BallotJson]
        url: str
        embed: JSONObject
        media: JSONObject
        data: DataJson

DomainOfInfluence: TypeAlias = Literal[
    'federation',
    'canton',
    'region',
    'district',
    'municipality',
    'none',
]

Status: TypeAlias = Literal[
    'unknown',
    'interim',
    'final',
]

Gender: TypeAlias = Literal[
    'male',
    'female',
    'undetermined',
]

BallotType: TypeAlias = Literal[
    'proposal',
    'counter-proposal',
    'tie-breaker',
]
