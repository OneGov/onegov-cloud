from datetime import date
from onegov.ballot import Candidate, List, ListResult
from onegov.ballot import CandidateResult
from onegov.ballot import ProporzElection
from onegov.ballot import ElectionResult


def test_candidate_percentages_proporz(session):
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
        eligible_voters=2000,
        received_ballots=1015,
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
        eligible_voters=2000,
        received_ballots=1005,
        blank_ballots=3,
        invalid_ballots=2,
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

    # Add 5 candidates
    candidate_1 = Candidate(
        elected=True,
        candidate_id='1',
        family_name='1',
        first_name='1',
    )
    candidate_2 = Candidate(
        elected=False,
        candidate_id='2',
        family_name='2',
        first_name='2',
    )
    candidate_3 = Candidate(
        elected=False,
        candidate_id='3',
        family_name='3',
        first_name='3',
    )
    candidate_4 = Candidate(
        elected=False,
        candidate_id='4',
        family_name='4',
        first_name='4',
    )
    candidate_5 = Candidate(
        elected=False,
        candidate_id='5',
        family_name='5',
        first_name='5',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)
    election.candidates.append(candidate_3)
    election.candidates.append(candidate_4)
    election.candidates.append(candidate_5)
    session.flush()

    # Add the candidate results to the first entity
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=50,
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_2.id,
            votes=10
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
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_5.id,
            votes=0
        )
    )

    # Add only two candidate results to the second entity.
    election_result_2.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=30
        )
    )
    election_result_2.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_5.id,
            votes=5
        )
    )

    # Add only one candidate results to the last entity
    election_result_4.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=10
        )
    )

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
    er1_list_votes = 52+11+20+1
    er2_list_votes = 20+5
    er4_list_votes = 10
    session.flush()

    def round_(votes, total):
        return round(100 * votes / total, 2)

    assert election.list_votes_by_entity.all() == [
        ('election', 1, True, er1_list_votes),
        ('election', 2, True, er2_list_votes),
        ('election', 3, False, 0),
        ('election', 4, True, er4_list_votes)
    ]

    assert election.list_votes_by_district.all() == [
        ('election', '1', [1, 2], True, er1_list_votes+er2_list_votes),
        ('election', '2', [3, 4], False, er4_list_votes)
    ]

    # election result 1 and 2 are belonging to district 1
    tot = er1_list_votes + er2_list_votes
    assert tot == 109

    assert candidate_1.percentage_by_district == {
        '1': {'counted': True, 'entities': [1, 2],
              'percentage': round_(50 + 30, 109)},
        '2': {'counted': False, 'entities': [3, 4], 'percentage': 0.0}
    }

    assert candidate_2.percentage_by_district == {
        '1': {'counted': True, 'entities': [1, 2], 'percentage': 0.0},
        '2': {'counted': False, 'entities': [3, 4], 'percentage': 0.0}
    }
    assert candidate_3.percentage_by_district == {
        '1': {'counted': True, 'entities': [1, 2], 'percentage': 0.0},
        '2': {'counted': False, 'entities': [3, 4], 'percentage': 0.0}
    }
    assert candidate_4.percentage_by_district == {
        '1': {'counted': True, 'entities': [1, 2], 'percentage': 0.0},
        '2': {'counted': False, 'entities': [3, 4], 'percentage': 0.0}
    }
    assert candidate_5.percentage_by_district == {
        '1': {'counted': True, 'entities': [1, 2],
              'percentage': round_(5, tot)},
        '2': {'counted': False, 'entities': [3, 4], 'percentage': 0.0}
    }

    assert candidate_1.percentage_by_entity == {
        1: {'counted': True, 'percentage': round_(50, er1_list_votes)},
        2: {'counted': True, 'percentage': round_(30, er2_list_votes)},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 100.0}
    }
    assert candidate_2.percentage_by_entity == {
        1: {'counted': True, 'percentage': round_(10, er1_list_votes)},
        2: {'counted': True, 'percentage': 0.0},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_3.percentage_by_entity == {
        1: {'counted': True, 'percentage': round_(20, er1_list_votes)},
        2: {'counted': True, 'percentage': 0.0},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_4.percentage_by_entity == {
        1: {'counted': True, 'percentage': round_(1, er1_list_votes)},
        2: {'counted': True, 'percentage': 0.0},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_5.percentage_by_entity == {
        1: {'counted': True, 'percentage': 0.0},
        2: {'counted': True, 'percentage': round_(5, er2_list_votes)},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }

