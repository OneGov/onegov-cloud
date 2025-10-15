from __future__ import annotations

import babel.dates
import json
import os
import pytest
import transaction
import yaml
import xml.etree.ElementTree as ET

from datetime import datetime, date, timedelta
from onegov.event.models import Event
from tempfile import TemporaryDirectory
from tests.shared.utils import create_image, create_pdf
from tests.shared.utils import get_meta
from unittest.mock import patch
from webtest.forms import Upload


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import ExtendedResponse
    from unittest.mock import MagicMock
    from .conftest import Client


def etree_to_dict(
    root: ET.Element,
    node_name: str = ''
) -> list[dict[str, str | None]]:
    return [
        {
            item.tag: item.text
            for item in node
        }
        for node in root.iter(node_name)
    ]


def test_view_occurrences(client: Client) -> None:
    client.login_admin()
    settings = client.get('/event-settings')
    settings.form['event_locations'] = [
        "Gemeindesaal", "Sportanlage", "Turnhalle"
    ]
    settings.form.submit()
    client.logout()

    def events(query: str = '') -> list[str]:
        page = client.get(f'/events/?{query}')
        return [event.text for event in page.pyquery('h3 a')]

    def dates(query: str = '') -> list[date]:
        page = client.get(f'/events/?{query}')
        return [
            datetime.strptime(div.text, '%d.%m.%Y').date()
            for div in page.pyquery('.occurrence-date')
        ]

    def tags(query: str = '') -> set[str]:
        page = client.get(f'/events/?{query}')
        return {s.text.strip() for s in page.pyquery('.occurrence-tags span')}

    def as_json(query: str = '') -> Any:
        return client.get(f'/events/json?{query}').json

    def as_xml() -> list[dict[str, str | None]]:
        response = client.get('/events/xml')
        xml_string = response.body.decode('utf-8')
        root = ET.fromstring(xml_string)
        return etree_to_dict(root, 'event')

    assert len(events()) == 10
    assert len(events('page=1')) == 2
    assert dates() == sorted(dates())

    # Test OpenGraph tags
    page = client.get('/events')
    assert get_meta(page, 'og:description') == 'Veranstaltungen'
    assert not get_meta(page, 'og:image')

    # Test tags
    query = 'tags=Party'
    assert tags(query) == {"Party"}
    assert events(query) == ["150 Jahre Govikon"]

    query = 'tags=Politics'
    assert tags(query) == {"Politik"}
    assert events(query) == ["Generalversammlung"]

    query = 'tags=Sports'
    assert tags(query) == {"Sport"}
    assert len(events(query)) == 10
    assert set(events(query)) == {"Gemeinsames Turnen", "Fussballturnier"}

    query = 'tags=Politics&tags=Party'
    assert tags(query) == {"Party", "Politik"}
    assert len(events(query)) == 2
    assert set(events(query)) == {"150 Jahre Govikon", "Generalversammlung"}

    # Test locations
    query = 'locations=Sportanlage'
    assert sorted(events(query)) == ["150 Jahre Govikon", "Fussballturnier"]

    query = 'locations=Gemeindesaal&locations=Turnhalle'
    assert set(events(query)) == {"Gemeinsames Turnen", "Generalversammlung"}

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
    assert tags(query) == {"Sport"}
    assert min(dates(query)) == unique_dates[1]
    assert max(dates(query)) == unique_dates[-2]

    query = 'range=weekend'
    assert tags(query) == {"Party"}
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

    # Test xml
    assert len(as_xml()) == 12
    assert list(as_xml()[0].keys()) == ['id', 'title', 'tags', 'description',
                                        'start', 'end', 'location', 'price',
                                        'organizer', 'event_url',
                                        'organizer_email', 'organizer_phone',
                                        'modified']

    # Test iCal
    assert client.get('/events/').click(
        'Diese Termine exportieren').text.startswith('BEGIN:VCALENDAR')


def test_view_occurrences_event_filter(client: Client) -> None:
    """
    This test switches the application settings event filter type between
    'tags', 'filters' and 'tags_and_filters'
    """

    def events(query: str = '') -> list[str]:
        page = client.get(f'/events/?{query}')
        return [event.text for event in page.pyquery('h3 a')]

    def dates(query: str = '') -> list[date]:
        page = client.get(f'/events/?{query}')
        return [
            datetime.strptime(div.text, '%d.%m.%Y').date()
            for div in page.pyquery('.occurrence-date')
        ]

    def set_setting_event_filter_type(
        client: Client,
        event_filter_type: str
    ) -> None:
        client.login_admin()
        settings = client.get('/event-settings')
        settings.form['event_filter_type'] = event_filter_type
        settings.form.submit()
        assert client.app.org.event_filter_type == event_filter_type
        client.logout()

    def setup_event_filter(client: Client) -> None:
        assert client.login_admin()
        assert client.app.org.event_filter_type in ['filters',
                                                    'tags_and_filters']
        page = client.get('/events')
        page = page.click('Konfigurieren')
        page.form['definition'] = """
            My Special Filter *=
                [ ] A Filter
                [ ] B Filter
        """
        page.form['keyword_fields'].value = 'My Special Filter'
        assert page.form.submit()
        client.logout()

    def set_filter_on_event(client: Client) -> None:
        # set single filter on one event
        client.login_admin()
        page = (client.get('/events').click('Fussballturnier').
                click('Bearbeiten'))
        page.form['my_special_filter'] = ['B Filter']
        page.form.submit()
        client.logout()

    assert len(events()) == 10
    assert len(events('page=1')) == 2
    assert dates() == sorted(dates())

    # default: event filter type = 'tags'
    client.app.org.event_filter_type = 'tags'
    page = client.get('/events')
    assert '<h2>Schlagwort</h2>' in page
    assert 'My Special Filter' not in page
    assert 'A Filter' not in page
    assert 'B Filter' not in page

    # default: event filter type = 'filters'
    set_setting_event_filter_type(client, 'filters')
    setup_event_filter(client)
    set_filter_on_event(client)

    page = client.get('/events')
    assert '<h2>Schlagwort</h2>' not in page
    assert 'My Special Filter' in page
    assert 'A Filter' not in page
    assert 'B Filter' in page

    # default: event filter type = 'tags_and_filters'
    set_setting_event_filter_type(client, 'tags_and_filters')
    client.app.org.event_filter_type = 'tags_and_filters'
    page = client.get('/events')
    assert '<h2>Schlagwort</h2>' in page
    assert 'My Special Filter' in page
    assert 'A Filter' not in page
    assert 'B Filter' in page


def test_view_occurrences_event_documents(client: Client) -> None:
    page = client.get('/events')
    assert "Dokumente" not in page

    with (TemporaryDirectory() as td):
        client.login_admin()
        settings = client.get('/event-settings')
        filename_1 = os.path.join(td, 'zoo-programm-saison-2024.pdf')
        create_pdf(filename_1)
        settings.form.set('event_files', [Upload(filename_1)], -1)
        settings = settings.form.submit().follow()
        assert settings.status_code == 200

        settings = client.get('/event-settings')
        assert "Verknüpfte Datei" in settings
        assert "zoo-programm-saison-2024.pdf" in settings
        client.logout()

        page = client.get('/events')
        assert "Dokumente" in page
        assert "zoo-programm-saison-2024.pdf" in page


def test_many_filters(client: Client) -> None:
    assert client.login_admin()
    page = client.get('/event-settings')
    page.form['event_filter_type'] = 'filters'
    page.form.submit()
    page = client.get('/events')
    page = page.click('Konfigurieren')
    page.form['definition'] = """
        Weitere Filter =
            [ ] Gemeinde
            [ ] Schule
            [ ] Akrobatik
            [ ] American Football
            [ ] Angeln
            [ ] Aquacura
            [ ] Armbrustschiessen
            [ ] Badminton
            [ ] Ballett
            [ ] Baseball
            [ ] Basketball
            [ ] Bouldering
            [ ] Karate
            [ ] Ski
            [ ] Yoga
    """
    page.form['keyword_fields'].value = 'weitere_filter'
    page.form.submit()

    events = client.get('/events')
    assert "Mehr anzeigen" not in events

    event = events.click("Generalversammlung")
    form = event.click("Bearbeiten")
    for i in range(0, 15):
        form.form.set('weitere_filter', True, index=i)
    form.form.submit()

    events = client.get('/events')
    assert "Mehr anzeigen" in events


def test_view_occurrence(client: Client) -> None:
    events = client.get('/events')

    event = events.click("Generalversammlung")
    assert event.pyquery('h1.main-title').text() == "Generalversammlung"
    assert "Gemeindesaal" in event
    assert "Politik" in event
    assert "Alle Jahre wieder" in event
    assert len(
        event.pyquery('.monthly-view').attr['data-dates'].split(';')
    ) == 1
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

    assert event.click(
        'Diesen Termin exportieren'
    ).text.startswith('BEGIN:VCALENDAR')
    assert event.click(
        'Alle Termine exportieren'
    ).text.startswith('BEGIN:VCALENDAR')


def fill_event_form(
    form_page: ExtendedResponse,
    start_date: date,
    end_date: date,
    add_image: bool = False
) -> ExtendedResponse:

    form_page.form['email'] = "test@example.org"
    form_page.form['title'] = "My Ewent"
    form_page.form['description'] = "My event is an event."
    form_page.form['location'] = "Location"
    form_page.form['organizer'] = "The Organizer"
    form_page.form['organizer_email'] = "event@myevents.ch"
    form_page.form['organizer_phone'] = "076 987 65 43"
    form_page.form.set('tags', True, index=0)
    form_page.form.set('tags', True, index=1)
    form_page.form['start_date'] = start_date.isoformat()
    form_page.form['start_time'] = "18:00"
    form_page.form['end_time'] = "22:00"
    form_page.form['end_date'] = end_date.isoformat()
    if add_image:
        form_page.form['image'] = Upload('event.jpg', create_image().read())
    return form_page


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
@pytest.mark.parametrize('skip', [True, False])
def test_submit_event(
    broadcast: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    client: Client,
    skip: bool
) -> None:

    if skip:
        client.login_admin()
        settings = client.get('/ticket-settings')
        settings.form['tickets_skip_opening_email'] = ['EVN']
        settings.form.submit()
        client = client.spawn()

    form_page = client.get('/events').click("Veranstaltung erfassen")

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
    assert "event@myevents.ch" in preview_page
    assert "+41 76 987 65 43" in preview_page
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

    assert form_page.form['repeat'].value == 'weekly'
    for i in range(7):
        checkbox = form_page.form.fields['weekly'][i]
        assert checkbox.checked  # type: ignore[attr-defined]

    preview_page = form_page.form.submit().follow()

    assert "My Ewent" not in preview_page
    assert "My Event" in preview_page

    # Submit event
    confirmation_page = preview_page.form.submit().follow()
    if skip:
        assert len(os.listdir(client.app.maildir)) == 0
        return

    assert "Vielen Dank für Ihre Eingabe!" in confirmation_page
    ticket_nr = confirmation_page.pyquery('.ticket-number').text()
    assert "EVN-" in ticket_nr

    assert "My Event" not in client.get('/events')

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message is not None
    assert message['To'] == "test@example.org"
    assert ticket_nr in message['TextBody']

    assert connect.call_count == 1
    assert authenticate.call_count == 1
    assert broadcast.call_count == 1
    assert broadcast.call_args[0][3]['event'] == 'browser-notification'
    assert broadcast.call_args[0][3]['title'] == 'Neues Ticket'
    assert broadcast.call_args[0][3]['created']

    # Make corrections, switch from weekly to dates
    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['description'] = "My event is exceptional."
    form_page.form['repeat'] = 'dates'
    next_dates = [date.today() + timedelta(days=3),
                  date.today() + timedelta(days=6)]
    form_page.form['dates'] = json.dumps(
        {
            'values': [
                {'date': d.isoformat()} for d in next_dates
            ]
        }
    )
    preview_page = form_page.form.submit().follow()
    assert "My event is exceptional." in preview_page
    assert "Alle Termine" in preview_page
    assert start_date.strftime('%d.%m.%Y') in preview_page
    for d in next_dates:
        assert d.strftime('%d.%m.%Y') in preview_page

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
    client.login_supporter()

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
    assert "event@myevents.ch" in preview_page
    assert "+41 76 987 65 43" in preview_page
    assert "Ausstellung" in ticket_page
    assert "Bibliothek" in ticket_page
    assert "Veranstaltung bearbeitet" in ticket_page

    assert "{} 18:00 - 22:00".format(
        babel.dates.format_date(
            start_date, format='d. MMMM yyyy', locale='de'
        )
    ) in ticket_page
    for d in next_dates + [start_date]:
        assert d.strftime('%d.%m.%Y') in ticket_page

    client.logout()

    # Make some more corrections
    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['organizer'] = "A carful organizer"
    form_page.form['organizer_email'] = "info@myevents.ch"
    for d in next_dates + [start_date]:
        assert d.isoformat() in form_page
    preview_page = form_page.form.submit().follow()
    assert "My event is exceptional." in preview_page

    session = client.app.session()
    event = session.query(Event).filter_by(title="My Event").one()
    event.meta['session_ids'] = []
    session.flush()
    transaction.commit()

    form_page = confirmation_page.click("Bearbeiten Sie diese Veranstaltung.")
    form_page.form['title'] = "My special event"
    form_page.form['organizer_phone'] = "076 111 22 33"
    preview_page = form_page.form.submit().follow()
    assert "A special place" in preview_page

    # Publish event
    client.login_supporter()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()

    assert "My special event" in client.get('/events')

    assert len(os.listdir(client.app.maildir)) == 2
    message = client.get_email(1)
    assert message is not None
    assert message['To'] == "test@example.org"
    message_body = message['TextBody']
    assert "My special event" in message_body
    assert "My event is exceptional." in message_body
    assert "A special place" in message_body
    assert "Ausstellung" in message_body
    assert "Bibliothek" in message_body
    assert "A carful organizer" in message_body
    assert "info@myevents.ch" in preview_page
    assert "+41 76 111 22 33" in preview_page
    assert "{} 18:00 - 22:00".format(
        babel.dates.format_date(
            start_date, format='d. MMMM yyyy', locale='de'
        )
    ) in ticket_page
    for d in next_dates + [start_date]:
        assert d.strftime('%d.%m.%Y') in ticket_page
    assert "Ihre Veranstaltung wurde angenommen" in message

    # Close ticket
    ticket_page.click("Ticket abschliessen").follow()

    assert len(os.listdir(client.app.maildir)) == 3
    message = client.get_email(2)
    assert message is not None
    assert message['To'] == "test@example.org"
    assert "Ihre Anfrage wurde abgeschlossen" in message['TextBody']

    client.logout()

    # Make sure, no more corrections can be done
    confirmation_page = client.get(confirmation_page.request.url)
    assert "Ihr Anliegen wurde abgeschlossen" in confirmation_page
    assert "Bearbeiten Sie diese Veranstaltung." not in confirmation_page
    assert client.get(
        form_page.request.url,
        expect_errors=True
    ).status_code == 403


def test_edit_event(client: Client) -> None:

    # Submit and publish an event
    form_page = client.get('/events').click("Veranstaltung erfassen")
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


def test_delete_event(client: Client) -> None:

    # Submit and publish an event
    form_page = client.get('/events').click("Veranstaltung erfassen")
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

    client.login_supporter()
    editor = client.spawn()
    editor.login_editor()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket_page = ticket_page.click("Veranstaltung annehmen").follow()
    ticket_nr = ticket_page.pyquery('.ticket-number').text()

    assert "My Event" in editor.get('/events')

    # Try to delete a submitted event directly
    event_page = editor.get('/events').click("My Event")

    assert ("Diese Veranstaltung kann nicht gelöscht werden."
        ) in event_page.pyquery('a.delete-link')[0].values()

    # Test OpenGraph Tags
    assert get_meta(event_page, 'og:image:alt') == 'test.jpg'
    assert not get_meta(event_page, 'og:description')

    # Delete the event via the ticket
    delete_link = ticket_page.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    assert len(os.listdir(client.app.maildir)) == 3
    message = client.get_email(2)
    assert message is not None
    assert message['To'] == "test@example.org"
    message_body = message['TextBody']
    assert "My Event" in message_body
    assert "Ihre Veranstaltung musste leider abgelehnt werden" in message_body
    assert ticket_nr in message_body

    assert "My Event" not in client.get('/events')

    # Delete a non-submitted event
    event_page = editor.get('/events').click("Generalversammlung")
    assert ("Möchten Sie die Veranstaltung wirklich löschen?"
        ) in event_page.pyquery('a.delete-link')[0].values()

    delete_link = event_page.pyquery('a.delete-link').attr('ic-delete-from')
    editor.delete(delete_link)

    assert "Generalversammlung" not in editor.get('/events')


def test_import_export_events(client: Client) -> None:
    session = client.app.session()
    for event in session.query(Event):
        session.delete(event)
    transaction.commit()

    # Submit and publish an event
    page = client.get('/events').click("Veranstaltung erfassen")
    event_date = date.today() + timedelta(days=1)
    page.form['email'] = "sinfonieorchester@govikon.org"
    page.form['title'] = "Weihnachtssingen"
    page.form['description'] = "Das Govikoner Sinfonieorchester lädt ein."
    page.form['location'] = "Konzertsaal"
    page.form['price'] = "CHF 75.-"
    page.form['organizer'] = "Sinfonieorchester"
    page.form['organizer_email'] = "sinfonieorchester@govikon.org"
    page.form['organizer_phone'] = "+41 41 123 45 67"
    page.form['tags'] = ["Music", "Tradition"]
    page.form['start_date'] = event_date.isoformat()
    page.form['start_time'] = "18:00"
    page.form['end_time'] = "22:00"
    page.form['repeat'] = 'without'
    page.form.submit().follow().form.submit().follow()

    client.login_editor()

    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    page = page.click("Veranstaltung annehmen").follow()

    assert "Weihnachtssingen" in client.get('/events')
    assert "Music" in client.get('/events')
    assert "Tradition" in client.get('/events')

    # Export
    page = client.get('/events').click("Export")
    page.form['file_format'] = 'xlsx'
    page = page.form.submit()

    file = Upload(
        'file',
        page.body,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Import (Dry run)
    page = client.get('/events').click("Import")
    page.form['dry_run'] = True
    page.form['file'] = file
    page = page.form.submit()
    assert "1 Veranstaltungen werden importiert" in page
    assert session.query(Event).count() == 1

    # Import
    page = client.get('/events').click("Import")
    page.form['file'] = file
    page = page.form.submit().follow()
    assert "1 Veranstaltungen importiert" in page
    assert session.query(Event).count() == 2

    # Re-Import with clear
    page = client.get('/events').click("Import")
    page.form['file'] = file
    page.form['clear'] = True
    page = page.form.submit().follow()
    assert "1 Veranstaltungen importiert" in page
    assert session.query(Event).count() == 2

    events = session.query(Event).all()
    assert events[0].title == events[1].title
    assert events[0].description == events[1].description
    assert events[0].location == events[1].location
    assert events[0].price == events[1].price
    assert events[0].organizer == events[1].organizer
    assert events[0].organizer_email == events[1].organizer_email
    assert events[0].organizer_phone == events[1].organizer_phone
    assert events[0].tags == events[1].tags
    assert events[0].start == events[1].start
    assert events[0].end == events[1].end
    assert events[0].timezone == events[1].timezone
    assert {event.meta['submitter_email'] for event in events} == {
        'sinfonieorchester@govikon.org', 'editor@example.org'
    }


def test_import_export_events_with_custom_tags(client: Client) -> None:
    session = client.app.session()
    for event in session.query(Event):
        session.delete(event)
    transaction.commit()

    fs = client.app.filestorage
    assert fs is not None
    data = {
        'event_tags': ['Singing', 'Christmas']
    }
    with fs.open('eventsettings.yml', 'w') as f:
        yaml.dump(data, f)

    # Submit and publish an event
    page = client.get('/events').click("Veranstaltung erfassen")
    event_date = date.today() + timedelta(days=1)
    page.form['email'] = "sinfonieorchester@govikon.org"
    page.form['title'] = "Weihnachtssingen"
    page.form['description'] = "Das Govikoner Sinfonieorchester lädt ein."
    page.form['location'] = "Konzertsaal"
    page.form['price'] = "CHF 75.-"
    page.form['organizer'] = "Sinfonieorchester"
    page.form['organizer_email'] = "sinfonieorchester@govikon.org"
    page.form['organizer_phone'] = "+41 41 123 45 67"
    page.form['tags'] = ["Singing", "Christmas"]
    page.form['start_date'] = event_date.isoformat()
    page.form['start_time'] = "18:00"
    page.form['end_time'] = "22:00"
    page.form['repeat'] = 'without'
    page.form.submit().follow().form.submit().follow()

    client.login_editor()

    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    page = page.click("Veranstaltung annehmen").follow()

    assert "Weihnachtssingen" in client.get('/events')
    assert "Singing" in client.get('/events')
    assert "Christmas" in client.get('/events')

    # Export
    page = client.get('/events').click("Export")
    page.form['file_format'] = 'xlsx'
    page = page.form.submit()

    file = Upload(
        'file',
        page.body,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Import (Dry run)
    page = client.get('/events').click("Import")
    page.form['dry_run'] = True
    page.form['file'] = file
    page = page.form.submit()
    assert "1 Veranstaltungen werden importiert" in page
    assert session.query(Event).count() == 1

    # Import
    page = client.get('/events').click("Import")
    page.form['file'] = file
    page = page.form.submit().follow()
    assert "1 Veranstaltungen importiert" in page
    assert session.query(Event).count() == 2

    # Re-Import with clear
    page = client.get('/events').click("Import")
    page.form['file'] = file
    page.form['clear'] = True
    page = page.form.submit().follow()
    assert "1 Veranstaltungen importiert" in page
    assert session.query(Event).count() == 2

    events = session.query(Event).all()
    assert events[0].title == events[1].title
    assert events[0].description == events[1].description
    assert events[0].location == events[1].location
    assert events[0].price == events[1].price
    assert events[0].organizer == events[1].organizer
    assert events[0].organizer_email == events[1].organizer_email
    assert events[0].organizer_phone == events[1].organizer_phone
    assert events[0].tags == events[1].tags
    assert events[0].start == events[1].start
    assert events[0].end == events[1].end
    assert events[0].timezone == events[1].timezone
    assert {event.meta['submitter_email'] for event in events} == {
        'sinfonieorchester@govikon.org', 'editor@example.org'
    }


def test_event_form_with_custom_lead(client: Client) -> None:
    fs = client.app.filestorage
    assert fs is not None
    data = {
        'event_form_lead': 'A completely different lead text'
    }
    with fs.open('eventsettings.yml', 'w') as f:
        yaml.dump(data, f)

    page = client.get('/events').click("Veranstaltung erfassen")
    assert 'A completely different lead text' in page
