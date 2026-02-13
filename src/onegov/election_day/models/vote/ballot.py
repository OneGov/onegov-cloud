from __future__ import annotations

from collections.abc import Mapping
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.election_day.models.mixins import summarized_property
from onegov.election_day.models.mixins import TitleTranslationsMixin
from onegov.election_day.models.vote.ballot_result import BallotResult
from onegov.election_day.models.vote.mixins import DerivedAttributesMixin
from onegov.election_day.models.vote.mixins import DerivedBallotsCountMixin
from onegov.election_day.types import BallotType
from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Vote
    from sqlalchemy.orm import Query
    from sqlalchemy.sql import ColumnElement
    from typing import NamedTuple

    class ResultsByDistrictRow(NamedTuple):
        name: str
        counted: bool
        accepted: bool | None
        yeas: int
        nays: int
        yeas_percentage: float
        nays_percentage: float
        empty: int
        invalid: int
        eligible_voters: int
        entity_ids: list[int]


class Ballot(Base, TimestampMixin, TitleTranslationsMixin,
             DerivedAttributesMixin, DerivedBallotsCountMixin):
    """ A ballot contains a single question asked for a vote.

    Usually each vote has exactly one ballot, but it's possible for votes to
    have multiple ballots.

    In the latter case there are usually two options that are mutually
    exclusive and a third option that acts as a tie breaker between
    the frist two options.

    The type of the ballot indicates this. Standard ballots only contain
    one question, variant ballots contain multiple questions.

    """

    __tablename__ = 'ballots'

    #: identifies the ballot, maybe used in the url
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: external identifier
    external_id: Mapped[str | None]

    #: the type of the ballot, 'standard' for normal votes, 'counter-proposal'
    #: if there's an alternative to the standard ballot. And 'tie-breaker',
    #: which must exist if there's a counter proposal. The tie breaker is
    #: only relevant if both standard and counter proposal are accepted.
    #: If that's the case, the accepted tie breaker selects the standard,
    #: the rejected tie breaker selects the counter proposal.
    type: Mapped[BallotType] = mapped_column(
        Enum(
            'proposal',
            'counter-proposal',
            'tie-breaker',
            name='ballot_result_type'
        )
    )

    #: identifies the vote this ballot result belongs to
    vote_id: Mapped[str] = mapped_column(
        ForeignKey('votes.id', onupdate='CASCADE')
    )

    #: all translations of the title
    title_translations: Mapped[Mapping[str, str] | None] = mapped_column(
        HSTORE
    )

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    #: a ballot contains n results
    results: Mapped[list[BallotResult]] = relationship(
        cascade='all, delete-orphan',
        back_populates='ballot',
        order_by='BallotResult.district, BallotResult.name',
    )

    vote: Mapped[Vote] = relationship(back_populates='ballots')

    @property
    def results_by_district(self) -> Query[ResultsByDistrictRow]:
        """ Returns the results aggregated by the distict.  """
        session = object_session(self)
        assert session is not None

        counted = func.coalesce(func.bool_and(BallotResult.counted), False)
        yeas = func.sum(BallotResult.yeas)
        nays = func.sum(BallotResult.nays)
        yeas_percentage = 100 * yeas / (
            cast(func.coalesce(func.nullif(yeas + nays, 0), 1), Float)
        )
        nays_percentage = 100 - yeas_percentage
        accepted = case(
            (counted.is_(False), None),
            (yeas > nays, True),
            else_=False
        )
        results = session.query(BallotResult).filter(
            BallotResult.ballot_id == self.id
        ).with_entities(
            BallotResult.district.label('name'),
            counted.label('counted'),
            accepted.label('accepted'),
            yeas.label('yeas'),
            nays.label('nays'),
            yeas_percentage.label('yeas_percentage'),
            nays_percentage.label('nays_percentage'),
            func.sum(BallotResult.empty).label('empty'),
            func.sum(BallotResult.invalid).label('invalid'),
            func.sum(BallotResult.eligible_voters).label('eligible_voters'),
            func.array_agg(BallotResult.entity_id).label('entity_ids')
        )
        results = results.group_by(BallotResult.district)
        results = results.order_by(None).order_by(BallotResult.district)
        return results

    @hybrid_property
    def counted(self) -> bool:
        """ True if all results have been counted. """
        if not self.results:
            return False

        return all(result.counted for result in self.results)

    @counted.inplace.expression
    @classmethod
    def _counted_expression(cls) -> ColumnElement[bool]:
        expr = select(
            func.coalesce(func.bool_and(BallotResult.counted), False)
        )
        expr = expr.where(BallotResult.ballot_id == cls.id)
        return expr.label('counted')

    @property
    def progress(self) -> tuple[int, int]:
        """ Returns a tuple with the first value being the number of counted
        ballot results and the second value being the number of total ballot
        results.

        """

        return (
            sum(1 for result in self.results if result.counted),
            len(self.results)
        )

    @property
    def answer(self) -> str | None:
        if not self.counted:
            return None

        if self.type == 'tie-breaker':
            return 'proposal' if self.accepted else 'counter-proposal'

        return 'accepted' if self.accepted else 'rejected'

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

        return sum(getattr(r, attribute, 0) or 0 for r in self.results)

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
                func.sum(getattr(BallotResult, attribute)),
                0
            )
        )
        expr = expr.where(BallotResult.ballot_id == cls.id)
        return expr.label(attribute)

    def clear_results(self, clear_all: bool = False) -> None:
        """ Clear all the results. """

        self.results = []
