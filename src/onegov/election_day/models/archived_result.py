from __future__ import annotations

from copy import deepcopy
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins.content import dictionary_based_property_factory
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.election_day.models.election import Election
from onegov.election_day.models.election_compound import ElectionCompound
from onegov.election_day.models.mixins import DomainOfInfluenceMixin
from onegov.election_day.models.mixins import TitleTranslationsMixin
from onegov.election_day.models.vote import Vote, ComplexVote
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4

from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    import uuid
    from builtins import type as _type
    from collections.abc import Mapping
    from onegov.election_day.request import ElectionDayRequest
    from typing import Literal
    from typing import Self
    from typing import TypeAlias

    ResultType: TypeAlias = Literal['election', 'election_compound', 'vote']

meta_local_property = dictionary_based_property_factory('local')


class ArchivedResult(Base, ContentMixin, TimestampMixin,
                     DomainOfInfluenceMixin, TitleTranslationsMixin):
    """ Stores the result of an election or vote. """

    __tablename__ = 'archived_results'

    #: Identifies the result
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The date of the election/vote
    date: Column[datetime.date] = Column(Date, nullable=False)

    #: The last change of the results election/vote
    last_modified: Column[datetime.datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )

    #: The last change of election/vote
    last_result_change: Column[datetime.datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )

    #: Type of the result
    type: Column[ResultType] = Column(
        Enum(  # type:ignore[arg-type]
            'vote', 'election', 'election_compound',
            name='type_of_result'
        ),
        nullable=False
    )

    #: Origin of the result
    schema: Column[str] = Column(Text, nullable=False)

    #: The name of the principal
    name: Column[str] = Column(Text, nullable=False)

    #: Total number of political entities
    total_entities: Column[int | None] = Column(Integer, nullable=True)

    #: Number of already counted political entities
    counted_entities: Column[int | None] = Column(Integer, nullable=True)

    @property
    def vote_finalized(self) -> bool:
        return self.counted_entities == self.total_entities

    @property
    def progress(self) -> tuple[int, int]:
        return self.counted_entities or 0, self.total_entities or 0

    #: Number of already counted political entities
    has_results: Column[bool | None] = Column(Boolean, nullable=True)

    #: The link to the detailed results
    url: Column[str] = Column(Text, nullable=False)

    #: Title of the election/vote
    title_translations: Column[Mapping[str, str]] = Column(
        HSTORE,
        nullable=False
    )
    title = translation_hybrid(title_translations)

    title_proposal: dict_property[str] = meta_property(
        'title_proposal',
        default=''
    )

    title_counter_proposal: dict_property[str] = meta_property(
        'title_counter_proposal',
        default=''
    )

    title_tie_breaker: dict_property[str] = meta_property(
        'title_tie_breaker',
        default=''
    )

    def title_prefix(self, request: ElectionDayRequest) -> str:
        if self.is_fetched(request) and self.domain == 'municipality':
            return self.name or ''

        return ''

    #: Shortcode for cantons that use it
    shortcode: Column[str | None] = Column(Text, nullable=True)

    #: The id of the election/vote.
    external_id: dict_property[str | None] = meta_property('id')

    #: The names of the elected candidates.
    elected_candidates: dict_property[list[tuple[str, str]]] = meta_property(
        'elected_candidates',
        default=list
    )

    #: The URLs of the elections (if it is a compound)
    elections: dict_property[list[str]] = meta_property(
        'elections',
        default=list
    )

    #: The answer of a vote (accepted, rejected, counter-proposal).
    answer: dict_property[str] = meta_property('answer', default='')

    #: The nays rate of a vote.
    nays_percentage: dict_property[float] = meta_property(
        'nays_percentage',
        default=100.0
    )

    #: The yeas rate of a vote.
    yeas_percentage: dict_property[float] = meta_property(
        'yeas_percentage',
        default=0.0
    )

    #: The nays rate of a vote proposal for complex votes.
    nays_percentage_proposal: dict_property[float] = meta_property(
        'nays_percentage_proposal',
        default=100.0
    )

    #: The yeas rate of a vote.
    yeas_percentage_proposal: dict_property[float] = meta_property(
        'yeas_percentage_proposal',
        default=0.0
    )

    #: The nays rate of a vote counterproposal for complex votes.
    nays_percentage_counter_proposal: dict_property[float] = meta_property(
        'nays_percentage_counter_proposal',
        default=100.0
    )

    #: The yeas rate of a vote counterproposal for complex votes.
    yeas_percentage_counter_proposal: dict_property[float] = meta_property(
        'yeas_percentage_counter_proposal',
        default=0.0
    )

    #: The nays rate of a vote tiebreaker for complex votes.
    nays_percentage_tie_breaker: dict_property[float] = meta_property(
        'nays_percentage_tie_breaker',
        default=100.0
    )

    #: The yeas rate of a vote tiebreaker for complex votes.
    yeas_percentage_tie_breaker: dict_property[float] = meta_property(
        'yeas_percentage_tie_breaker',
        default=0.0
    )

    #: True, if the vote or election has been counted.
    counted: dict_property[bool] = meta_property('counted', default=False)

    #: True, if the vote or election has been completed.
    completed: dict_property[bool] = meta_property(
        'completed',
        default=False
    )

    #: Turnout (vote/elections)
    turnout: dict_property[float | None] = meta_property('turnout')

    #: True, if this is direct complex vote
    direct: dict_property[bool] = meta_property(
        'direct',
        default=True
    )

    #: The local results (municipal results if fetched from cantonal instance)
    local: dict_property[dict[str, Any] | None] = meta_property('local')

    #: The answer if this a fetched cantonal/federal result on a communal
    #: instance.
    local_answer: dict_property[str] = meta_local_property('answer', '')

    #: The nays rate if this a fetched cantonal/federal result on a communal
    #: instance.
    local_nays_percentage: dict_property[float] = meta_local_property(
        'nays_percentage',
        100.0
    )

    #: The yeas rate if this a fetched cantonal/federal result on a communal
    #: instance.
    local_yeas_percentage: dict_property[float] = meta_local_property(
        'yeas_percentage',
        0.0
    )

    @property
    def type_class(self) -> _type[Election | ElectionCompound | Vote]:
        if self.type == 'vote':
            return Vote
        elif self.type == 'election':
            return Election
        elif self.type == 'election_compound':
            return ElectionCompound
        raise NotImplementedError

    def is_complex_vote(self, request: ElectionDayRequest) -> bool:
        """ Returns True if this result represents a complex vote. """
        # circular import
        from onegov.election_day.collections import VoteCollection

        if not self.external_id:
            return False

        vote = VoteCollection(request.session).by_id(self.external_id)
        if isinstance(vote, ComplexVote):  # other options to test? new column?
            # test if additional columns filled, otherwise populate them
            if (self.nays_percentage_proposal == 100.0 or
                    self.yeas_percentage_proposal == 0.0 or
                    self.nays_percentage_counter_proposal == 100.0 or
                    self.yeas_percentage_counter_proposal == 0.0 or
                    self.nays_percentage_tie_breaker == 100.0 or
                    self.yeas_percentage_tie_breaker == 0.0 or
                    self.title_proposal == ''):
                for ballot in vote.ballots:
                    if ballot.type == 'proposal':
                        self.title_proposal = ballot.title or self.title or ''
                        self.nays_percentage_proposal = ballot.nays_percentage
                        self.yeas_percentage_proposal = ballot.yeas_percentage
                    if ballot.type == 'counter-proposal':
                        self.title_counter_proposal = ballot.title or ''
                        self.nays_percentage_counter_proposal = (
                            ballot.nays_percentage)
                        self.yeas_percentage_counter_proposal = (
                            ballot.yeas_percentage)
                    if ballot.type == 'tie-breaker':
                        self.title_tie_breaker = ballot.title or ''
                        self.nays_percentage_tie_breaker = (
                            ballot.nays_percentage)
                        self.yeas_percentage_tie_breaker = (
                            ballot.yeas_percentage)

            return True

        return False

    def is_fetched(self, request: ElectionDayRequest) -> bool:
        """ Returns True, if this results has been fetched from another
        instance.

        """
        return self.schema != request.app.schema

    def is_fetched_by_municipality(
        self,
        request: ElectionDayRequest
    ) -> bool:
        """ Returns True, if this results has been fetched from another
        instance by a communal instance.

        """
        return (
            self.is_fetched(request)
            and request.app.principal.domain == 'municipality'
        )

    def adjusted_url(self, request: ElectionDayRequest) -> str:
        """ Returns the url adjusted to the current host. Needed if the
        instance is accessible under different hosts at the same time.

        """
        if self.is_fetched(request):
            return self.url

        return request.class_link(
            self.type_class,
            {'id': self.external_id}
        )

    def display_answer(self, request: ElectionDayRequest) -> str:
        """ Returns the answer (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_answer
        return self.answer

    def display_nays_percentage(self, request: ElectionDayRequest) -> float:
        """ Returns the nays rate (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_nays_percentage
        return self.nays_percentage

    def display_yeas_percentage(self, request: ElectionDayRequest) -> float:
        """ Returns the yeas rate (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_yeas_percentage
        return self.yeas_percentage

    def display_nays_percentage_proposal(self) -> float:
        """ Returns the proposal nays rate for complex votes. """
        return self.nays_percentage_proposal

    def display_yeas_percentage_proposal(self) -> float:
        """ Returns the proposal yeas rate for complex votes. """
        return self.yeas_percentage_proposal

    def display_nays_percentage_counter_proposal(self) -> float:
        """ Returns the counterproposal nays rate for complex votes. """
        return self.nays_percentage_counter_proposal

    def display_yeas_percentage_counter_proposal(self) -> float:
        """ Returns the counterproposal yeas rate for complex votes. """
        return self.yeas_percentage_counter_proposal

    def display_nays_percentage_tie_breaker(self) -> float:
        """ Returns the tiebreaker nays rate for complex votes. """
        return self.nays_percentage_tie_breaker

    def display_yeas_percentage_tie_breaker(self) -> float:
        """ Returns the tiebreaker yeas rate for complex votes. """
        return self.yeas_percentage_tie_breaker

    def copy_from(self, source: Self) -> None:
        self.date = source.date
        self.last_modified = source.last_modified
        self.last_result_change = source.last_result_change
        self.type = source.type
        self.schema = source.schema
        self.name = source.name
        self.total_entities = source.total_entities
        self.counted_entities = source.counted_entities
        self.has_results = source.has_results
        self.url = source.url
        self.title_translations = deepcopy(dict(source.title_translations))
        self.shortcode = source.shortcode
        self.domain = source.domain
        self.meta = deepcopy(dict(source.meta))
