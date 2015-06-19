# -*- coding: utf-8 -*-

""" OneGov Ballot models the aggregated results of Swiss ballots.
It takes hints from the CH-0155 Standard.

See:

`eCH-0155: Datenstandard politische Rechte \
<http://www.ech.ch/vechweb/page?p=dossier&documentNumber=eCH-0155>`_

As of this writing onegov.ballot only aims to implement votes, not elections.
Though it will do so in the future.

"""

from __future__ import division

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, Text
from sqlalchemy import select, func, case
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, object_session
from sqlalchemy_utils import observes
from uuid import uuid4


class DerivedPercentage(object):

    @hybrid_property
    def yays_percentage(self):
        """ The percentage of yays (discounts empty/invalid ballots). """
        return self.yays / (self.yays + self.nays) * 100

    @hybrid_property
    def nays_percentage(self):
        """ The percentage of nays (discounts empty/invalid ballots). """
        return 100 - self.yays_percentage


class DerivedAcceptance(object):

    @hybrid_property
    def accepted(self):
        return self.yays > self.nays if self.counted else None

    @accepted.expression
    def accepted(cls):
        return case({True: cls.yays > cls.nays}, cls.counted)


class DerivedBallotsCount(object):

    @hybrid_property
    def cast_ballots(self):
        return self.yays + self.nays + self.empty + self.invalid

    @hybrid_property
    def turnout(self):
        return self.cast_ballots / self.elegible_voters * 100


class Vote(Base, TimestampMixin, DerivedPercentage, DerivedBallotsCount):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    summarized_properties = [
        'yays', 'nays', 'empty', 'invalid', 'elegible_voters',
    ]

    #: identifies the vote, may be used in the url, generated from the title
    id = Column(Text, primary_key=True)

    #: title of the vote
    title = Column(Text, nullable=False)

    #: identifies the date of the vote
    date = Column(Date, nullable=False)

    #: defines the scope of the vote - eCH-0115 calls this the domain of
    #: influence. Unlike eCH-0115 we refrain from putting this in a separate
    #: model. We also only include domains we currently support.
    domain = Column(
        Enum(
            'federation',
            'canton',
            name='domain_of_influence'
        ),
        nullable=False
    )

    #: a vote contains n ballots
    ballots = relationship(
        "Ballot",
        cascade="all, delete-orphan",
        order_by="Ballot.type",
        backref=backref("vote"),
        lazy='joined'
    )

    #: a vote contains either one ballot (a proposal), or three ballots (a
    #: proposal, a counter proposal and a tie breaker)
    @property
    def proposal(self):
        return self.ballots and self.ballots[0]

    @property
    def counter_proposal(self):
        return len(self.ballots) == 3 and self.ballots[1]

    @property
    def tie_breaker(self):
        return len(self.ballots) == 3 and self.ballots[2]

    @observes('title')
    def title_observer(self, title):
        self.id = normalize_for_url(title)

    @property
    def counted(self):
        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

    @property
    def answer(self):
        if not self.counted:
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
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        ballot result groups and the second value being the number of total
        result groups related to this vote.

        """

        ballot_ids = set(b.id for b in self.ballots)

        if not ballot_ids:
            return 0, 0

        query = object_session(self).query(BallotResult)
        query = query.with_entities(BallotResult.counted)
        query = query.filter(BallotResult.ballot_id.in_(ballot_ids))

        results = query.all()

        return sum(1 for r in results if r[0]), len(results)

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


class Ballot(Base, TimestampMixin,
             DerivedPercentage, DerivedAcceptance, DerivedBallotsCount):
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
        'yays', 'nays', 'empty', 'invalid', 'elegible_voters'
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
        "BallotResult",
        cascade="all, delete-orphan",
        backref=backref("ballot"),
        lazy='joined',
        order_by="BallotResult.group",
    )

    @hybrid_property
    def counted(self):
        """ True if all results have been counted. """
        return sum(1 for r in self.results if r.counted) == len(self.results)

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

    def percentage_by_municipality(self):
        """ Returns the yays/nays percentage grouped and keyed by
        municipality_id.

        Uncounted municipalities are not included.

        """

        query = object_session(self).query(BallotResult)

        query = query.with_entities(
            BallotResult.municipality_id,
            func.sum(BallotResult.yays),
            func.sum(BallotResult.nays)
        )

        query = query.group_by(BallotResult.municipality_id)
        query = query.filter(BallotResult.counted == True)
        query = query.filter(BallotResult.ballot_id == self.id)

        result = {}

        for id, yays, nays in query.all():
            result[id] = {}
            result[id]['yays_percentage'] = yays / (yays + nays) * 100
            result[id]['nays_percentage'] = 100 - result[id]['yays_percentage']

        return result


class BallotResult(Base, TimestampMixin,
                   DerivedPercentage, DerivedAcceptance, DerivedBallotsCount):
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

    #: The municipality id (BFS Nummer).
    municipality_id = Column(Integer, nullable=False)

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted = Column(Boolean, nullable=False)

    #: number of yays, in case of variants, the number of yays for the first
    #: option of the tie breaker
    yays = Column(Integer, nullable=False, default=lambda: 0)

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


@listens_for(Vote, 'mapper_configured')
@listens_for(Ballot, 'mapper_configured')
def add_summarized_properties(mapper, cls):
    """ Takes the following attributes and adds them as hybrid_properties
    to the ballot. This results in a Ballot class that has all the following
    properties which will return the sum of the underlying results if called.

    E.g. this will return all the yays of the joined ballot results::

        ballot.yays

    """

    attributes = cls.summarized_properties

    def new_hybrid_property(attribute):
        @hybrid_property
        def sum_result(self):
            return self.aggregate_results(attribute)

        @sum_result.expression
        def sum_result(cls):
            return cls.aggregate_results_expression(cls, attribute)

        return sum_result

    for attribute in attributes:
        setattr(cls, attribute, new_hybrid_property(attribute))
