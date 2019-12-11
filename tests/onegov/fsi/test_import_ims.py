from onegov.core.utils import module_path
from onegov.fsi.ims_import import import_ims_data

data_path = module_path('tests.onegov.fsi', 'ims_test_data')

attendees_file = f'{data_path}/Teilnehmer.txt'
events_file = f'{data_path}/Ausführungen.txt'
courses_file = f'{data_path}/Kurse.txt'


def test_import_ims(session, attendee):

    # member@example.org is needed to link the reservation in the file
    att, data = attendee(session)

    errors = import_ims_data(
        session,
        attendees_file,
        events_file,
        courses_file
    )
    print('errors in reservation parsing: ', errors)
