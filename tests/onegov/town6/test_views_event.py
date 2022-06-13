import babel
import os
import transaction

from datetime import date, timedelta
from onegov.event import Event
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

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message['To'] == "test@example.org"
    assert ticket_nr in message['TextBody']

    # Make corrections
    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['description'] = "My event is exceptional."
    preview_page = form_page.form.submit().follow()
    assert "My event is exceptional." in preview_page

    session = client.app.session()
    event = session.query(Event).filter_by(title="My Event").one()
    event.meta['session_ids'] = []
    session.flush()
    transaction.commit()

    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['location'] = "A special place"
    preview_page = form_page.form.submit().follow()
    assert "A special place" in preview_page

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
    assert "My event is exceptional." in ticket_page
    assert "A special place" in ticket_page
    assert "The Organizer" in ticket_page
    assert "Ausstellung" in ticket_page
    assert "Bibliothek" in ticket_page
    assert "Veranstaltung bearbeitet" in ticket_page

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

    client.logout()

    # Make some more corrections
    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['organizer'] = "A carful organizer"
    preview_page = form_page.form.submit().follow()
    assert "My event is exceptional." in preview_page

    session = client.app.session()
    event = session.query(Event).filter_by(title="My Event").one()
    event.meta['session_ids'] = []
    session.flush()
    transaction.commit()

    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['title'] = "My special event"
    preview_page = form_page.form.submit().follow()
    assert "A special place" in preview_page

    # Publish event
    client.login_editor()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My special event" in client.get('/events')

    assert len(os.listdir(client.app.maildir)) == 2
    message = client.get_email(1)
    assert message['To'] == "test@example.org"
    message = message['TextBody']
    assert "My special event" in message
    assert "My event is exceptional." in message
    assert "A special place" in message
    assert "Ausstellung" in message
    assert "Bibliothek" in message
    assert "A carful organizer" in message
    assert "{} 18:00 - 22:00".format(
        start_date.strftime('%d.%m.%Y')) in message
    for days in range(5):
        assert (start_date + timedelta(days=days)).strftime('%d.%m.%Y') in \
            message
    assert "Ihre Veranstaltung wurde angenommen" in message

    # Close ticket
    ticket_page.click("Ticket abschliessen").follow()

    assert len(os.listdir(client.app.maildir)) == 3
    message = client.get_email(2)
    assert message['To'] == "test@example.org"
    assert "Ihre Anfrage wurde abgeschlossen" in message['TextBody']

    client.logout()

    # Make sure, no more corrections can be done
    confirmation_page = client.get(confirmation_page.request.url)
    assert "Ihr Anliegen wurde abgeschlossen" in confirmation_page
    assert "Bearbeiten Sie diese Veranstaltung." not in confirmation_page
    assert client.get(form_page.request.url, expect_errors=True).status_code \
        == 403
