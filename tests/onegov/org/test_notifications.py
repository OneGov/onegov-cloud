import os
from pathlib import Path

import transaction

from datetime import datetime
from freezegun import freeze_time
from onegov.org.models import ResourceRecipientCollection
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from tests.shared.utils import add_reservation


def test_new_reservation_notification(client):
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.add('Gymnasium', 'Europe/Zurich', type='room')
    resource.definition = 'Email = ___'
    resource.definition = 'Note = ___'
    scheduler = resource.get_scheduler(client.app.libres_context)

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        new_reservations=True,
        daily_reservations=True,
        send_on=['FR'],
        resources=[
            resource.id.hex
        ]
    )
    recipients.add(
        name='Paul',
        medium='email',
        address='paul@example.org',
        new_reservations=False,
        daily_reservations=True,
        send_on=['FR'],
        resources=[
            resource.id.hex
        ]
    )

    with freeze_time('2024-01-29'):
        allocations = scheduler.allocate(
            dates=(datetime.utcnow(), datetime.utcnow()),
            whole_day=True,
        )

        reserve = client.bound_reserve(allocations[0])
        transaction.commit()

        # create a reservation
        result = reserve(whole_day=True)
        assert result.json == {'success': True}

        # and fill out the form
        formular = client.get('/resource/gymnasium/form')
        formular.form['email'] = 'jessie@example.org'
        formular.form['note'] = 'Foobar'

        formular.form.submit().follow().form.submit().follow()

    client.login_admin()

    ticket = client.get('/tickets/ALL/open')
    ticket = ticket.click("Annehmen").follow()
    ticket.click("Alle Reservationen annehmen")

    # two mails for Jessie, one for John and none for Paul
    assert len(os.listdir(client.app.maildir)) == 3

    mails = [client.get_email(i) for i in range(3)]
    for mail in mails:
        if mail['To'] == 'jessie@example.org':  # email to customer
            assert ("Ihre Anfrage wurde erfasst" in mail['Subject']
                    or "Ihre Reservationen wurden angenommen" in
                    mail['Subject'])
            assert "Gymnasium" in mail['TextBody']
            assert 'Montag, 29. Januar 2024' in mail['TextBody']
            assert "Anzahl:" in mail['TextBody']
            assert "Foobar" in mail['TextBody']
        if mail['To'] == "john@example.org":
            assert "Neue Reservation(en)" in mail['Subject']
            assert "Gymnasium" in mail['TextBody']
            assert 'Montag, 29. Januar 2024' in mail['TextBody']
            assert "Anzahl:" in mail['TextBody']
            assert "Foobar" in mail['TextBody']
        if mail['To'] == "paul@example.org":
            raise AssertionError()


def test_reservation_ticket_new_note_sends_email(client):
    resources = ResourceCollection(client.app.libres_context)
    gymnasium = resources.add('Gymnasium', 'Europe/Zurich', type='room')
    dailypass = resources.add('Dailypass', 'Europe/Zurich', type='daypass')
    meeting = resources.add('Meeting', 'Europe/Zurich', type='room')

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        internal_notes=True,  # this sends email on new notes on the ticket
        resources=[
            gymnasium.id.hex,
            dailypass.id.hex,
            meeting.id.hex
        ]
    )

    add_reservation(
        gymnasium, client, datetime(2017, 1, 6, 12), datetime(2017, 1, 6, 16))
    transaction.commit()

    tickets = TicketCollection(client.app.session())
    assert tickets.query().count() == 1

    client.login_admin()

    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    page = page.click("Neue Notiz")
    page.form['text'] = "some note"
    page = page.form.submit().follow()

    assert "some note" in page
    assert len(os.listdir(client.app.maildir)) == 1

    mail = Path(client.app.maildir) / os.listdir(client.app.maildir)[0]
    with open(mail, 'r') as file:
        assert "some note" in file.read()
