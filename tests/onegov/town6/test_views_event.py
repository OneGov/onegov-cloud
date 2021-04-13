from datetime import date, timedelta

import babel
from tests.onegov.town6.common import step_class


def test_event_steps(client):

    form_page = client.get('/events').click("Veranstaltung melden")
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=4)

    # Fill out event
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['description'] = "My event is an event."
    form_page.form['location'] = "Location"
    form_page.form['organizer'] = "The Organizer"
    form_page.form.set('tags', True, index=0)
    form_page.form.set('tags', True, index=1)
    form_page.form['start_date'] = start_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['end_date'] = end_date.isoformat()
    form_page.form['repeat'] = 'weekly'
    form_page.form.set('weekly', True, index=0)
    form_page.form.set('weekly', True, index=1)
    form_page.form.set('weekly', True, index=2)
    form_page.form.set('weekly', True, index=3)
    form_page.form.set('weekly', True, index=4)
    form_page.form.set('weekly', True, index=5)
    form_page.form.set('weekly', True, index=6)

    assert step_class(form_page, 1) == 'is-current'
    assert step_class(form_page, 2) == ''

    preview_page = form_page.form.submit().follow()
    assert "My Ewent" in preview_page
    assert "My event is an event." in preview_page
    assert "Location" in preview_page
    assert "Ausstellung" in preview_page
    assert "Bibliothek" in preview_page
    assert "The Organizer" in preview_page
    assert "{} 18:00 - 22:00".format(
        babel.dates.format_date(
            start_date, format='d. MMMM yyyy', locale='de'
        )
    ) in preview_page

    assert "Jeden Mo, Di, Mi, Do, Fr, Sa, So bis zum {}".format(
        end_date.strftime('%d.%m.%Y')
    ) in preview_page
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            preview_page

    assert step_class(preview_page, 1) == 'is-complete'
    assert step_class(preview_page, 2) == 'is-current'

    # Edit event
    form_page = preview_page.click("Bearbeiten", index=0)
    form_page.form['title'] = "My Event"
    assert step_class(form_page, 1) == 'is-complete'
    assert step_class(form_page, 2) == 'is-current'

    preview_page = form_page.form.submit().follow()

    assert "My Ewent" not in preview_page
    assert "My Event" in preview_page

    # Submit event
    confirmation_page = preview_page.form.submit().follow()

    assert "Vielen Dank für Ihre Eingabe!" in confirmation_page
    ticket_nr = confirmation_page.pyquery('.ticket-number').text()
    assert "EVN-" in ticket_nr
    assert "My Event" not in client.get('/events')

    assert step_class(confirmation_page, 1) == 'is-complete'
    assert step_class(confirmation_page, 2) == 'is-complete'
    assert step_class(confirmation_page, 3) == 'is-current'

    assert len(client.app.smtp.outbox) == 1
    message = client.app.smtp.outbox[0]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert ticket_nr in message

    assert "Zugriff verweigert" in preview_page.form.submit(expect_errors=True)

    # Accept ticket
    client.login_editor()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '1'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert ticket_nr in ticket_page
    assert "test@example.org" in ticket_page
    assert "My Event" in ticket_page
    assert "My event is an event." in ticket_page
    assert "Location" in ticket_page
    assert "The Organizer" in ticket_page
    assert "Ausstellung" in ticket_page
    assert "Bibliothek" in ticket_page

    assert "{} 18:00 - 22:00".format(
        babel.dates.format_date(
            start_date, format='d. MMMM yyyy', locale='de'
        )
    ) in ticket_page

    assert "Jeden Mo, Di, Mi, Do, Fr, Sa, So bis zum {}".format(
        end_date.strftime('%d.%m.%Y')
    ) in ticket_page
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            ticket_page

    # Publish event
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Event" in client.get('/events')

    assert len(client.app.smtp.outbox) == 2
    message = client.app.smtp.outbox[1]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "My event is an event." in message
    assert "Location" in message
    assert "Ausstellung" in message
    assert "Bibliothek" in message
    assert "The Organizer" in message
    assert "{} 18:00 - 22:00".format(
        start_date.strftime('%d.%m.%Y')) in message
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            message
    assert "Ihre Veranstaltung wurde angenommen" in message

    # Close ticket
    ticket_page.click("Ticket abschliessen").follow()

    assert len(client.app.smtp.outbox) == 3
    message = client.app.smtp.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')

    assert "Ihre Anfrage wurde abgeschlossen" in message
