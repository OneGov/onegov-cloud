from collections import OrderedDict
from onegov.ballot.models.election_compound.association import \
    ElectionCompoundAssociation
from onegov.ballot.models.election_compound.mixins import \
    DerivedAttributesMixin
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import ExplanationsPdfMixin
from onegov.ballot.models.mixins import LastModifiedMixin
from onegov.ballot.models.mixins import named_file
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.party_result.mixins import PartyResultExportMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from onegov.core.utils import groupbylist
from sqlalchemy import Column, Boolean
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class ElectionCompound(
    Base, ContentMixin, LastModifiedMixin,
    DomainOfInfluenceMixin, TitleTranslationsMixin,
    PartyResultExportMixin, ExplanationsPdfMixin, DerivedAttributesMixin
):

    __tablename__ = 'election_compounds'

    #: Identifies the election compound, may be used in the url
    id = Column(Text, primary_key=True)

    #: all translations of the title
    title_translations = Column(HSTORE, nullable=False)

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: The date of the elections
    date = Column(Date, nullable=False)

    #: Doppelter Pukelsheim
    pukelsheim = Column(Boolean, nullable=False, default=False)

    #: Allow setting the status of the compound and its elections manually
    completes_manually = Column(Boolean, nullable=False, default=False)

    #: Status of the compound and its elections
    manually_completed = Column(Boolean, nullable=False, default=False)

    #: Display voters counts instead of votes in views with party results.
    voters_counts = meta_property('voters_counts', default=False)

    #: Display exact voters counts instead of rounded values.
    exact_voters_counts = meta_property('exact_voters_counts', default=False)

    #: An election compound may contains n party results
    party_results = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        backref=backref('election_compound'),
        lazy='dynamic',
    )

    #: An election compound may contains n panachage results
    panachage_results = relationship(
        'PanachageResult',
        cascade='all, delete-orphan',
        backref=backref('election_compound'),
        lazy='dynamic',
    )

    #: Defines optional colors for parties
    colors = meta_property('colors', default=dict)

    #: Defines the domain of the elections
    domain_elections = meta_property('domain_elections', default='district')

    @property
    def elections(self):
        elections = [association.election for association in self.associations]
        return sorted(elections, key=lambda x: x.shortcode or '')

    @elections.setter
    def elections(self, value):
        self.associations = [
            ElectionCompoundAssociation(election_id=election.id)
            for election in value
        ]

        # update last result change (only newer)
        new = [x.last_result_change for x in value]
        new = [x for x in new if x]
        new = max(new) if new else None
        if new:
            old = self.last_result_change
            if not old or (old and old < new):
                self.last_result_change = new

    @property
    def session(self):
        return object_session(self)

    @property
    def progress(self):
        """ Returns a tuple with the current progress.

        If the elections define a `domain_supersegment` (i.e. superregions),
        this is the number of fully counted supersegments vs. the total number
        of supersegments.

        If no `domain_supersegment` is defined, this is the number of counted
        elections vs. the total number of elections.

        """

        result = [(e.domain_supersegment, e.completed) for e in self.elections]
        result = groupbylist(sorted(result), lambda x: x[0])
        result = {k: [x[1] for x in v] for k, v in result}

        if len(result) == 1 and '' in result:
            result = list(result.values())[0]
        else:
            result = [all(v) for k, v in result.items()]

        return sum(1 for r in result if r), len(result)

    @property
    def has_results(self):
        """ Returns True, if the election compound has any results. """

        if self.party_results.first():
            return True
        if self.panachage_results.first():
            return True
        for election in self.elections:
            if election.has_results:
                return True

        return False

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
    def elected_candidates(self):
        """ Returns the first and last names of the elected candidates. """

        result = []
        for election in self.elections:
            result.extend(election.elected_candidates)

        return result

    #: may be used to store a link related to this election
    related_link = meta_property('related_link')
    related_link_label = meta_property('related_link_label')

    #: additional file in case of Doppelter Pukelsheim
    upper_apportionment_pdf = named_file()

    #: additional file in case of Doppelter Pukelsheim
    lower_apportionment_pdf = named_file()

    #: may be used to enable/disable the visibility of the seat allocation
    show_seat_allocation = meta_property('show_seat_allocation')

    #: may be used to enable/disable the visibility of the list groups
    show_list_groups = meta_property('show_list_groups')

    #: may be used to enable/disable the visibility of party strengths
    show_party_strengths = meta_property('show_party_strengths')

    #: show a horizontal party strengths bar chart instead of a vertical
    horizontal_party_strengths = meta_property('horizontal_party_strengths')

    #: may be used to enable/disable the visibility of party panachage
    show_party_panachage = meta_property('show_party_panachage')

    def clear_results(self):
        """ Clears all related results. """

        self.last_result_change = None

        session = object_session(self)
        for result in self.party_results:
            session.delete(result)
        for result in self.panachage_results:
            session.delete(result)

        for election in self.elections:
            election.clear_results()

    def export(self, locales):
        """ Returns all data connected to this election compound as list with
        dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        If consider completed, status for candidate_elected and
        absolute_majority will be set to None if election is not completed.

        """

        common = OrderedDict()
        for locale in locales:
            common[f'compound_title_{locale}'] = self.title_translations.get(
                locale, ''
            )
        common['compound_date'] = self.date.isoformat()
        common['compound_mandates'] = self.number_of_mandates

        rows = []
        for election in self.elections:
            for row in election.export(locales):
                rows.append(
                    OrderedDict(list(common.items()) + list(row.items()))
                )
        return rows
