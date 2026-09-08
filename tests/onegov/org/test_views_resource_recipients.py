from __future__ import annotations

import transaction

from onegov.org.models import ResourceRecipientCollection
from onegov.reservation import ResourceCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.org.conftest import Client
    from tests.shared.client import ExtendedResponse


def test_resource_recipient_overview(client: Client) -> None:
    resources = ResourceCollection(client.app.libres_context)
    gymnasium = resources.add('Gymnasium', 'Europe/Zurich', type='room')
    dailypass = resources.add('Dailypass', 'Europe/Zurich', type='daypass')
    resources.add('Meeting', 'Europe/Zurich', type='room')

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        new_reservations=True,
        daily_reservations=True,
        send_on=['FR', 'SU'],
        resources=[gymnasium.id.hex, dailypass.id.hex]
    )
    transaction.commit()
    client.login_admin()

    page = client.get('/resource-recipients')
    assert "John" in page
    assert "john@example.org" in page
    assert "Erhält Benachrichtigungen für neue Reservationen." in page
    assert "für Reservationen des Tages an folgenden Tagen:" in page
    assert "Fr , So" in page
    assert "Gymnasium" in page
    assert "Dailypass" in page
    assert "Meeting" not in page


def test_resource_recipient_overview_with_notes_notification(
    client: Client,
) -> None:
    resources = ResourceCollection(client.app.libres_context)
    gymnasium = resources.add('Gymnasium', 'Europe/Zurich', type='room')
    dailypass = resources.add('Dailypass', 'Europe/Zurich', type='daypass')
    resources.add('Meeting', 'Europe/Zurich', type='room')

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        internal_notes=True,
        resources=[gymnasium.id.hex, dailypass.id.hex]
    )
    transaction.commit()
    client.login_admin()

    page = client.get('/resource-recipients')
    assert "John" in page
    assert "john@example.org" in page
    assert "Erhält Benachrichtigungen für interne Notizen" in page


def test_resource_recipient_delivery_times(client: Client) -> None:
    resources = ResourceCollection(client.app.libres_context)
    resources.add('Room', 'Europe/Zurich', type='room')
    transaction.commit()
    client.login_admin()

    # new form pre-fills 06:00
    page: ExtendedResponse = client.get('/resource-recipients/new-recipient')
    assert '06:00' in page

    # create with two delivery times
    page.form['name'] = 'User A'
    page.form['address'] = 'user@example.org'
    page.form['daily_reservations'] = True
    page.form['daily_reservations_times'] = '09:00,14:30'
    page.form.set('resources', True, index=0)
    page = page.form.submit().follow()
    assert 'User A' in page

    # both times round-trip to the edit form (not corrupted to e.g. 0,9,:,0,0)
    edit_page: ExtendedResponse = client.get('/resource-recipients')
    edit_page = edit_page.click('Bearbeiten', index=0)
    assert '09:00' in edit_page
    assert '14:30' in edit_page

    # update to a single time
    edit_page.form['daily_reservations_times'] = '08:00'
    edit_page = edit_page.form.submit().follow()
    edit_page = client.get('/resource-recipients').click('Bearbeiten', index=0)
    assert '08:00' in edit_page

    # invalid: single-digit hour
    edit_page.form['daily_reservations_times'] = '7:03'
    result = edit_page.form.submit()
    assert result.status_int == 200
    assert 'HH:MM' in result

    # invalid: mixed valid/invalid in a list
    edit_page.form['daily_reservations_times'] = '06:35,7:05'
    result = edit_page.form.submit()
    assert result.status_int == 200
    assert 'HH:MM' in result

    # invalid: minutes not a multiple of 5
    edit_page.form['daily_reservations_times'] = '06:35,07:03'
    result = edit_page.form.submit()
    assert result.status_int == 200
    assert 'Minuten müssen ein Vielfaches von 5 sein' in result

    # empty times are rejected
    edit_page = client.get('/resource-recipients').click('Bearbeiten', index=0)
    edit_page.form['daily_reservations_times'] = ''
    result = edit_page.form.submit()
    assert result.status_int == 200
    assert 'Bitte mindestens eine Zustellungszeit eingeben' in result

    # delivery times are not validated when daily_reservations is unchecked
    edit_page = client.get('/resource-recipients').click('Bearbeiten', index=0)
    edit_page.form['daily_reservations'] = False
    edit_page.form['daily_reservations_times'] = 'badtime'
    edit_page.form['new_reservations'] = True
    edit_page = edit_page.form.submit().follow()
    assert 'User A' in edit_page


def test_resource_recipient_legacy_delivery_time(client: Client) -> None:
    resources = ResourceCollection(client.app.libres_context)
    room = resources.add('Room', 'Europe/Zurich', type='room')

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='Legacy',
        medium='email',
        address='user@example.org',
        daily_reservations=True,
        send_on=['MO'],
        resources=[room.id.hex]
    )
    transaction.commit()
    client.login_admin()

    edit_page: ExtendedResponse = client.get(
        '/resource-recipients').click('Bearbeiten', index=0)
    assert '06:00' in edit_page
