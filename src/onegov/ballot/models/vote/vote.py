from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import ExplanationsPdfMixin
from onegov.ballot.models.mixins import LastModifiedMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.vote.ballot import Ballot
from onegov.ballot.models.vote.ballot_result import BallotResult
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from onegov.core.orm import Base, observes
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import overload, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from collections.abc import Mapping
    from onegov.ballot.types import BallotType
    from onegov.core.types import AppenderQuery
    from sqlalchemy.sql import ColumnElement


class Vote(Base, ContentMixin, LastModifiedMixin,
           DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
           DerivedBallotsCountMixin, ExplanationsPdfMixin):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    # FIXME: This should probably not be nullable
    type: 'Column[str | None]' = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'simple'
    }

    #: identifies the vote, may be used in the url, generated from the title
    id: 'Column[str]' = Column(Text, primary_key=True)

    #: external identifier
    external_id: 'Column[str | None]' = Column(Text, nullable=True)

    #: shortcode for cantons that use it
    shortcode: 'Column[str | None]' = Column(Text, nullable=True)

    #: all translations of the title
    title_translations: 'Column[Mapping[str, str]]' = Column(
        HSTORE,
        nullable=False
    )

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations: 'Mapping[str, str]') -> None:
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: identifies the date of the vote
    date: 'Column[datetime.date]' = Column(Date, nullable=False)

    #: a vote contains n ballots
    ballots: 'relationship[AppenderQuery[Ballot]]' = relationship(
        'Ballot',
        cascade='all, delete-orphan',
        order_by='Ballot.type',
        backref=backref('vote'),
        lazy='dynamic'
    )

    @overload
    def ballot(
        self,
        ballot_type: 'BallotType',
        create: Literal[True]
    ) -> Ballot: ...

    @overload
    def ballot(
        self,
        ballot_type: 'BallotType',
        create: bool = False
    ) -> Ballot | None: ...

    def ballot(
        self,
        ballot_type: 'BallotType',
        create: bool = False
    ) -> Ballot | None:
        """ Returns the given ballot if it exists. Optionally creates the
        ballot.

        """

        result = next((b for b in self.ballots if b.type == ballot_type), None)

        if not result and create:
            result = Ballot(id=uuid4(), type=ballot_type)
            self.ballots.append(result)

        return result

    @property
    def proposal(self) -> Ballot:
        return self.ballot('proposal', create=True)

    @property
    def counted(self) -> bool:  # type:ignore[override]
        """ Checks if there are results for all entitites. """

        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

    @property
    def has_results(self) -> bool:
        """ Returns True, if there are any results. """

        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            for result in ballot.results:
                if result.counted:
                    return True

        return False

    @property
    def answer(self) -> str | None:
        if not self.counted or not self.proposal:
            return None

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

        We assume that for complex votes, every ballot has the same progress.
        """

        ballot_ids = {b.id for b in self.ballots}

        if not ballot_ids:
            return 0, 0

        query = object_session(self).query(BallotResult)
        query = query.with_entities(BallotResult.counted)
        query = query.filter(BallotResult.ballot_id.in_(ballot_ids))

        results = query.all()
        divider = len(ballot_ids) or 1

        return (
            int(sum(1 for r in results if r[0]) / divider),
            int(len(results) / divider)
        )

    @property
    def counted_entities(self) -> list[str]:
        """ Returns the names of the already counted entities.

        Might contain an empty string in case of expats.

        """

        ballot_ids = {b.id for b in self.ballots}

        if not ballot_ids:
            return []

        query = object_session(self).query(BallotResult.name)
        query = query.filter(BallotResult.counted.is_(True))
        query = query.filter(BallotResult.ballot_id.in_(ballot_ids))
        query = query.order_by(BallotResult.name)
        query = query.distinct()
        return [result.name for result in query]

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

    @staticmethod
    def aggregate_results_expression(
        cls: 'Vote',
        attribute: str
    ) -> 'ColumnElement[int]':
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([
            func.coalesce(
                func.sum(getattr(Ballot, attribute)),
                0
            )
        ])
        expr = expr.where(Ballot.vote_id == cls.id)
        return expr.label(attribute)

    if TYPE_CHECKING:
        last_ballot_change: Column[datetime.datetime | None]
        last_modified: Column[datetime.datetime | None]

    @hybrid_property  # type:ignore[no-redef]
    def last_ballot_change(self) -> 'datetime.datetime | None':
        """ Returns last change of the vote, its ballots and any of its
        results.

        """
        changes = [
            change
            for ballot in self.ballots
            if (change := ballot.last_change)
        ]
        return max(changes) if changes else None

    @last_ballot_change.expression  # type:ignore[no-redef]
    def last_ballot_change(cls) -> 'ColumnElement[datetime.datetime | None]':
        expr = select([func.max(Ballot.last_change)])
        expr = expr.where(Ballot.vote_id == cls.id)
        expr = expr.label('last_ballot_change')
        return expr

    @hybrid_property  # type:ignore[no-redef]
    def last_modified(self) -> 'datetime.datetime | None':
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

    @last_modified.expression  # type:ignore[no-redef]
    def last_modified(cls) -> 'ColumnElement[datetime.datetime | None]':
        return func.greatest(
            cls.last_change, cls.last_result_change, cls.last_ballot_change
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

    def clear_results(self) -> None:
        """ Clear all the results. """

        self.status = None
        self.last_result_change = None

        for ballot in self.ballots:
            ballot.clear_results()
