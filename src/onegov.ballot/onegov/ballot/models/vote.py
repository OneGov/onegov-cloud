from collections import OrderedDict
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UUID
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from sqlalchemy import Boolean
from sqlalchemy import case
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import desc
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


class DerivedAttributes(object):

    """ A simple mixin to add commonly used functions to ballots and their
    results. """

    @hybrid_property
    def yeas_percentage(self):
        """ The percentage of yeas (discounts empty/invalid ballots). """

        return self.yeas / ((self.yeas + self.nays) or 1) * 100

    @yeas_percentage.expression
    def yeas_percentage(self):
        # coalesce will pick the first non-null result
        # nullif will return null if division by zero
        # => when all yeas and nays are zero the yeas percentage is 0%
        return 100 * (
            self.yeas / (
                func.coalesce(
                    func.nullif(self.yeas + self.nays, 0), 1
                )
            )
        )

    @hybrid_property
    def nays_percentage(self):
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @hybrid_property
    def accepted(self):
        return self.yeas > self.nays if self.counted else None

    @accepted.expression
    def accepted(cls):
        return case({True: cls.yeas > cls.nays}, cls.counted)


class DerivedBallotsCount(object):

    """ A simple mixin to add commonly used functions to votes, ballots and
    their results. """

    @hybrid_property
    def cast_ballots(self):
        return self.yeas + self.nays + self.empty + self.invalid

    @hybrid_property
    def turnout(self):
        return self.cast_ballots / self.elegible_voters * 100\
            if self.elegible_voters else 0


class Vote(Base, TimestampMixin, DerivedBallotsCount, DomainOfInfluenceMixin,
           ContentMixin, StatusMixin):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    #: identifies the vote, may be used in the url, generated from the title
    id = Column(Text, primary_key=True)

    #: shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: title of the vote
    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    #: identifies the date of the vote
    date = Column(Date, nullable=False)

    #: a vote contains n ballots
    ballots = relationship(
        'Ballot',
        cascade='all, delete-orphan',
        order_by='Ballot.type',
        backref=backref('vote'),
        lazy='dynamic'
    )

    def ballot(self, ballot_type, create=False):
        """ Returns the given ballot if it exists. Optionally creates the
        ballot.

        """

        result = self.ballots.filter(Ballot.type == ballot_type).first()

        if not result and create:
            result = Ballot(type=ballot_type)
            self.ballots.append(result)

        return result

    @property
    def proposal(self):
        return self.ballot('proposal')

    @property
    def counter_proposal(self):
        return self.ballot('counter-proposal')

    @property
    def tie_breaker(self):
        return self.ballot('tie-breaker')

    #: may be used to identify the vote type, e.g. simple or complex.
    vote_type = meta_property('vote_type')

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            id = normalize_for_url(self.title) or 'vote'
            session = object_session(self)
            while session.query(Vote.id).filter(Vote.id == id).first():
                id = increment_name(id)
            self.id = id

    @property
    def counted(self):
        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

    @property
    def answer(self):
        if not self.counted or not self.proposal:
            return None

        # standard ballot, no counter proposal
        if not self.counter_proposal:
            return 'accepted' if self.proposal.accepted else 'rejected'

        # variant ballot, with proposal, coutner proposal and tie breaker
        elif all((self.proposal, self.counter_proposal, self.tie_breaker)):

            if self.proposal.accepted and self.counter_proposal.accepted:
                if self.tie_breaker.accepted:
                    return 'proposal'
                else:
                    return 'counter-proposal'

            elif self.proposal.accepted:
                return 'proposal'

            elif self.counter_proposal.accepted:
                return 'counter-proposal'

            else:
                return 'rejected'

        # not implemeneted here, not implemented in Swiss law either (at least
        # on a federal level)
        else:
            raise NotImplementedError

    @property
    def yeas_percentage(self):
        """ The percentage of yeas (discounts empty/invalid ballots). """

        # if we have no counter proposal, the yeas are a simple sum
        if not self.counter_proposal:
            subject = self
        else:
            if self.answer in ('proposal', 'rejected'):
                # if the proposal won or both proposal and counter-proposal
                # were rejected, we show the yeas/nays of the proposal
                subject = self.proposal
            else:
                subject = self.counter_proposal

        return subject.yeas / ((subject.yeas + subject.nays) or 1) * 100

    @property
    def nays_percentage(self):
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        entities and the second value being the number of total entities.

        If this is complex vote with proposal, counter-proposal and tie-breaker
        it's assumed all three ballots are present/not present for one entity
        (otherwise there might be a rounding error).

        """

        ballot_ids = set(b.id for b in self.ballots)

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

        return sum(getattr(ballot, attribute) for ballot in self.ballots)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([func.sum(getattr(Ballot, attribute))])
        expr = expr.where(Ballot.vote_id == cls.id)
        expr = expr.label(attribute)

        return expr

    @property
    def last_result_change(self):
        """ Gets the latest created/modified date of the vote or amongst the
        results of this vote.

        """

        last_changes = []
        if self.last_change:
            last_changes.append(self.last_change)

        session = object_session(self)

        ballot_ids = session.query(Ballot)
        ballot_ids = ballot_ids.with_entities(Ballot.id)
        ballot_ids = ballot_ids.filter(Ballot.vote_id == self.id)
        ballot_ids = ballot_ids.subquery()

        results = session.query(BallotResult)
        results = results.with_entities(BallotResult.last_change)
        results = results.order_by(desc(BallotResult.last_change))
        results = results.filter(BallotResult.ballot_id.in_(ballot_ids))

        last_change = results.first()
        if last_change:
            last_changes.append(last_change[0])

        if not len(last_changes):
            return None

        return max(last_changes)

    #: may be used to store a link related to this vote
    related_link = meta_property('related_link')

    def clear_results(self):
        """ Clear all the results. """

        self.status = None

        for ballot in self.ballots:
            ballot.clear_results()

    def export(self):
        """ Returns all data connected to this vote as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        ballot result.

        """

        rows = []

        for ballot in self.ballots:
            for result in ballot.results:
                row = OrderedDict()

                titles = (
                    ballot.title_translations or self.title_translations or {}
                )
                for locale, title in titles.items():
                    row['title_{}'.format(locale)] = (title or '').strip()
                row['date'] = self.date.isoformat()
                row['shortcode'] = self.shortcode
                row['domain'] = self.domain
                row['status'] = self.status or 'unknown'
                row['type'] = ballot.type
                row['group'] = result.group
                row['entity_id'] = result.entity_id
                row['counted'] = result.counted
                row['yeas'] = result.yeas
                row['nays'] = result.nays
                row['invalid'] = result.invalid
                row['empty'] = result.empty
                row['elegible_voters'] = result.elegible_voters

                rows.append(row)

        return rows


class Ballot(Base, TimestampMixin, DerivedAttributes, DerivedBallotsCount):
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
    vote_id = Column(Text, ForeignKey(Vote.id), nullable=False)

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

        return (
            sum(1 for r in self.results if r.counted) == self.results.count()
        )

    @counted.expression
    def counted(cls):
        expr = select([func.bool_and(BallotResult.counted)])
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


class BallotResult(Base, TimestampMixin, DerivedAttributes,
                   DerivedBallotsCount):
    """ The result of a specific ballot. Each ballot may have multiple
    results. Those results may be aggregated or not.

    """

    __tablename__ = 'ballot_results'

    #: identifies the result, may be used in the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: groups the ballots in whatever structure makes sense. For example:
    #: /ZH/Bezirk Zürich/Stadt Zürich/Kreis 1
    #: the idea is to have an instrument to group ballot results at various
    #: levels. We could use the example, to group by '/ZH' or by
    #: '/ZH/Bezirk Zürich/Stadt Zürich'
    group = Column(Text, nullable=False)

    #: The entity id (e.g. BFS number).
    entity_id = Column(Integer, nullable=False)

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted = Column(Boolean, nullable=False)

    #: number of yeas, in case of variants, the number of yeas for the first
    #: option of the tie breaker
    yeas = Column(Integer, nullable=False, default=lambda: 0)

    #: number of nays, in case of variants, the number of nays for the first
    #: option of the tie breaker (so a yay for the second option)
    nays = Column(Integer, nullable=False, default=lambda: 0)

    #: number of empty votes
    empty = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid votes
    invalid = Column(Integer, nullable=False, default=lambda: 0)

    #: number of elegible voters
    elegible_voters = Column(Integer, nullable=False, default=lambda: 0)

    #: the ballot this result belongs to
    ballot_id = Column(UUID, ForeignKey(Ballot.id), nullable=False)
