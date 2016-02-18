from collections import OrderedDict
from onegov.ballot.models.common import DomainOfInfluenceMixin
from onegov.core.orm import Base, translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE, UUID
from onegov.core.utils import normalize_for_url
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, Text
from sqlalchemy import select, func, desc
from sqlalchemy_utils import observes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, object_session
from uuid import uuid4


class DerivedBallotsCount(object):

    @hybrid_property
    def unaccounted_ballots(self):
        return self.blank_ballots + self.invalid_ballots

    @hybrid_property
    def accounted_ballots(self):
        return self.received_ballots - self.unaccounted_ballots

    @hybrid_property
    def turnout(self):
        return self.received_ballots / self.elegible_voters * 100\
            if self.elegible_voters else 0


class Election(Base, TimestampMixin, DerivedBallotsCount,
               DomainOfInfluenceMixin):

    __tablename__ = 'elections'

    summarized_properties = [
        'elegible_voters',
        'received_ballots',
        'accounted_ballots',
        'blank_ballots',
        'invalid_ballots',
        'accounted_votes'
    ]

    #: identifies the result, may be used in the url
    id = Column(Text, primary_key=True)

    #: title of the election
    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            self.id = normalize_for_url(self.title)

    #: shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: identifies the date of the vote
    date = Column(Date, nullable=False)

    #: the type of the election
    type = Column(
        Enum(
            'proporz',
            'majorz',
            name='type_of_election'
        ),
        nullable=False
    )

    #: the number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    #: Total number of municipalities
    total_municipalities = Column(Integer, nullable=True)

    #: number counted of municipalities
    counted_municipalities = Column(Integer, nullable=True)

    @property
    def counted(self):
        if self.total_municipalities and self.counted_municipalities:
            return self.total_municipalities == self.counted_municipalities

        return False

    #: an election contains n results (one for each municipality)
    results = relationship(
        "ElectionResult",
        cascade="all, delete-orphan",
        backref=backref("election"),
        lazy='joined',
        order_by="ElectionResult.group",
    )

    @property
    def list_results(self):
        """ Returns a tuple (list id, list name, cumulated votes) for each
        list.

        """
        session = object_session(self)

        result_ids = session.query(ElectionResult)
        result_ids = result_ids.with_entities(ElectionResult.id)
        result_ids = result_ids.filter(ElectionResult.election_id == self.id)
        result_ids = result_ids.subquery()

        results = session.query(
            ListResult.list_id,
            ListResult.name,
            func.sum(ListResult.votes),
            ListResult.number_of_mandates
        )
        results = results.group_by(
            ListResult.list_id,
            ListResult.name,
            ListResult.number_of_mandates
        )
        results = results.order_by(
            ListResult.name
        )
        results = results.filter(
            ListResult.election_result_id.in_(result_ids)
        )

        return results.all()

    @property
    def candidate_results(self):
        """ Returns a tuple (candidate id, family name, first name, elected,
        list name, cumulated votes) for each candidate.

        """
        session = object_session(self)

        result_ids = session.query(ElectionResult)
        result_ids = result_ids.with_entities(ElectionResult.id)
        result_ids = result_ids.filter(ElectionResult.election_id == self.id)
        result_ids = result_ids.subquery()

        results = session.query(
            CandidateResult.candidate_id,
            CandidateResult.family_name,
            CandidateResult.first_name,
            CandidateResult.elected,
            CandidateResult.list_name,
            func.sum(CandidateResult.votes),
        )
        results = results.group_by(
            CandidateResult.candidate_id,
            CandidateResult.family_name,
            CandidateResult.first_name,
            CandidateResult.elected,
            CandidateResult.list_name
        )
        results = results.order_by(
            CandidateResult.family_name,
            CandidateResult.first_name
        )
        results = results.filter(
            CandidateResult.election_result_id.in_(result_ids)
        )

        return results.all()

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
        """ Gets the latest created/modified date amongst the results of
        this election.

        """
        results = object_session(self).query(ElectionResult)
        results = results.with_entities(ElectionResult.last_change)
        results = results.order_by(desc(ElectionResult.last_change))
        results = results.filter(ElectionResult.election_id == self.id)

        last_change = results.first()
        return last_change and last_change[0] or None

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

        * ``municipality_name``:
            The name of the municipality.

        * ``municipality_bfs_number``:
            The id of the municipality/locale ("BFS Nummer").

        * ``municipality_elegible_voters``:
            The number of people elegible to vote for this municipality.

        * ``municipality_received_ballots``:
            The number of received ballots for this municipality.

        * ``municipality_blank_ballots``:
            The number of blank ballots for this municipality.

        * ``municipality_invalid_ballots``:
            The number of invalid ballots for this municipality.

        * ``municipality_unaccounted_ballots``:
            The number of unaccounted ballots for this municipality.

        * ``municipality_accounted_ballots``:
            The nubmer of accounted ballots for this municipality.

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

        * ``list_votes``:
            The number of votes this list has got. Only relevant for
            elections based on proportional representation.

        * ``candidate_family_name``:
            The family name of the candidate.

        * ``candidate_first_name``:
            The first name of the candiate.

        * ``candidate_elected``:
            True if the candidate has been elected.

        * ``candidate_votes``:
            The number of votes this candidate got.
        """

        rows = []

        for r in self.results:
            lists = dict(((l.list_id, l) for l in r.lists))
            for c in r.candidates:
                row = OrderedDict()

                row['election_title'] = self.title.strip()
                row['election_date'] = self.date.isoformat()
                row['election_type'] = self.type
                row['election_mandates'] = self.number_of_mandates

                row['municipality_name'] = r.group
                row['municipality_bfs_number'] = r.municipality_id
                row['municipality_elegible_voters'] = r.elegible_voters
                row['municipality_received_ballots'] = r.received_ballots
                row['municipality_blank_ballots'] = r.blank_ballots
                row['municipality_invalid_ballots'] = r.invalid_ballots
                row['municipality_unaccounted_ballots'] = r.unaccounted_ballots
                row['municipality_accounted_ballots'] = r.accounted_ballots
                row['municipality_blank_votes'] = r.blank_votes
                row['municipality_invalid_votes'] = r.invalid_votes
                row['municipality_accounted_votes'] = r.accounted_votes

                row['list_name'] = None
                row['list_votes'] = None
                if c.list_id:
                    row['list_name'] = lists[c.list_id].name
                    row['list_votes'] = lists[c.list_id].votes

                row['candidate_family_name'] = c.family_name
                row['candidate_first_name'] = c.first_name
                row['candidate_elected'] = c.elected
                row['candidate_votes'] = c.votes

                rows.append(row)

        return rows


class ElectionResult(Base, TimestampMixin, DerivedBallotsCount):

    __tablename__ = 'election_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=False)

    #: groups the result in whatever structure makes sense
    group = Column(Text, nullable=False)

    # : The municipality id (BFS Nummer).
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

    @property
    def accounted_votes(self):
        """ Number of accounted votes """
        return (
            self.election.number_of_mandates * self.accounted_ballots -
            self.blank_votes - self.invalid_votes
        )

    #: an election result may contain n list results
    lists = relationship(
        "ListResult",
        cascade="all, delete-orphan",
        backref=backref("election_result"),
        lazy='dynamic',
        order_by="ListResult.group",
    )

    #: an election result contains n candidate results
    candidates = relationship(
        "CandidateResult",
        cascade="all, delete-orphan",
        backref=backref("election_result"),
        lazy='dynamic',
        order_by="CandidateResult.group",
    )


class ListResult(Base, TimestampMixin):
    __tablename__ = 'list_results'

    #: identifies the candidate, maybe used in the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election result this result belongs to
    election_result_id = Column(
        UUID, ForeignKey(ElectionResult.id), nullable=False
    )

    #: groups the list in whatever structure makes sense
    group = Column(Text, nullable=False)

    # number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    #: the identification of the list
    list_id = Column(Text, nullable=False)

    #: the name of the list
    name = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)


class CandidateResult(Base, TimestampMixin):

    __tablename__ = 'candiate_results'

    #: identifies the candidate, maybe used in the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election result this result belongs to
    election_result_id = Column(
        UUID, ForeignKey(ElectionResult.id), nullable=False
    )

    #: True if the candidate is elected (election-wide property)
    elected = Column(Boolean, nullable=False)

    #: groups the candidate in whatever structure makes sense
    group = Column(Text, nullable=False)

    #: the identification of the candidate
    candidate_id = Column(Text, nullable=False)

    #: the identification of the list
    list_id = Column(Text, nullable=True)

    #: the name of the list (for convenience)
    list_name = Column(Text, nullable=True)

    #: the family name
    family_name = Column(Text, nullable=False)

    #: the first name
    first_name = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)
