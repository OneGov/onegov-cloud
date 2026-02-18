from __future__ import annotations

from datetime import date
from decimal import Decimal
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidatePanachageResult
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import ElectionRelationship
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ListResult
from onegov.election_day.models import PartyPanachageResult
from onegov.election_day.models import PartyResult
from onegov.election_day.models import ProporzElection
from pytest import mark
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from io import BytesIO
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def proporz_election() -> ProporzElection:
    eid = uuid4()
    pid = uuid4()
    cid = uuid4()
    sid = uuid4()
    lid = uuid4()
    election = ProporzElection(
        title='Election',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim',
        absolute_majority=10000
    )
    election.list_connections.append(
        ListConnection(id=pid, connection_id='1')
    )
    election.list_connections.append(
        ListConnection(id=sid, connection_id='2', parent_id=pid)
    )
    election.lists.append(
        List(
            id=lid,
            number_of_mandates=0,
            list_id='A',
            name='List',
            connection_id=sid
        )
    )
    election.lists[0].panachage_results.append(
        ListPanachageResult(
            source_id=None,
            votes=0
        )
    )
    election.candidates.append(
        Candidate(
            id=cid,
            candidate_id='0',
            family_name='X',
            first_name='Y',
            elected=False,
            list_id=lid,
        )
    )
    election.candidates[0].panachage_results.append(
        CandidatePanachageResult(
            election_result_id=eid,
            source_id=None,
            votes=0
        )
    )
    election_result = ElectionResult(
        id=eid,
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=100,
        received_ballots=2,
        blank_ballots=3,
        invalid_ballots=4,
        blank_votes=5,
        invalid_votes=6
    )
    election_result.list_results.append(
        ListResult(list_id=lid, votes=10)
    )
    election_result.candidate_results.append(
        CandidateResult(candidate_id=cid, votes=0)
    )

    election.results.append(election_result)
    election.party_results.append(
        PartyResult(
            year=2017,
            number_of_mandates=0,
            votes=0,
            total_votes=100,
            name_translations={'en_US': 'A'},
            party_id='1'
        )
    )

    election.party_panachage_results.append(
        PartyPanachageResult(target=str(lid), source='1', votes=0)
    )

    election.last_result_change = election.timestamp()

    return election


def test_proporz_election_create_all_models(session: Session) -> None:
    election = ProporzElection(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    connection = ListConnection(
        connection_id='0',
        election_id=election.id,
    )

    session.add(connection)
    session.flush()

    subconnection = ListConnection(
        connection_id='0',
        parent_id=connection.id,
    )

    session.add(subconnection)
    session.flush()

    list_ = List(
        number_of_mandates=0,
        list_id="0",
        name="List A",
        election_id=election.id,
        connection_id=subconnection.id
    )

    session.add(list_)
    session.flush()

    candidate = Candidate(
        candidate_id="0",
        family_name="Quimby",
        first_name="Joe",
        elected=False,
        election_id=election.id,
        list_id=list_.id,
    )

    session.add(candidate)
    session.flush()

    party_result = PartyResult(
        election_id=election.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name_translations={'en_US': 'Libertarian'},
        party_id='1',
    )

    session.add(party_result)
    session.flush()

    election_result = ElectionResult(
        election_id=election.id,
        name='name',
        entity_id=1000,
        counted=False,
        eligible_voters=0,
        received_ballots=0,
        blank_ballots=0,
        invalid_ballots=0,
        blank_votes=0,
        invalid_votes=0
    )

    session.add(election_result)
    session.flush()

    list_result = ListResult(
        election_result_id=election_result.id,
        list_id=list_.id,
        votes=0
    )

    session.add(list_result)
    session.flush()

    list_panachage_result = ListPanachageResult(
        target_id=list_.id,
        source_id=None,
        votes=0
    )

    session.add(list_panachage_result)
    session.flush()

    candidate_result = CandidateResult(
        election_result_id=election_result.id,
        candidate_id=candidate.id,
        votes=0
    )

    candidate_panachage_result = CandidatePanachageResult(
        election_result_id=election_result.id,
        target_id=candidate.id,
        source_id=list_.id,
        votes=0
    )

    session.add(candidate_panachage_result)
    session.add(candidate_result)
    session.flush()
    session.expire_all()

    assert election.list_connections == [connection]
    assert election.lists == [list_]
    assert election.candidates == [candidate]
    assert election.party_results == [party_result]
    assert election.results == [election_result]

    assert connection.election == election
    assert connection.lists == []
    if not TYPE_CHECKING:
        # NOTE: Can't be true at type checking time
        assert connection.parent is None
    assert connection.children.all() == [subconnection]

    if not TYPE_CHECKING:
        # NOTE: Can't be true at type checking time
        assert subconnection.election is None
    assert subconnection.lists == [list_]
    assert subconnection.parent == connection
    assert subconnection.children.all() == []

    assert list_.candidates == [candidate]
    assert list_.results == [list_result]
    assert list_.election == election

    assert candidate.results == [candidate_result]
    assert candidate.election == election
    assert candidate.list == list_
    assert candidate.panachage_results == [candidate_panachage_result]

    assert party_result.election_id == election.id

    assert election_result.list_results == [list_result]
    assert election_result.candidate_results == [candidate_result]
    assert election_result.election == election

    assert list_result.election_result == election_result
    assert list_result.list == list_

    assert list_.panachage_results == [list_panachage_result]

    if not TYPE_CHECKING:
        # NOTE: Can't be true at type checking time
        assert list_panachage_result.source is None
    assert list_panachage_result.target == list_

    assert candidate_result.election_result == election_result
    assert candidate_result.candidate == candidate

    session.delete(election)
    session.flush()

    assert session.query(Candidate).all() == []
    assert session.query(CandidateResult).all() == []
    assert session.query(CandidatePanachageResult).all() == []
    assert session.query(ProporzElection).all() == []
    assert session.query(ElectionResult).all() == []
    assert session.query(List).all() == []
    assert session.query(ListConnection).all() == []
    assert session.query(ListResult).all() == []
    assert session.query(ListPanachageResult).all() == []


def test_proporz_election_has_data(session: Session) -> None:
    election = ProporzElection(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )
    list_1 = List(
        id=uuid4(),
        number_of_mandates=0,
        list_id="1",
        name="List A",
    )
    list_2 = List(
        number_of_mandates=0,
        list_id="2",
        name="List B",
    )
    candidate = Candidate(
        candidate_id="0",
        family_name="Quimby",
        first_name="Joe",
        elected=False,
        list_id=list_1.id,
    )
    election_result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=1000,
        expats=35,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election.lists.append(list_1)
    election.lists.append(list_2)
    election.candidates.append(candidate)
    election.results.append(election_result)
    session.add(election)
    session.flush()
    assert election.has_lists_panachage_data is False
    assert election.has_party_results is False
    assert election.has_party_panachage_results is False

    # lists panachage
    list_panachage_result = ListPanachageResult(
        target_id=list_1.id,
        source_id=list_2.id,
        votes=0
    )
    election.lists[0].panachage_results.append(list_panachage_result)
    election.lists[1].panachage_results.append(
        ListPanachageResult(
            target_id=list_2.id,
            source_id=list_1.id,
            votes=0
        )
    )
    assert election.has_lists_panachage_data is False
    list_panachage_result.votes = 10
    # undo mypy narrowing
    election = election
    assert election.has_lists_panachage_data is True

    # candidate panachage
    candidate_panachage_result = CandidatePanachageResult(
        election_result_id=election_result.id,
        source_id=list_2.id,
        votes=0
    )
    candidate.panachage_results.append(candidate_panachage_result)
    candidate.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result.id,
            source_id=list_1.id,
            votes=0
        )
    )
    assert election.has_candidate_panachage_data is False
    candidate_panachage_result.votes = 10
    # undo mypy narrowing
    election = election
    assert election.has_candidate_panachage_data is True

    # party results
    party_result = PartyResult(
        election_id=election.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name_translations={'en_US': 'Libertarian'},
        party_id='1'
    )
    election.party_results = [party_result]
    assert election.has_party_results is False
    party_result.votes = 10
    # undo mypy narrowing
    election = election
    assert election.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = Decimal('10')
    assert election.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = Decimal('0')
    party_result.number_of_mandates = 1
    assert election.has_party_results is True

    # party panachage
    panachage_result = PartyPanachageResult(
        election_id=election.id,
        source='A',
        target='B',
        votes=0,
    )
    election.party_panachage_results = [panachage_result]
    assert election.has_party_panachage_results is False
    panachage_result.votes = 10
    assert election.has_party_panachage_results is True


def test_proporz_election_results(session: Session) -> None:
    election = ProporzElection(
        title='Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )

    session.add(election)
    session.flush()

    assert sorted((l.votes for l in election.lists)) == []
    assert sorted((c.votes for c in election.candidates)) == []
    assert sorted((c.votes for c in election.list_connections)) == []

    # Add two entities
    election_result_1 = ElectionResult(
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
    election_result_2 = ElectionResult(
        name='name',
        entity_id=2,
        counted=True,
        eligible_voters=100,
        received_ballots=50,
        blank_ballots=1,
        invalid_ballots=0,
        blank_votes=8,
        invalid_votes=1
    )
    election.results.append(election_result_1)
    election.results.append(election_result_2)

    session.flush()

    assert sorted((l.votes for l in election.lists)) == []
    assert sorted((c.votes for c in election.candidates)) == []
    assert sorted((c.votes for c in election.list_connections)) == []

    # Add 4 lists
    list_1 = List(
        id=uuid4(),
        list_id='1',
        number_of_mandates=1,
        name='Quimby Again!',
    )
    list_2 = List(
        id=uuid4(),
        list_id='2',
        number_of_mandates=1,
        name='Kwik-E-Major',
    )
    list_3 = List(
        id=uuid4(),
        list_id='3',
        number_of_mandates=2,
        name='Partey A',
    )
    list_4 = List(
        id=uuid4(),
        list_id='4',
        number_of_mandates=0,
        name='Partey B',
    )
    election.lists.append(list_1)
    election.lists.append(list_2)
    election.lists.append(list_3)
    election.lists.append(list_4)

    # Add party results
    election.party_results.append(
        PartyResult(
            name_translations={'en_US': 'Republican Party'},
            number_of_mandates=1,
            votes=10,
            total_votes=100,
            party_id='1',
        )
    )
    election.party_results.append(
        PartyResult(
            name_translations={'en_US': 'Democratic Party'},
            number_of_mandates=1,
            votes=20,
            total_votes=100,
            party_id='2',
        )
    )

    # Add list panachage results
    list_1.panachage_results.append(
        ListPanachageResult(
            target_id=list_1.id,
            source_id=list_2.id,
            votes=1
        )
    )
    list_1.panachage_results.append(
        ListPanachageResult(
            target_id=list_1.id,
            source_id=list_3.id,
            votes=1
        )
    )
    list_1.panachage_results.append(
        ListPanachageResult(
            target_id=list_1.id,
            source_id=list_4.id,
            votes=1
        )
    )

    list_2.panachage_results.append(
        ListPanachageResult(
            target_id=list_2.id,
            source_id=list_1.id,
            votes=2
        )
    )
    list_2.panachage_results.append(
        ListPanachageResult(
            target_id=list_2.id,
            source_id=list_3.id,
            votes=2
        )
    )
    list_2.panachage_results.append(
        ListPanachageResult(
            target_id=list_2.id,
            source_id=list_4.id,
            votes=2
        )
    )

    list_3.panachage_results.append(
        ListPanachageResult(
            target_id=list_3.id,
            source_id=list_1.id,
            votes=3
        )
    )
    list_3.panachage_results.append(
        ListPanachageResult(
            target_id=list_3.id,
            source_id=list_2.id,
            votes=3
        )
    )
    list_3.panachage_results.append(
        ListPanachageResult(
            target_id=list_3.id,
            source_id=list_4.id,
            votes=3
        )
    )

    list_4.panachage_results.append(
        ListPanachageResult(
            target_id=list_4.id,
            source_id=list_1.id,
            votes=4
        )
    )
    list_4.panachage_results.append(
        ListPanachageResult(
            target_id=list_4.id,
            source_id=list_2.id,
            votes=4
        )
    )
    list_4.panachage_results.append(
        ListPanachageResult(
            target_id=list_4.id,
            source_id=list_3.id,
            votes=4
        )
    )

    # Add 5 candidates
    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        list_id=list_1.id,
        family_name='Quimby',
        first_name='Joe',
        party='Republican Party',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        list_id=list_2.id,
        family_name='Nahasapeemapetilon',
        first_name='Apu',
        party='Democratic Party',
    )
    candidate_3 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='3',
        list_id=list_3.id,
        family_name='Flanders',
        first_name='Ned',
        party='Republican Party',
    )
    candidate_4 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='4',
        list_id=list_3.id,
        family_name='Lovejoy',
        first_name='Tim',
        party='Republican Party',
    )
    candidate_5 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='5',
        list_id=list_4.id,
        family_name='Smithers',
        first_name='Waylon',
        party='Democratic Party',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)
    election.candidates.append(candidate_3)
    election.candidates.append(candidate_4)
    election.candidates.append(candidate_5)

    # Add 4 candidate results to the first entity
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=520,
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_2.id,
            votes=111
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_3.id,
            votes=20
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_4.id,
            votes=1
        )
    )

    # Add 2 candidate results to the second entity
    election_result_2.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=20
        )
    )
    election_result_2.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_5.id,
            votes=5
        )
    )

    # Add candidate panachage results to the first candidate / two lists
    candidate_1.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result_1.id,
            source_id=list_1.id,
            votes=3
        )
    )
    candidate_1.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result_1.id,
            source_id=list_2.id,
            votes=4
        )
    )
    candidate_1.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result_2.id,
            source_id=list_1.id,
            votes=5
        )
    )
    candidate_1.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result_2.id,
            source_id=list_2.id,
            votes=6
        )
    )

    # Add 3 list results to the first entity
    election_result_1.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=520
        )
    )
    election_result_1.list_results.append(
        ListResult(
            list_id=list_2.id,
            votes=111
        )
    )
    election_result_1.list_results.append(
        ListResult(
            list_id=list_3.id,
            votes=21
        )
    )

    # Add 2 list results to the second entity
    election_result_2.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=20
        )
    )
    election_result_2.list_results.append(
        ListResult(
            list_id=list_4.id,
            votes=5
        )
    )

    session.flush()

    expected = [5, 21, 111, 540]
    assert sorted((l.votes for l in election.lists)) == expected
    votes = session.query(List.votes, List.name)
    votes = votes.order_by(List.votes)
    assert [vote[0] for vote in votes] == expected

    expected = [1, 5, 20, 111, 540]
    assert sorted((c.votes for c in election.candidates)) == expected
    votes = session.query(Candidate.votes, Candidate.family_name)
    votes = votes.order_by(Candidate.votes)
    assert [vote[0] for vote in votes] == expected
    assert sorted(set((
        (c.party, c.list.name) for c in election.candidates
    ))) == [
        ('Democratic Party', 'Kwik-E-Major'),
        ('Democratic Party', 'Partey B'),
        ('Republican Party', 'Partey A'),
        ('Republican Party', 'Quimby Again!')
    ]

    assert sorted((c.votes for c in election.list_connections)) == []

    assert election.number_of_mandates == election.allocated_mandates
    assert election.elected_candidates == [('Joe', 'Quimby')]

    assert sum(
        [p.votes for l in election.lists for p in l.panachage_results]
    ) == 30

    assert sum(
        [p.votes for c in election.candidates for p in c.panachage_results]
    ) == 18

    # Add list connections
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
    subconnection = ListConnection(
        id=uuid4(),
        connection_id='B.1',
    )
    connection_2.children.append(subconnection)
    election.list_connections.append(connection_1)
    election.list_connections.append(connection_2)

    list_1.connection_id = connection_1.id
    list_2.connection_id = connection_2.id
    list_3.connection_id = subconnection.id
    list_4.connection_id = subconnection.id

    session.flush()

    assert connection_1.number_of_mandates == 1
    assert connection_2.number_of_mandates == 1
    assert subconnection.number_of_mandates == 2
    assert connection_1.total_number_of_mandates == 1
    assert connection_2.total_number_of_mandates == 3
    assert subconnection.total_number_of_mandates == 2

    assert sorted((c.votes for c in election.list_connections)) == [111, 540]
    assert sorted((c.total_votes for c in election.list_connections)) == [
        137, 540
    ]
    votes = session.query(ListConnection.votes, ListConnection.connection_id)
    votes = votes.order_by(ListConnection.votes)
    assert [int(vote[0]) for vote in votes] == [26, 111, 540]

    parties = session.query(
        PartyResult.party_id,
        PartyResult.name_translations['en_US'],
        PartyResult.votes,
        PartyResult.number_of_mandates
    )
    parties = parties.order_by(PartyResult.name_translations['en_US'])
    assert parties.all() == [
        ('2', 'Democratic Party', 20, 1),
        ('1', 'Republican Party', 10, 1)
    ]

    assert election.votes_by_district.all() == [  # type: ignore[comparison-overlap]
        ('election', None, [1, 2], True, 677)
    ]


@mark.parametrize('clear_all', [True, False])
def test_proporz_election_clear(clear_all: bool, session: Session) -> None:
    election = proporz_election()
    session.add(election)
    session.flush()

    assert election.last_result_change
    assert election.absolute_majority
    assert election.status
    assert election.list_connections
    assert election.lists
    assert election.candidates
    assert election.results
    assert election.party_results
    assert election.party_panachage_results

    assert session.query(Candidate).first()
    assert session.query(CandidateResult).first()
    assert session.query(CandidatePanachageResult).first()
    assert session.query(ElectionResult).first()
    assert session.query(List).first()
    assert session.query(ListConnection).first()
    assert session.query(ListPanachageResult).first()
    assert session.query(ListResult).first()
    assert session.query(PartyPanachageResult).first()
    assert session.query(PartyResult).first()

    election.clear_results(clear_all)

    # undo mypy narrowing
    election = election
    assert election.last_result_change is None
    assert election.absolute_majority is None
    assert election.status is None
    assert election.results == []
    assert election.party_results == []
    assert election.party_panachage_results == []

    assert session.query(CandidateResult).first() is None
    assert session.query(CandidatePanachageResult).first() is None
    assert session.query(ElectionResult).first() is None
    assert session.query(ListPanachageResult).first() is None
    assert session.query(ListResult).first() is None
    assert session.query(PartyPanachageResult).first() is None
    assert session.query(PartyResult).first() is None

    if clear_all:
        assert len(election.list_connections) == 0
        assert len(election.lists) == 0
        assert len(election.candidates) == 0

        assert session.query(Candidate).first() is None
        assert session.query(List).first() is None
        assert session.query(ListConnection).first() is None
    else:
        assert len(election.list_connections) > 0
        assert len(election.lists) > 0
        assert len(election.candidates) > 0

        assert session.query(Candidate).first()
        assert session.query(List).first()
        assert session.query(ListConnection).first()


def test_proporz_election_rename(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    session = election_day_app_zg.session()

    election = proporz_election()
    election.id = 'x'
    session.add(election)
    session.flush()

    election.explanations_pdf = (explanations_pdf, 'explanations.pdf')

    assert session.query(Candidate.election_id).distinct().scalar() == 'x'
    assert session.query(ElectionResult.election_id).distinct().scalar() == 'x'
    assert session.query(List.election_id).distinct().scalar() == 'x'
    assert session.query(ListConnection.election_id).distinct().scalar() == 'x'
    assert session.query(PartyResult.election_id).distinct().scalar() == 'x'
    assert session.query(
        PartyPanachageResult.election_id
    ).distinct().scalar() == 'x'

    election.id = 'y'
    session.flush()

    assert session.query(Candidate.election_id).distinct().scalar() == 'y'
    assert session.query(ElectionResult.election_id).distinct().scalar() == 'y'
    assert session.query(List.election_id).distinct().scalar() == 'y'
    assert session.query(ListConnection.election_id).distinct().scalar() == 'y'
    assert session.query(PartyResult.election_id).distinct().scalar() == 'y'
    assert session.query(
        PartyPanachageResult.election_id
    ).distinct().scalar() == 'y'


def test_proporz_election_attachments(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    model = ProporzElection(
        title='Election',
        domain='canton',
        date=date(2017, 1, 1),
    )

    assert model.explanations_pdf is None
    del model.explanations_pdf
    model.explanations_pdf = (explanations_pdf, 'explanations.pdf')
    # undo mypy narrowing
    model = model
    assert model.explanations_pdf is not None
    assert model.explanations_pdf.name == 'explanations_pdf'
    assert model.explanations_pdf.reference.filename == 'explanations.pdf'
    assert model.explanations_pdf.reference.content_type == 'application/pdf'
    del model.explanations_pdf
    assert model.explanations_pdf is None


def test_proporz_election_historical_party_strengths(session: Session) -> None:
    first = ProporzElection(
        title='First',
        domain='federation',
        date=date(2014, 1, 1),
        number_of_mandates=1,
        colors={'a': 'x'}
    )
    second = ProporzElection(
        title='Second',
        domain='federation',
        date=date(2018, 1, 1),
        number_of_mandates=1,
        colors={'a': 'y', 'b': 'y'}
    )
    third = ProporzElection(
        title='Third',
        domain='federation',
        date=date(2022, 1, 1),
        number_of_mandates=1,
        colors={'b': 'z', 'c': 'z'}
    )
    session.add(first)
    session.add(second)
    session.add(third)
    session.flush()

    assert first.historical_party_results == []
    assert second.historical_party_results == []
    assert third.historical_party_results == []
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y'}
    assert third.historical_colors == {'b': 'z', 'c': 'z'}

    # add results
    for (election, year, party_id, domain) in (
        (first, 2014, 1, 'canton'),
        (first, 2014, 2, 'canton'),
        (first, 2014, 3, 'canton'),
        (first, 2010, 1, 'canton'),
        (first, 2010, 2, 'canton'),
        (first, 2010, 3, 'canton'),
        (second, 2022, 2, 'canton'),
        (second, 2022, 3, 'canton'),
        (second, 2018, 2, 'canton'),
        (second, 2018, 3, 'canton'),
        (second, 2018, 4, 'canton'),
        (second, 2010, 2, 'canton'),
        (second, 2010, 3, 'canton'),
        (third, 2022, 1, 'canton'),
        (third, 2022, 3, 'canton'),
        (third, 2022, 5, 'canton'),
        (third, 2022, 5, 'superregion'),
    ):
        election.party_results.append(
            PartyResult(
                year=year,
                number_of_mandates=0,
                votes=1,
                total_votes=100,
                name_translations={'en_US': str(party_id)},
                party_id=str(party_id),
                domain=domain
            )
        )

    # no relationships yet
    assert len(first.historical_party_results) == 6
    assert len(second.historical_party_results) == 7
    assert len(third.historical_party_results) == 4
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y'}
    assert third.historical_colors == {'b': 'z', 'c': 'z'}

    # add relationships
    for (source_, target, type_) in (
        (third, second, 'historical'),
        (third, first, 'historical'),
        (second, first, 'historical'),
        (first, second, None),
        (second, third, 'historical')
    ):
        session.add(
            ElectionRelationship(
                source_id=source_.id, target_id=target.id, type=type_
            )
        )

    def extract(
        election: ProporzElection
    ) -> list[tuple[str | None, int, str]]:
        return sorted(
            (result.election_id, result.year, result.party_id)
            for result in election.historical_party_results
        )

    assert extract(first) == [
        ('first', 2010, '1'),
        ('first', 2010, '2'),
        ('first', 2010, '3'),
        ('first', 2014, '1'),
        ('first', 2014, '2'),
        ('first', 2014, '3'),
    ]
    assert extract(second) == [
        ('first', 2014, '1'),
        ('first', 2014, '2'),
        ('first', 2014, '3'),
        ('second', 2010, '2'),
        ('second', 2010, '3'),
        ('second', 2018, '2'),
        ('second', 2018, '3'),
        ('second', 2018, '4'),
        ('second', 2022, '2'),
        ('second', 2022, '3'),
    ]
    assert extract(third) == [
        ('second', 2018, '2'),
        ('second', 2018, '3'),
        ('second', 2018, '4'),
        ('third', 2022, '1'),
        ('third', 2022, '3'),
        ('third', 2022, '5'),
        ('third', 2022, '5'),
    ]
    assert len([
        result for result in third.historical_party_results
        if result.domain == 'superregion'
    ]) == 1
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y', 'c': 'z'}
    assert third.historical_colors == {'b': 'z', 'c': 'z', 'a': 'y'}
