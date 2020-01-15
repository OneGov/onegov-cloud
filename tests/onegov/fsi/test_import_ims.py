import pytest

from onegov.fsi.ims_import import parse_ims_data
import os
data_path = os.environ.get('IMS_DATA_PATH')

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
