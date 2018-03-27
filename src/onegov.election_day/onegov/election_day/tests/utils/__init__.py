from datetime import date
from io import BytesIO
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import ProporzElection
from onegov.ballot import Vote
from onegov.election_day.utils.d3_renderer import D3Renderer
from reportlab.pdfgen.canvas import Canvas
from uuid import uuid4


class PatchedD3Renderer(D3Renderer):
    def get_chart(self, chart, fmt, data, width=1000, params=None):
        chart = BytesIO()
        canvas = Canvas(chart, pagesize=(140, 140))
        canvas.drawString(10, 70, "This is a diagram")
        canvas.save()
        chart.seek(0)
        return chart


def add_majorz_election(session):
    election = Election(
        title='Majorz Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=200
    )
    session.add(election)
    session.flush()

    result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election.results.append(result)

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        family_name='N1',
        first_name='F1',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        family_name='N2',
        first_name='F2',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_1.id, votes=520)
    )
    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_2.id, votes=111)
    )
    session.flush()

    return election


def add_proporz_election(session, year=2015):
    election = ProporzElection(
        title='Proporz Election',
        domain='federation',
        date=date(year, 6, 14),
        number_of_mandates=1
    )
    session.add(election)
    session.flush()

    result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election.results.append(result)

    list_1 = List(id=uuid4(), list_id='1', number_of_mandates=1, name='L1')
    list_2 = List(id=uuid4(), list_id='2', number_of_mandates=1, name='L2')
    list_3 = List(id=uuid4(), list_id='3', number_of_mandates=2, name='L3')
    election.lists.append(list_1)
    election.lists.append(list_2)
    election.lists.append(list_3)

    election.party_results.append(
        PartyResult(name='Party 1', number_of_mandates=1, votes=10)
    )
    election.party_results.append(
        PartyResult(name='Party 2', number_of_mandates=1, votes=20)
    )
    election.panachage_results.append(
        PanachageResult(source='Party 1', target='Party 2', votes=12)
    )
    election.panachage_results.append(
        PanachageResult(source='Party 2', target='Party 1', votes=21)
    )

    list_1.panachage_results.append(
        PanachageResult(target=str(list_1.id), source=2, votes=1)
    )
    list_1.panachage_results.append(
        PanachageResult(target=str(list_1.id), source=3, votes=1)
    )
    list_2.panachage_results.append(
        PanachageResult(target=str(list_2.id), source=1, votes=2)
    )
    list_2.panachage_results.append(
        PanachageResult(target=str(list_2.id), source=3, votes=2)
    )
    list_3.panachage_results.append(
        PanachageResult(target=str(list_3.id), source=1, votes=3)
    )
    list_3.panachage_results.append(
        PanachageResult(target=str(list_3.id), source=2, votes=3)
    )

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        list_id=list_1.id,
        family_name='N1',
        first_name='F1',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        list_id=list_2.id,
        family_name='N2',
        first_name='F2',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_1.id, votes=520)
    )
    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_2.id, votes=111)
    )

    result.list_results.append(ListResult(list_id=list_1.id, votes=520))
    result.list_results.append(ListResult(list_id=list_2.id, votes=111))
    result.list_results.append(ListResult(list_id=list_3.id, votes=21))

    connection_1 = ListConnection(
        id=uuid4(),
        connection_id='A',
        election_id=election.id,
        parent_id=None,
    )
    connection_2 = ListConnection(
        id=uuid4(),
        connection_id='B',
        election_id=election.id,
        parent_id=None,
    )
    subconnection = ListConnection(id=uuid4(), connection_id='B.1')
    connection_2.children.append(subconnection)
    election.list_connections.append(connection_1)
    election.list_connections.append(connection_2)
    election.list_connections.append(subconnection)
    list_1.connection_id = connection_1.id
    list_2.connection_id = connection_2.id
    list_3.connection_id = subconnection.id
    session.flush()

    return election


def add_vote(session, type_):
    vote = Vote.get_polymorphic_class(type_, Vote)(
        title='Vote', domain='federation', date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    if type_ == 'complex':
        vote.ballots.append(Ballot(type='counter-proposal'))
        vote.ballots.append(Ballot(type='tie-breaker'))
    session.add(vote)
    session.flush()

    vote.proposal.results.append(BallotResult(
        name='x', yeas=0, nays=100, counted=True, entity_id=1
    ))
    if type_ == 'complex':
        vote.counter_proposal.results.append(BallotResult(
            name='x', yeas=90, nays=10, counted=True, entity_id=1
        ))
        vote.tie_breaker.results.append(BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1
        ))
    session.flush()

    return vote


def add_election_compound(session, year=2015, elections=None):
    compound = ElectionCompound(
        title='Election Compound',
        domain='canton',
        date=date(year, 6, 14),
        elections=elections or []
    )
    session.add(compound)
    session.flush()

    compound.party_results.append(
        PartyResult(name='Party 1', number_of_mandates=1, votes=10)
    )
    compound.party_results.append(
        PartyResult(name='Party 2', number_of_mandates=1, votes=20)
    )
    compound.panachage_results.append(
        PanachageResult(source='Party 1', target='Party 2', votes=12)
    )
    compound.panachage_results.append(
        PanachageResult(source='Party 2', target='Party 1', votes=21)
    )

    return compound
