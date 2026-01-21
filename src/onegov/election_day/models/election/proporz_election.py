from __future__ import annotations

from onegov.election_day.models.election.candidate_panachage_result import \
    CandidatePanachageResult
from onegov.election_day.models.election.election import Election
from onegov.election_day.models.election.election_result import ElectionResult
from onegov.election_day.models.election.list import List
from onegov.election_day.models.election.list_connection import ListConnection
from onegov.election_day.models.election.list_panachage_result import \
    ListPanachageResult
from onegov.election_day.models.election.list_result import ListResult
from onegov.election_day.models.party_result.mixins import \
    HistoricalPartyResultsMixin
from onegov.election_day.models.party_result.mixins import \
    PartyResultsCheckMixin
from onegov.election_day.models.party_result.party_panachage_result import \
    PartyPanachageResult
from onegov.election_day.models.party_result.party_result import PartyResult
from sqlalchemy import func
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import AppenderQuery
    from onegov.election_day.models import ElectionRelationship
    from onegov.election_day.models.election.election import \
        VotesByDistrictRow
    from sqlalchemy.orm import Query
    from typing import NamedTuple

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
    list_connections: relationship[list[ListConnection]] = relationship(
        'ListConnection',
        cascade='all, delete-orphan',
        back_populates='election',
        order_by='ListConnection.connection_id'
    )

    #: An election contains n lists
    lists: relationship[list[List]] = relationship(
        'List',
        cascade='all, delete-orphan',
        back_populates='election',
    )

    #: An election may contains n party results
    party_results: relationship[list[PartyResult]] = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        back_populates='election',
        overlaps='party_results'  # type: ignore[call-arg]
    )

    #: An election may contains n party panachage results
    party_panachage_results: relationship[list[PartyPanachageResult]]
    party_panachage_results = relationship(
        'PartyPanachageResult',
        cascade='all, delete-orphan',
        back_populates='election',
        overlaps='panachage_results'  # type: ignore[call-arg]
    )

    @property
    def votes_by_entity(self) -> Query[VotesByEntityRow]:
        query = self.results_query.order_by(None)
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
    def votes_by_district(self) -> Query[VotesByDistrictRow]:
        query = self.results_query.order_by(None)
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
    def has_lists_panachage_data(self) -> bool:
        """ Checks if there are lists panachage data available. """

        for list_ in self.lists:
            for result in list_.panachage_results:
                if result.votes > 0:
                    return True
        return False

    @property
    def has_candidate_panachage_data(self) -> bool:
        """ Checks if there are candidate panachage data available. """

        for candidate in self.candidates:
            for result in candidate.panachage_results:
                if result.votes > 0:
                    return True

        return False

    @property
    def relationships_for_historical_party_results(
        self
    ) -> AppenderQuery[ElectionRelationship]:
        return self.related_elections

    def clear_results(self, clear_all: bool = False) -> None:
        """ Clears all the results. """

        super().clear_results(clear_all)

        session = object_session(self)
        if clear_all:
            session.query(List).filter(List.election_id == self.id).delete()
            session.query(ListConnection).filter(
                ListConnection.election_id == self.id
            ).delete()
        else:
            e_ids = session.query(ElectionResult.id).filter(
                ElectionResult.election_id == self.id
            ).scalar_subquery()
            session.query(CandidatePanachageResult).filter(
                CandidatePanachageResult.election_result_id.in_(e_ids)
            ).delete()
            l_ids = session.query(List.id).filter(
                List.election_id == self.id
            ).scalar_subquery()
            session.query(ListPanachageResult).filter(
                ListPanachageResult.target_id.in_(l_ids)
            ).delete()
        session.query(PartyResult).filter(
            PartyResult.election_id == self.id
        ).delete()
        session.query(PartyPanachageResult).filter(
            PartyPanachageResult.election_id == self.id
        ).delete()
        session.flush()
        session.expire_all()
