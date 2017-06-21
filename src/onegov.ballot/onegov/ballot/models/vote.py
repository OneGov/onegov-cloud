from collections import OrderedDict
from onegov.ballot.models.common import DomainOfInfluenceMixin
from onegov.ballot.models.common import MetaMixin
from onegov.ballot.models.common import StatusMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
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
           MetaMixin, StatusMixin):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    summarized_properties = [
        'yeas', 'nays', 'empty', 'invalid', 'elegible_voters',
    ]

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

    #: a vote contains either one ballot (a proposal), or three ballots (a
    #: proposal, a counter proposal and a tie breaker)
    @property
    def proposal(self):
        if self.ballots.count() >= 1:
            return self.ballots[0]
        return None

    @property
    def counter_proposal(self):
        if self.ballots.count() == 3:
            return self.ballots[1]
        return None

    @property
    def tie_breaker(self):
        if self.ballots.count() == 3:
            return self.ballots[2]
        return None

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

    def export(self):
        """ Returns all data connected to this vote as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        ballot result.

        Each entry in the list (row) has the following format:

        * ``title``:
            Title of the vote.

        * ``date``:
            The date of the vote (an ISO 8601 date string).

        * ``shortcode``:
            Internal shortcode (defines the ordering of votes on the same day).

        * ``domain``:
            ``federation`` for federal, ``canton`` for cantonal,
            ``municipality`` for communal votes.

        * ``status``:
            The status of the vote: ``unknown``, ``interim`` or ``final``.

        * ``type``:
            ``proposal`` (Vorschlag), ``counter-proposal`` (Gegenvorschlag) or
            ``tie-breaker`` (Stichfrage).

        * ``group``: The designation of the result. May be the district and
            the town's name divided by a slash, the city's name and the
            city's district divided by a slash or simply the town's name. This
            depends entirely on the canton.

        * ``entity_id``: The id of the political entity. The
            "BFS Nummer" for example.

        * ``counted``: True if the result was counted, False if the result is
            not known yet (the voting counts are not final yet).

        * ``yeas``:
            The number of yes votes.

        * ``nays``:
            The number of no votes.

        * ``invalid``:
            The number of invalid votes.

        * ``empty``:
            The number of empty votes.

        * ``elegible_voters``:
            The number of people elegible to vote.

        """

        rows = []

        for ballot in self.ballots:
            for result in ballot.results:
                # have the dict ordered so it works directly with onegov.core's
                # :func:`onegov.core.csv.convert_list_of_dicts_to_csv`
                row = OrderedDict()

                for locale, title in (self.title_translations or {}).items():
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

    summarized_properties = [
        'yeas', 'nays', 'empty', 'invalid', 'elegible_voters'
    ]

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
