from __future__ import annotations

from datetime import date
from onegov.election_day.models import Election
from onegov.election_day.models import ProporzElection

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

    # flush must succeed
    session.flush()


def test_import_ech_election_sg_proportional(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # The datasets contain proportional election information and results
    # for the "SEANTIS Proporz" test election in the eCH-0252 format

    # import election information
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='proportional_info'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    elections = [u for u in updated if isinstance(u, ProporzElection)]
    assert len(elections) == 1
    assert not deleted

    election = elections[0]
    assert election.domain == 'federation'
    assert election.date == date(2027, 10, 12)
    assert election.number_of_mandates == 2
    assert len(election.candidates) == 2
    assert len(election.lists) == 3

    # re-import should be idempotent
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='proportional_info'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    # import results (info must be imported first)
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='proportional_result'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 1
    assert not deleted

    updated_election = next(iter(updated))
    assert isinstance(updated_election, ProporzElection)
    assert updated_election.has_results is True
    # 3 counted circles + remaining uncounted
    assert updated_election.status == 'interim'
    counted_results = [r for r in updated_election.results if r.counted]
    assert len(counted_results) == 3

    # verify aggregate vote counts across counted circles
    total_eligible = sum(r.eligible_voters for r in counted_results)
    assert total_eligible == 8500
    total_received = sum(r.received_ballots for r in counted_results)
    assert total_received == 4800
    total_blank_ballots = sum(r.blank_ballots for r in counted_results)
    assert total_blank_ballots == 18
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
    # Altstätten: 150+700, Amden: 80+250, Andwil: 60+200
    assert fischer_votes == 1440

    muster_votes = sum(
        cr.votes for r in counted_results
        for cr in r.candidate_results
        if cr.candidate.family_name == 'Muster'
    )
    # Altstätten: 200+800, Amden: 100+300, Andwil: 80+250
    assert muster_votes == 1730

    # verify list vote totals (countOfCandidateVotes)
    list_votes = sum(
        lr.votes for r in counted_results
        for lr in r.list_results
    )
    # Liste 1: 900+350+290=1540, Liste 2: 750+280+220=1250
    assert list_votes == 2790


def test_import_ech_election_sg_proportional_combined(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # Test the combined delivery (info + results in a single file)
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='proportional_combined'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    elections = [u for u in updated if isinstance(u, ProporzElection)]
    assert len(elections) == 1

    election = elections[0]
    assert election.date == date(2027, 10, 12)
    assert election.number_of_mandates == 2
    assert len(election.candidates) == 2
    assert len(election.lists) == 3
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
    # Muster: 1730, Fischer: 1440
    assert total_candidate_votes == 3170


def test_import_ech_election_sg_multi_combined(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # A single delivery containing both a majority and a proportional
    # election with only 3 counting circles
    results = import_test_datasets(
        api_format='ech',
        principal='sg',
        dataset_name='multi_combined'
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    # Should create both elections
    majority_elections = [
        u for u in updated
        if isinstance(u, Election) and not isinstance(u, ProporzElection)
    ]
    proporz_elections = [u for u in updated if isinstance(u, ProporzElection)]

    assert len(majority_elections) == 1
    assert len(proporz_elections) == 1

    # Verify majority election
    maj = majority_elections[0]
    assert maj.date == date(2027, 10, 11)
    assert maj.number_of_mandates == 2
    assert len(maj.candidates) == 2
    assert maj.has_results is True
    # 2 counted (Altstätten, Amden), 1 uncounted (Andwil)
    assert maj.status == 'interim'
    maj_counted = [r for r in maj.results if r.counted]
    assert len(maj_counted) == 2

    total_eligible = sum(r.eligible_voters for r in maj_counted)
    assert total_eligible == 7000  # 5000 + 2000
    total_received = sum(r.received_ballots for r in maj_counted)
    assert total_received == 4000  # 3000 + 1000

    total_maj_candidate_votes = sum(
        cr.votes for r in maj_counted
        for cr in r.candidate_results
    )
    # Muster: 1500+500=2000, Fischer: 1200+400=1600
    assert total_maj_candidate_votes == 3600

    # Verify proportional election
    prop = proporz_elections[0]
    assert prop.date == date(2027, 10, 11)
    assert prop.number_of_mandates == 2
    assert len(prop.candidates) == 2
    assert len(prop.lists) == 3
    assert prop.has_results is True
    # 1 counted (Altstätten), 2 uncounted (Amden, Andwil)
    assert prop.status == 'interim'
    prop_counted = [r for r in prop.results if r.counted]
    assert len(prop_counted) == 1

    total_prop_candidate_votes = sum(
        cr.votes for r in prop_counted
        for cr in r.candidate_results
    )
    # Muster: 200+800=1000, Fischer: 150+700=850
    assert total_prop_candidate_votes == 1850

    list_votes = sum(
        lr.votes for r in prop_counted
        for lr in r.list_results
    )
    # Liste 1: 900, Liste 2: 750, Empty: 0
    assert list_votes == 1650
