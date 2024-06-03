from datetime import date
from onegov.election_day.models import Election


def test_import_ech_election_gr(session, import_test_datasets):
    # The datasets contain an election information and an election result
    # delivery for the SRW and NRW 2023

    # initial import
    errors, updated, deleted = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='elections-information'
    )
    assert not errors
    assert len(updated) == 2
    assert not deleted

    # ... test majorz
    election = next(u for u in updated if u.type == 'majorz')
    assert election.domain == 'canton'
    assert election.id == 'i75'
    assert election.external_id == 'I75'
    assert election.date == date(2023, 10, 22)
    assert election.progress == (0, 0)
    assert election.has_results is False
    assert election.title_translations == {
        'de_CH': 'Ständeratswahlen',
        'rm_CH': 'Elecziuns dal Cussegl dals chantuns',
        'it_CH': 'Elezioni del Consiglio degli Stati'
    }
    assert len(election.candidates) == 3

    # ... test proporz
    election = next(u for u in updated if u.type == 'proporz')
    assert election.domain == 'federation'
    assert election.id == 'i74'
    assert election.external_id == 'I74'
    assert election.date == date(2023, 10, 22)
    assert election.progress == (0, 0)
    assert election.has_results is False
    assert election.title_translations == {
        'de_CH': 'Nationalratswahlen',
        'rm_CH': 'Elecziuns dal Cussegl naziunal',
        'it_CH': 'Elezioni del Consiglio nazionale'
    }
    assert len(election.candidates) == 122
    assert len(election.lists) == 25
    assert len(election.list_connections) == 9

    # re-import
    errors, updated, deleted = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='elections-information'
    )
    assert not errors
    assert len(updated) == 2
    assert not deleted

    # import of results
    errors, updated, deleted = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='elections-results'
    )
    assert not errors
    assert len(updated) == 2
    assert not deleted

    # ... test majorz
    election = next(u for u in updated if u.type == 'majorz')
    assert election.has_results is True
    assert election.counted is True
    assert election.absolute_majority == 22000
    assert election.accounted_ballots == 49605
    assert election.accounted_votes == 87996
    candidate = next(
        c for c in election.candidates if c.family_name == 'Engler'
    )
    assert candidate.elected is True
    assert candidate.votes == 38316

    # ... test proporz
    election = next(u for u in updated if u.type == 'proporz')
    assert election.has_results is True
    assert election.counted is True
    assert election.accounted_ballots == 59521
    assert election.accounted_votes == 294087
    candidate = next(
        c for c in election.candidates if c.family_name == 'Candinas'
    )
    assert candidate.elected is True
    assert candidate.votes == 28400
    list_ = next(l for l in election.lists if 'POWER' in l.name)
    assert list_.number_of_mandates == 2
    assert list_.votes == 65747
    result = next(r for r in list_.panachage_results if r.source is None)
    assert result.votes == 7509

    # re-import of results
    errors, updated, deleted = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='elections-results'
    )
    assert not errors
    assert len(updated) == 2
    assert not deleted

    # test removing items
    session.add(
        Election(
            date=date(2023, 10, 22),
            id='remove',
            domain='canton',
            title_translations={'de_CH': 'remove'}
        )
    )
    session.add(
        Election(
            date=date(2023, 1, 1),
            id='keep',
            domain='canton',
            title_translations={'de_CH': 'keep'}
        )
    )
    session.flush()

    # ... election on the same day marked for deletion
    errors, updated, deleted = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='elections-information'
    )
    assert not errors
    assert len(updated) == 2
    assert len(deleted) == 1
    assert list(deleted)[0].id == 'remove'

    # test missing information
    for election in updated:
        election.clear_results(True)

    errors, updated, deleted = import_test_datasets(
        api_format='ech',
        principal='gr',
        dataset_name='elections-results'
    )
    assert errors
