from __future__ import annotations


from typing import NamedTuple
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Election
    from sqlalchemy.orm import Mapped
    from sqlalchemy.orm import Session
    from typing import TypeAlias

    Elections: TypeAlias = Mapped[list[Election]] | list[Election]


class ResultRow(NamedTuple):
    domain_segment: str
    domain_supersegment: str
    counted: bool
    turnout: float
    eligible_voters: int
    expats: int
    received_ballots: int
    accounted_ballots: int
    blank_ballots: int
    invalid_ballots: int
    accounted_votes: int


class TotalRow(NamedTuple):
    turnout: float
    eligible_voters: int
    expats: int
    received_ballots: int
    accounted_ballots: int
    blank_ballots: int
    invalid_ballots: int
    accounted_votes: int


class DerivedAttributesMixin:

    """ A simple mixin to add commonly used functions to election compounds
    and parts.

    Requires an elections and session attribute.
    """

    if TYPE_CHECKING:
        # forward declare required attributes
        @property
        def session(self) -> Session: ...
        @property
        def elections(self) -> Elections: ...
        completes_manually: Mapped[bool]
        manually_completed: Mapped[bool]

    @property
    def number_of_mandates(self) -> int:
        """ The (total) number of mandates. """

        return sum(
            election.number_of_mandates for election in self.elections
        )

    @property
    def allocated_mandates(self) -> int:
        """ Number of already allocated mandates/elected candidates. """

        return sum(
            election.allocated_mandates for election in self.elections
        )

    @property
    def completed(self) -> bool:
        """ Returns True, if all elections are completed. """

        elections = self.elections
        if not elections:
            return False

        for election in elections:
            if not election.completed:
                return False

        if self.completes_manually and not self.manually_completed:
            return False

        return True

    @property
    def counted(self) -> bool:
        """ True if all elections have been counted. """

        for election in self.elections:
            if not election.counted:
                return False

        return True

    @property
    def counted_entities(self) -> list[str | None]:
        return [
            election.domain_segment for election in self.elections
            if election.completed
        ]

    @property
    def results(self) -> list[ResultRow]:
        return [
            ResultRow(
                domain_segment=election.domain_segment,
                domain_supersegment=election.domain_supersegment,
                counted=election.counted,
                turnout=election.turnout,
                eligible_voters=election.eligible_voters,
                expats=election.expats,
                received_ballots=election.received_ballots,
                accounted_ballots=election.accounted_ballots,
                blank_ballots=election.blank_ballots,
                invalid_ballots=election.invalid_ballots,
                accounted_votes=election.accounted_votes,
            )
            for election in self.elections
        ]

    @property
    def totals(self) -> TotalRow:
        results = [r for r in self.results if r.counted]

        def _sum(attr: str) -> int:
            return sum(getattr(r, attr) for r in results) or 0

        eligible_voters = _sum('eligible_voters')
        received_ballots = _sum('received_ballots')
        turnout = 0.0
        if eligible_voters:
            turnout = 100 * received_ballots / eligible_voters

        return TotalRow(
            turnout=turnout,
            eligible_voters=eligible_voters,
            expats=_sum('expats'),
            received_ballots=received_ballots,
            accounted_ballots=_sum('accounted_ballots'),
            blank_ballots=_sum('blank_ballots'),
            invalid_ballots=_sum('invalid_ballots'),
            accounted_votes=_sum('accounted_votes'),
        )
