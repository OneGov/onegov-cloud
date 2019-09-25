from datetime import date

from onegov.election_day.utils.election.connections import \
    get_connection_results_api


def test_get_connection_results(import_test_datasets, session):
    election, errors = import_test_datasets(
        'internal',
        'election',
        'gr',
        'canton',
        election_type='proporz',
        number_of_mandates=5,
        date_=date(2019, 10, 20),
        dataset_name='nationalratswahlen-2019-final',
        app_session=session
    )
    assert not errors
    results = get_connection_results_api(election, session)

    print(results)
    assert False
