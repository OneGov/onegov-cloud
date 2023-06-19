import os
from pathlib import Path

import transaction

from datetime import datetime
from onegov.core.request import CoreRequest
from onegov.org.models import ResourceRecipientCollection
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from tests.onegov.org.test_views_resources import add_reservation


def test_rejected_reservation_sends_email_to_configured_recipients(client,
                                                                   town_app):
    resources = ResourceCollection(client.app.libres_context)
    dailypass = resources.add('Dailypass', 'Europe/Zurich', type='daypass')

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        rejected_reservations=True,
        resources=[
            dailypass.id.hex,
        ]
    )

    add_reservation(
        dailypass, client, datetime(2017, 1, 6, 12), datetime(2017, 1, 6, 16))
    transaction.commit()

    tickets = TicketCollection(client.app.session())
    assert tickets.query().count() == 1

    client.login_admin()
    request = CoreRequest(
        environ={
            "wsgi.url_scheme": "https",
            "PATH_INFO": "/",
            "SERVER_NAME": "",
            "SERVER_PORT": "",
            "SERVER_PROTOCOL": "https",
            "HTTP_HOST": "localhost",
        }, app=town_app,
    )
    tickets = TicketCollection(client.app.session()).by_handler_code('RSV')
    assert len(tickets) == 1
    ticket = tickets[0]
    # The 'reject reservation' link is somehow not present in page for some
    # reason this is why we craft the link manually.
    crafted_link = request.link(ticket, 'reject')
    client.get(crafted_link)

    assert len(os.listdir(client.app.maildir)) == 1
    mail = Path(client.app.maildir) / os.listdir(client.app.maildir)[0]
    with open(mail, 'r') as file:
        mail_content = file.read()
        assert "Die folgenden Reservationen mussten leider abgesagt werden:" \
               in mail_content


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
        if mail['To'] == 'day@example.org':
            assert "Neue Reservation(en)" in mail['Subject']
            assert "Gymnasium" in mail['TextBody']
            assert "jessie@example.org" in mail['TextBody']
            assert "Foobar" in mail['TextBody']


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
