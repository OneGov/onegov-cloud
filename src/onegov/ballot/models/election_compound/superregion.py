from onegov.ballot.models.election.candidate import Candidate
from sqlalchemy import func
from sqlalchemy.orm import object_session


class Superregion:

    """ A superregion of an election compound. """

    def __init__(self, election_compound, segment):
        self.election_compound = election_compound
        self.election_compound_id = election_compound.id
        self.segment = segment
        self.id = segment.replace(' ', '-').lower()

    @classmethod
    def by_id(cls, app, election_compound_id, id):
        from onegov.ballot.collections import ElectionCompoundCollection

        compound = ElectionCompoundCollection(app.session()).by_id(
            election_compound_id
        )
        if compound:
            segment = id.title().replace('-', ' ')
            if segment in app.principal.get_superregions(compound.date.year):
                return cls(compound, segment)

    @property
    def date(self):
        return self.election_compound.date

    @property
    def title(self):
        return f'{self.election_compound.title} {self.segment}'

    @property
    def completed(self):
        return self.election_compound.completed

    @property
    def last_result_change(self):
        return self.election_compound.last_result_change

    @property
    def elections(self):
        return [
            election for election in
            self.election_compound.elections
            if election.domain_supersegment == self.segment
        ]

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
        session = object_session(self.election_compound)
        mandates = session.query(
            func.count(func.nullif(Candidate.elected, False))
        )
        mandates = mandates.filter(Candidate.election_id.in_(election_ids))
        mandates = mandates.first()
        return mandates[0] if mandates else 0

    # todo: ?
    # @property
    # def counted(self):
    #     """ True if all elections have been counted. """
    #
    #     for election in self.elections:
    #         if not election.counted:
    #             return False
    #
    #     return True

    @property
    def progress(self):
        result = [e.completed for e in self.elections]
        return sum(1 for r in result if r), len(result)

    # todo: ?
    # @property
    # def counted_entities(self):
    #     return [
    #         election.domain_segment for election in self.elections
    #         if election.completed
    #     ]

    @property
    def party_results(self):
        return self.election_compound.party_results.filter_by(
            domain='superregion', domain_segment=self.segment
        )

    @property
    def has_results(self):
        """ Returns True, if the election compound has any results. """

        if self.party_results.first():
            return True
        for election in self.elections:
            if election.has_results:
                return True

        return False
