from __future__ import annotations

from datetime import date
from onegov.election_day.models import Election

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_import_ech_election_sg_majority(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # The datasets contain majority election information and results
    # for the "SEANTIS Majorz" test election in the eCH-0252 format

    # import election information
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='majority_info'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    elections = [u for u in updated if isinstance(u, Election)]
    assert len(elections) == 1
    assert not deleted

    election = elections[0]
    assert election.domain == 'federation'
    assert election.date == date(2027, 10, 11)
    assert election.number_of_mandates == 2
    assert len(election.candidates) == 2

    # re-import should be idempotent
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='majority_info'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    # import results (info must be imported first)
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='majority_result'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 1
    assert not deleted

    updated_election = next(iter(updated))
    assert isinstance(updated_election, Election)
    assert updated_election.has_results is True
    # 3 counted circles + remaining uncounted
    assert updated_election.status == 'interim'
    counted_results = [r for r in updated_election.results if r.counted]
    assert len(counted_results) == 3

    # verify aggregate vote counts across counted circles
    # Altstätten: 5000, Amden: 2000, Andwil: 1500
    total_eligible = sum(r.eligible_voters for r in counted_results)
    assert total_eligible == 8500
    # Altstätten: 3000, Amden: 1000, Andwil: 800
    total_received = sum(r.received_ballots for r in counted_results)
    assert total_received == 4800
    # Altstätten: 10, Amden: 5, Andwil: 3
    total_blank_ballots = sum(r.blank_ballots for r in counted_results)
    assert total_blank_ballots == 18
    # Altstätten: 20, Amden: 8, Andwil: 5
    total_invalid_ballots = sum(r.invalid_ballots for r in counted_results)
    assert total_invalid_ballots == 33

    # verify candidate vote totals
    candidates = sorted(
        updated_election.candidates, key=lambda c: c.family_name
    )
    assert candidates[0].family_name == 'Fischer'
    assert candidates[1].family_name == 'Muster'

    fischer_votes = sum(
        cr.votes for r in counted_results
        for cr in r.candidate_results
        if cr.candidate.family_name == 'Fischer'
    )
    # Altstätten: 1200, Amden: 400, Andwil: 350
    assert fischer_votes == 1950

    muster_votes = sum(
        cr.votes for r in counted_results
        for cr in r.candidate_results
        if cr.candidate.family_name == 'Muster'
    )
    # Altstätten: 1500, Amden: 500, Andwil: 400
    assert muster_votes == 2400


def test_import_ech_election_sg_majority_combined(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # Test the combined delivery (info + results in a single file)
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='majority_combined'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    elections = [u for u in updated if isinstance(u, Election)]
    assert len(elections) == 1

    election = elections[0]
    assert election.date == date(2027, 10, 11)
    assert election.number_of_mandates == 2
    assert len(election.candidates) == 2
    assert election.has_results is True
    assert election.status == 'interim'

    counted_results = [r for r in election.results if r.counted]
    assert len(counted_results) == 3

    total_eligible = sum(r.eligible_voters for r in counted_results)
    assert total_eligible == 8500
    total_received = sum(r.received_ballots for r in counted_results)
    assert total_received == 4800

    # verify total candidate votes across counted circles
    total_candidate_votes = sum(
        cr.votes for r in counted_results
        for cr in r.candidate_results
    )
    # Muster: 1500+500+400=2400, Fischer: 1200+400+350=1950
    assert total_candidate_votes == 4350
