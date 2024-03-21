from datetime import date
from io import BytesIO

from onegov.ballot import ProporzElection
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import export_election_internal_proporz
from onegov.election_day.formats import import_election_internal_proporz
from tests.onegov.election_day.common import create_principal


def test_roundtrip_wabstic_internal_alphanum(import_test_datasets, session):
    principal = 'sg'
    election, errors = import_test_datasets(
        'wabstic',
        'election',
        principal,
        domain='canton',
        election_type='proporz',
        dataset_name='NR2019-alphanumerische_list_nr',
        number_of_mandates=12,
        date_=date(2019, 10, 20)
    )
    assert not errors
    csv = convert_list_of_dicts_to_csv(
        export_election_internal_proporz(
            election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

    election_copy = ProporzElection(
        title='copy',
        domain='canton',
        type='proporz',
        number_of_mandates=12,
        date=date(2019, 10, 20)
    )

    session.add(election_copy)
    session.flush()

    errors = import_election_internal_proporz(
        election, create_principal(principal), BytesIO(csv), 'text/plain'
    )
    assert not errors
