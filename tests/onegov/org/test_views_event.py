from datetime import datetime, date, timedelta

import babel.dates
import pytest

from tests.shared.utils import get_meta
from webtest.forms import Upload
from tests.shared.utils import create_image


def test_view_occurrences(client):
    client.login_admin()
    settings = client.get('/module-settings')
    settings.form['event_locations'] = [
        "Gemeindesaal", "Sportanlage", "Turnhalle"
    ]
    settings.form.submit()
    client.logout()

    def events(query=''):
        page = client.get(f'/events/?{query}')
        return [event.text for event in page.pyquery('h3 a')]

    def dates(query=''):
        page = client.get(f'/events/?{query}')
        return [
            datetime.strptime(div.text, '%d.%m.%Y').date()
            for div in page.pyquery('.occurrence-date')
        ]

    def tags(query=''):
        page = client.get(f'/events/?{query}')
        tags = [s.text.strip() for s in page.pyquery('.occurrence-tags span')]
        return list(set(tags))

    def as_json(query=''):
        return client.get(f'/events/json?{query}').json

    assert len(events()) == 10
    assert len(events('page=1')) == 2
    assert dates() == sorted(dates())

    # Test OpenGraph tags
    page = client.get('/events')
    assert get_meta(page, 'og:description') == 'Veranstaltungen'
    assert not get_meta(page, 'og:image')

    # Test tags
    query = 'tags=Party'
    assert tags(query) == ["Party"]
    assert events(query) == ["150 Jahre Govikon"]

    query = 'tags=Politics'
    assert tags(query) == ["Politik"]
    assert events(query) == ["Generalversammlung"]

    query = 'tags=Sports'
    assert tags(query) == ["Sport"]
    assert len(events(query)) == 10
    assert set(events(query)) == set(["Gemeinsames Turnen", "Fussballturnier"])

    query = 'tags=Politics&tags=Party'
    assert sorted(tags(query)) == ["Party", "Politik"]
    assert len(events(query)) == 2
    assert set(events(query)) == set(["150 Jahre Govikon",
                                      "Generalversammlung"])

    # Test locations
    query = 'locations=Sportanlage'
    assert sorted(events(query)) == ["150 Jahre Govikon", "Fussballturnier"]

    query = 'locations=Gemeindesaal&locations=Turnhalle'
    assert sorted(set(events(query))) == [
        "Gemeinsames Turnen", "Generalversammlung"
    ]

    query = 'locations=halle'
    assert events(query) == []

    # Test dates
    unique_dates = sorted(set(dates()))

    query = 'start={}'.format(unique_dates[1].isoformat())
    assert unique_dates[0] not in dates(query)

    query = 'end={}'.format(unique_dates[-2].isoformat())
    assert unique_dates[-1] not in dates(query)

    query = 'start={}&end={}'.format(unique_dates[1].isoformat(),
                                     unique_dates[-2].isoformat())
    assert unique_dates[0] not in dates(query)

    query = 'start={}&end={}'.format(unique_dates[1].isoformat(),
                                     unique_dates[-2].isoformat())
    assert unique_dates[-1] not in dates(query)

    query = 'start={}&end={}&tags=Sports'.format(
        unique_dates[1].isoformat(),
        unique_dates[-2].isoformat()
    )
    assert tags(query) == ["Sport"]
    assert min(dates(query)) == unique_dates[1]
    assert max(dates(query)) == unique_dates[-2]

    query = 'range=weekend'
    assert tags(query) == ["Party"]
    assert min(dates(query)) == unique_dates[0]
    assert max(dates(query)) == unique_dates[0]
    assert len(events(query)) == 1

    query = 'range=weekend&start={}'.format(unique_dates[-2].isoformat())
    assert len(events(query)) == 1

    # Test JSON
    assert len(as_json()) == 12
    assert len(as_json('max=3')) == 3
    assert len(as_json('cat1=Party')) == 1
    assert len(as_json('cat1=Party&cat2=Sportanlage')) == 1
    assert len(as_json('cat1=Politics')) == 1
    assert len(as_json('cat2=Gemeindesaal')) == 1
    assert len(as_json('cat2=saal')) == 0
    assert len(as_json('cat1=Sports')) == 10
    assert len(as_json('cat2=Turnhalle&cat2=Sportanlage')) == 11
    assert len(as_json('cat1=Politics&cat1=Party')) == 2
    assert len(as_json('max=1&cat1=Politics&cat1=Party')) == 1

    # Test iCal
    assert client.get('/events/').click('Diese Termine exportieren').\
        text.startswith('BEGIN:VCALENDAR')


def test_view_occurrence(client):
    events = client.get('/events')

    event = events.click("Generalversammlung")
    assert event.pyquery('h1.main-title').text() == "Generalversammlung"
    assert "Gemeindesaal" in event
    assert "Politik" in event
    assert "Alle Jahre wieder" in event
    assert len(event.pyquery('.monthly-view').attr['data-dates'].split(';')) \
        == 1
    assert len(event.pyquery('.calendar-export-list li')) == 1
    assert event.click('Diesen Termin exportieren').text.startswith(
        'BEGIN:VCALENDAR'
    )

    # Test meta tags
    assert get_meta(event, 'og:title') == 'Generalversammlung'
    assert get_meta(event, 'og:description') == 'Alle Jahre wieder.'
    assert not get_meta(event, 'og:image')

    event = events.click("Gemeinsames Turnen", index=0)
    assert event.pyquery('h1.main-title').text() == "Gemeinsames Turnen"
    assert "Turnhalle" in event
    assert "Sport" in event
    assert "fit werden" in event
    assert len(event.pyquery('.monthly-view').attr['data-dates'].split(';')) \
        == 9
    assert len(event.pyquery('.calendar-export-list li')) == 2

    assert event.click('Diesen Termin exportieren').\
        text.startswith('BEGIN:VCALENDAR')
    assert event.click('Alle Termine exportieren').\
        text.startswith('BEGIN:VCALENDAR')


def fill_event_form(form_page, start_date, end_date, add_image=False):
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
    if add_image:
        form_page.form['image'] = Upload('event.jpg', create_image().read())
    return form_page


@pytest.mark.skip('Re-enable if adding EVN to choices in ticket settings form')
@pytest.mark.parametrize('mute,mail_count', [(False, 1), (True, 0)])
def test_submit_event_auto_accept_no_emails(client, mute, mail_count):
    client.login_admin()
    settings = client.get('/ticket-settings')
    settings.form['ticket_auto_accepts'] = ['EVN']
    if mute:
        # this should even mute the accept confirmation email
        settings.form['mute_all_tickets'] = 'yes'
    settings.form.submit()
    anon = client.spawn()

    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=4)

    form_page = anon.get('/events').click("Veranstaltung melden")

    # Fill out event
    form_page = fill_event_form(form_page, start_date, end_date)
    preview_page = form_page.form.submit().follow()
    # Submit event
    confirmation_page = preview_page.form.submit().follow()

    assert 'Ihr Anliegen wurde abgeschlossen' in confirmation_page
    client.login_editor()
    page = client.get('/events')

    assert len(client.app.smtp.outbox) == mail_count
    if not mute:
        message = client.app.smtp.outbox[0]
        assert 'Ihre Veranstaltung wurde angenommen' in message.get('subject')

    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '1'
    assert "My Ewent" in page


@pytest.mark.parametrize('skip_opening_email', [True, False])
def test_submit_event(client, skip_opening_email):

    if skip_opening_email:
        client.login_admin()
        settings = client.get('/ticket-settings')
        settings.form['tickets_skip_opening_email'] = ['EVN']
        settings.form.submit()
        client = client.spawn()

    form_page = client.get('/events').click("Veranstaltung melden")

    assert "Das Formular enthält Fehler" in form_page.form.submit()

    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=4)

    # Fill out event
    form_page = fill_event_form(form_page, start_date, end_date)
    form_page.form['repeat'] = 'weekly'
    form_page.form.set('weekly', True, index=0)
    form_page.form.set('weekly', True, index=1)
    form_page.form.set('weekly', True, index=2)
    form_page.form.set('weekly', True, index=3)
    form_page.form.set('weekly', True, index=4)
    form_page.form.set('weekly', True, index=5)
    form_page.form.set('weekly', True, index=6)

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

    # Edit event
    form_page = preview_page.click("Bearbeiten", index=0)
    form_page.form['title'] = "My Event"

    preview_page = form_page.form.submit().follow()

    assert "My Ewent" not in preview_page
    assert "My Event" in preview_page

    # Submit event
    confirmation_page = preview_page.form.submit().follow()
    if skip_opening_email:
        assert len(client.app.smtp.outbox) == 0
        return

    assert "Vielen Dank für Ihre Eingabe!" in confirmation_page
    ticket_nr = confirmation_page.pyquery('.ticket-number').text()
    assert "EVN-" in ticket_nr

    assert "My Event" not in client.get('/events')

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


def test_edit_event(client):

    # Submit and publish an event
    form_page = client.get('/events').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['location'] = "Lokation"
    form_page.form['organizer'] = "Organixator"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['repeat'] = 'without'
    form_page.form.submit().follow().form.submit().follow()

    client.login_editor()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My Ewent" in client.get('/events')
    assert "Lokation" in client.get('/events')

    # Edit a submitted event
    event_page = client.get('/events').click("My Ewent")
    event_page = event_page.click("Bearbeiten")
    event_page.form['title'] = "My Event"
    event_page.form.submit().follow()

    assert "My Ewent" not in client.get('/events')
    assert "My Event" in client.get('/events')

    # Edit a submitted event via the ticket
    event_page = ticket_page.click("Veranstaltung bearbeiten")
    event_page.form['location'] = "Location"
    event_page.form.submit().follow()

    assert "Lokation" not in client.get('/events')
    assert "Location" in client.get('/events')

    # Edit a non-submitted event
    event_page = client.get('/events').click("150 Jahre Govikon")
    event_page = event_page.click("Bearbeiten")
    event_page.form['title'] = "Stadtfest"
    event_page.form.submit().follow()

    assert "150 Jahre Govikon" not in client.get('/events')
    assert "Stadtfest" in client.get('/events')


def test_delete_event(client):

    # Submit and publish an event
    form_page = client.get('/events').click("Veranstaltung melden")
    event_date = date.today() + timedelta(days=1)
    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Event"
    form_page.form['organizer'] = "Organizer"
    form_page.form['location'] = "Location"
    form_page.form['start_date'] = event_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['repeat'] = 'without'
    form_page.form['image'] = Upload('test.jpg', create_image().read())
    form_page.form.submit().follow().form.submit().follow()

    client.login_editor()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()
    ticket_nr = ticket_page.pyquery('.ticket-number').text()

    assert "My Event" in client.get('/events')

    # Try to delete a submitted event directly
    event_page = client.get('/events').click("My Event")

    assert "Diese Veranstaltung kann nicht gelöscht werden." in \
        event_page.pyquery('a.delete-link')[0].values()

    # Test OpenGraph Tags
    assert get_meta(event_page, 'og:image:alt') == 'test.jpg'
    assert not get_meta(event_page, 'og:description')

    # Delete the event via the ticket
    delete_link = ticket_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert len(client.app.smtp.outbox) == 3
    message = client.app.smtp.outbox[2]
    assert message.get('to') == "test@example.org"
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "My Event" in message
    assert "Ihre Veranstaltung musste leider abgelehnt werden" in message
    assert ticket_nr in message

    assert "My Event" not in client.get('/events')

    # Delete a non-submitted event
    event_page = client.get('/events').click("Generalversammlung")
    assert "Möchten Sie die Veranstaltung wirklich löschen?" in \
        event_page.pyquery('a.delete-link')[0].values()

    delete_link = event_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert "Generalversammlung" not in client.get('/events')
