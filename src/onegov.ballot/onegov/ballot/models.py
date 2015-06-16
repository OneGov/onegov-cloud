""" OneGov Ballot models the aggregated results of Swiss ballots.
It takes hints from the CH-0155 Standard.

See:

`eCH-0155: Datenstandard politische Rechte \
<http://www.ech.ch/vechweb/page?p=dossier&documentNumber=eCH-0155>`_

As of this writing onegov.ballot only aims to implement votes, not elections.
Though it will do so in the future.

"""

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy_utils import observes
from uuid import uuid4


class Contest(Base, TimestampMixin):
    """ A contest contains all votes and elections decided upon on a given
    date.

    """

    __tablename__ = 'contests'

    #: there's only one contest for each date
    date = Column(Date, nullable=False, primary_key=True)

    #: a contest contains n votes
    votes = relationship(
        "Vote",
        cascade="all, delete-orphan",
        backref=backref("contest")
    )


class Vote(Base, TimestampMixin):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    #: identifies the vote, may be used in the url, generated from the title
    id = Column(Text, primary_key=True)

    #: title of the vote
    title = Column(Text, nullable=False)

    #: defines the scope of the vote - eCH-0115 calls this the domain of
    #: influence. Unlike eCH-0115 we refrain from putting this in a separate
    #: model. We also don't include domains smaller than municipality.
    domain = Column(
        Enum(
            'federation', 'canton', 'district', 'municipality',
            name='domain_of_influence'
        ),
        nullable=False
    )

    #: identifies the contest this vote belongs to
    contest_date = Column(Date, ForeignKey(Contest.date), nullable=False)

    #: number of elegible voters
    elegible_voters = Column(Integer, nullable=False)

    #: a vote contains n ballots
    ballots = relationship(
        "Ballot",
        cascade="all, delete-orphan",
        backref=backref("vote")
    )

    @observes('title')
    def title_observer(self, title):
        self.id = normalize_for_url(title)


class Ballot(Base, TimestampMixin):
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

    #: the question of the ballot
    question = Column(Text, nullable=False)

    #: the type of the ballot, 'standard' for normal votes, 'variant'
    #: for tie breaker ballots (ballots defining which option is preferred if
    #: ballots are about two mutually exclusive options and both options have
    #: the yays)
    type = Column(
        Enum('standard', 'variant', name='ballot_result_type'), nullable=False
    )

    #: identifies the vote this ballot result belongs to
    vote_id = Column(Text, ForeignKey(Vote.id), nullable=False)

    #: a ballot contains n results
    results = relationship(
        "BallotResult",
        cascade="all, delete-orphan",
        backref=backref("ballot")
    )


class BallotResult(Base, TimestampMixin):
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

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    is_established = Column(Boolean, nullable=False)

    #: number of yays, in case of variants, the number of yays for the first
    #: option of the tie breaker
    yays = Column(Integer, nullable=True)

    #: number of nays, in case of variants, the number of nays for the first
    #: option of the tie breaker (so a yay for the second option)
    nays = Column(Integer, nullable=True)

    #: number of empty votes
    empty = Column(Integer, nullable=True)

    #: number of invalid votes
    invalid = Column(Integer, nullable=True)

    #: the answer value that actually won
    result = Column(Text, nullable=False)

    #: the ballot this result belongs to
    ballot_id = Column(UUID, ForeignKey(Ballot.id), nullable=False)
