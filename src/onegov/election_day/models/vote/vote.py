from __future__ import annotations

import datetime

from collections.abc import Mapping
from onegov.core.orm import Base, observes
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from onegov.election_day.models.mixins import DomainOfInfluenceMixin
from onegov.election_day.models.mixins import ExplanationsPdfMixin
from onegov.election_day.models.mixins import IdFromTitlesMixin
from onegov.election_day.models.mixins import LastModifiedMixin
from onegov.election_day.models.mixins import StatusMixin
from onegov.election_day.models.mixins import summarized_property
from onegov.election_day.models.mixins import TitleTranslationsMixin
from onegov.election_day.models.vote.ballot import Ballot
from onegov.election_day.models.vote.mixins import DerivedBallotsCountMixin
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DynamicMapped
from sqlalchemy.orm import Mapped
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import DataSourceItem
    from onegov.election_day.models import Notification
    from onegov.election_day.models import Screen
    from onegov.election_day.types import BallotType
    from sqlalchemy.sql import ColumnElement


class Vote(
    Base, ContentMixin, LastModifiedMixin, DomainOfInfluenceMixin,
    StatusMixin, TitleTranslationsMixin, IdFromTitlesMixin,
    DerivedBallotsCountMixin, ExplanationsPdfMixin
):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    @property
    def polymorphic_base(self) -> type[Vote]:
        return Vote

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column()

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'simple'
    }

    #: identifies the vote, may be used in the url, generated from the title
    id: Mapped[str] = mapped_column(primary_key=True)

    #: external identifier
    external_id: Mapped[str | None]

    #: shortcode for cantons that use it
    shortcode: Mapped[str | None]

    #: all translations of the title
    title_translations: Mapped[Mapping[str, str]] = mapped_column(HSTORE)

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    #: all translations of the short title
    short_title_translations: Mapped[Mapping[str, str] | None] = mapped_column(
        HSTORE
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
            session = object_session(self)
            assert session is not None
            self.id = self.id_from_title(session)

    #: identifies the date of the vote
    date: Mapped[datetime.date]

    #: a vote contains n ballots
    ballots: Mapped[list[Ballot]] = relationship(
        cascade='all, delete-orphan',
        order_by='Ballot.type',
        lazy='selectin',
        back_populates='vote'
    )

    def ballot(
        self,
        ballot_type: BallotType
    ) -> Ballot:
        """ Returns the given ballot if it exists, creates it if not. """

        result = None
        for ballot in self.ballots:
            if ballot.type == ballot_type:
                result = ballot
                break

        if not result:
            result = Ballot(id=uuid4(), type=ballot_type)
            self.ballots.append(result)

        return result

    @property
    def proposal(self) -> Ballot:
        return self.ballot('proposal')

    @property
    def counted(self) -> bool:  # type:ignore[override]
        """ Checks if there are results for all entities. """

        if not self.ballots:
            return False

        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

    @property
    def has_results(self) -> bool:
        """ Returns True, if there are any results. """

        for ballot in self.ballots:
            for result in ballot.results:
                if result.counted:
                    return True

        return False

    @property
    def answer(self) -> str | None:
        if not self.counted or not self.proposal:
            return None

        if self.tie_breaker_vocabulary:
            return 'proposal' if self.proposal.accepted else 'counter-proposal'

        return 'accepted' if self.proposal.accepted else 'rejected'

    @property
    def yeas_percentage(self) -> float:
        """ The percentage of yeas (discounts empty/invalid ballots). """

        return self.yeas / ((self.yeas + self.nays) or 1) * 100

    @property
    def nays_percentage(self) -> float:
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @property
    def progress(self) -> tuple[int, int]:
        """ Returns a tuple with the first value being the number of counted
        entities and the second value being the number of total entities.

        For complex votes, it is assumed that every ballot has the same
        progress.
        """

        if not self.proposal or not self.proposal.results:
            return 0, 0

        return (
            sum(1 for result in self.proposal.results if result.counted),
            len(self.proposal.results)
        )

    @property
    def counted_entities(self) -> list[str]:
        """ Returns the names of the already counted entities.

        Might contain an empty string in case of expats.

        For complex votes, it is assumed that every ballot has the same
        progress.
        """

        if not self.proposal or not self.proposal.results:
            return []

        return sorted(
            result.name for result in self.proposal.results if result.counted
        )

    #: the total yeas
    yeas = summarized_property('yeas')

    #: the total nays
    nays = summarized_property('nays')

    #: the total empty votes
    empty = summarized_property('empty')

    #: the total invalid votes
    invalid = summarized_property('invalid')

    #: the total eligible voters
    eligible_voters = summarized_property('eligible_voters')

    #: the total expats
    expats = summarized_property('expats')

    def aggregate_results(self, attribute: str) -> int:
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(ballot, attribute) for ballot in self.ballots)

    @classmethod
    def aggregate_results_expression(
        cls,
        attribute: str
    ) -> ColumnElement[int]:
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select(
            func.coalesce(
                func.sum(getattr(Ballot, attribute)),
                0
            )
        )
        expr = expr.where(Ballot.vote_id == cls.id)
        return expr.label(attribute)

    @hybrid_property
    def last_ballot_change(self) -> datetime.datetime | None:
        """ Returns last change of the vote, its ballots and any of its
        results.

        """
        changes = [
            change
            for ballot in self.ballots
            if (change := ballot.last_change)
        ]
        return max(changes) if changes else None

    @last_ballot_change.inplace.expression
    @classmethod
    def _last_ballot_change_expression(
        cls
    ) -> ColumnElement[datetime.datetime | None]:
        expr = select(func.max(Ballot.last_change))
        expr = expr.where(Ballot.vote_id == cls.id)
        return expr.label('last_ballot_change')

    @hybrid_property
    def last_modified(self) -> datetime.datetime | None:
        """ Returns last change of the vote, its ballots and any of its
        results.

        """
        changes = [
            change
            for ballot in self.ballots
            if (change := ballot.last_change)
        ]

        last_change = self.last_change
        if last_change is not None:
            changes.append(last_change)

        last_result_change = self.last_result_change
        if last_result_change is not None:
            changes.append(last_result_change)

        return max(changes) if changes else None

    @last_modified.inplace.expression
    @classmethod
    def _last_modified_expression(
        cls
    ) -> ColumnElement[datetime.datetime | None]:
        return func.greatest(
            cls.last_change, cls.last_result_change, cls.last_ballot_change
        )

    #: data source items linked to this vote
    data_sources: Mapped[list[DataSourceItem]] = relationship(
        back_populates='vote'
    )

    #: notifcations linked to this vote
    notifications: DynamicMapped[Notification] = relationship(
        'onegov.election_day.models.notification.Notification',
        back_populates='vote',
    )

    #: screens linked to this vote
    screens: DynamicMapped[Screen] = relationship(
        back_populates='vote',
    )

    #: may be used to store a link related to this vote
    related_link: dict_property[str | None] = meta_property('related_link')

    #: Additional, translatable label for the link
    related_link_label: dict_property[dict[str, str] | None] = meta_property(
        'related_link_label'
    )

    #: may be used to indicate that the vote contains expats as seperate
    #: resultas (typically with entity_id = 0)
    has_expats: dict_property[bool] = meta_property('expats', default=False)

    #: The segment of the domain. This might be the municipality, if this is a
    #: communal vote.
    domain_segment: dict_property[str] = meta_property(
        'domain_segment',
        default=''
    )

    #: Use the vocabulary of a tie breaker. This is a silly trick introduced
    #: 2024 by ZG in the course of the transparency initiative and only used
    #: there - all other principals use a proper complex vote.
    tie_breaker_vocabulary: dict_property[bool] = meta_property(
        'tie_breaker_vocabulary',
        default=False
    )

    #: direct or indirect counter/proposal
    direct: dict_property[bool] = meta_property('direct', default=True)

    def clear_results(self, clear_all: bool = False) -> None:
        """ Clear all the results. """

        self.status = None
        self.last_result_change = None

        if clear_all:
            self.ballots = []
        else:
            for ballot in self.ballots:
                ballot.clear_results()
