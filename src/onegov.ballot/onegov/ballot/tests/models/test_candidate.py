from datetime import date
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ProporzElection
from onegov.ballot import ElectionResult


def test_candidate_percentages(session):
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
    session.flush()

    assert candidate_1.percentage_by_entity == {
        1: {'counted': True, 'percentage': 100 * 50 / 1000},
        2: {'counted': True, 'percentage': 100 * 30 / 1000},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_2.percentage_by_entity == {
        1: {'counted': True, 'percentage': 100 * 10 / 1000},
        2: {'counted': True, 'percentage': 0.0},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_3.percentage_by_entity == {
        1: {'counted': True, 'percentage': 100 * 20 / 1000},
        2: {'counted': True, 'percentage': 0.0},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_4.percentage_by_entity == {
        1: {'counted': True, 'percentage': 100 * 1 / 1000},
        2: {'counted': True, 'percentage': 0.0},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }
    assert candidate_5.percentage_by_entity == {
        1: {'counted': True, 'percentage': 0.0},
        2: {'counted': True, 'percentage': 100 * 5 / 1000},
        3: {'counted': False, 'percentage': 0.0},
        4: {'counted': True, 'percentage': 0.0}
    }

    assert candidate_1.percentage_by_district == {
        '1': {'counted': True, 'entities': [1, 2], 'percentage': 8000 / 2000},
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
        '1': {'counted': True, 'entities': [1, 2], 'percentage': 500 / 2000},
        '2': {'counted': False, 'entities': [3, 4], 'percentage': 0.0}
    }
