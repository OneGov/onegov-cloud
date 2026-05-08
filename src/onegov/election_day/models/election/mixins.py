from __future__ import annotations

from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import Float
from sqlalchemy.ext.hybrid import hybrid_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped
    from sqlalchemy.sql import ColumnElement


class DerivedAttributesMixin:

    """ A simple mixin to add commonly used functions to elections and their
    results. """

    if TYPE_CHECKING:
        # forward declare required columns
        eligible_voters: Mapped[int]
        received_ballots: Mapped[int]
        blank_ballots: Mapped[int]
        invalid_ballots: Mapped[int]

    @hybrid_property
    def unaccounted_ballots(self) -> int:
        """ The number of unaccounted ballots. """

        return self.blank_ballots + self.invalid_ballots

    @hybrid_property
    def accounted_ballots(self) -> int:
        """ The number of accounted ballots. """

        return self.received_ballots - self.unaccounted_ballots

    @hybrid_property
    def turnout(self) -> float:
        """ The turnout of the election. """

        if not self.eligible_voters:
            return 0

        return self.received_ballots / self.eligible_voters * 100

    @turnout.inplace.expression
    @classmethod
    def _turnout_expression(cls) -> ColumnElement[float]:
        """ The turnout of the election. """
        return case(
            (
                cls.eligible_voters > 0,
                cast(cls.received_ballots, Float)
                / cast(cls.eligible_voters, Float) * 100
            ),
            else_=0
        )
