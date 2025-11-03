from __future__ import annotations

import transaction

from onegov.org.models import ResourceRecipientCollection
from onegov.reservation import ResourceCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


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
        resources=[
            gymnasium.id.hex,
            dailypass.id.hex
        ]
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
    client: Client
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
        resources=[
            gymnasium.id.hex,
            dailypass.id.hex
        ]
    )

    transaction.commit()
    client.login_admin()

    page = client.get('/resource-recipients')

    assert "John" in page
    assert "john@example.org" in page
    assert "Erhält Benachrichtigungen für interne Notizen" in page
