from tempfile import TemporaryDirectory

import babel
import os
import transaction

from datetime import date, timedelta

from onegov.event import Event
from tests.onegov.town6.common import step_class
from unittest.mock import patch
from webtest import Upload

from tests.shared.utils import create_pdf


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_event_steps(broadcast, authenticate, connect, client):

    form_page = client.get('/events').click("Veranstaltung erfassen")
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

    assert connect.call_count == 1
    assert authenticate.call_count == 1
    assert broadcast.call_count == 1
    assert broadcast.call_args[0][3]['event'] == 'browser-notification'
    assert broadcast.call_args[0][3]['title'] == 'Neues Ticket'
    assert broadcast.call_args[0][3]['created']

    # Make corrections
    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['description'] = "My event is exceptional."
    form_page.form['organizer_email'] = "a@b.ch"
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
    assert "a@b.ch" in ticket_page

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
    form_page.form['organizer'] = "A careful organizer"
    form_page.form['organizer_phone'] = "079 123 45 56"
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
    assert "A careful organizer" in message
    assert "+41 79 123 45 56" in ticket_page
    assert "a@b.ch" in ticket_page
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


def test_create_events_directly(client):
    client.login_admin()
    form_page = client.get('/events').click("^Veranstaltung$")
    # As admin or editor, the progress indicator should not be displayed.
    # This only makes sense in the publishing process for visitors.
    assert 'progress-indicator' not in form_page

    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=4)

    # Fill out event
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Event"
    form_page.form['description'] = "My event is an event."
    form_page.form['location'] = "Location"
    form_page.form['organizer'] = "The Organizer"
    form_page.form['organizer_email'] = "a@b.ch"
    form_page.form['organizer_phone'] = "+41 41 123 45 67"
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

    events_redirect = form_page.form.submit().follow().follow()
    assert "Event 'My Event' erfolgreich erstellt" in events_redirect


def test_hide_event_submission_option(client):
    events_page = client.get('/events')
    assert "Veranstaltung erfassen" in events_page

    client.login_admin()
    settings = client.get('/event-settings')
    settings.form['submit_events_visible'] = False
    settings.form.submit()

    events_page = client.get('/events')
    assert "Veranstaltung erfassen" not in events_page

    settings.form['submit_events_visible'] = True
    settings.form.submit()

    events_page = client.get('/events')
    assert "Veranstaltung erfassen" in events_page


def test_view_occurrences_event_documents(client):
    page = client.get('/events')
    assert "Dokumente" not in page

    with (TemporaryDirectory() as td):
        client.login_admin()
        settings = client.get('/event-settings')
        filename_1 = os.path.join(td, 'zoo-programm-saison-2024.pdf')
        create_pdf(filename_1)
        settings.form.fields['event_files'][-1].value = [Upload(filename_1)]
        settings = settings.form.submit().follow()
        assert settings.status_code == 200

        settings = client.get('/event-settings')
        assert "Verknüpfte Datei" in settings
        assert "zoo-programm-saison-2024.pdf" in settings
        client.logout()

        page = client.get('/events')
        assert "Dokumente" in page
        assert "zoo-programm-saison-2024.pdf" in page


def test_view_occurrences_event_information(client):
    client.login_admin()
    settings = client.get('/event-settings')
    settings.form['event_header_html'] = (
        '<em>My <strong>bold</strong> Header</em>')
    settings.form['event_footer_html'] = (
        '<em>My\n<strong>bold</strong>\nFooter</em>')
    settings.form.submit()

    client.logout()

    page = client.get('/events')
    assert 'My bold Header' in page.pyquery('.event-header').text()
    assert 'My bold Footer' in page.pyquery('.event-footer').text()
