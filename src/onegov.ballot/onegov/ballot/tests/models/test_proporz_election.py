from datetime import date
from freezegun import freeze_time
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import PanachageResult
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
            name='A',
        )
    )

    election.panachage_results.append(
        PanachageResult(target=lid, source=1, votes=0)
    )

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
        owner=election.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name='Libertarian',
        color='black'
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

    panachage_result = PanachageResult(
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

    assert party_result.owner == election.id

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
    assert session.query(PanachageResult).all() == []


def test_proporz_election_last_change(session):
    # Add the election
    with freeze_time("2001-01-01"):
        election = ProporzElection(
            title='Legislative Election',
            domain='federation',
            date=date(2015, 6, 14),
        )
        session.add(election)
        session.flush()

    assert election.last_modified.isoformat().startswith('2001')
    assert election.last_result_change is None

    # Add a result
    with freeze_time("2002-01-01"):
        election.results.append(ElectionResult(
            name='name',
            entity_id=1,
            counted=True,
            eligible_voters=100,
            received_ballots=50,
            blank_ballots=2,
            invalid_ballots=5,
            blank_votes=4,
            invalid_votes=3
        ))
        session.flush()

    assert election.last_modified.isoformat().startswith('2002')
    assert election.last_result_change.isoformat().startswith('2002')

    # Add another result
    with freeze_time("2003-01-01"):
        election.results.append(ElectionResult(
            name='name',
            entity_id=2,
            counted=True,
            eligible_voters=200,
            received_ballots=150,
            blank_ballots=6,
            invalid_ballots=15,
            blank_votes=12,
            invalid_votes=9
        ))
        session.flush()

    # Add a candidate
    with freeze_time("2004-01-01"):
        candidate = Candidate(
            elected=True,
            candidate_id='1',
            family_name='Quimby',
            first_name='Joe'
        )
        election.candidates.append(candidate)
        session.flush()

    assert election.last_modified.isoformat().startswith('2004')
    assert election.last_result_change.isoformat().startswith('2003')

    # Add candidate results
    with freeze_time("2005-01-01"):
        election.results.first().candidate_results.append(
            CandidateResult(candidate_id=candidate.id, votes=520)
        )
        session.flush()

    assert election.last_modified.isoformat().startswith('2005')
    assert election.last_result_change.isoformat().startswith('2005')

    # Add a list
    with freeze_time("2006-01-01"):
        list_ = List(
            list_id='1', number_of_mandates=1, name='Quimby Again!',
        )
        election.lists.append(list_)
        session.flush()

    assert election.last_modified.isoformat().startswith('2006')
    assert election.last_result_change.isoformat().startswith('2005')

    # Add a list result
    with freeze_time("2007-01-01"):
        election.results.first().list_results.append(
            ListResult(list_id=list_.id, votes=520)
        )
        session.flush()

    assert election.last_modified.isoformat().startswith('2007')
    assert election.last_result_change.isoformat().startswith('2007')

    # Add a list connection
    with freeze_time("2008-01-01"):
        election.list_connections.append(ListConnection(connection_id='A'))
        session.flush()

    assert election.last_modified.isoformat().startswith('2008')
    assert election.last_result_change.isoformat().startswith('2007')

    # Add a panachage result
    with freeze_time("2009-01-01"):
        election.lists.first().panachage_results.append(
            PanachageResult(source=2, votes=1)
        )
        session.flush()

    assert election.last_modified.isoformat().startswith('2009')
    assert election.last_result_change.isoformat().startswith('2009')

    # Add a party result
    with freeze_time("2010-01-01"):
        election.party_results.append(
            PartyResult(
                name='Republican Party', votes=10, total_votes=100
            )
        )
        session.flush()

    assert election.last_modified.isoformat().startswith('2010')
    assert election.last_result_change.isoformat().startswith('2010')

    # Change a result
    with freeze_time("2011-01-01"):
        election.results.first().blank_ballots = 7
        session.flush()

    assert election.last_modified.isoformat().startswith('2011')
    assert election.last_result_change.isoformat().startswith('2011')

    # Change the candidate result
    with freeze_time("2012-01-01"):
        election.candidates.first().results.first().votes = 510
        session.flush()

    assert election.last_modified.isoformat().startswith('2012')
    assert election.last_result_change.isoformat().startswith('2012')

    # Change the list result
    with freeze_time("2013-01-01"):
        election.lists.first().results.first().votes = 530
        session.flush()

    assert election.last_modified.isoformat().startswith('2013')
    assert election.last_result_change.isoformat().startswith('2013')

    # Change the panachage result
    with freeze_time("2014-01-01"):
        election.lists.first().panachage_results.first().votes = 2
        session.flush()

    assert election.last_modified.isoformat().startswith('2014')
    assert election.last_result_change.isoformat().startswith('2014')

    # Change the party result
    with freeze_time("2015-01-01"):
        election.party_results.first().votes = 20
        session.flush()

    assert election.last_modified.isoformat().startswith('2015')
    assert election.last_result_change.isoformat().startswith('2015')

    # Change the candidate
    with freeze_time("2016-01-01"):
        election.candidates.first().elected = False
        session.flush()

    assert election.last_modified.isoformat().startswith('2016')
    assert election.last_result_change.isoformat().startswith('2015')

    # Change the list
    with freeze_time("2017-01-01"):
        election.lists.first().name = 'Quimby Forever!'
        session.flush()

    assert election.last_modified.isoformat().startswith('2017')
    assert election.last_result_change.isoformat().startswith('2015')

    # Change the list connection
    with freeze_time("2018-01-01"):
        election.list_connections.first().connection_id = 'B'
        session.flush()

    assert election.last_modified.isoformat().startswith('2018')
    assert election.last_result_change.isoformat().startswith('2015')

    # Change the election
    with freeze_time("2019-01-01"):
        election.domain = 'canton'
        session.flush()

    assert election.last_modified.isoformat().startswith('2019')
    assert election.last_result_change.isoformat().startswith('2015')

    # Add a panachage result
    with freeze_time("2020-01-01"):
        election.panachage_results.append(
            PanachageResult(
                source='',
                target='Republican Party',
                votes=10
            )
        )
        session.flush()

    assert election.last_modified.isoformat().startswith('2020')
    assert election.last_result_change.isoformat().startswith('2020')


def test_proporz_election_has_lists_panachage_data(session):
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

    assert not election.has_lists_panachage_data

    election.lists[0].panachage_results.append(
        PanachageResult(
            target=election.lists[0].id,
            source=2,
            votes=0
        )
    )
    election.lists[1].panachage_results.append(
        PanachageResult(
            target=election.lists[1].id,
            source=1,
            votes=0
        )
    )

    session.flush()

    assert election.has_lists_panachage_data


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
            name='Republican Party', number_of_mandates=1, votes=10,
            total_votes=100, color='red'
        )
    )
    election.party_results.append(
        PartyResult(
            name='Democratic Party', number_of_mandates=1, votes=20,
            total_votes=100, color='blue'
        )
    )

    # Add panachage results
    list_1.panachage_results.append(
        PanachageResult(target=list_1.id, source=2, votes=1)
    )
    list_1.panachage_results.append(
        PanachageResult(target=list_1.id, source=3, votes=1)
    )
    list_1.panachage_results.append(
        PanachageResult(target=list_1.id, source=4, votes=1)
    )

    list_2.panachage_results.append(
        PanachageResult(target=list_2.id, source=1, votes=2)
    )
    list_2.panachage_results.append(
        PanachageResult(target=list_2.id, source=3, votes=2)
    )
    list_2.panachage_results.append(
        PanachageResult(target=list_2.id, source=4, votes=2)
    )

    list_3.panachage_results.append(
        PanachageResult(target=list_3.id, source=1, votes=3)
    )
    list_3.panachage_results.append(
        PanachageResult(target=list_3.id, source=2, votes=3)
    )
    list_3.panachage_results.append(
        PanachageResult(target=list_3.id, source=4, votes=3)
    )

    list_4.panachage_results.append(
        PanachageResult(target=list_4.id, source=1, votes=4)
    )
    list_4.panachage_results.append(
        PanachageResult(target=list_4.id, source=2, votes=4)
    )
    list_4.panachage_results.append(
        PanachageResult(target=list_4.id, source=3, votes=4)
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
        PartyResult.name,
        PartyResult.votes,
        PartyResult.number_of_mandates
    )
    parties = parties.order_by(PartyResult.name)
    assert parties.all() == [
        ('Democratic Party', 20, 1),
        ('Republican Party', 10, 1)
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

    assert election.export() == []

    election_result = ElectionResult(
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
        PanachageResult(source=list_2.list_id, votes=12)
    )
    list_1.panachage_results.append(
        PanachageResult(source='99', votes=4)
    )

    session.flush()

    assert election.export() == [
        {
            'election_title_de_CH': 'Wahl',
            'election_title_it_CH': 'Elezione',
            'election_date': '2015-06-14',
            'election_domain': 'federation',
            'election_type': 'proporz',
            'election_mandates': 1,
            'election_absolute_majority': 144,
            'election_status': 'unknown',
            'entity_district': '',
            'entity_name': 'name',
            'entity_id': 1,
            'entity_counted': True,
            'entity_eligible_voters': 1000,
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
            'list_number_of_mandates': 0,
            'list_votes': 111,
            'list_connection': 'A.1',
            'list_connection_parent': 'A',
            'candidate_family_name': 'Nahasapeemapetilon',
            'candidate_first_name': 'Apu',
            'candidate_id': '2',
            'candidate_elected': False,
            'candidate_party': 'Democratic Party',
            'candidate_votes': 111,
            'panachage_votes_from_list_1': None,
            'panachage_votes_from_list_2': None,
            'panachage_votes_from_list_99': None,
        }, {
            'election_title_de_CH': 'Wahl',
            'election_title_it_CH': 'Elezione',
            'election_date': '2015-06-14',
            'election_domain': 'federation',
            'election_type': 'proporz',
            'election_mandates': 1,
            'election_absolute_majority': 144,
            'election_status': 'unknown',
            'entity_district': '',
            'entity_name': 'name',
            'entity_id': 1,
            'entity_counted': True,
            'entity_eligible_voters': 1000,
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
            'list_number_of_mandates': 1,
            'list_votes': 520,
            'list_connection': None,
            'list_connection_parent': None,
            'candidate_family_name': 'Quimby',
            'candidate_first_name': 'Joe',
            'candidate_id': '1',
            'candidate_elected': True,
            'candidate_party': 'Republican Party',
            'candidate_votes': 520,
            'panachage_votes_from_list_1': None,
            'panachage_votes_from_list_2': 12,
            'panachage_votes_from_list_99': 4,
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

    assert election.export_parties() == []

    # Add party results
    election.party_results.append(
        PartyResult(
            number_of_mandates=0,
            votes=0,
            total_votes=100,
            name='Libertarian',
            color='black',
            year=2012
        )
    )
    election.party_results.append(
        PartyResult(
            number_of_mandates=2,
            votes=2,
            total_votes=50,
            name='Libertarian',
            color='black',
            year=2016
        )
    )
    election.party_results.append(
        PartyResult(
            number_of_mandates=1,
            votes=1,
            total_votes=100,
            name='Conservative',
            color='red',
            year=2012
        )
    )
    election.party_results.append(
        PartyResult(
            number_of_mandates=3,
            votes=3,
            total_votes=50,
            name='Conservative',
            color='red',
            year=2016
        )
    )
    assert election.export_parties() == [
        {
            'color': 'red',
            'mandates': 3,
            'name': 'Conservative',
            'id': 0,
            'total_votes': 50,
            'votes': 3,
            'year': 2016,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_999': '',

        }, {
            'color': 'black',
            'mandates': 2,
            'name': 'Libertarian',
            'id': 1,
            'total_votes': 50,
            'votes': 2,
            'year': 2016,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_999': '',
        }, {
            'color': 'red',
            'mandates': 1,
            'name': 'Conservative',
            'id': 0,
            'total_votes': 100,
            'votes': 1,
            'year': 2012,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_999': '',
        }, {
            'color': 'black',
            'mandates': 0,
            'name': 'Libertarian',
            'id': 1,
            'total_votes': 100,
            'votes': 0,
            'year': 2012,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_999': '',
        }
    ]

    for idx, source in enumerate(('Conservative', 'Libertarian', 'Other', '')):
        election.panachage_results.append(
            PanachageResult(
                target='Conservative',
                source=source,
                votes=idx + 1
            )
        )
    election.panachage_results.append(
        PanachageResult(
            target='Libertarian',
            source='Conservative',
            votes=5,
        )
    )
    assert election.export_parties() == [
        {
            'color': 'red',
            'mandates': 3,
            'name': 'Conservative',
            'id': 0,
            'total_votes': 50,
            'votes': 3,
            'year': 2016,
            'panachage_votes_from_0': 1,
            'panachage_votes_from_1': 2,
            'panachage_votes_from_2': 3,
            'panachage_votes_from_999': 4,

        }, {
            'color': 'black',
            'mandates': 2,
            'name': 'Libertarian',
            'id': 1,
            'total_votes': 50,
            'votes': 2,
            'year': 2016,
            'panachage_votes_from_0': 5,
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'color': '',
            'mandates': '',
            'name': 'Other',
            'id': 2,
            'total_votes': '',
            'votes': '',
            'year': 2016,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'color': 'red',
            'mandates': 1,
            'name': 'Conservative',
            'id': 0,
            'total_votes': 100,
            'votes': 1,
            'year': 2012,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'color': 'black',
            'mandates': 0,
            'name': 'Libertarian',
            'id': 1,
            'total_votes': 100,
            'votes': 0,
            'year': 2012,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'color': '',
            'mandates': '',
            'name': 'Other',
            'id': 2,
            'total_votes': '',
            'votes': '',
            'year': 2012,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }
    ]


def test_proporz_election_clear_results(session):
    election = proporz_election()
    session.add(election)
    session.flush()

    election.clear_results()

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
    assert session.query(ListResult).first() is None
    assert session.query(PanachageResult).first() is None
    assert session.query(PartyResult).first() is None


def test_proporz_election_rename(session):
    election = proporz_election()
    session.add(election)
    session.flush()

    session.query(Candidate).one().election_id == 'election'
    session.query(ElectionResult).one().election_id == 'election'
    session.query(List).one().election_id == 'election'
    session.query(ListConnection).first().election_id == 'election'

    election.id = 'elerction'
    session.flush()

    session.query(Candidate).one().election_id == 'elerction'
    session.query(ElectionResult).one().election_id == 'elerction'
    session.query(List).one().election_id == 'elerction'
    session.query(ListConnection).first().election_id == 'elerction'
