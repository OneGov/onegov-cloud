from __future__ import annotations

from psycopg2.extras import NumericRange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    class BoundedIntegerRange(NumericRange):
        def __init__(
            self,
            lower: int,
            upper: int,
            bounds: str = '[)'
        ) -> None: ...
        @property
        def upper(self) -> int: ...
        @property
        def lower(self) -> int: ...
else:
    # NOTE: We can probably get rid of this once we upgrade to SQLAlchemy 2.0
    #       since they provide their own Range value types that we can inherit
    #       from (if even necessary at that point).
    def BoundedIntegerRange(  # noqa: N802
        lower: int,
        upper: int,
        bounds: str = '[)'
    ) -> NumericRange:
        """
        A NumericRange which can't be empty or have unbounded edges.
        """
        assert lower is not None and upper is not None
        return NumericRange(lower, upper, bounds)
