from __future__ import annotations

from onegov.election_day.models.election.candidate import Candidate
from onegov.election_day.models.election.candidate_panachage_result import \
    CandidatePanachageResult
from onegov.election_day.models.election.candidate_result import \
    CandidateResult
from onegov.election_day.models.election.election import Election
from onegov.election_day.models.election.election_result import ElectionResult
from onegov.election_day.models.election.list import List
from onegov.election_day.models.election.list_connection import ListConnection
from onegov.election_day.models.election.list_panachage_result import \
    ListPanachageResult
from onegov.election_day.models.election.list_result import ListResult
from onegov.election_day.models.election.proporz_election import \
    ProporzElection
from onegov.election_day.models.election.relationship import \
    ElectionRelationship


__all__ = (
    'Candidate',
    'CandidatePanachageResult',
    'CandidateResult',
    'Election',
    'ElectionRelationship',
    'ElectionResult',
    'List',
    'ListConnection',
    'ListPanachageResult',
    'ListResult',
    'ProporzElection',
)
