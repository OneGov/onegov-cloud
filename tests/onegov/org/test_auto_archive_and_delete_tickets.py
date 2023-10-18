from datetime import datetime
import transaction
from onegov.core.utils import normalize_for_url
from onegov.reservation import ResourceCollection
from onegov.ticket import Ticket


def test_has_future_reservations(client):
    def setup_resource(
        name, title, definition, dates, whole_day, ctx, client
    ):
        res = ResourceCollection(ctx).by_name(name)
        res.definition, res.title = definition, title
        alloc = res.get_scheduler(ctx).allocate(
            dates=dates, whole_day=whole_day
        )
        return client.bound_reserve(alloc[0])

    def fill_and_submit_form(client, resource_name, form_data):
        formular = client.get(f'/resource/{resource_name}/form')
        for key, value in form_data.items():
            formular.form[key] = value
        formular.form.submit().follow().form.submit()

    def accept_all_reservations(client):
        ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
        ticket.click('Alle Reservationen annehmen')

    ctx = client.app.libres_context
    client.login_admin()

    transaction.begin()
    reserve_daypass = setup_resource(
        'tageskarte',
        'Tageskarte',
        "Vorname *= ___\nNachname *= ___",
        (datetime(2100, 8, 28, 12, 0),
         datetime(2100, 8, 28, 13, 0)),
        False,
        ctx,
        client,
    )

    ResourceCollection(ctx).add(
        "Conference room",
        'Europe/Zurich',
        type='room',
        name='conference-room',
    )

    reserve_room = setup_resource(
        'conference-room',
        normalize_for_url(
            "Gemeindeverwaltung Sitzungszimmer gross (2. OG)"
        ),
        "Name *= ___",
        (datetime(2100, 8, 28),
         datetime(2100, 8, 28)),
        True,
        ctx,
        client,
    )

    transaction.commit()

    assert reserve_daypass().json == {'success': True}
    assert reserve_room().json == {'success': True}

    fill_and_submit_form(
        client,
        'tageskarte',
        {
            'email': 'info@example.org',
            'vorname': 'Charlie',
            'nachname': 'Carson',
        },
    )
    accept_all_reservations(client)

    fill_and_submit_form(client, 'conference-room', {'name': 'Name'})
    accept_all_reservations(client)

    session = client.app.session()
    handlers = [h.handler for h in session.query(Ticket)]
    assert all(h.has_future_reservation() for h in handlers)

    # now setup a reservation which is in the past
    transaction.begin()

    ResourceCollection(ctx).add(
        "Conference room",
        'Europe/Zurich',
        type='room',
        name='conference-room2',
    )
    reserve_room2 = setup_resource(
        'conference-room2',
        'Conference Room',
        "Vorname *= ___\nNachname *= ___",
        (datetime(2009, 8, 28, 12, 0),
         datetime(2009, 8, 28, 13, 0)),
        False,
        ctx,
        client,
    )
    transaction.commit()

    assert reserve_room2().json == {'success': True}

    fill_and_submit_form(
        client,
        'conference-room2',
        {
            'email': 'info2@example.org',
            'vorname': 'Charlie2',
            'nachname': 'Carson2',
        },
    )

    accept_all_reservations(client)

    session = client.app.session()
    handler = [
        t.handler
        for t in session.query(Ticket).filter(
            Ticket.title == '28.08.2009 12:00 - 13:00'
        )
    ][0]
    assert not handler.has_future_reservation()
