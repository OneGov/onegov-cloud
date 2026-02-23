from __future__ import annotations

from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import Float
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped
    from sqlalchemy.sql import ColumnElement


class DerivedAttributesMixin:

    """ A simple mixin to add commonly used functions to ballots and their
    results. """

    if TYPE_CHECKING:
        # forward declare required attributes
        yeas: Mapped[int]
        nays: Mapped[int]
        counted: Mapped[bool]

    @hybrid_property
    def yeas_percentage(self) -> float:
        """ The percentage of yeas (discounts empty/invalid ballots). """

        return self.yeas / ((self.yeas + self.nays) or 1) * 100

    @yeas_percentage.inplace.expression
    @classmethod
    def _yeas_percentage_expression(cls) -> ColumnElement[float]:
        # coalesce will pick the first non-null result
        # nullif will return null if division by zero
        # => when all yeas and nays are zero the yeas percentage is 0%
        return 100 * (
            cast(cls.yeas, Float) / cast(
                func.coalesce(
                    func.nullif(cls.yeas + cls.nays, 0), 1
                ),
                Float
            )
        )

    @hybrid_property
    def nays_percentage(self) -> float:
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @hybrid_property
    def accepted(self) -> bool | None:
        return self.yeas > self.nays if self.counted else None

    @accepted.inplace.expression
    @classmethod
    def _accepted_expression(cls) -> ColumnElement[bool | None]:
        return case(
            (cls.counted.is_(False), None),
            (cls.yeas > cls.nays, True),
            else_=False
        )


class DerivedBallotsCountMixin:

    """ A simple mixin to add commonly used functions to votes, ballots and
    their results. """

    if TYPE_CHECKING:
        # forward declare required columns
        yeas: Mapped[int]
        nays: Mapped[int]
        empty: Mapped[int]
        invalid: Mapped[int]
        eligible_voters: Mapped[int]

    @hybrid_property
    def cast_ballots(self) -> int:
        return (
            (self.yeas or 0) + (self.nays or 0) + (self.empty or 0)
            + (self.invalid or 0)
        )

    @hybrid_property
    def turnout(self) -> float:
        return (
            self.cast_ballots / self.eligible_voters * 100
            if self.eligible_voters else 0
        )

    @turnout.inplace.expression
    @classmethod
    def _turnout_expression(cls) -> ColumnElement[float]:
        return case(
            (
                cls.eligible_voters > 0,
                cast(cls.cast_ballots, Float)
                / cast(cls.eligible_voters, Float) * 100
            ),
            else_=0
        )
