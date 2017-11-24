from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.vote.ballot_result import BallotResult
from onegov.ballot.models.vote.mixins import DerivedAttributesMixin
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


class Ballot(Base, TimestampMixin, DerivedAttributesMixin,
             DerivedBallotsCountMixin):
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
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the type of the ballot, 'standard' for normal votes, 'counter-proposal'
    #: if there's an alternative to the standard ballot. And 'tie-breaker',
    #: which must exist if there's a counter proposal. The tie breaker is
    #: only relevant if both standard and counter proposal are accepted.
    #: If that's the case, the accepted tie breaker selects the standard,
    #: the rejected tie breaker selects the counter proposal.
    type = Column(
        Enum(
            'proposal', 'counter-proposal', 'tie-breaker',
            name='ballot_result_type'
        ),
        nullable=False
    )

    #: identifies the vote this ballot result belongs to
    vote_id = Column(Text, ForeignKey('votes.id'), nullable=False)

    #: title of the ballot
    title_translations = Column(HSTORE, nullable=True)
    title = translation_hybrid(title_translations)

    #: a ballot contains n results
    results = relationship(
        'BallotResult',
        cascade='all, delete-orphan',
        backref=backref('ballot'),
        lazy='dynamic',
        order_by='BallotResult.group',
    )

    @hybrid_property
    def counted(self):
        """ True if all results have been counted. """

        count = self.results.count()
        if not count:
            return False

        return (sum(1 for r in self.results if r.counted) == count)

    @counted.expression
    def counted(cls):
        expr = select([
            func.coalesce(func.bool_and(BallotResult.counted), False)
        ])
        expr = expr.where(BallotResult.ballot_id == cls.id)
        expr = expr.label('counted')

        return expr

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        ballot result groups and the second value being the number of total
        result groups related to this vote.

        """

        query = object_session(self).query(BallotResult)
        query = query.with_entities(BallotResult.counted)
        query = query.filter(BallotResult.ballot_id == self.id)

        results = query.all()

        return sum(1 for r in results if r[0]), len(results)

    #: the total yeas
    yeas = summarized_property('yeas')

    #: the total nays
    nays = summarized_property('nays')

    #: the total empty votes
    empty = summarized_property('empty')

    #: the total invalid votes
    invalid = summarized_property('invalid')

    #: the total elegible voters
    elegible_voters = summarized_property('elegible_voters')

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([func.sum(getattr(BallotResult, attribute))])
        expr = expr.where(BallotResult.ballot_id == cls.id)
        expr = expr.label(attribute)

        return expr

    def percentage_by_entity(self):
        """ Returns the yeas/nays percentage grouped and keyed by
        entity_id.

        Uncounted entities are not included.

        """

        query = object_session(self).query(BallotResult)

        query = query.with_entities(
            BallotResult.entity_id,
            func.sum(BallotResult.yeas),
            func.sum(BallotResult.nays),
            BallotResult.counted
        )

        query = query.group_by(
            BallotResult.entity_id,
            BallotResult.counted
        )

        query = query.filter(BallotResult.ballot_id == self.id)

        result = {}

        for id, yeas, nays, counted in query.all():
            r = {'counted': counted}

            if counted:
                r['yeas_percentage'] = yeas / ((yeas + nays) or 1) * 100
                r['nays_percentage'] = 100 - r['yeas_percentage']

            result[id] = r

        return result

    def clear_results(self):
        """ Clear all the results. """

        session = object_session(self)
        for result in self.results:
            session.delete(result)
