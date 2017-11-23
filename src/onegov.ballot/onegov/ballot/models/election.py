from collections import OrderedDict
from itertools import groupby
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UUID
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from sqlalchemy import Boolean
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
from sqlalchemy.orm import aliased
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


class DerivedAttributes(object):

    """ A simple mixin to add commonly used functions to elections and their
    results. """

    @hybrid_property
    def unaccounted_ballots(self):
        """ The number of unaccounted ballots. """

        return self.blank_ballots + self.invalid_ballots

    @hybrid_property
    def accounted_ballots(self):
        """ The number of accounted ballots. """

        return self.received_ballots - self.unaccounted_ballots

    @hybrid_property
    def turnout(self):
        """ The turnout of the election. """

        if not self.elegible_voters:
            return 0

        return self.received_ballots / self.elegible_voters * 100


class Election(Base, TimestampMixin, DerivedAttributes,
               DomainOfInfluenceMixin, ContentMixin, StatusMixin):

    __tablename__ = 'elections'

    #: Identifies the result, may be used in the url
    id = Column(Text, primary_key=True)

    #: Title of the election
    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            id = normalize_for_url(self.title) or 'election'
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

    #: Total number of political entities
    total_entities = Column(Integer, nullable=True)

    #: Number of already counted political entitites
    counted_entities = Column(Integer, nullable=True)

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        entities and the second value being the number of total entities.

        """

        return (self.counted_entities or 0, self.total_entities or 0)

    @property
    def counted(self):
        """ Checks if there are results for all entitites. """

        if self.total_entities and self.counted_entities:
            return self.total_entities == self.counted_entities

        return False

    #: An election contains n list connections
    list_connections = relationship(
        'ListConnection',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='ListConnection.connection_id'
    )

    #: An election contains n lists
    lists = relationship(
        'List',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    #: An election contains n candidates
    candidates = relationship(
        'Candidate',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='Candidate.candidate_id',
    )

    #: An election contains n results, one for each political entity
    results = relationship(
        'ElectionResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='ElectionResult.group',
    )

    #: An election may contains n party results
    party_results = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    #: The total elegible voters
    elegible_voters = summarized_property('elegible_voters')

    #: The total recceived ballots
    received_ballots = summarized_property('received_ballots')

    #: The total accounted ballots
    accounted_ballots = summarized_property('accounted_ballots')

    #: The total blank ballots
    blank_ballots = summarized_property('blank_ballots')

    #: The total invalid ballots
    invalid_ballots = summarized_property('invalid_ballots')

    #: The total accounted votes
    accounted_votes = summarized_property('accounted_votes')

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

        This does include changes made to the election itself (title, ...),
        the candidate results and the party results.

        This does not include changes made to candidates, lists, list
        connections and children of election results such as candidate
        results, list results, ...

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

        results = object_session(self).query(PartyResult)
        results = results.with_entities(PartyResult.last_change)
        results = results.order_by(desc(PartyResult.last_change))
        results = results.filter(PartyResult.election_id == self.id)
        last_change = results.first()
        if last_change:
            last_changes.append(last_change[0])

        if not len(last_changes):
            return None

        return max(last_changes)

    @property
    def elected_candidates(self):
        """ Returns the first and last names of the elected candidates. """

        results = object_session(self).query(
            Candidate.first_name,
            Candidate.family_name
        )
        results = results.filter(
            Candidate.election_id == self.id,
            Candidate.elected == True
        )
        results = results.order_by(
            Candidate.family_name,
            Candidate.first_name
        )
        return results.all()

    @property
    def has_panachage_data(self):
        """ Checks if there are panachage data available. """

        session = object_session(self)

        ids = session.query(List.id)
        ids = ids.filter(List.election_id == self.id)

        results = session.query(PanachageResult)
        results = results.filter(PanachageResult.target_list_id.in_(ids))

        return results.first() is not None

    #: may be used to store a link related to this election
    related_link = meta_property('related_link')

    def clear_results(self):
        """ Clears all the results. """

        self.counted_entities = 0
        self.total_entities = 0
        self.absolute_majority = None
        self.status = None

        session = object_session(self)
        for connection in self.list_connections:
            session.delete(connection)
        for list_ in self.lists:
            session.delete(list_)
        for candidate in self.candidates:
            session.delete(candidate)
        for result in self.results:
            session.delete(result)
        for result in self.party_results:
            session.delete(result)

    def export(self):
        """ Returns all data connected to this election as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        """

        session = object_session(self)

        ids = session.query(ElectionResult.id)
        ids = ids.filter(ElectionResult.election_id == self.id)

        SubListConnection = aliased(ListConnection)
        results = session.query(
            CandidateResult.votes,
            Election.title_translations,
            Election.date,
            Election.domain,
            Election.type,
            Election.number_of_mandates,
            Election.absolute_majority,
            Election.status,
            Election.counted_entities,
            Election.total_entities,
            ElectionResult.group,
            ElectionResult.entity_id,
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
            Candidate.party,
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

        # We need to merge in the list results per entity
        list_results = session.query(
            ListResult.votes,
            ElectionResult.entity_id,
            List.list_id
        )
        list_results = list_results.outerjoin(ListResult.election_result)
        list_results = list_results.outerjoin(ListResult.list)
        list_results = list_results.filter(
            ListResult.election_result_id.in_(ids)
        )
        list_results = list_results.order_by(
            ElectionResult.entity_id,
            List.list_id
        )
        list_results_grouped = {}
        for key, group in groupby(list_results, lambda x: x[1]):
            list_results_grouped[key] = dict([(g[2], g[0]) for g in group])

        # We need to collect the panachage results per list
        list_ids = session.query(List.id, List.list_id)
        list_ids = list_ids.filter(List.election_id == self.id)

        panachage_lists = []
        panachage = {}
        if self.has_panachage_data:
            panachage_results = session.query(PanachageResult)
            panachage_results = panachage_results.filter(
                PanachageResult.target_list_id.in_((id[0] for id in list_ids))
            )

            panachage_lists = session.query(List.list_id)
            panachage_lists = panachage_lists.filter(
                List.election_id == self.id
            )
            panachage_lists = [t[0] for t in panachage_lists]
            panachage_lists = sorted(
                set(panachage_lists) |
                set([r.source_list_id for r in panachage_results])
            )

            list_lookup = {id[0]: id[1] for id in list_ids}
            panachage = {id: {} for id in panachage_lists}
            for result in panachage_results:
                key = list_lookup.get(result.target_list_id)
                panachage[key][result.source_list_id] = result.votes

        rows = []
        for result in results:
            row = OrderedDict()
            for locale, title in (result[1] or {}).items():
                row['election_title_{}'.format(locale)] = (title or '').strip()
            row['election_date'] = result[2].isoformat()
            row['election_domain'] = result[3]
            row['election_type'] = result[4]
            row['election_mandates'] = result[5]
            row['election_absolute_majority'] = result[6]
            row['election_status'] = result[7] or 'unknown'
            row['election_counted_entities'] = result[8]
            row['election_total_entities'] = result[9]

            row['entity_name'] = result[10]
            row['entity_id'] = result[11]
            row['entity_elegible_voters'] = result[12]
            row['entity_received_ballots'] = result[13]
            row['entity_blank_ballots'] = result[14]
            row['entity_invalid_ballots'] = result[15]
            row['entity_unaccounted_ballots'] = result[16]
            row['entity_accounted_ballots'] = result[17]
            row['entity_blank_votes'] = result[18]
            row['entity_invalid_votes'] = result[19]
            row['entity_accounted_votes'] = result[20]

            row['list_name'] = result[21]
            row['list_id'] = result[22]
            row['list_number_of_mandates'] = result[23]
            row['list_votes'] = list_results_grouped.get(
                row['entity_id'], {}
            ).get(row['list_id'], 0)

            row['list_connection'] = result[24]
            row['list_connection_parent'] = result[25]

            row['candidate_family_name'] = result[26]
            row['candidate_first_name'] = result[27]
            row['candidate_id'] = result[28]
            row['candidate_elected'] = result[29]
            row['candidate_party'] = result[30]
            row['candidate_votes'] = result[0]

            for target_id in panachage_lists:
                key = 'panachage_votes_from_list_{}'.format(target_id)
                row[key] = panachage.get(result[22], {}).get(target_id)

            rows.append(row)

        return rows


class ListConnection(Base, TimestampMixin):

    """ A list connection. """

    __tablename__ = 'list_connections'

    #: internal id of the list
    id = Column(UUID, primary_key=True, default=uuid4)

    #: external id of the list
    connection_id = Column(Text, nullable=False)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=True)

    #: ID of the parent list connection
    parent_id = Column(UUID, ForeignKey('list_connections.id'), nullable=True)

    #: a list connection contains n lists
    lists = relationship(
        'List',
        cascade='all, delete-orphan',
        backref=backref('connection'),
        lazy='dynamic',
        order_by='List.list_id'
    )

    #: a list connection contains n sub-connection
    children = relationship(
        'ListConnection',
        cascade='all, delete-orphan',
        backref=backref('parent', remote_side='ListConnection.id'),
        lazy='dynamic',
        order_by='ListConnection.connection_id'
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

    #: the total votes
    votes = summarized_property('votes')

    #: the total number of mandates
    number_of_mandates = summarized_property('number_of_mandates')

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
    """ A list. """

    __tablename__ = 'lists'

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
        'Candidate',
        cascade='all, delete-orphan',
        backref=backref('list'),
        lazy='dynamic',
    )

    #: a list contains n results
    results = relationship(
        'ListResult',
        cascade='all, delete-orphan',
        backref=backref('list'),
        lazy='dynamic',
    )

    #: a (proporz) list contains votes from other other lists
    panachage_results = relationship(
        'PanachageResult',
        cascade='all, delete-orphan',
        backref=backref('list'),
        lazy='dynamic'
    )

    #: the total votes
    votes = summarized_property('votes')

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
    """ A candidate. """

    __tablename__ = 'candidates'

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

    #: the party name
    party = Column(Text, nullable=True)

    #: a candidate contains n results
    results = relationship(
        'CandidateResult',
        cascade='all, delete-orphan',
        backref=backref('candidate'),
        lazy='dynamic',
    )

    #: the total votes
    votes = summarized_property('votes')

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


class ElectionResult(Base, TimestampMixin, DerivedAttributes):
    """ The election result in a single political entity. """

    __tablename__ = 'election_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=False)

    #: groups the result in whatever structure makes sense
    group = Column(Text, nullable=False)

    #: entity id (e.g. a BFS number).
    entity_id = Column(Integer, nullable=False)

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
        """ The number of accounted votes. """

        return (
            self.election.number_of_mandates * self.accounted_ballots -
            self.blank_votes - self.invalid_votes
        )

    @accounted_votes.expression
    def accounted_votes(cls):
        """ The number of accounted votes. """

        # A bit of a hack :|
        number_of_mandates = select(
            [Election.number_of_mandates],
            whereclause='elections.id = election_results.election_id'
        )
        return (
            number_of_mandates * (
                cls.received_ballots - cls.blank_ballots - cls.invalid_ballots
            ) - cls.blank_votes - cls.invalid_votes
        )

    #: an election result may contain n list results
    list_results = relationship(
        'ListResult',
        cascade='all, delete-orphan',
        backref=backref('election_result'),
        lazy='dynamic',
    )

    #: an election result contains n candidate results
    candidate_results = relationship(
        'CandidateResult',
        cascade='all, delete-orphan',
        backref=backref('election_result'),
        lazy='dynamic',
    )


class ListResult(Base, TimestampMixin):
    """ The election result of a list in a single political entity. """

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


class PanachageResult(Base, TimestampMixin):

    """ The votes transferred from one list to another. """

    __tablename__ = 'panachage_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the target this result belongs to
    target_list_id = Column(UUID, ForeignKey(List.id), nullable=False)

    #: the source this result belongs to
    source_list_id = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)


class CandidateResult(Base, TimestampMixin):
    """ The election result of a candidate in a single political entity. """

    __tablename__ = 'candidate_results'

    #: identifies the candidate result
    id = Column(UUID, primary_key=True, default=uuid4)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)

    #: the election result this result belongs to
    election_result_id = Column(
        UUID, ForeignKey(ElectionResult.id), nullable=False
    )

    #: the candidate this result belongs to
    candidate_id = Column(UUID, ForeignKey(Candidate.id), nullable=False)


class PartyResult(Base, TimestampMixin):
    """ The election result of a party in an election for a given year. """

    __tablename__ = 'party_results'

    #: identifies the party result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey(Election.id), nullable=False)

    # number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)

    # total votes
    total_votes = Column(Integer, nullable=False, default=lambda: 0)

    #: name of the party
    name = Column(Text, nullable=False)

    #: year
    year = Column(Integer, nullable=False, default=lambda: 0)

    #: color code
    color = Column(Text, nullable=True)
