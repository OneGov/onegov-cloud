from collections import OrderedDict
from onegov.ballot.constants import election_day_i18n_used_locales
from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election import Election
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.list import List
from onegov.ballot.models.election.list_connection import ListConnection
from onegov.ballot.models.election.list_result import ListResult
from onegov.ballot.models.election.mixins import PartyResultExportMixin
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
from onegov.core.orm.types import UUID
from sqlalchemy import cast
from sqlalchemy import Column, Boolean
from sqlalchemy import Date
from sqlalchemy import desc
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import literal_column
from uuid import uuid4


class ElectionCompoundAssociation(Base):

    __tablename__ = 'election_compound_associations'

    #: identifies the candidate result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The election compound ID
    election_compound_id = Column(
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE')
    )

    #: The election ID
    election_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE'),
        primary_key=True
    )

    election_compound = relationship(
        'ElectionCompound', backref=backref(
            'associations',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    election = relationship(
        'Election', backref=backref(
            'associations',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )


class ElectionCompound(
    Base, ContentMixin, TimestampMixin,
    DomainOfInfluenceMixin, TitleTranslationsMixin,
    PartyResultExportMixin
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

    #: Enable Doppelter Pukelsheim for setting status of child elections
    after_pukelsheim = Column(Boolean, nullable=False, default=False)

    #: Status for Doppelter Pukelsheim to set via Website
    pukelsheim_completed = Column(Boolean, nullable=False, default=False)

    #: An election compound may contains n party results
    party_results = relationship(
        'PartyResult',
        primaryjoin=(
            'foreign(PartyResult.owner) == ElectionCompound.id'
        ),
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    #: An election compound may contains n panachage results
    panachage_results = relationship(
        'PanachageResult',
        primaryjoin=(
            'foreign(PanachageResult.owner) == ElectionCompound.id'
        ),
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    #: Defines optional colors for parties
    colors = meta_property('colors', default=dict)

    @property
    def elections(self):
        elections = [association.election for association in self.associations]
        return sorted(
            elections,
            key=lambda x: f"{x.status}{x.shortcode or ''}"
        )

    @elections.setter
    def elections(self, value):
        self.associations = [
            ElectionCompoundAssociation(election_id=election.id)
            for election in value
        ]

    @property
    def number_of_mandates(self):
        """ The (total) number of mandates. """
        return sum([
            election.number_of_mandates for election in self.elections
        ])

    def allocated_mandates(self, consider_completed=False):
        """ Number of already allocated mandates/elected candidates. """

        if consider_completed:
            election_ids = [e.id for e in self.elections if e.completed]
        else:
            election_ids = [e.id for e in self.elections]

        if not election_ids:
            return 0
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
    def counted_entities(self):
        return [
            election.title for election in self.elections
            if election.completed
        ]

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
        """ Returns True, if the all elections are completed. """

        if self.after_pukelsheim:
            return self.pukelsheim_completed

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

        # Get the last election change
        result = object_session(self).query(Election.last_change)
        result = result.order_by(desc(Election.last_change))
        result = result.filter(Election.id.in_(election_ids))
        changes.append(result.first()[0] if result.first() else None)

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
            ids = [str(id_[0]) for id_ in ids]
            result = session.query(PanachageResult.last_change)
            result = result.order_by(desc(PanachageResult.last_change))
            result = result.filter(
                or_(
                    PanachageResult.target.in_(ids),
                    PanachageResult.owner == self.id,
                )
            )
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

    def get_list_results(self, order_by='votes'):
        """ Returns the aggregated number of mandates and votes of all the
        lists.

        """
        assert order_by in ('votes', 'number_of_mandates')

        session = object_session(self)

        # Query number of mandates
        mandates = session.query(
            List.name.label('name'),
            func.sum(List.number_of_mandates).label('number_of_mandates'),
            literal_column('0').label('votes')
        )
        mandates = mandates.join(
            ElectionCompound.associations
        )
        mandates = mandates.filter(
            ElectionCompound.id == self.id,
        )
        mandates = mandates.join(Election, List)
        mandates = mandates.group_by(List.name)

        # Query votes
        votes = session.query(
            List.name.label('name'),
            literal_column('0').label('number_of_mandates'),
            func.sum(ListResult.votes).label('votes')
        )
        votes = votes.join(
            ElectionCompound.associations
        )
        votes = votes.filter(
            ElectionCompound.id == self.id,
        )
        votes = votes.join(Election, List, ListResult)
        votes = votes.group_by(List.name)

        # Combine
        union = mandates.union_all(votes).subquery('union')
        query = session.query(
            union.c.name.label('name'),
            cast(func.sum(union.c.number_of_mandates), Integer).label(
                'number_of_mandates'
            ),
            cast(func.sum(union.c.votes), Integer).label('votes')
        )
        query = query.group_by(union.c.name)
        query = query.order_by(desc(order_by))
        return query

    #: may be used to store a link related to this election
    related_link = meta_property('related_link')
    related_link_label = meta_property('related_link_label')

    #: may be used to enable/disable the visibility of party strengths
    show_party_strengths = meta_property('party_strengths')

    #: may be used to enable/disable the visibility of mandate allocation
    show_mandate_allocation = meta_property('mandate_allocation')

    def clear_results(self):
        """ Clears all own results. """

        session = object_session(self)
        for result in self.party_results:
            session.delete(result)
        for result in self.panachage_results:
            session.delete(result)

    def export(self, consider_completed=False):
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
        for locale in election_day_i18n_used_locales:
            common[f'compound_title_{locale}'] = \
                self.title_translations.get(locale, '')
        for locale, title in self.title_translations.items():
            common[f'compound_title_{locale}'] = (title or '').strip()
        common['compound_date'] = self.date.isoformat()
        common['compound_mandates'] = self.number_of_mandates

        rows = []
        for election in self.elections:
            for row in election.export(consider_completed):
                rows.append(
                    OrderedDict(list(common.items()) + list(row.items()))
                )
        return rows
