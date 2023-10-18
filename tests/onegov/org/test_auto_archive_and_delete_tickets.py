import tempfile
from datetime import datetime, date
from pathlib import Path
import transaction
from freezegun import freeze_time
from openpyxl import load_workbook
from onegov.core.utils import normalize_for_url
from onegov.reservation import ResourceCollection


@freeze_time("2023-04-28", tick=True)
def test_has_future_reservations(client):

    resources = ResourceCollection(client.app.libres_context)
    daypass_resource = resources.by_name('tageskarte')
    daypass_resource.definition = "Vorname *= ___\nNachname *= ___"
    daypass_resource.title = 'Tageskarte'

    scheduler = daypass_resource.get_scheduler(client.app.libres_context)
    daypass_allocations = scheduler.allocate(
        dates=(datetime(2023, 8, 28, 12, 0), datetime(2023, 8, 28, 13, 0)),
        whole_day=False
    )

    reserve_daypass = client.bound_reserve(daypass_allocations[0])

    resources.add(
        "Conference room",
        'Europe/Zurich',
        type='room',
        name='conference-room'
    )

    room_resource = resources.by_name('conference-room')
    room_resource.definition = "Name *= ___"
    room_resource.title = normalize_for_url("Gemeindeverwaltung Sitzungszimmer "
                                        "gross (2. OG)")

    room_allocations = room_resource.scheduler.allocate(
        dates=(datetime(2023, 8, 28), datetime(2023, 8, 28)),
        whole_day=True
    )

    reserve_room = client.bound_reserve(room_allocations[0])
    transaction.commit()
    client.login_admin()

    # create all reservations
    assert reserve_daypass().json == {'success': True}
    assert reserve_room().json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'info@example.org'
    formular.form['vorname'] = 'Charlie'
    formular.form['nachname'] = 'Carson'

    formular.form.submit().follow().form.submit()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    ticket.click('Alle Reservationen annehmen')

    formular = client.get('/resource/conference-room/form')
    formular.form['name'] = 'Name'
    formular.form.submit().follow().form.submit()

    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
    ticket.click('Alle Reservationen annehmen')


