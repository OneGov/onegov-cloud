from collections import OrderedDict
from itertools import groupby
from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election import Election
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.list import List
from onegov.ballot.models.election.list_connection import ListConnection
from onegov.ballot.models.election.list_result import ListResult
from onegov.ballot.models.election.mixins import PartyResult
from onegov.ballot.models.election.mixins import PartyResultsExportMixin
from onegov.ballot.models.election.panachage_result import PanachageResult
from sqlalchemy import cast
from sqlalchemy import desc
from sqlalchemy import String
from sqlalchemy.orm import aliased
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class ProporzElection(Election, PartyResultsExportMixin):
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
        primaryjoin=(
            'foreign(PartyResult.owner) == ProporzElection.id'
        ),
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    @property
    def polymorphic_base(self):
        return Election

    @property
    def last_modified(self):
        """ Returns last change of the election, its candidates, lists, list
        connections and any of its results.

        """
        session = object_session(self)

        changed = super(ProporzElection, self).last_modified

        connections = session.query(ListConnection.last_change)
        connections = connections.order_by(desc(ListConnection.last_change))
        connections = connections.filter(ListConnection.election_id == self.id)
        connections = connections.first()[0] if connections.first() else None

        lists = session.query(List.last_change)
        lists = lists.order_by(desc(List.last_change))
        lists = lists.filter(List.election_id == self.id)
        lists = lists.first()[0] if lists.first() else None

        changes = [changed, connections, lists]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def last_result_change(self):
        """ Returns the last change of the results of the election and the
        candidates.

        """
        session = object_session(self)

        changed = super(ProporzElection, self).last_result_change

        lists = None
        pan = None
        ids = session.query(List.id)
        ids = ids.filter(List.election_id == self.id).all()
        if ids:
            lists = session.query(ListResult.last_change)
            lists = lists.order_by(desc(ListResult.last_change))
            lists = lists.filter(ListResult.list_id.in_(ids))
            lists = lists.first()[0] if lists.first() else None

            ids = [str(id_[0]) for id_ in ids]
            pan = session.query(PanachageResult.last_change)
            pan = pan.order_by(desc(PanachageResult.last_change))
            pan = pan.filter(PanachageResult.target.in_(ids))
            pan = pan.first()[0] if pan.first() else None

        parties = session.query(PartyResult.last_change)
        parties = parties.order_by(desc(PartyResult.last_change))
        parties = parties.filter(PartyResult.owner == self.id)
        parties = parties.first()[0] if parties.first() else None

        changes = [changed, lists, pan, parties]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def has_panachage_data(self):
        """ Checks if there are panachage data available. """

        session = object_session(self)

        ids = session.query(cast(List.id, String))
        ids = ids.filter(List.election_id == self.id)

        results = session.query(PanachageResult)
        results = results.filter(PanachageResult.target.in_(ids))

        return results.first() is not None

    def clear_results(self):
        """ Clears all the results. """

        super(ProporzElection, self).clear_results()

        session = object_session(self)
        for connection in self.list_connections:
            session.delete(connection)
        for list_ in self.lists:
            session.delete(list_)
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
            ElectionResult.district,
            ElectionResult.name,
            ElectionResult.entity_id,
            ElectionResult.counted,
            ElectionResult.eligible_voters,
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

        panachage_lists = []
        panachage = {}
        if self.has_panachage_data:
            panachage_results = session.query(PanachageResult)
            panachage_results = panachage_results.filter(
                PanachageResult.target.in_((str(id[0]) for id in list_ids))
            )

            panachage_lists = session.query(List.list_id)
            panachage_lists = panachage_lists.filter(
                List.election_id == self.id
            )
            panachage_lists = [t[0] for t in panachage_lists]
            panachage_lists = sorted(
                set(panachage_lists) |
                set([r.source for r in panachage_results])
            )

            list_lookup = {str(id[0]): id[1] for id in list_ids}
            panachage = {id: {} for id in panachage_lists}
            for result in panachage_results:
                key = list_lookup.get(result.target)
                panachage[key][result.source] = result.votes

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

            row['entity_district'] = result[8] or ''
            row['entity_name'] = result[9]
            row['entity_id'] = result[10]
            row['entity_counted'] = result[11]
            row['entity_eligible_voters'] = result[12]
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
