from datetime import datetime
import transaction
from onegov.core.utils import normalize_for_url
from onegov.org.models.ticket import ReservationHandler
from onegov.reservation import ResourceCollection
from onegov.ticket import Ticket


def test_has_future_reservations(client):

    ctx = client.app.libres_context

    def setup_resource(name, title, definition, dates, whole_day):
        res = ResourceCollection(ctx).by_name(name)
        res.definition, res.title = definition, title
        alloc = res.get_scheduler(ctx).allocate(
            dates=dates, whole_day=whole_day
        )
        return client.bound_reserve(alloc[0])

    # Setting time to a distant future year as func.now() isn't impacted by
    # freezegun
    reserve_daypass = setup_resource(
        'tageskarte',
        'Tageskarte',
        "Vorname *= " "___\nNachname *= ___",
        (datetime(2100, 8, 28, 12, 0),
         datetime(2100, 8, 28, 13, 0)),
        False,
    )

    ResourceCollection(ctx).add(
        "Conference room", 'Europe/Zurich', type='room', name='conference-room'
    )

    reserve_room = setup_resource(
        'conference-room',
        normalize_for_url("Gemeindeverwaltung Sitzungszimmer gross (2. OG)"),
        "Name *= ___",
        (datetime(2100, 8, 28),
         datetime(2100, 8, 28)),
        True,
    )

    transaction.commit()
    client.login_admin()

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

    session = client.app.session()

    handlers: list[ReservationHandler] = [
        h.handler for h in session.query(Ticket)
    ]
    assert all(h.has_future_reservation() for h in handlers)
