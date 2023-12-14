from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Literal
    from typing import TypedDict
    from typing_extensions import TypeAlias

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

    class EntityPercentage(TypedDict):
        counted: bool
        votes: int
        percentage: float

    class DistrictPercentage(TypedDict):
        entities: list[int]
        counted: bool
        votes: int
        percentage: float
