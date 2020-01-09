from onegov.core.utils import module_path
from onegov.fsi.ims_import import import_ims_data

data_path = module_path('tests.onegov.fsi', 'temp_data')

persons_file = f'{data_path}/Personen.txt'
subscriptions_file = f'{data_path}/Teilnehmer.txt'
events_file = f'{data_path}/Ausführungen.txt'
courses_file = f'{data_path}/Kurse.txt'


def test_import_ims(session, attendee):

    errors = import_ims_data(
        session,
        subscriptions_file,
        events_file,
        courses_file,
        persons_file
    )
    print(errors)
    assert not errors
    assert False
