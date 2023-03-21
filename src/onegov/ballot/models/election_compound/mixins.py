from onegov.ballot.models.election.candidate import Candidate
from onegov.core.utils import Bunch
from sqlalchemy import func


class DerivedAttributesMixin:

    """ A simple mixin to add commonly used functions to election compounds
    and parts.

    Requires an elections and session attribute.
    """

    @property
    def number_of_mandates(self):
        """ The (total) number of mandates. """

        return sum([
            election.number_of_mandates for election in self.elections
        ])

    @property
    def allocated_mandates(self):
        """ Number of already allocated mandates/elected candidates. """

        election_ids = [e.id for e in self.elections if e.completed]
        if not election_ids:
            return 0
        mandates = self.session.query(
            func.count(func.nullif(Candidate.elected, False))
        )
        mandates = mandates.filter(Candidate.election_id.in_(election_ids))
        mandates = mandates.first()
        return mandates[0] if mandates else 0

    @property
    def completed(self):
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
    def counted(self):
        """ True if all elections have been counted. """

        for election in self.elections:
            if not election.counted:
                return False

        return True

    @property
    def counted_entities(self):
        return [
            election.domain_segment for election in self.elections
            if election.completed
        ]

    @property
    def results(self):
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
    def totals(self):
        results = [r for r in self.results if r.counted]

        def _sum(attr):
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
