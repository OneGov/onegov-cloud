from io import BytesIO

from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import import_election_internal_proporz
from tests.onegov.election_day.common import create_principal, print_errors


def test_roundtrip_wabstic_internal_alphanum(import_test_datasets):
    principal = 'sg'
    election = import_test_datasets(
        'wabstic',
        'election',
        principal,
        domain='canton',
        election_type='proporz',
        dataset_name='NR2019-alphanumerische_list_nr',
        number_of_mandates=12
    )

    # print(election)
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')
    print(csv)

    errors = import_election_internal_proporz(
        election, create_principal(principal), BytesIO(csv), 'text/plain'
    )
    print_errors(errors)
    assert not errors


