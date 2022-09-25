import os
import transaction

from datetime import datetime
from onegov.org.models import ResourceRecipientCollection
from onegov.reservation import ResourceCollection


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
