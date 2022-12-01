from onegov.ballot.models.election.candidate import Candidate
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
