from onegov.ballot.models.election.candidate import Candidate
from onegov.core.utils import Bunch
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models.election import Election
    from sqlalchemy import Column
    from sqlalchemy.orm import Session


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
        def elections(self) -> list[Election]: ...
        completes_manually: Column[bool]
        manually_completed: Column[bool]

    @property
    def number_of_mandates(self) -> int:
        """ The (total) number of mandates. """

        return sum(
            election.number_of_mandates for election in self.elections
        )

    @property
    def allocated_mandates(self) -> int:
        """ Number of already allocated mandates/elected candidates. """

        election_ids = [e.id for e in self.elections if e.completed]
        if not election_ids:
            return 0
        mandates = self.session.query(
            func.count(func.nullif(Candidate.elected, False))
        )
        mandates = mandates.filter(Candidate.election_id.in_(election_ids))
        result = mandates.first()
        return result[0] if result else 0

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
    def results(self) -> list[Bunch]:  # FIXME: use NamedTuple
        return [
            Bunch(
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
    def totals(self) -> Bunch:  # FIXME: use NamedTuple
        results = [r for r in self.results if r.counted]

        def _sum(attr: str) -> int:
            return sum((getattr(r, attr) for r in results)) or 0

        result = Bunch(
            turnout=0,
            eligible_voters=_sum('eligible_voters'),
            expats=_sum('expats'),
            received_ballots=_sum('received_ballots'),
            accounted_ballots=_sum('accounted_ballots'),
            blank_ballots=_sum('blank_ballots'),
            invalid_ballots=_sum('invalid_ballots'),
            accounted_votes=_sum('accounted_votes'),
        )

        if result.eligible_voters:
            result.turnout = (
                100 * result.received_ballots / result.eligible_voters
            )

        return result
