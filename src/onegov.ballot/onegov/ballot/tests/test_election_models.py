from datetime import date
from freezegun import freeze_time
from onegov.ballot import (
    Candidate,
    CandidateResult,
    Election,
    ElectionResult,
    List,
    ListConnection,
    ListResult,
)
from uuid import uuid4


def test_election_create_all_models(session):
    election = Election(
        title="Election",
        domain='federation',
        type='majorz',
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

    election_result = ElectionResult(
        election_id=election.id,
        group='group',
        municipality_id=1000,
        elegible_voters=0,
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
    assert election.results.one() == election_result

    assert connection.election == election
    assert connection.lists.all() == []
    assert connection.parent == None
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

    assert election_result.list_results.one() == list_result
    assert election_result.candidate_results.one() == candidate_result
    assert election_result.election == election

    assert list_result.election_result == election_result
    assert list_result.list == list

    assert candidate_result.election_result == election_result
    assert candidate_result.candidate == candidate

    session.delete(election)
    session.flush()

    assert session.query(Candidate).all() == []
    assert session.query(CandidateResult).all() == []
    assert session.query(Election).all() == []
    assert session.query(ElectionResult).all() == []
    assert session.query(List).all() == []
    assert session.query(ListConnection).all() == []
    assert session.query(ListResult).all() == []


def test_election_id_generation(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-election'

    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-election-1'


def test_election_summarized_properties(session):
    election = Election(
        title="Election",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=2
    )
    for x in range(1, 4):
        election.results.append(
            ElectionResult(
                group='group',
                municipality_id=x,
                elegible_voters=100 * x,
                received_ballots=80 * x,
                blank_ballots=4 * x,
                invalid_ballots=3 * x,
                blank_votes=2 * x,
                invalid_votes=x
            )
        )

    session.add(election)
    session.flush()

    assert election.elegible_voters == 600
    assert election.received_ballots == 480
    assert election.accounted_ballots == 438
    assert election.blank_ballots == 24
    assert election.invalid_ballots == 18
    assert election.accounted_votes == 858


def test_derived_properties(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )
    election.results.append(ElectionResult(
        group='group',
        municipality_id=1,
        elegible_voters=100,
        received_ballots=50,
        blank_ballots=2,
        invalid_ballots=5,
        blank_votes=4,
        invalid_votes=3
    ))
    election.results.append(ElectionResult(
        group='group',
        municipality_id=2,
        elegible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))

    session.add(election)
    session.flush()

    assert election.results[0].unaccounted_ballots == 7
    assert election.results[0].accounted_ballots == 43
    assert election.results[0].turnout == 50.0
    assert election.results[1].unaccounted_ballots == 21
    assert election.results[1].accounted_ballots == 129
    assert election.results[1].turnout == 75.0
    assert election.unaccounted_ballots == 28
    assert election.accounted_ballots == 172
    assert int(election.turnout) == 66
    assert session.query(
        Election.elegible_voters,
        Election.received_ballots,
        Election.accounted_ballots,
        Election.blank_ballots,
        Election.invalid_ballots
    ).one() == (300, 200, 172, 8, 20)


def test_election_counted(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.counted == False

    election.total_municipalities = 2
    assert election.counted == False

    election.counted_municipalities = 1
    assert election.counted == False

    election.counted_municipalities = 2
    assert election.counted == True

    election.total_municipalities = 0
    assert election.counted == False

    election.total_municipalities = None
    assert election.counted == False


def test_election_last_result_change(session):
    with freeze_time("2014-01-01 12:00"):
        election = Election(
            title='Legislative Election',
            domain='federation',
            type='majorz',
            date=date(2015, 6, 14),
        )

        session.add(election)
        session.flush()

    with freeze_time("2015-01-01 12:00"):
        election.results.append(ElectionResult(
            group='group',
            municipality_id=1,
            elegible_voters=100,
            received_ballots=50,
            blank_ballots=2,
            invalid_ballots=5,
            blank_votes=4,
            invalid_votes=3
        ))

        session.flush()

    assert election.last_result_change.isoformat() == \
        '2015-01-01T12:00:00+00:00'

    with freeze_time("2015-01-01 13:00"):
        election.results.append(ElectionResult(
            group='group',
            municipality_id=2,
            elegible_voters=200,
            received_ballots=150,
            blank_ballots=6,
            invalid_ballots=15,
            blank_votes=12,
            invalid_votes=9
        ))

        session.flush()

    assert election.last_result_change.isoformat() == \
        '2015-01-01T13:00:00+00:00'


def test_election_results(session):
    election = Election(
        title='Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )

    session.add(election)
    session.flush()

    assert sorted((l.votes for l in election.lists)) == []
    assert sorted((c.votes for c in election.candidates)) == []
    assert sorted((c.votes for c in election.list_connections)) == []

    # Add two municipalities
    election_result_1 = ElectionResult(
        group='group',
        municipality_id=1,
        elegible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election_result_2 = ElectionResult(
        group='group',
        municipality_id=2,
        elegible_voters=100,
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

    # Add 5 candidates
    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        list_id=list_1.id,
        family_name='Quimby',
        first_name='Joe',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        list_id=list_2.id,
        family_name='Nahasapeemapetilon',
        first_name='Apu',
    )
    candidate_3 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='3',
        list_id=list_3.id,
        family_name='Flanders',
        first_name='Ned',
    )
    candidate_4 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='4',
        list_id=list_3.id,
        family_name='Lovejoy',
        first_name='Tim',
    )
    candidate_5 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='5',
        list_id=list_4.id,
        family_name='Smithers',
        first_name='Waylon',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)
    election.candidates.append(candidate_3)
    election.candidates.append(candidate_4)
    election.candidates.append(candidate_5)

    # Add 4 candidate results to the first municipality
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

    # Add 2 candidate results to the second municipality
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

    # Add 3 list results to the first municipality
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

    # Add 2 list results to the second municipality
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

    assert sorted((c.votes for c in election.list_connections)) == []

    assert election.number_of_mandates == election.allocated_mandates

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


def test_election_export(session):
    election = Election(
        title='Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144,
        counted_municipalities=1,
        total_municipalities=2
    )

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
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        list_id=list_2.id,
        family_name='Nahasapeemapetilon',
        first_name='Apu',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    session.add(election)
    session.flush()

    assert election.export() == []

    election_result = ElectionResult(
        group='group',
        municipality_id=1,
        elegible_voters=1000,
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

    session.flush()

    assert election.export() == [
        {
            'election_title': 'Election',
            'election_date': '2015-06-14',
            'election_type': 'majorz',
            'election_mandates': 1,
            'election_absolute_majority': 144,
            'election_counted_municipalities': 1,
            'election_total_municipalities': 2,
            'municipality_name': 'group',
            'municipality_bfs_number': 1,
            'municipality_elegible_voters': 1000,
            'municipality_received_ballots': 500,
            'municipality_blank_ballots': 10,
            'municipality_invalid_ballots': 5,
            'municipality_unaccounted_ballots': 15,
            'municipality_accounted_ballots': 485,
            'municipality_blank_votes': 80,
            'municipality_invalid_votes': 120,
            'municipality_accounted_votes': 285,
            'list_name': 'Kwik-E-Major',
            'list_id': '2',
            'list_number_of_mandates': 0,
            'list_votes': 111,
            'list_connection': 'A.1',
            'list_connection_parent': 'A',
            'candidate_family_name': 'Nahasapeemapetilon',
            'candidate_first_name': 'Apu',
            'candidate_id': '2',
            'candidate_elected': False,
            'candidate_votes': 111
        },
        {
            'election_title': 'Election',
            'election_date': '2015-06-14',
            'election_type': 'majorz',
            'election_mandates': 1,
            'election_absolute_majority': 144,
            'election_counted_municipalities': 1,
            'election_total_municipalities': 2,
            'municipality_name': 'group',
            'municipality_bfs_number': 1,
            'municipality_elegible_voters': 1000,
            'municipality_received_ballots': 500,
            'municipality_blank_ballots': 10,
            'municipality_invalid_ballots': 5,
            'municipality_unaccounted_ballots': 15,
            'municipality_accounted_ballots': 485,
            'municipality_blank_votes': 80,
            'municipality_invalid_votes': 120,
            'municipality_accounted_votes': 285,
            'list_name': 'Quimby Again!',
            'list_id': '1',
            'list_number_of_mandates': 1,
            'list_votes': 520,
            'list_connection': None,
            'list_connection_parent': None,
            'candidate_family_name': 'Quimby',
            'candidate_first_name': 'Joe',
            'candidate_id': '1',
            'candidate_elected': True,
            'candidate_votes': 520
        }
    ]


def test_election_meta_data(session):
    election = Election(
        title='Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    assert not election.meta

    session.add(election)
    session.flush()

    assert not election.meta

    election.meta['a'] = 1
    assert election.meta['a'] == 1

    session.flush()
    election.meta['b'] = 2
    assert election.meta['a'] == 1
    assert election.meta['b'] == 2
