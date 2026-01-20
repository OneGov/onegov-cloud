from __future__ import annotations

from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import Float
from sqlalchemy.ext.hybrid import hybrid_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy import Column


class DerivedAttributesMixin:

    """ A simple mixin to add commonly used functions to elections and their
    results. """

    if TYPE_CHECKING:
        unaccounted_ballots: Column[int]
        accounted_ballots: Column[int]
        turnout: Column[float]

        # forward declare required columns
        eligible_voters: Column[int]
        received_ballots: Column[int]
        blank_ballots: Column[int]
        invalid_ballots: Column[int]

    @hybrid_property  # type:ignore[no-redef]
    def unaccounted_ballots(self) -> int:
        """ The number of unaccounted ballots. """

        return self.blank_ballots + self.invalid_ballots

    @hybrid_property  # type:ignore[no-redef]
    def accounted_ballots(self) -> int:
        """ The number of accounted ballots. """

        return self.received_ballots - self.unaccounted_ballots

    @hybrid_property  # type:ignore[no-redef]
    def turnout(self) -> float:
        """ The turnout of the election. """

        if not self.eligible_voters:
            return 0

        return self.received_ballots / self.eligible_voters * 100

    @turnout.expression  # type:ignore[no-redef]
    def turnout(cls) -> float:
        """ The turnout of the election. """
        return case(
            [(
                cls.eligible_voters > 0,
                cast(cls.received_ballots, Float)
                / cast(cls.eligible_voters, Float) * 100
            )],
            else_=0
        )
