from datetime import date
from decimal import Decimal
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionRelationship
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import ListPanachageResult
from onegov.ballot import PartyPanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import ProporzElection
from uuid import uuid4


def proporz_election():
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

    election.panachage_results.append(
        PartyPanachageResult(target=lid, source=1, votes=0)
    )

    election.last_result_change = election.timestamp()

    return election


def test_proporz_election_create_all_models(session):
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

    list = List(
        number_of_mandates=0,
        list_id="0",
        name="List A",
        election_id=election.id,
        connection_id=subconnection.id
    )

    session.add(list)
    session.flush()

    candidate = Candidate(
        candidate_id="0",
        family_name="Quimby",
        first_name="Joe",
        elected=False,
        election_id=election.id,
        list_id=list.id,
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
        list_id=list.id,
        votes=0
    )

    session.add(list_result)
    session.flush()

    panachage_result = ListPanachageResult(
        target=list.id,
        source=1,
        votes=0
    )

    session.add(panachage_result)
    session.flush()

    candidate_result = CandidateResult(
        election_result_id=election_result.id,
        candidate_id=candidate.id,
        votes=0
    )

    session.add(candidate_result)
    session.flush()

    assert election.list_connections.one() == connection
    assert election.lists.one() == list
    assert election.candidates.one() == candidate
    assert election.party_results.one() == party_result
    assert election.results.one() == election_result

    assert connection.election == election
    assert connection.lists.all() == []
    assert connection.parent is None
    assert connection.children.one() == subconnection

    assert subconnection.election is None
    assert subconnection.lists.one() == list
    assert subconnection.parent == connection
    assert subconnection.children.all() == []

    assert list.candidates.one() == candidate
    assert list.results.one() == list_result
    assert list.election == election

    assert candidate.results.one() == candidate_result
    assert candidate.election == election
    assert candidate.list == list

    assert party_result.election_id == election.id

    assert election_result.list_results.one() == list_result
    assert election_result.candidate_results.one() == candidate_result
    assert election_result.election == election

    assert list_result.election_result == election_result
    assert list_result.list == list

    assert list.panachage_results.one() == panachage_result

    assert candidate_result.election_result == election_result
    assert candidate_result.candidate == candidate

    session.delete(election)
    session.flush()

    assert session.query(Candidate).all() == []
    assert session.query(CandidateResult).all() == []
    assert session.query(ProporzElection).all() == []
    assert session.query(ElectionResult).all() == []
    assert session.query(List).all() == []
    assert session.query(ListConnection).all() == []
    assert session.query(ListResult).all() == []
    assert session.query(ListPanachageResult).all() == []


def test_proporz_election_has_data(session):
    # todo:

    election = ProporzElection(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )
    election.lists.append(
        List(
            number_of_mandates=0,
            list_id="1",
            name="List A",
        )
    )
    election.lists.append(
        List(
            number_of_mandates=0,
            list_id="2",
            name="List B",
        )
    )
    session.add(election)
    session.flush()
    assert election.has_lists_panachage_data is False
    assert election.has_party_results is False
    assert election.has_party_panachage_results is False

    # lists panachage
    election.lists[0].panachage_results.append(
        ListPanachageResult(
            target=election.lists[0].id,
            source=2,
            votes=0
        )
    )
    election.lists[1].panachage_results.append(
        ListPanachageResult(
            target=election.lists[1].id,
            source=1,
            votes=0
        )
    )

    session.flush()
    assert election.has_lists_panachage_data

    # party results
    party_result = PartyResult(
        election_id=election.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name_translations={'en_US': 'Libertarian'},
        party_id='1'
    )
    session.add(party_result)
    session.flush()
    assert election.party_results.one() == party_result
    assert election.has_party_results is False
    party_result.votes = 10
    assert election.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = 10
    assert election.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = 0
    party_result.number_of_mandates = 1
    assert election.has_party_results is True

    # party panachage
    panachage_result = PartyPanachageResult(
        election_id=election.id,
        source='A',
        target='B',
        votes=0,
    )
    session.add(panachage_result)
    session.flush()
    assert election.panachage_results.one() == panachage_result
    assert election.has_party_panachage_results is True


def test_proporz_election_results(session):
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

    # Add panachage results
    list_1.panachage_results.append(
        ListPanachageResult(target=list_1.id, source=2, votes=1)
    )
    list_1.panachage_results.append(
        ListPanachageResult(target=list_1.id, source=3, votes=1)
    )
    list_1.panachage_results.append(
        ListPanachageResult(target=list_1.id, source=4, votes=1)
    )

    list_2.panachage_results.append(
        ListPanachageResult(target=list_2.id, source=1, votes=2)
    )
    list_2.panachage_results.append(
        ListPanachageResult(target=list_2.id, source=3, votes=2)
    )
    list_2.panachage_results.append(
        ListPanachageResult(target=list_2.id, source=4, votes=2)
    )

    list_3.panachage_results.append(
        ListPanachageResult(target=list_3.id, source=1, votes=3)
    )
    list_3.panachage_results.append(
        ListPanachageResult(target=list_3.id, source=2, votes=3)
    )
    list_3.panachage_results.append(
        ListPanachageResult(target=list_3.id, source=4, votes=3)
    )

    list_4.panachage_results.append(
        ListPanachageResult(target=list_4.id, source=1, votes=4)
    )
    list_4.panachage_results.append(
        ListPanachageResult(target=list_4.id, source=2, votes=4)
    )
    list_4.panachage_results.append(
        ListPanachageResult(target=list_4.id, source=3, votes=4)
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


def test_proporz_election_export(session):
    election = ProporzElection(
        title='Wahl',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144
    )
    election.title_translations['it_CH'] = 'Elezione'
    election.colors = {
        'Kwik-E-Major': '#112233',
        'Democratic Party': '#223344'
    }

    connection = ListConnection(
        connection_id='A'
    )
    subconnection = ListConnection(
        id=uuid4(),
        connection_id='A.1'
    )
    connection.children.append(subconnection)
    election.list_connections.append(connection)

    list_1 = List(
        id=uuid4(),
        list_id='1',
        number_of_mandates=1,
        name='Quimby Again!',
    )
    list_2 = List(
        id=uuid4(),
        list_id='2',
        number_of_mandates=0,
        name='Kwik-E-Major',
        connection_id=subconnection.id
    )
    election.lists.append(list_1)
    election.lists.append(list_2)

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        list_id=list_1.id,
        family_name='Quimby',
        first_name='Joe',
        party='Republican Party',
        gender='male',
        year_of_birth=1970
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
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    session.add(election)
    session.flush()

    assert election.export(['de_CH']) == []

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

    election_result.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=520,
        )
    )
    election_result.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_2.id,
            votes=111
        )
    )

    election_result.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=520
        )
    )
    election_result.list_results.append(
        ListResult(
            list_id=list_2.id,
            votes=111
        )
    )
    election.results.append(election_result)

    list_1.panachage_results.append(
        ListPanachageResult(source=list_2.list_id, votes=12)
    )
    list_1.panachage_results.append(
        ListPanachageResult(source='99', votes=4)
    )

    session.flush()

    assert election.export(['de_CH', 'fr_CH', 'it_CH']) == [
        {
            'election_title_de_CH': 'Wahl',
            'election_title_fr_CH': '',
            'election_title_it_CH': 'Elezione',
            'election_date': '2015-06-14',
            'election_domain': 'federation',
            'election_type': 'proporz',
            'election_mandates': 1,
            'election_absolute_majority': 144,
            'election_status': 'unknown',
            'entity_superregion': '',
            'entity_superregion': '',
            'entity_district': '',
            'entity_name': 'name',
            'entity_id': 1,
            'entity_counted': True,
            'entity_eligible_voters': 1000,
            'entity_expats': 35,
            'entity_received_ballots': 500,
            'entity_blank_ballots': 10,
            'entity_invalid_ballots': 5,
            'entity_unaccounted_ballots': 15,
            'entity_accounted_ballots': 485,
            'entity_blank_votes': 80,
            'entity_invalid_votes': 120,
            'entity_accounted_votes': 285,
            'list_name': 'Kwik-E-Major',
            'list_id': '2',
            'list_color': '#112233',
            'list_number_of_mandates': 0,
            'list_votes': 111,
            'list_connection': 'A.1',
            'list_connection_parent': 'A',
            'candidate_family_name': 'Nahasapeemapetilon',
            'candidate_first_name': 'Apu',
            'candidate_id': '2',
            'candidate_elected': False,
            'candidate_party': 'Democratic Party',
            'candidate_party_color': '#223344',
            'candidate_gender': '',
            'candidate_year_of_birth': '',
            'candidate_votes': 111,
            'list_panachage_votes_from_list_1': None,
            'list_panachage_votes_from_list_2': None,
            'list_panachage_votes_from_list_99': None,
        }, {
            'election_title_de_CH': 'Wahl',
            'election_title_fr_CH': '',
            'election_title_it_CH': 'Elezione',
            'election_date': '2015-06-14',
            'election_domain': 'federation',
            'election_type': 'proporz',
            'election_mandates': 1,
            'election_absolute_majority': 144,
            'election_status': 'unknown',
            'entity_superregion': '',
            'entity_district': '',
            'entity_name': 'name',
            'entity_id': 1,
            'entity_counted': True,
            'entity_eligible_voters': 1000,
            'entity_expats': 35,
            'entity_received_ballots': 500,
            'entity_blank_ballots': 10,
            'entity_invalid_ballots': 5,
            'entity_unaccounted_ballots': 15,
            'entity_accounted_ballots': 485,
            'entity_blank_votes': 80,
            'entity_invalid_votes': 120,
            'entity_accounted_votes': 285,
            'list_name': 'Quimby Again!',
            'list_id': '1',
            'list_color': '',
            'list_number_of_mandates': 1,
            'list_votes': 520,
            'list_connection': None,
            'list_connection_parent': None,
            'candidate_family_name': 'Quimby',
            'candidate_first_name': 'Joe',
            'candidate_id': '1',
            'candidate_elected': True,
            'candidate_party': 'Republican Party',
            'candidate_party_color': '',
            'candidate_gender': 'male',
            'candidate_year_of_birth': 1970,
            'candidate_votes': 520,
            'list_panachage_votes_from_list_1': None,
            'list_panachage_votes_from_list_2': 12,
            'list_panachage_votes_from_list_99': 4,
        }
    ]


def test_proporz_election_export_parties(session):
    session.add(
        ProporzElection(
            title='Wahl',
            domain='federation',
            date=date(2016, 6, 14),
            number_of_mandates=1,
            absolute_majority=144
        )
    )
    session.flush()
    election = session.query(ProporzElection).one()
    election.colors = {
        'Conservative': 'red',
        'Libertarian': 'black'
    }

    assert election.export_parties(['en_US'], 'en_US') == []

    # Add party results
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=0,
            votes=0,
            voters_count=Decimal('1.01'),
            voters_count_percentage=Decimal('100.02'),
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='2',
            year=2012
        )
    )
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=2,
            votes=2,
            voters_count=Decimal('3.01'),
            voters_count_percentage=Decimal('50.02'),
            total_votes=50,
            name_translations={'en_US': 'Libertarian'},
            party_id='2',
            year=2016
        )
    )
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('2.01'),
            voters_count_percentage=Decimal('100.02'),
            total_votes=100,
            name_translations={'en_US': 'Conservative'},
            party_id='1',
            year=2012
        )
    )
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=3,
            votes=3,
            voters_count=Decimal('4.01'),
            voters_count_percentage=Decimal('50.02'),
            total_votes=50,
            name_translations={'en_US': 'Conservative'},
            party_id='1',
            year=2016
        )
    )
    election.party_results.append(
        PartyResult(
            domain='quarter',
            domain_segment='Quarter 1',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('4.01'),
            voters_count_percentage=Decimal('50.02'),
            total_votes=50,
            name_translations={'en_US': 'Conservative'},
            party_id='1',
            year=2016
        )
    )
    assert election.export_parties(['en_US', 'de_CH'], 'en_US') == [
        {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'red',
            'mandates': 3,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
        }, {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'black',
            'mandates': 2,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '2',
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
        }, {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'red',
            'mandates': 1,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
            'year': 2012,
        }, {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'black',
            'mandates': 0,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '2',
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
            'year': 2012,
        }, {
            'domain': 'quarter',
            'domain_segment': 'Quarter 1',
            'color': 'red',
            'mandates': 1,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 50,
            'votes': 1,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
        }
    ]

    for idx, source in enumerate(('1', '2', '3', '')):
        election.panachage_results.append(
            PartyPanachageResult(
                target='1',
                source=source,
                votes=idx + 1
            )
        )
    election.panachage_results.append(
        PartyPanachageResult(
            target='2',
            source='1',
            votes=5,
        )
    )
    assert election.export_parties(['de_CH', 'en_US'], 'de_CH') == [
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '1',
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_1': 1,
            'panachage_votes_from_2': 2,
            'panachage_votes_from_999': 4,
        },
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '2',
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_1': 5,
            'panachage_votes_from_2': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '1',
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_1': None,
            'panachage_votes_from_2': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '2',
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_1': None,
            'panachage_votes_from_2': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'quarter',
            'domain_segment': 'Quarter 1',
            'color': 'red',
            'mandates': 1,
            'name': None,
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 50,
            'votes': 1,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
            'panachage_votes_from_1': None,
            'panachage_votes_from_999': None,
        }
    ]


def test_proporz_election_clear_results(session):
    election = proporz_election()
    session.add(election)
    session.flush()

    election.clear_results()

    assert election.last_result_change is None
    assert election.absolute_majority is None
    assert election.status is None
    assert election.list_connections.all() == []
    assert election.lists.all() == []
    assert election.candidates.all() == []
    assert election.results.all() == []
    assert election.party_results.all() == []
    assert election.panachage_results.all() == []

    assert session.query(Candidate).first() is None
    assert session.query(CandidateResult).first() is None
    assert session.query(ElectionResult).first() is None
    assert session.query(List).first() is None
    assert session.query(ListConnection).first() is None
    assert session.query(ListPanachageResult).first() is None
    assert session.query(ListResult).first() is None
    assert session.query(PartyPanachageResult).first() is None
    assert session.query(PartyResult).first() is None


def test_proporz_election_rename(session):
    election = proporz_election()
    election.id = 'x'
    session.add(election)
    session.flush()

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


def test_proporz_election_attachments(test_app, explanations_pdf):
    model = ProporzElection(
        title='Election',
        domain='canton',
        date=date(2017, 1, 1),
    )

    assert model.explanations_pdf is None
    del model.explanations_pdf
    model.explanations_pdf = (explanations_pdf, 'explanations.pdf')
    assert model.explanations_pdf.name == 'explanations_pdf'
    assert model.explanations_pdf.reference.filename == 'explanations.pdf'
    assert model.explanations_pdf.reference.content_type == 'application/pdf'
    del model.explanations_pdf
    assert model.explanations_pdf is None


def test_proporz_election_historical_party_strengths(session):
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

    assert first.historical_party_results.count() == 0
    assert second.historical_party_results.count() == 0
    assert third.historical_party_results.count() == 0
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
    assert first.historical_party_results.count() == 6
    assert second.historical_party_results.count() == 7
    assert third.historical_party_results.count() == 4
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

    def extract(election):
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
    assert third.historical_party_results.filter_by(
        domain='superregion'
    ).count() == 1
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y', 'c': 'z'}
    assert third.historical_colors == {'b': 'z', 'c': 'z', 'a': 'y'}
