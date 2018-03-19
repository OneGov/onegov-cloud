from collections import OrderedDict
from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election import Election
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.list import List
from onegov.ballot.models.election.list_connection import ListConnection
from onegov.ballot.models.election.list_result import ListResult
from onegov.ballot.models.election.panachage_result import PanachageResult
from onegov.ballot.models.election.party_result import PartyResult
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class ElectionCompound(
    Base, ContentMixin, TimestampMixin,
    DomainOfInfluenceMixin, TitleTranslationsMixin
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

    #: An election compound contains n elections
    _elections = Column(
        MutableDict.as_mutable(HSTORE), name='elections', nullable=True
    )

    #: An election compound may contains n party results
    party_results = relationship(
        'PartyResult',
        primaryjoin=(
            'foreign(PartyResult.owner) == ElectionCompound.id'
        ),
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    @property
    def elections(self):
        if not self._elections:
            return []

        query = object_session(self).query(Election)
        query = query.filter(Election.id.in_(self._elections))
        query = query.order_by(Election.shortcode)
        return query.all()

    @elections.setter
    def elections(self, value):
        self._elections = {getattr(item, 'id', item): None for item in value}

    @property
    def number_of_mandates(self):
        """ The (total) number of mandates. """
        return sum([
            election.number_of_mandates for election in self.elections
        ])

    @property
    def allocated_mandates(self):
        """ Number of already allocated mandates/elected candidates. """

        election_ids = [election.id for election in self.elections]
        session = object_session(self)
        mandates = session.query(
            func.count(func.nullif(Candidate.elected, False))
        )
        mandates = mandates.filter(Candidate.election_id.in_(election_ids))
        mandates = mandates.first()
        return mandates[0] if mandates else 0

    @property
    def counted(self):
        """ True if all elections have been counted. """

        for election in self.elections:
            if not election.counted:
                return False

        return True

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        elections and the second value being the number of total elections.

        """

        results = [election.completed for election in self.elections]
        return sum(1 for result in results if result), len(results)

    @property
    def has_results(self):
        """ Returns True, if the election compound has any results. """

        for election in self.elections:
            if election.has_results:
                return True

        return False

    @property
    def completed(self):
        """ Returns True, if the all elections are completed. """

        for election in self.elections:
            if not election.completed:
                return False

        return True

    @property
    def last_modified(self):
        """ Returns last change of the elections. """

        changes = [self.last_change, self.last_result_change]
        session = object_session(self)
        election_ids = [election.id for election in self.elections]

        # Get the last candidate change
        result = object_session(self).query(Candidate.last_change)
        result = result.order_by(desc(Candidate.last_change))
        result = result.filter(Candidate.election_id.in_(election_ids))
        changes.append(result.first()[0] if result.first() else None)

        # Get the last list connection change
        result = session.query(ListConnection.last_change)
        result = result.order_by(desc(ListConnection.last_change))
        result = result.filter(ListConnection.election_id.in_(election_ids))
        changes.append(result.first()[0] if result.first() else None)

        # Get the last list change
        result = session.query(List.last_change)
        result = result.order_by(desc(List.last_change))
        result = result.filter(List.election_id == self.id)
        changes.append(result.first()[0] if result.first() else None)

        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def last_result_change(self):
        """ Returns the last change of the results of the elections. """

        changes = []
        session = object_session(self)
        election_ids = [election.id for election in self.elections]

        # Get the last election result change
        result = session.query(ElectionResult.last_change)
        result = result.order_by(desc(ElectionResult.last_change))
        result = result.filter(ElectionResult.election_id.in_(election_ids))
        changes.append(result.first()[0] if result.first() else None)

        # Get the last candidate result change
        ids = session.query(Candidate.id)
        ids = ids.filter(Candidate.election_id.in_(election_ids)).all()
        result = session.query(CandidateResult.last_change)
        result = result.order_by(desc(CandidateResult.last_change))
        result = result.filter(CandidateResult.candidate_id.in_(ids))
        changes.append(result.first()[0] if result.first() else None)

        # Get the last list result changes
        ids = session.query(List.id)
        ids = ids.filter(List.election_id.in_(election_ids)).all()
        if ids:
            result = session.query(ListResult.last_change)
            result = result.order_by(desc(ListResult.last_change))
            result = result.filter(ListResult.list_id.in_(ids))
            changes.append(result.first()[0] if result.first() else None)

        # Get the last panachage result changes
        if ids:
            result = session.query(PanachageResult.last_change)
            result = result.order_by(desc(PanachageResult.last_change))
            result = result.filter(PanachageResult.target_list_id.in_(ids))
            changes.append(result.first()[0] if result.first() else None)

        # Get the last party result changes
        result = session.query(PartyResult.last_change)
        result = result.order_by(desc(PartyResult.last_change))
        result = result.filter(PartyResult.owner.in_(election_ids + [self.id]))
        changes.append(result.first()[0] if result.first() else None)

        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def elected_candidates(self):
        """ Returns the first and last names of the elected candidates. """

        result = []
        for election in self.elections:
            result.extend(election.elected_candidates)

        return result

    #: may be used to store a link related to this election
    related_link = meta_property('related_link')

    def clear_results(self):
        """ Clears all own results. """

        session = object_session(self)
        for result in self.party_results:
            session.delete(result)

    def export(self):
        """ Returns all data connected to this election compound as list with
        dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        """

        common = OrderedDict()
        for locale, title in self.title_translations.items():
            common['compound_title_{}'.format(locale)] = (title or '').strip()
        common['compound_date'] = self.date.isoformat()
        common['compound_mandates'] = self.number_of_mandates

        rows = []
        for election in self.elections:
            for row in election.export():
                rows.append(
                    OrderedDict(list(common.items()) + list(row.items()))
                )
        return rows
