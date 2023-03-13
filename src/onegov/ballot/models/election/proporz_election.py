from collections import OrderedDict
from itertools import groupby
from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_panachage_result import \
    CandidatePanachageResult
from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election import Election
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.list import List
from onegov.ballot.models.election.list_connection import ListConnection
from onegov.ballot.models.election.list_panachage_result import \
    ListPanachageResult
from onegov.ballot.models.election.list_result import ListResult
from onegov.ballot.models.party_result.party_panachage_result import \
    PartyPanachageResult
from onegov.ballot.models.party_result.party_result import PartyResult
from onegov.ballot.models.party_result.mixins import PartyResultsCheckMixin
from onegov.ballot.models.party_result.mixins import PartyResultsExportMixin
from onegov.ballot.models.party_result.mixins import \
    HistoricalPartyResultsMixin
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class ProporzElection(
    Election, PartyResultsCheckMixin, PartyResultsExportMixin,
    HistoricalPartyResultsMixin
):
    __mapper_args__ = {
        'polymorphic_identity': 'proporz'
    }

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

    #: An election may contains n party results
    party_results = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    #: An election may contains n party panachage results
    party_panachage_results = relationship(
        'PartyPanachageResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
    )

    @property
    def compound(self):
        associations = self.associations
        if not associations:
            return None
        compounds = [
            a.election_compound for a in associations
            if a.election_compound.date == self.date
        ]
        return compounds[0] if compounds else None

    @property
    def completed(self):
        """ Overwrites StatusMixin's 'completed' for compounds with manual
        completion. """

        result = super(ProporzElection, self).completed

        compound = self.compound
        if compound and compound.completes_manually:
            return compound.manually_completed and result

        return result

    @property
    def votes_by_entity(self):
        results = self.results.order_by(None)
        results = results.outerjoin(ListResult)
        results = results.with_entities(
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
    def votes_by_district(self):
        results = self.results.order_by(None)
        results = results.outerjoin(ListResult)
        results = results.with_entities(
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
    def polymorphic_base(self):
        return Election

    @property
    def has_lists_panachage_data(self):
        """ Checks if there are lists panachage data available. """

        session = object_session(self)

        ids = session.query(List.id)
        ids = ids.filter(List.election_id == self.id)

        results = session.query(ListPanachageResult)
        results = results.filter(
            ListPanachageResult.target_id.in_(ids),
            ListPanachageResult.votes > 0
        )

        return results.first() is not None

    @property
    def has_candidate_panachage_data(self):
        """ Checks if there are candidate panachage data available. """

        session = object_session(self)

        ids = session.query(Candidate.id)
        ids = ids.filter(Candidate.election_id == self.id)

        results = session.query(CandidatePanachageResult)
        results = results.filter(
            CandidatePanachageResult.target_id.in_(ids),
            CandidatePanachageResult.votes > 0
        )

        return results.first() is not None

    @property
    def relationships_for_historical_party_results(self):
        return self.related_elections

    def clear_results(self):
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

    def export(self, locales):
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
            Election.number_of_mandates.label('election_mandates'),
            Election.absolute_majority,
            Election.status,
            ElectionResult.superregion,
            ElectionResult.district,
            ElectionResult.name.label('entity_name'),
            ElectionResult.entity_id,
            ElectionResult.counted,
            ElectionResult.eligible_voters,
            ElectionResult.expats,
            ElectionResult.received_ballots,
            ElectionResult.blank_ballots,
            ElectionResult.invalid_ballots,
            ElectionResult.unaccounted_ballots,
            ElectionResult.accounted_ballots,
            ElectionResult.blank_votes,
            ElectionResult.invalid_votes,
            ElectionResult.accounted_votes,
            List.name.label('list_name'),
            List.list_id,
            List.number_of_mandates.label('list_number_of_mandates'),
            SubListConnection.connection_id,
            ListConnection.connection_id.label('parent_connection_id'),
            Candidate.family_name,
            Candidate.first_name,
            Candidate.candidate_id,
            Candidate.elected,
            Candidate.party,
            Candidate.gender,
            Candidate.year_of_birth,
        )
        results = results.outerjoin(CandidateResult.candidate)
        results = results.outerjoin(CandidateResult.election_result)
        results = results.outerjoin(Candidate.list)
        results = results.outerjoin(SubListConnection, List.connection)
        results = results.outerjoin(SubListConnection.parent)
        results = results.outerjoin(Candidate.election)
        results = results.filter(CandidateResult.election_result_id.in_(ids))
        results = results.order_by(
            ElectionResult.district,
            ElectionResult.name,
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
        list_ids = dict(list_ids)
        list_ids[None] = '999'
        list_panachage_results = session.query(ListPanachageResult)
        list_panachage_results = list_panachage_results.filter(
            ListPanachageResult.target_id.in_(list_ids)
        )
        list_panachage = {}
        for result in list_panachage_results:
            target = list_ids[result.target_id]
            source = list_ids[result.source_id]
            list_panachage.setdefault(target, {})
            list_panachage[target][source] = result.votes

        # We need to collect the panchage results per candidate
        candidate_ids = session.query(Candidate.id, Candidate.candidate_id)
        candidate_ids = candidate_ids.filter(Candidate.election_id == self.id)
        candidate_ids = dict(candidate_ids)
        candidate_panachage_results = session.query(
            CandidatePanachageResult.target_id,
            CandidatePanachageResult.source_id,
            CandidatePanachageResult.votes,
            ElectionResult.entity_id
        )
        candidate_panachage_results = candidate_panachage_results.outerjoin(
            ElectionResult
        )
        candidate_panachage_results = candidate_panachage_results.filter(
            CandidatePanachageResult.target_id.in_(candidate_ids)
        )
        candidate_panachage = {}
        for result in candidate_panachage_results:
            target = candidate_ids[result.target_id]
            source = list_ids[result.source_id]
            entity = result.entity_id
            candidate_panachage.setdefault(entity, {})
            candidate_panachage[entity].setdefault(target, {})
            candidate_panachage[entity][target][source] = result.votes

        rows = []
        for result in results:
            row = OrderedDict()
            translations = result.title_translations or {}
            for locale in locales:
                title = translations.get(locale, '') or ''
                row[f'election_title_{locale}'] = title.strip()
            row['election_date'] = result.date.isoformat()
            row['election_domain'] = result.domain
            row['election_type'] = result.type
            row['election_mandates'] = result.election_mandates
            row['election_absolute_majority'] = result.absolute_majority
            row['election_status'] = result.status or 'unknown'
            row['entity_superregion'] = result.superregion or ''
            row['entity_district'] = result.district or ''
            row['entity_name'] = result.entity_name
            row['entity_id'] = result.entity_id
            row['entity_counted'] = result.counted
            row['entity_eligible_voters'] = result.eligible_voters
            row['entity_expats'] = result.expats
            row['entity_received_ballots'] = result.received_ballots
            row['entity_blank_ballots'] = result.blank_ballots
            row['entity_invalid_ballots'] = result.invalid_ballots
            row['entity_unaccounted_ballots'] = result.unaccounted_ballots
            row['entity_accounted_ballots'] = result.accounted_ballots
            row['entity_blank_votes'] = result.blank_votes
            row['entity_invalid_votes'] = result.invalid_votes
            row['entity_accounted_votes'] = result.accounted_votes
            row['list_name'] = result.list_name
            row['list_id'] = result.list_id
            row['list_color'] = self.colors.get(result.list_name, '')
            row['list_number_of_mandates'] = result.list_number_of_mandates
            row['list_votes'] = list_results_grouped.get(
                result.entity_id, {}
            ).get(result.list_id, 0)
            row['list_connection'] = result.connection_id
            row['list_connection_parent'] = result.parent_connection_id
            row['candidate_family_name'] = result.family_name
            row['candidate_first_name'] = result.first_name
            row['candidate_id'] = result.candidate_id
            row['candidate_elected'] = result.elected
            row['candidate_party'] = result.party
            row['candidate_party_color'] = self.colors.get(result.party, '')
            row['candidate_gender'] = result.gender or ''
            row['candidate_year_of_birth'] = result.year_of_birth or ''
            row['candidate_votes'] = result.votes
            for id_ in sorted(list_ids.values()):
                key = f'list_panachage_votes_from_list_{id_}'
                row[key] = list_panachage.get(result.list_id, {}).get(id_)
            if candidate_panachage:
                for id_ in sorted(list_ids.values()):
                    key = f'candidate_panachage_votes_from_list_{id_}'
                    row[key] = candidate_panachage.get(
                        result.entity_id, {}
                    ).get(result.candidate_id, {}).get(id_)
            rows.append(row)

        return rows
