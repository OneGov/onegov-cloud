from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_panachage_result import (
    CandidatePanachageResult)
from onegov.ballot.models.election.election import Election
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.list import List
from onegov.ballot.models.election.list_connection import ListConnection
from onegov.ballot.models.election.list_panachage_result import (
    ListPanachageResult)
from onegov.ballot.models.election.list_result import ListResult
from onegov.ballot.models.party_result.party_panachage_result import (
    PartyPanachageResult)
from onegov.ballot.models.party_result.party_result import PartyResult
from onegov.ballot.models.party_result.mixins import PartyResultsCheckMixin
from onegov.ballot.models.party_result.mixins import (
    HistoricalPartyResultsMixin)
from sqlalchemy import func
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import Query
    from typing import NamedTuple

    from .election import VotesByDistrictRow
    from ..election_compound import ElectionCompound
    from ..election_compound import ElectionCompoundAssociation

    rel = relationship

    class VotesByEntityRow(NamedTuple):
        election_id: str
        entity_id: int
        counted: bool
        votes: int


class ProporzElection(
    Election, PartyResultsCheckMixin, HistoricalPartyResultsMixin
):
    __mapper_args__ = {
        'polymorphic_identity': 'proporz'
    }

    #: An election contains n list connections
    list_connections: 'rel[AppenderQuery[ListConnection]]' = relationship(
        'ListConnection',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='ListConnection.connection_id'
    )

    #: An election contains n lists
    lists: 'rel[AppenderQuery[List]]' = relationship(
        'List',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    #: An election may contains n party results
    party_results: 'rel[AppenderQuery[PartyResult]]' = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    #: An election may contains n party panachage results
    party_panachage_results: 'rel[AppenderQuery[PartyPanachageResult]]'
    party_panachage_results = relationship(
        'PartyPanachageResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    if TYPE_CHECKING:
        # backrefs
        associations: rel[AppenderQuery[ElectionCompoundAssociation]]

    @property
    def compound(self) -> 'ElectionCompound | None':
        associations = self.associations
        if not associations:
            return None
        compounds = [
            a.election_compound for a in associations
            if a.election_compound.date == self.date
        ]
        return compounds[0] if compounds else None

    @property
    def completed(self) -> bool:
        """ Overwrites StatusMixin's 'completed' for compounds with manual
        completion. """

        result = super(ProporzElection, self).completed

        compound = self.compound
        if compound and compound.completes_manually:
            return compound.manually_completed and result

        return result

    @property
    def votes_by_entity(self) -> 'Query[VotesByEntityRow]':
        query = self.results.order_by(None)
        query = query.outerjoin(ListResult)
        results = query.with_entities(
            ElectionResult.election_id,
            ElectionResult.entity_id,
            ElectionResult.counted,
            func.coalesce(func.sum(ListResult.votes), 0).label('votes')
        )
        results = results.group_by(
            ElectionResult.entity_id,
            ElectionResult.counted,
            ElectionResult.election_id
        )
        return results

    @property
    def votes_by_district(self) -> 'Query[VotesByDistrictRow]':
        query = self.results.order_by(None)
        query = query.outerjoin(ListResult)
        results = query.with_entities(
            ElectionResult.election_id,
            ElectionResult.district,
            func.array_agg(
                ElectionResult.entity_id.distinct()).label('entities'),
            func.coalesce(
                func.bool_and(ElectionResult.counted), False
            ).label('counted'),
            func.coalesce(func.sum(ListResult.votes), 0).label('votes')
        )
        results = results.group_by(
            ElectionResult.district,
            ElectionResult.election_id,
        )
        results = results.filter(ElectionResult.election_id == self.id)
        return results

    @property
    def polymorphic_base(self) -> type[Election]:
        return Election

    @property
    def has_lists_panachage_data(self) -> bool:
        """ Checks if there are lists panachage data available. """

        session = object_session(self)

        # FIXME: Why are we doing two queries instead of a join?
        ids = session.query(List.id)
        ids = ids.filter(List.election_id == self.id)

        results = session.query(ListPanachageResult)
        results = results.filter(
            ListPanachageResult.target_id.in_(ids),
            ListPanachageResult.votes > 0
        )

        return session.query(results.exists()).scalar()

    @property
    def has_candidate_panachage_data(self) -> bool:
        """ Checks if there are candidate panachage data available. """

        session = object_session(self)

        # FIXME: Why are we doing two queries instead of a join?
        ids = session.query(Candidate.id)
        ids = ids.filter(Candidate.election_id == self.id)

        results = session.query(CandidatePanachageResult)
        results = results.filter(
            CandidatePanachageResult.target_id.in_(ids),
            CandidatePanachageResult.votes > 0
        )

        return session.query(results.exists()).scalar()

    @property
    def relationships_for_historical_party_results(
        self
    ) -> 'AppenderQuery[Election]':
        return self.related_elections

    def clear_results(self) -> None:
        """ Clears all the results. """

        super(ProporzElection, self).clear_results()

        session = object_session(self)
        session.query(List).filter(List.election_id == self.id).delete()
        session.query(ListConnection).filter(
            ListConnection.election_id == self.id
        ).delete()
        session.query(PartyResult).filter(
            PartyResult.election_id == self.id
        ).delete()
        session.query(PartyPanachageResult).filter(
            PartyPanachageResult.election_id == self.id
        ).delete()
