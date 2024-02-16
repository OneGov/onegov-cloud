from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.vote.ballot_result import BallotResult
from onegov.ballot.models.vote.mixins import DerivedAttributesMixin
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UUID
from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Mapping
    from onegov.ballot.types import BallotType
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import Query
    from sqlalchemy.sql import ColumnElement
    from typing import NamedTuple

    from .vote import Vote

    class ResultsByDistrictRow(NamedTuple):
        name: str
        counted: bool
        accepted: bool
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
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: external identifier
    external_id: 'Column[str | None]' = Column(Text, nullable=True)

    #: the type of the ballot, 'standard' for normal votes, 'counter-proposal'
    #: if there's an alternative to the standard ballot. And 'tie-breaker',
    #: which must exist if there's a counter proposal. The tie breaker is
    #: only relevant if both standard and counter proposal are accepted.
    #: If that's the case, the accepted tie breaker selects the standard,
    #: the rejected tie breaker selects the counter proposal.
    type: 'Column[BallotType]' = Column(
        Enum(  # type:ignore[arg-type]
            'proposal',
            'counter-proposal',
            'tie-breaker',
            name='ballot_result_type'
        ),
        nullable=False
    )

    #: identifies the vote this ballot result belongs to
    vote_id: 'Column[str]' = Column(
        Text, ForeignKey('votes.id', onupdate='CASCADE'), nullable=False
    )

    #: all translations of the title
    title_translations: 'Column[Mapping[str, str] | None]' = Column(
        HSTORE,
        nullable=True
    )

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    #: a ballot contains n results
    results: 'relationship[AppenderQuery[BallotResult]]' = relationship(
        'BallotResult',
        cascade='all, delete-orphan',
        backref=backref('ballot'),
        lazy='dynamic',
        order_by='BallotResult.district, BallotResult.name',
    )

    if TYPE_CHECKING:
        # backrefs
        vote: relationship[Vote]

    @property
    def results_by_district(self) -> 'Query[ResultsByDistrictRow]':
        """ Returns the results aggregated by the distict.  """

        counted = func.coalesce(func.bool_and(BallotResult.counted), False)
        yeas = func.sum(BallotResult.yeas)
        nays = func.sum(BallotResult.nays)
        yeas_percentage = 100 * yeas / (
            cast(func.coalesce(func.nullif(yeas + nays, 0), 1), Float)
        )
        nays_percentage = 100 - yeas_percentage
        accepted = case({True: yeas > nays}, counted)
        results = self.results.with_entities(
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

    if TYPE_CHECKING:
        counted: Column[bool]

    @hybrid_property  # type:ignore[no-redef]
    def counted(self) -> bool:
        """ True if all results have been counted. """

        result = self.results.with_entities(
            func.coalesce(func.bool_and(BallotResult.counted), False)
        )
        result = result.order_by(None)
        result = result.first()
        return result[0] if result else False

    @counted.expression  # type:ignore[no-redef]
    def counted(cls) -> 'ColumnElement[bool]':
        expr = select([
            func.coalesce(func.bool_and(BallotResult.counted), False)
        ])
        expr = expr.where(BallotResult.ballot_id == cls.id)
        return expr.label('counted')

    @property
    def progress(self) -> tuple[int, int]:
        """ Returns a tuple with the first value being the number of counted
        ballot results and the second value being the number of total ballot
        results.

        """

        query = object_session(self).query(BallotResult)
        query = query.with_entities(BallotResult.counted)
        query = query.filter(BallotResult.ballot_id == self.id)

        results = query.all()

        return sum(1 for r in results if r[0]), len(results)

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
        result = self.results.with_entities(
            func.sum(getattr(BallotResult, attribute))
        )
        result = result.order_by(None)
        result = result.first()
        return (result[0] or 0) if result else 0

    @staticmethod
    def aggregate_results_expression(
        cls: 'Ballot',
        attribute: str
    ) -> 'ColumnElement[int]':
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([
            func.coalesce(
                func.sum(getattr(BallotResult, attribute)),
                0
            )
        ])
        expr = expr.where(BallotResult.ballot_id == cls.id)
        return expr.label(attribute)

    def clear_results(self) -> None:
        """ Clear all the results. """

        session = object_session(self)
        session.query(BallotResult).filter(
            BallotResult.ballot_id == self.id
        ).delete()
