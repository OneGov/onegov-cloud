from collections import OrderedDict
from onegov.ballot.models.common import DomainOfInfluenceMixin, MetaMixin
from onegov.core.orm import Base, translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE, UUID
from onegov.core.utils import normalize_for_url, increment_name
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, Text
from sqlalchemy import select, func, desc
from sqlalchemy_utils import observes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased, backref, relationship, object_session
from uuid import uuid4
from itertools import groupby


class DerivedBallotsCount(object):

    @hybrid_property
    def unaccounted_ballots(self):
        """ Number of unaccounted ballots, """
        return self.blank_ballots + self.invalid_ballots

    @hybrid_property
    def accounted_ballots(self):
        """ Number of accounted ballots. """
        return self.received_ballots - self.unaccounted_ballots

    @hybrid_property
    def turnout(self):
        """ Turnout of the election. """
        return self.received_ballots / self.elegible_voters * 100\
            if self.elegible_voters else 0


class Election(Base, TimestampMixin, DerivedBallotsCount,
               DomainOfInfluenceMixin, MetaMixin):

    __tablename__ = 'elections'

    summarized_properties = [
        'elegible_voters',
        'received_ballots',
        'accounted_ballots',
        'blank_ballots',
        'invalid_ballots',
        'accounted_votes'
    ]

    #: Identifies the result, may be used in the url
    id = Column(Text, primary_key=True)

    #: Title of the election
    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            id = normalize_for_url(self.title) or "election"
            session = object_session(self)
            while session.query(Election.id).filter(Election.id == id).first():
                id = increment_name(id)
            self.id = id

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: Identifies the date of the vote
    date = Column(Date, nullable=False)

    #: Type of the election
    type = Column(
        Enum(
            'proporz',
            'majorz',
            name='type_of_election'
        ),
        nullable=False
    )

    #: Number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    @property
    def allocated_mandates(self):
        """ Number of already allocated mandates/elected candidates. """
        results = object_session(self).query(
            func.count(
                func.nullif(Candidate.elected, False)
            )
        )
        results = results.filter(Candidate.election_id == self.id)

        mandates = results.first()
        return mandates and mandates[0] or 0

    #: Absolute majority (majorz elections only)
    absolute_majority = Column(Integer, nullable=True, default=lambda: 0)

    #: Total number of municipalities
    total_municipalities = Column(Integer, nullable=True)

    #: Number of already counted municipalities
    counted_municipalities = Column(Integer, nullable=True)

    @property
    def counted(self):
        """ Checks if there are results for all municipalities. """
        if self.total_municipalities and self.counted_municipalities:
            return self.total_municipalities == self.counted_municipalities

        return False

    #: An election contains n list connections
    list_connections = relationship(
        "ListConnection",
        cascade="all, delete-orphan",
        backref=backref("election"),
        lazy="dynamic",
        order_by="ListConnection.connection_id"
    )

    #: An election contains n lists
    lists = relationship(
        "List",
        cascade="all, delete-orphan",
        backref=backref("election"),
        lazy="dynamic",
    )

    #: An election contains n candidates
    candidates = relationship(
        "Candidate",
        cascade="all, delete-orphan",
        backref=backref("election"),
        lazy="dynamic",
        order_by="Candidate.candidate_id",
    )

    #: An election contains n results, one for each municipality
    results = relationship(
        "ElectionResult",
        cascade="all, delete-orphan",
        backref=backref("election"),
        lazy="dynamic",
        order_by="ElectionResult.group",
    )

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """
        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """
        expr = select([func.sum(getattr(ElectionResult, attribute))])
        expr = expr.where(ElectionResult.election_id == cls.id)
        expr = expr.label(attribute)
        return expr

    @property
    def last_result_change(self):
        """ Gets the latest created/modified date of the election or amongst
        the results of this election.

        """
        last_changes = []

        if self.last_change:
            last_changes.append(self.last_change)

        results = object_session(self).query(ElectionResult)
        results = results.with_entities(ElectionResult.last_change)
        results = results.order_by(desc(ElectionResult.last_change))
        results = results.filter(ElectionResult.election_id == self.id)

        last_change = results.first()
        if last_change:
            last_changes.append(last_change[0])

        if not len(last_changes):
            return None

        return max(last_changes)

    def export(self):
        """ Returns all date connected to this election as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each municipality.

        Each entry in the list (row) has the following format:

        * ``election_title``:
            Title of the election.

        * ``election_date``:
            The date of the election (an ISO 8601 date string).

        * ``election_type``:
            ``proporz`` for proportional, ``majorz`` for majority system.

        * ``election_mandates``:
            The number of mandates.

        * ``election_absolute_majority``:
            The absolute majority.  Only relevant for elections based on
            majority system.

        * ``election_counted_municipalities``:
            The number of already counted municipalities.

        * ``election_total_municipalities``:
            The total number of municipalities.

        * ``municipality_name``:
            The name of the municipality.

        * ``municipality_bfs_number``:
            The id of the municipality/locale ("BFS Nummer").

        * ``municipality_elegible_voters``:
            The number of people eligible to vote for this municipality.

        * ``municipality_received_ballots``:
            The number of received ballots for this municipality.

        * ``municipality_blank_ballots``:
            The number of blank ballots for this municipality.

        * ``municipality_invalid_ballots``:
            The number of invalid ballots for this municipality.

        * ``municipality_unaccounted_ballots``:
            The number of unaccounted ballots for this municipality.

        * ``municipality_accounted_ballots``:
            The number of accounted ballots for this municipality.

        * ``municipality_blank_votes``:
            The number of blank votes for this municipality.

        * ``municipality_invalid_votes``:
            The number of invalid votes for this municipality. Is zero for
            elections based on proportional representation.

        * ``municipality_accounted_votes``:
            The number of accounted votes for this municipality.

        * ``list_name``:
            The name of the list this candidate appears on. Only relevant for
            elections based on proportional representation.

        * ``list_id``:
            The id of the list this candidate appears on. Only relevant for
            elections based on proportional representation.

        * ``list_number_of_mandates``:
            The number of mandates this list has got. Only relevant for
            elections based on proportional representation.

        * ``list_votes``:
            The number of votes this list has got in this municipality.
            Only relevant for elections based on proportional representation.

        * ``list_connection``:
            The ID of the list connection this list is connected to. Only
            relevant for elections based on proportional representation.

        * ``list_connection_parent``:
            The ID of the parent list conneciton this list is connected to.
            Only relevant for elections based on proportional representation.

        * ``candidate_family_name``:
            The family name of the candidate.

        * ``candidate_first_name``:
            The first name of the candidate.

        * ``candidate_id``:
            The ID of the candidate.

        * ``candidate_elected``:
            True if the candidate has been elected.

        * ``candidate_votes``:
            The number of votes this candidate got.

        """

        session = object_session(self)

        ids = session.query(ElectionResult.id)
        ids = ids.filter(ElectionResult.election_id == self.id)

        SubListConnection = aliased(ListConnection)
        results = session.query(
            CandidateResult.votes,
            Election.title,
            Election.date,
            Election.type,
            Election.number_of_mandates,
            Election.absolute_majority,
            Election.counted_municipalities,
            Election.total_municipalities,
            ElectionResult.group,
            ElectionResult.municipality_id,
            ElectionResult.elegible_voters,
            ElectionResult.received_ballots,
            ElectionResult.blank_ballots,
            ElectionResult.invalid_ballots,
            ElectionResult.unaccounted_ballots,
            ElectionResult.accounted_ballots,
            ElectionResult.blank_votes,
            ElectionResult.invalid_votes,
            ElectionResult.accounted_votes,
            List.name,
            List.list_id,
            List.number_of_mandates,
            SubListConnection.connection_id,
            ListConnection.connection_id,
            Candidate.family_name,
            Candidate.first_name,
            Candidate.candidate_id,
            Candidate.elected,
        )
        results = results.outerjoin(CandidateResult.candidate)
        results = results.outerjoin(CandidateResult.election_result)
        results = results.outerjoin(Candidate.list)
        results = results.outerjoin(SubListConnection, List.connection)
        results = results.outerjoin(SubListConnection.parent)
        results = results.outerjoin(Candidate.election)
        results = results.filter(CandidateResult.election_result_id.in_(ids))
        results = results.order_by(
            ElectionResult.group,
            List.name,
            Candidate.family_name,
            Candidate.first_name
        )

        # We need to merge in the list results per municipality
        list_results = session.query(
            ListResult.votes,
            ElectionResult.municipality_id,
            List.list_id
        )
        list_results = list_results.outerjoin(ListResult.election_result)
        list_results = list_results.outerjoin(ListResult.list)
        list_results = list_results.filter(
            ListResult.election_result_id.in_(ids)
        )
        list_results = list_results.order_by(
            ElectionResult.municipality_id,
            List.list_id
        )
        list_results_grouped = {}
        for key, group in groupby(list_results, lambda x: x[1]):
            list_results_grouped[key] = dict([(g[2], g[0]) for g in group])

        rows = []
        for result in results:
            row = OrderedDict()

            row['election_title'] = result[1].strip()
            row['election_date'] = result[2].isoformat()
            row['election_type'] = result[3]
            row['election_mandates'] = result[4]
            row['election_absolute_majority'] = result[5]
            row['election_counted_municipalities'] = result[6]
            row['election_total_municipalities'] = result[7]

            row['municipality_name'] = result[8]
            row['municipality_bfs_number'] = result[9]
            row['municipality_elegible_voters'] = result[10]
            row['municipality_received_ballots'] = result[11]
            row['municipality_blank_ballots'] = result[12]
            row['municipality_invalid_ballots'] = result[13]
            row['municipality_unaccounted_ballots'] = result[14]
            row['municipality_accounted_ballots'] = result[15]
            row['municipality_blank_votes'] = result[16]
            row['municipality_invalid_votes'] = result[17]
            row['municipality_accounted_votes'] = result[18]

            row['list_name'] = result[19]
            row['list_id'] = result[20]
            row['list_number_of_mandates'] = result[21]
            row['list_votes'] = list_results_grouped.get(
                row['municipality_bfs_number'], {}
            ).get(row['list_id'], 0)

            row['list_connection'] = result[22]
            row['list_connection_parent'] = result[23]

            row['candidate_family_name'] = result[24]
            row['candidate_first_name'] = result[25]
            row['candidate_id'] = result[26]
            row['candidate_elected'] = result[27]
            row['candidate_votes'] = result[0]

            rows.append(row)

        return rows


class ListConnection(Base, TimestampMixin):

    __tablename__ = 'list_connections'

    summarized_properties = ['votes', 'number_of_mandates']

    #: internal id of the list
    id = Column(UUID, primary_key=True, default=uuid4)

    #: external id of the list
    connection_id = Column(Text, nullable=False)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    #: ID of the parent
    parent_id = Column(UUID, ForeignKey('list_connections.id'), nullable=True)

    #: a list connection contains n lists
    lists = relationship(
        "List",
        cascade="all, delete-orphan",
        backref=backref("connection"),
        lazy="dynamic",
        order_by="List.list_id"
    )

    #: a list connection contains n sub-connection
    children = relationship(
        "ListConnection",
        cascade="all, delete-orphan",
        backref=backref("parent", remote_side='ListConnection.id'),
        lazy="dynamic",
        order_by="ListConnection.connection_id"
    )

    @property
    def total_votes(self):
        """ Returns the total number of votes. """
        return self.votes + sum(child.total_votes for child in self.children)

    @property
    def total_number_of_mandates(self):
        """ Returns the total number of mandates. """
        return self.number_of_mandates + sum(
            child.total_number_of_mandates for child in self.children
        )

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """
        return sum(getattr(list, attribute) for list in self.lists)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """
        expr = select([func.sum(getattr(List, attribute))])
        expr = expr.where(List.connection_id == cls.id)
        expr = expr.label(attribute)
        return expr


class List(Base, TimestampMixin):
    """ A list used in an election. """

    __tablename__ = 'lists'

    summarized_properties = ['votes']

    #: internal id of the list
    id = Column(UUID, primary_key=True, default=uuid4)

    #: external id of the list
    list_id = Column(Text, nullable=False)

    # number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    #: name of the list
    name = Column(Text, nullable=False)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=False)

    #: the list connection id
    connection_id = Column(UUID, ForeignKey(ListConnection.id), nullable=True)

    #: a list contains n candidates
    candidates = relationship(
        "Candidate",
        cascade="all, delete-orphan",
        backref=backref("list"),
        lazy="dynamic",
    )

    #: a list contains n results
    results = relationship(
        "ListResult",
        cascade="all, delete-orphan",
        backref=backref("list"),
        lazy="dynamic",
    )

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """
        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """
        expr = select([func.sum(getattr(ListResult, attribute))])
        expr = expr.where(ListResult.list_id == cls.id)
        expr = expr.label(attribute)
        return expr


class Candidate(Base, TimestampMixin):
    """ A candidate for an election. """

    __tablename__ = 'candiates'

    summarized_properties = ['votes']

    #: the internal id of the candidate
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the external id of the candidate
    candidate_id = Column(Text, nullable=False)

    #: the family name
    family_name = Column(Text, nullable=False)

    #: the first name
    first_name = Column(Text, nullable=False)

    #: True if the candidate is elected
    elected = Column(Boolean, nullable=False)

    #: the election this candidate belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=False)

    #: the list this candidate belongs to
    list_id = Column(UUID, ForeignKey(List.id), nullable=True)

    #: a candidate contains n results
    results = relationship(
        "CandidateResult",
        cascade="all, delete-orphan",
        backref=backref("candidate"),
        lazy="dynamic",
    )

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """
        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """
        expr = select([func.sum(getattr(CandidateResult, attribute))])
        expr = expr.where(CandidateResult.candidate_id == cls.id)
        expr = expr.label(attribute)
        return expr


class ElectionResult(Base, TimestampMixin, DerivedBallotsCount):
    """ The result of an election for a municipality. """

    __tablename__ = 'election_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=False)

    #: groups the result in whatever structure makes sense
    group = Column(Text, nullable=False)

    #: municipality id (BFS Nummer).
    municipality_id = Column(Integer, nullable=False)

    #: number of elegible voters
    elegible_voters = Column(Integer, nullable=False, default=lambda: 0)

    #: number of received ballots
    received_ballots = Column(Integer, nullable=False, default=lambda: 0)

    #: number of blank ballots
    blank_ballots = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid ballots
    invalid_ballots = Column(Integer, nullable=False, default=lambda: 0)

    #: number of blank votes
    blank_votes = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid votes
    invalid_votes = Column(Integer, nullable=False, default=lambda: 0)

    @hybrid_property
    def accounted_votes(self):
        """ Number of accounted votes """
        return (
            self.election.number_of_mandates * self.accounted_ballots -
            self.blank_votes - self.invalid_votes
        )

    @accounted_votes.expression
    def accounted_votes(cls):
        """ Number of accounted votes """
        # A bit of a hack :|
        number_of_mandates = select(
            [Election.number_of_mandates],
            whereclause="elections.id = election_results.election_id"
        )
        return (
            number_of_mandates * (
                cls.received_ballots - cls.blank_ballots - cls.invalid_ballots
            ) - cls.blank_votes - cls.invalid_votes
        )

    #: an election result may contain n list results
    list_results = relationship(
        "ListResult",
        cascade="all, delete-orphan",
        backref=backref("election_result"),
        lazy="dynamic",
    )

    #: an election result contains n candidate results
    candidate_results = relationship(
        "CandidateResult",
        cascade="all, delete-orphan",
        backref=backref("election_result"),
        lazy="dynamic",
    )


class ListResult(Base, TimestampMixin):
    """ The result of an election for a list in  a municipality. """

    __tablename__ = 'list_results'

    #: identifies the list
    id = Column(UUID, primary_key=True, default=uuid4)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)

    #: the election result this result belongs to
    election_result_id = Column(
        UUID, ForeignKey(ElectionResult.id), nullable=False
    )

    #: the list this result belongs to
    list_id = Column(UUID, ForeignKey(List.id), nullable=False)


class CandidateResult(Base, TimestampMixin):
    """ The result of an election for a candidate in  a municipality.

    There are some properties (elected, candidate id, list id, list name,
    family name, first name) which stay the same for a whole election and
    could be therefore stored globally or as a reference.

    """

    __tablename__ = 'candiate_results'

    #: identifies the candidate result
    id = Column(UUID, primary_key=True, default=uuid4)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)

    #: the election result this result belongs to
    election_result_id = Column(
        UUID, ForeignKey(ElectionResult.id), nullable=False
    )

    #: the canidate this result belongs to
    candidate_id = Column(UUID, ForeignKey(Candidate.id), nullable=False)
