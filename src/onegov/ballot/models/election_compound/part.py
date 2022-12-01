from onegov.ballot.models.election_compound.mixins import \
    DerivedAttributesMixin
from sqlalchemy.orm import object_session


class inherited_attribute:

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return getattr(instance.election_compound, self.name)


class ElectionCompoundPart(DerivedAttributesMixin):

    """ A part of an election compound.

    Covers a part of an election compound between the domain of the compound
    and the domain of the elections.

    There is no database object behind a part of an election compound, all
    the results are either taken from the compound (parties) or elections
    (candidates)-

    """

    def __init__(self, election_compound, domain, segment):
        self.election_compound = election_compound
        self.election_compound_id = election_compound.id
        self.domain = domain
        self.segment = segment
        self.id = segment.replace(' ', '-').lower()

    @classmethod
    def by_id(cls, app, election_compound_id, domain, id):
        from onegov.ballot.collections import ElectionCompoundCollection

        compound = ElectionCompoundCollection(app.session()).by_id(
            election_compound_id
        )
        if compound:
            segment = id.title().replace('-', ' ')
            segments = []
            if domain == 'district':
                segments = app.principal.get_districts(compound.date.year)
            if domain == 'region':
                segments = app.principal.get_regions(compound.date.year)
            if domain == 'superregion':
                segments = app.principal.get_superregions(compound.date.year)
            if segment in segments:
                return cls(compound, domain, segment)

    date = inherited_attribute()
    completed = inherited_attribute()
    last_result_change = inherited_attribute()
    last_modified = inherited_attribute()
    domain_elections = inherited_attribute()
    colors = inherited_attribute()
    voters_counts = inherited_attribute()
    horizontal_party_strengths = inherited_attribute()
    show_party_strengths = inherited_attribute()

    @property
    def title(self):
        return f'{self.election_compound.title} {self.segment}'

    @property
    def title_translations(self):
        return {
            locale: f'{title} {self.segment}'
            for locale, title
            in self.election_compound.title_translations.items()
        }

    @property
    def elections(self):
        return [
            election for election in
            self.election_compound.elections
            if election.domain_supersegment == self.segment
        ]

    @property
    def session(self):
        return object_session(self.election_compound)

    @property
    def progress(self):
        result = [e.completed for e in self.elections]
        return sum(1 for r in result if r), len(result)

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
