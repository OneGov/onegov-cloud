from __future__ import annotations

from datetime import date
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_import_ech_election_zh(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # The datasets contain proportional election information and results
    # for the Nationalratswahl 2023 and Kantonsratswahlen Wahlkreis I
    # in the newer Abraxas eCH-0252 format

    # import election information
    results = import_test_datasets(
        api_format='ech',
        principal='zh',
        dataset_name=(
            'eCH-0252_proportional-election-info-delivery_20240101'
        )
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    # 2 elections + 1 compound
    elections = [u for u in updated if isinstance(u, ProporzElection)]
    compounds = [u for u in updated if isinstance(u, ElectionCompound)]
    assert len(elections) == 2
    assert len(compounds) == 1
    assert not deleted

    # Nationalratswahl 2023
    nrw = next(
        e for e in elections
        if 'Nationalrat' in (e.title or '')
    )
    assert nrw.domain == 'federation'
    assert nrw.date == date(2024, 1, 1)
    assert nrw.number_of_mandates == 36
    assert len(nrw.candidates) == 1341
    assert len(nrw.lists) == 45
    assert len(nrw.list_connections) == 14

    # Kantonsratswahlen Wahlkreis I
    krw = next(
        e for e in elections
        if 'Kantonsrat' in (e.title or '')
    )
    assert krw.date == date(2024, 1, 1)
    assert krw.number_of_mandates == 5
    assert len(krw.candidates) == 49
    assert len(krw.lists) == 12
    assert krw.election_compound_id == compounds[0].id

    # re-import should be idempotent
    results = import_test_datasets(
        api_format='ech',
        principal='zh',
        dataset_name=(
            'eCH-0252_proportional-election-info-delivery_20240101'
        )
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    # import results (info must be imported first)
    results = import_test_datasets(
        api_format='ech',
        principal='zh',
        dataset_name=(
            'eCH-0252_proportional-election-result-delivery_20240101'
        )
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 2
    assert not deleted

    nrw = next(
        u for u in updated
        if isinstance(u, ProporzElection)
        and 'Nationalrat' in (u.title or '')
    )
    assert nrw.has_results is True


def test_import_ech_election_zh_combined(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # Test the combined result delivery (results only, no info delivery)
    # Info must be imported first for election/candidate definitions
    results = import_test_datasets(
        api_format='ech',
        principal='zh',
        dataset_name=(
            'eCH-0252_proportional-election-info-delivery_20240101'
        )
    )
    errors, updated, deleted = next(iter(results.values()))
    assert not errors

    results = import_test_datasets(
        api_format='ech',
        principal='zh',
        dataset_name=(
            'eCH-0252_proportional-election-result-delivery'
            '_with_info_20240101'
        )
    )
    assert len(results) == 1
    errors, updated, deleted = next(iter(results.values()))
    assert not errors
    assert len(updated) == 2

    elections = [u for u in updated if isinstance(u, ProporzElection)]
    assert len(elections) == 2

    nrw = next(
        e for e in elections
        if 'Nationalrat' in (e.title or '')
    )
    assert nrw.number_of_mandates == 36
    assert len(nrw.candidates) == 1341
    assert nrw.has_results is True
