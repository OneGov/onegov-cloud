import pytest

from onegov.core.utils import module_path
from onegov.fsi.ims_import import parse_ims_data

data_path = module_path('tests.onegov.fsi', 'temp_data')

persons_file = f'{data_path}/Personen.txt'
subscriptions_file = f'{data_path}/Teilnehmer.txt'
events_file = f'{data_path}/Ausführungen.txt'
courses_file = f'{data_path}/Kurse.txt'


@pytest.mark.skip('Runs only with the original data, was used for testing')
def test_import_ims(session, attendee):

    errors, persons, courses, events, possible_ldap_users = parse_ims_data(
        subscriptions_file,
        events_file,
        courses_file,
        persons_file
    )
    assert not errors
    assert all((persons, courses, events, possible_ldap_users))
