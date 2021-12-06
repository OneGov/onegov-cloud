from datetime import date
from onegov.ballot import List
from onegov.ballot import ListResult
from onegov.ballot import ProporzElection
from onegov.ballot import ElectionResult


def test_list_percentages(session):
    election = ProporzElection(
        title='Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    session.add(election)
    session.flush()

    # Add four entities/two districts
    election_result_1 = ElectionResult(
        name='1',
        district='1',
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
        name='2',
        district='1',
        entity_id=2,
        counted=True,
        eligible_voters=100,
        received_ballots=50,
        blank_ballots=1,
        invalid_ballots=0,
        blank_votes=8,
        invalid_votes=1
    )
    election_result_3 = ElectionResult(
        name='3',
        district='2',
        entity_id=3,
        counted=False,
        eligible_voters=500,
    )
    election_result_4 = ElectionResult(
        name='4',
        district='2',
        entity_id=4,
        counted=True,
        eligible_voters=200,
        received_ballots=0,
        blank_ballots=0,
        invalid_ballots=0,
        blank_votes=0,
        invalid_votes=0
    )
    election.results.append(election_result_1)
    election.results.append(election_result_2)
    election.results.append(election_result_3)
    election.results.append(election_result_4)
    session.flush()

    # Add 5 lists
    list_1 = List(
        number_of_mandates=1,
        list_id='1',
        name='1'
    )
    list_2 = List(
        list_id='2',
        name='2'
    )
    list_3 = List(
        list_id='3',
        name='3'
    )
    list_4 = List(
        list_id='4',
        name='4'
    )
    list_5 = List(
        list_id='5',
        name='5'
    )
    election.lists.append(list_1)
    election.lists.append(list_2)
    election.lists.append(list_3)
    election.lists.append(list_4)
    election.lists.append(list_5)
    session.flush()

    # Add the list results to the first entity
    election_result_1.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=52,
        )
    )
    election_result_1.list_results.append(
        ListResult(
            list_id=list_2.id,
            votes=11
        )
    )
    election_result_1.list_results.append(
        ListResult(
            list_id=list_3.id,
            votes=20
        )
    )
    election_result_1.list_results.append(
        ListResult(
            list_id=list_4.id,
            votes=1
        )
    )
    election_result_1.list_results.append(
        ListResult(
            list_id=list_5.id,
            votes=0
        )
    )

    # Add only two list results to the second entity.
    election_result_2.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=20
        )
    )
    election_result_2.list_results.append(
        ListResult(
            list_id=list_5.id,
            votes=5
        )
    )

    # Add only one list results to the last entity
    election_result_4.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=10
        )
    )
    session.flush()

    tot = {t.entity_id: t.votes for t in election.votes_by_entity.all()}
    tot_d = {t.district: t.votes for t in election.votes_by_district.all()}
    print(tot)
    print(tot_d)

    def round_(n, z):
        return round(100 * n / z, 2)

    assert list_1.percentage_by_entity == {
        1: {'counted': True, 'votes': 52, 'percentage': round_(52, tot[1])},
        2: {'counted': True, 'votes': 20, 'percentage': round_(20, tot[2])},
        3: {'counted': False, 'votes': 0, 'percentage': 0.0},
        4: {'counted': True, 'votes': 10, 'percentage': round_(10, tot[4])}
    }
    assert list_2.percentage_by_entity == {
        1: {'counted': True, 'votes': 11, 'percentage': round_(11, tot[1])},
        2: {'counted': True, 'votes': 0, 'percentage': 0.0},
        3: {'counted': False, 'votes': 0, 'percentage': 0.0},
        4: {'counted': True, 'votes': 0, 'percentage': 0.0}
    }
    assert list_3.percentage_by_entity == {
        1: {'counted': True, 'votes': 20, 'percentage': round_(20, tot[1])},
        2: {'counted': True, 'votes': 0, 'percentage': 0.0},
        3: {'counted': False, 'votes': 0, 'percentage': 0.0},
        4: {'counted': True, 'votes': 0, 'percentage': 0.0}
    }
    assert list_4.percentage_by_entity == {
        1: {'counted': True, 'votes': 1, 'percentage': round_(1, tot[1])},
        2: {'counted': True, 'votes': 0, 'percentage': 0.0},
        3: {'counted': False, 'votes': 0, 'percentage': 0.0},
        4: {'counted': True, 'votes': 0, 'percentage': 0.0}
    }
    assert list_5.percentage_by_entity == {
        1: {'counted': True, 'votes': 0, 'percentage': 0.0},
        2: {'counted': True, 'votes': 5, 'percentage': round_(5, tot[2])},
        3: {'counted': False, 'votes': 0, 'percentage': 0.0},
        4: {'counted': True, 'votes': 0, 'percentage': 0.0}
    }

    assert list_1.percentage_by_district == {
        '1': {'votes': 72, 'counted': True, 'entities': [1, 2],
              'percentage': round_(72, tot_d['1'])},
        '2': {'votes': 10, 'counted': False, 'entities': [3, 4],
              'percentage': 100.0}
    }
    assert list_2.percentage_by_district == {
        '1': {'votes': 11, 'counted': True, 'entities': [1, 2],
              'percentage': round_(11, tot_d['1'])},
        '2': {'votes': 0, 'counted': False, 'entities': [3, 4],
              'percentage': 0.0}
    }
    assert list_3.percentage_by_district == {
        '1': {'votes': 20, 'counted': True, 'entities': [1, 2],
              'percentage': round_(20, tot_d['1'])},
        '2': {'votes': 0, 'counted': False, 'entities': [3, 4],
              'percentage': 0.0}
    }
    assert list_4.percentage_by_district == {
        '1': {'votes': 1, 'counted': True, 'entities': [1, 2],
              'percentage': round_(1, tot_d['1'])},
        '2': {'votes': 0, 'counted': False, 'entities': [3, 4],
              'percentage': 0.0}
    }
    assert list_5.percentage_by_district == {
        '1': {'votes': 5, 'counted': True, 'entities': [1, 2],
              'percentage': round_(5, tot_d['1'])},
        '2': {'votes': 0, 'counted': False, 'entities': [3, 4],
              'percentage': 0.0}
    }
