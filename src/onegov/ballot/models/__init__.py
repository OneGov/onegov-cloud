""" OneGov Ballot models the aggregated results of Swiss ballots and elections.
It takes hints from the eCH-0110 & eCH-0155 Standards.

See:

`eCH-0155: Datenstandard politische Rechte \
<https://www.ech.ch/vechweb/page?p=dossier&documentNumber=eCH-0155>`_

"""
from onegov.ballot.models.election import Candidate
from onegov.ballot.models.election import CandidatePanachageResult
from onegov.ballot.models.election import CandidateResult
from onegov.ballot.models.election import Election
from onegov.ballot.models.election import ElectionRelationship
from onegov.ballot.models.election import ElectionResult
from onegov.ballot.models.election import List
from onegov.ballot.models.election import ListConnection
from onegov.ballot.models.election import ListPanachageResult
from onegov.ballot.models.election import ListResult
from onegov.ballot.models.election import ProporzElection
from onegov.ballot.models.election_compound import ElectionCompound
from onegov.ballot.models.election_compound import ElectionCompoundPart
from onegov.ballot.models.election_compound import ElectionCompoundRelationship
from onegov.ballot.models.party_result import PartyPanachageResult
from onegov.ballot.models.party_result import PartyResult
from onegov.ballot.models.vote import Ballot
from onegov.ballot.models.vote import BallotResult
from onegov.ballot.models.vote import ComplexVote
from onegov.ballot.models.vote import Vote

__all__ = (
    'Ballot',
    'BallotResult',
    'Candidate',
    'CandidatePanachageResult',
    'CandidateResult',
    'ComplexVote',
    'Election',
    'ElectionCompound',
    'ElectionCompoundPart',
    'ElectionCompoundRelationship',
    'ElectionRelationship',
    'ElectionResult',
    'List',
    'ListConnection',
    'ListPanachageResult',
    'ListResult',
    'PartyPanachageResult',
    'PartyResult',
    'ProporzElection',
    'Vote',
)
