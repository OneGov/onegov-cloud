from __future__ import annotations

from sqlalchemy.dialects.postgresql import Range

from typing import Literal, TYPE_CHECKING


if TYPE_CHECKING:
    class BoundedIntegerRange(Range[int]):
        def __init__(
            self,
            lower: int,
            upper: int,
            *,
            bounds: Literal['()', '[)', '(]', '[]'] = '[)',
            empty: bool = False,
        ) -> None: ...
        @property
        def upper(self) -> int: ...
        @property
        def lower(self) -> int: ...
else:
    BoundedIntegerRange = Range[int]
