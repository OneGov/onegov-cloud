from __future__ import annotations

from onegov.core.orm import Base, observes
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from onegov.election_day.models.election.candidate import Candidate
from onegov.election_day.models.election.election_result import ElectionResult
from onegov.election_day.models.election.mixins import DerivedAttributesMixin
from onegov.election_day.models.mixins import DomainOfInfluenceMixin
from onegov.election_day.models.mixins import ExplanationsPdfMixin
from onegov.election_day.models.mixins import IdFromTitlesMixin
from onegov.election_day.models.mixins import LastModifiedMixin
from onegov.election_day.models.mixins import StatusMixin
from onegov.election_day.models.mixins import summarized_property
from onegov.election_day.models.mixins import TitleTranslationsMixin
from onegov.election_day.models.party_result.mixins import (
    PartyResultsOptionsMixin)
from operator import itemgetter
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from collections.abc import Mapping
    from onegov.core.types import AppenderQuery
    from onegov.election_day.models import DataSourceItem
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import ElectionRelationship
    from onegov.election_day.models import Notification
    from onegov.election_day.models import Screen
    from sqlalchemy.orm import Query
    from sqlalchemy.sql import ColumnElement
    from typing import NamedTuple

    class VotesByDistrictRow(NamedTuple):
        election_id: str
        district: str
        entities: list[int]
        counted: bool
        votes: int


class Election(Base, ContentMixin, LastModifiedMixin,
               DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
               IdFromTitlesMixin, DerivedAttributesMixin, ExplanationsPdfMixin,
               PartyResultsOptionsMixin):

    __tablename__ = 'elections'

    @property
    def polymorphic_base(self) -> type[Election]:
        return Election

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(Text, nullable=False)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'majorz'
    }

    #: Identifies the election, may be used in the url
    id: Column[str] = Column(Text, primary_key=True)

    #: external identifier
    external_id: Column[str | None] = Column(Text, nullable=True)

    #: all translations of the title
    title_translations: Column[Mapping[str, str]] = Column(
        HSTORE,
        nullable=False
    )

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    #: all translations of the short title
    short_title_translations: Column[Mapping[str, str] | None] = Column(
        HSTORE,
        nullable=True
    )

    #: the translated short title (uses the locale of the request, falls back
    #: to the default locale of the app)
    short_title = translation_hybrid(short_title_translations)

    @observes('title_translations', 'short_title_translations')
    def title_observer(
        self,
        title_translations: Mapping[str, str],
        short_title_translations: Mapping[str, str]
    ) -> None:
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: Shortcode for cantons that use it
    shortcode: Column[str | None] = Column(Text, nullable=True)

    #: The date of the election
    date: Column[datetime.date] = Column(Date, nullable=False)

    #: Number of mandates
    number_of_mandates: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    @property
    def allocated_mandates(self) -> int:
        """ Number of already allocated mandates/elected candidates. """

        # Unless an election is finished, allocated mandates are 0
        if not self.completed:
            return 0

        return sum(c.elected for c in self.candidates)

    #: Defines the type of majority (e.g. 'absolute', 'relative')
    majority_type: dict_property[str | None] = meta_property('majority_type')

    #: Absolute majority
    absolute_majority: Column[int | None] = Column(Integer, nullable=True)

    if TYPE_CHECKING:
        counted: Column[bool]

    @hybrid_property  # type:ignore[no-redef]
    def counted(self) -> bool:
        """ True if all results have been counted. """

        if not self.results:
            return False

        return all(r.counted for r in self.results)

    @counted.expression  # type:ignore[no-redef]
    def counted(cls) -> ColumnElement[bool]:
        expr = select([
            func.coalesce(func.bool_and(ElectionResult.counted), False)
        ])
        expr = expr.where(ElectionResult.election_id == cls.id)
        expr = expr.label('counted')

        return expr

    @property
    def progress(self) -> tuple[int, int]:
        """ Returns a tuple with the first value being the number of counted
        election results and the second value being the number of total
        results.

        """

        return sum(r.counted for r in self.results), len(self.results)

    @property
    def counted_entities(self) -> list[str]:
        """ Returns the names of the already counted entities.

        Might contain an empty string in case of expats.

        """

        return sorted(r.name for r in self.results if r.counted)

    @property
    def has_results(self) -> bool:
        """ Returns True, if the election has any results. """

        for result in self.results:
            if result.counted:
                return True
        return False

    #: An election contains n candidates
    candidates: relationship[list[Candidate]] = relationship(
        'Candidate',
        cascade='all, delete-orphan',
        back_populates='election',
        order_by='Candidate.candidate_id',
    )

    #: An election contains n results, one for each political entity
    results: relationship[list[ElectionResult]] = relationship(
        'ElectionResult',
        cascade='all, delete-orphan',
        back_populates='election',
        order_by='ElectionResult.district, ElectionResult.name',
    )

    @property
    def results_query(self) -> Query[ElectionResult]:
        session = object_session(self)
        query = session.query(ElectionResult)
        query = query.filter(ElectionResult.election_id == self.id)
        query = query.order_by(ElectionResult.district, ElectionResult.name)
        return query

    #: An election may have related elections
    related_elections: relationship[AppenderQuery[ElectionRelationship]] = (
        relationship(
            'ElectionRelationship',
            foreign_keys='ElectionRelationship.source_id',
            cascade='all, delete-orphan',
            back_populates='source',
            lazy='dynamic'
        )
    )

    #: An election may be related by other elections
    referencing_elections: (
        relationship[AppenderQuery[ElectionRelationship]]) = (
        relationship(
            'ElectionRelationship',
            foreign_keys='ElectionRelationship.target_id',
            cascade='all, delete-orphan',
            back_populates='target',
            lazy='dynamic'
        )
    )

    #: An election may be part of an election compound
    election_compound_id: Column[str | None] = Column(
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE'),
        nullable=True
    )

    #: The election compound this election belongs to
    election_compound: relationship[ElectionCompound] = relationship(
        'ElectionCompound',
        back_populates='elections'
    )

    @property
    def completed(self) -> bool:
        """ Overwrites StatusMixin's 'completed' for compounds with manual
        completion. """

        result = super().completed

        compound = self.election_compound
        if compound and compound.completes_manually:
            return compound.manually_completed and result

        return result

    #: The total eligible voters
    eligible_voters = summarized_property('eligible_voters')

    #: The expats
    expats = summarized_property('expats')

    #: The total received ballots
    received_ballots = summarized_property('received_ballots')

    #: The total accounted ballots
    accounted_ballots = summarized_property('accounted_ballots')

    #: The total blank ballots
    blank_ballots = summarized_property('blank_ballots')

    #: The total invalid ballots
    invalid_ballots = summarized_property('invalid_ballots')

    #: The total accounted votes
    accounted_votes = summarized_property('accounted_votes')

    def aggregate_results(self, attribute: str) -> int:
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(result, attribute) or 0 for result in self.results)

    @classmethod
    def aggregate_results_expression(
        cls,
        attribute: str
    ) -> ColumnElement[int]:
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([
            func.coalesce(
                func.sum(getattr(ElectionResult, attribute)),
                0
            )
        ])
        expr = expr.where(ElectionResult.election_id == cls.id)
        return expr.label(attribute)

    @property
    def elected_candidates(self) -> list[tuple[str, str]]:
        """ Returns the first and last names of the elected candidates. """

        return sorted(
            (
                (c.first_name, c.family_name)
                for c in self.candidates if c.elected
            ),
            key=itemgetter(1, 0)
        )

    #: may be used to store a link related to this election
    related_link: dict_property[str | None] = meta_property('related_link')
    related_link_label: dict_property[dict[str, str] | None] = meta_property(
        'related_link_label'
    )

    #: may be used to mark an election as a tacit election
    tacit: dict_property[bool] = meta_property('tacit', default=False)

    #: may be used to indicate that the vote contains expats as seperate
    #: results (typically with entity_id = 0)
    has_expats: dict_property[bool] = meta_property('expats', default=False)

    #: The segment of the domain. This might be the district, if this is a
    #: regional (district) election; the region, if it's a regional (region)
    #: election or the municipality, if this is a communal election.
    domain_segment: dict_property[str] = meta_property(
        'domain_segment',
        default=''
    )

    #: The supersegment of the domain. This might be superregion, if it's a
    #: regional (region) election.
    domain_supersegment: dict_property[str] = meta_property(
        'domain_supersegment',
        default=''
    )

    @property
    def votes_by_district(self) -> Query[VotesByDistrictRow]:
        query = self.results_query.order_by(None)
        results = query.with_entities(
            self.__class__.id.label('election_id'),
            ElectionResult.district,
            func.array_agg(
                ElectionResult.entity_id.distinct()).label('entities'),
            func.coalesce(
                func.bool_and(ElectionResult.counted), False
            ).label('counted'),
            func.coalesce(
                func.sum(ElectionResult.accounted_ballots), 0).label('votes')
        )
        results = results.group_by(
            ElectionResult.district,
            self.__class__.id.label('election_id')
        )
        return results

    #: Defines optional colors for lists and parties
    colors: dict_property[dict[str, str]] = meta_property(
        'colors',
        default=dict
    )

    def clear_results(self, clear_all: bool = False) -> None:
        """ Clears all the results. """

        self.absolute_majority = None
        self.status = None
        self.last_result_change = None

        session = object_session(self)
        if clear_all:
            session.query(Candidate).filter(
                Candidate.election_id == self.id
            ).delete()
        session.query(ElectionResult).filter(
            ElectionResult.election_id == self.id
        ).delete()
        session.flush()
        session.expire_all()

    #: data source items linked to this election
    data_sources: relationship[list[DataSourceItem]] = relationship(
        'DataSourceItem',
        back_populates='election'
    )

    #: notifcations linked to this election
    notifications: relationship[AppenderQuery[Notification]] = (
        relationship(  # type:ignore[misc]
            'onegov.election_day.models.notification.Notification',
            back_populates='election',
            lazy='dynamic'
        )
    )

    #: screens linked to this election
    screens: relationship[AppenderQuery[Screen]] = relationship(
        'Screen',
        back_populates='election',
    )
