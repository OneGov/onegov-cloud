from __future__ import annotations

import onegov.feriennet
import os
import pytest
import re
import requests_mock
import transaction

from datetime import datetime, timedelta, date, time
from freezegun import freeze_time
from onegov.activity import Booking, BookingPeriodInvoice, ActivityInvoiceItem
from onegov.activity.utils import generate_xml
from onegov.core.custom import json
from onegov.feriennet.utils import NAME_SEPARATOR
from onegov.file import FileCollection
from onegov.gis import Coordinates
from onegov.pay import Payment
from psycopg2.extras import NumericRange
from sedate import utcnow
from tests.shared import utils
from unittest.mock import patch
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models.booking import BookingState
    from tests.shared.client import ExtendedResponse
    from unittest.mock import MagicMock
    from .conftest import Client, Scenario


def test_wwf_fixed_pass_system(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        title='WWF Period',
        phase='wishlist',
        active=True,
        confirmable=True,
        finalizable=True,
    )
    # Add booking user
    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=True
    )
    scenario.add_attendee(name='George', username='member@example.org')

    # Add activities
    tags = ['Familienlager', 'Ferienlager']
    scenario.add_activity(title='Surfing', state='accepted', tags=[tags[1]])
    scenario.add_occasion(cost=250)
    scenario.add_activity(title='Sailing', state='accepted', tags=[tags[1]])
    scenario.add_occasion(cost=500)
    scenario.add_activity(title='Fishing', state='accepted', tags=[tags[0]])
    scenario.add_occasion(cost=50)

    scenario.commit()
    scenario.refresh()

    admin = client
    admin.login_admin()

    # Edit the period
    fixed_system_limit = 1
    page = admin.get('/periods').click('Bearbeiten')
    page.form['pass_system'] = 'fixed'
    page.form['fixed_system_limit'] = fixed_system_limit
    page.form['single_booking_cost'] = 11
    page.form.submit().follow()

    scenario.refresh()
    period = scenario.latest_period
    assert period is not None
    booking_start = period.booking_start
    assert period.all_inclusive is False
    assert period.max_bookings_per_attendee == 1
    assert period.booking_cost == 11
    assert period.pay_organiser_directly is False

    def login_member(client: Client) -> Client:
        login = client.get('/').click("Anmelden", index=1)
        login.form['username'] = 'member@example.org'
        login.form['password'] = 'hunter2'
        login.form.submit().follow()
        return client

    member = login_member(client.spawn())

    activities = member.get('/activities')

    def register_for_activity(name: str) -> ExtendedResponse:
        # Register the first attendee available
        page = activities.click(name).click('Anmelden').form.submit().follow()
        assert 'Durchführung wurde zu Georges Wunschliste hinzugefügt' in page
        return page

    register_for_activity('Sailing')
    page = register_for_activity('Fishing')

    # We check his wishlist
    wishlist = page.click('Wunschliste')

    # We do not want a link to the limit view of the attendee
    assert not wishlist.pyquery('div.booking-limit a')

    book_limit_text = wishlist.pyquery('div.booking-limit span')[0].text
    assert book_limit_text == f'Limitiert auf {fixed_system_limit} Buchungen'

    page = admin.get('/matching')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'y'
    page = page.form.submit()
    assert 'Die Zuteilung wurde erfolgreich abgeschlossen' in page

    # confirm period, proceed to booking phase
    with freeze_time(booking_start + timedelta(days=1)):
        page = member.get('/my-bookings')
        assert 'Die Buchungsphase ist jetzt bis am' in page
        assert 'Gebucht (1)' in page
        assert 'Blockiert (1)' in page


def test_view_permissions() -> None:
    utils.assert_explicit_permissions(
        onegov.feriennet, onegov.feriennet.FeriennetApp)


def test_view_hint_max_activities(client: Client, scenario: Scenario) -> None:
    client.login_admin()

    scenario.add_period(
        title='Testperiod',
        active=True,
        confirmable=True,
        finalizable=True,
        max_bookings_per_attendee=4,
    )
    scenario.commit()
    scenario.refresh()

    page = client.get('/')
    page = page.click('Wunschliste')
    assert "Teilnehmende werden in bis zu 4 Angebot(e) eingeteilt." in page
    assert "bis zu 4 Angebot(e) angemeldet werden." not in page

    period_settings = client.get('/periods')
    period_settings.click('Deaktivieren')

    scenario.add_period(
        title='Testperiod2',
        active=True,
        confirmable=False,
        finalizable=True,
        max_bookings_per_attendee=4,
    )
    scenario.commit()
    scenario.refresh()

    page = client.get('/')
    page = page.click('Wunschliste')
    assert "bis zu 4 Angebot(e) angemeldet werden." in page
    assert "Teilnehmende werden in bis zu 4 Angebot(e) eingeteilt." not in page


def test_activity_permissions(client: Client, scenario: Scenario) -> None:
    anon = client.spawn()
    admin = client.spawn()
    editor = client.spawn()

    admin.login_admin()
    editor.login_editor()

    scenario.add_period()
    scenario.add_activity(
        title="Learn How to Program",
        username='editor@example.org'
    )
    scenario.add_occasion()
    scenario.commit()

    url = '/activity/learn-how-to-program'

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities/json')
    assert "Learn How to Program" not in editor.get('/activities/json')
    assert "Learn How to Program" not in admin.get('/activities/json')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)

    editor.get(url).click("Publikation beantragen")

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities/json')
    assert "Learn How to Program" not in editor.get('/activities/json')
    assert "Learn How to Program" not in admin.get('/activities/json')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket.click("Veröffentlichen")

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert "Learn How to Program" in anon.get('/activities/json')
    assert "Learn How to Program" in editor.get('/activities/json')
    assert "Learn How to Program" in admin.get('/activities/json')
    assert editor.get(url, status=200)
    assert anon.get(url, status=200)
    assert admin.get(url, status=200)

    ticket = admin.get(ticket.request.url)
    ticket.click("Archivieren")

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities/json')
    assert "Learn How to Program" not in editor.get('/activities/json')
    assert "Learn How to Program" not in admin.get('/activities/json')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_activity_communication(
    broadcast: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period()
    scenario.add_activity(
        title="Learn Python",
        lead="Using a Raspberry Pi we will learn Python",
        username='editor@example.org'
    )
    scenario.add_occasion()
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()

    editor = client.spawn()
    editor.login_editor()

    editor.get('/activity/learn-python').click("Publikation beantragen")

    assert len(os.listdir(client.app.maildir)) == 1
    assert "Ihre Anfrage wurde unter der " \
           "folgenden Referenz registriert" in admin.get_email(0)['HtmlBody']

    assert connect.call_count == 1
    assert authenticate.call_count == 1
    assert broadcast.call_count == 1
    assert broadcast.call_args[0][3]['event'] == 'browser-notification'
    assert broadcast.call_args[0][3]['title'] == 'Neues Ticket'
    assert broadcast.call_args[0][3]['created']

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Learn Python" in ticket

    ticket.click("Veröffentlichen")
    assert len(os.listdir(client.app.maildir)) == 2

    message = admin.get_email(1)['TextBody']
    assert "wurde veröffentlicht" in message
    assert "Learn Python" in message
    assert "Using a Raspberry Pi we will learn Python" in message


def test_basic_search(client_with_fts: Client) -> None:
    client = client_with_fts
    anom = client.spawn()

    # basic test
    assert 'Resultate' in client.get('/search?q=test')
    assert client.get('/search/suggest?q=test').json == []
    assert 'Resultate' in anom.get('/search?q=test')
    assert anom.get('/search/suggest?q=test').json == []


def test_activity_search(client_with_fts: Client, scenario: Scenario) -> None:
    client = client_with_fts

    scenario.add_period()
    scenario.add_activity(
        title="Learn How to Program",
        lead="Using a Raspberry Pi we will learn Python",
        username='editor@example.org'
    )
    scenario.add_occasion()
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()

    editor = client.spawn()
    editor.login_editor()

    # in preview, activities can't be found
    assert 'search-result-activities' not in admin.get('/search?q=Learn')
    assert 'search-result-activities' not in editor.get('/search?q=Learn')
    assert 'search-result-activities' not in client.get('/search?q=Learn')

    url = '/activity/learn-how-to-program'
    editor.get(url).click("Publikation beantragen")

    # once proposed, activities can be found by the admin only
    assert 'search-result-activities' in admin.get('/search?q=Learn')
    assert 'search-result-activities' not in editor.get('/search?q=Learn')
    assert 'search-result-activities' not in client.get('/search?q=Learn')

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket.click("Veröffentlichen")

    # once accepted, activities can be found by anyone
    assert 'search-result-activities' in admin.get('/search?q=Learn')
    assert 'search-result-activities' in editor.get('/search?q=Learn')
    assert 'search-result-activities' in client.get('/search?q=Learn')

    ticket = admin.get(ticket.request.url)
    ticket.click("Archivieren")

    # archived the search will fail again, except for admins
    assert 'search-result-activities' in admin.get('/search?q=Learn')
    assert 'search-result-activities' not in editor.get('/search?q=Learn')
    assert 'search-result-activities' not in client.get('/search?q=Learn')


@pytest.mark.skip('Activities work differently now, skip for now')
def test_activity_filter_tags(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        prebooking_start=datetime(2015, 1, 1),
        prebooking_end=datetime(2015, 12, 31),
        booking_start=datetime(2015, 12, 31),
        booking_end=datetime(2015, 12, 31),
        execution_start=datetime(2016, 1, 1),
        execution_end=datetime(2016, 12, 31)
    )

    scenario.add_activity(
        title="Learn How to Program",
        lead="Using a Rasperry Pi we will learn Python",
        tags=['Computer', 'Science'],
        username='editor@example.org'
    ).propose().accept()

    scenario.add_activity(
        title="Learn How to Cook",
        lead="Using a Stove we will cook a Python",
        tags=['Cooking', 'Science'],
        username='editor@example.org'
    ).propose().accept()

    scenario.commit()

    editor = client.spawn()
    editor.login_editor()

    admin = client.spawn()
    admin.login_admin()

    # only show activites to anonymous if there's an active period..
    page = client.get('/activities')
    assert "Keine Angebote" in page

    # ..and if there are any occasions for those activities
    with scenario.update():
        for activity in scenario.activities:
            scenario.add_occasion(
                activity=activity,
                start=datetime(2016, 1, 1, 10),
                end=datetime(2016, 1, 1, 18)
            )

    page = client.get('/activities')
    assert "Learn How to Cook" in page
    assert "Learn How to Program" in page

    page = client.get('/activities?filter=tags%3AComputer')
    assert "Learn How to Cook" not in page
    assert "Learn How to Program" in page

    page = page.click('Computer')
    assert "Learn How to Cook" in page
    assert "Learn How to Program" in page

    page = page.click('Kochen')
    assert "Learn How to Cook" in page
    assert "Learn How to Program" not in page

    page = page.click('Computer')
    assert "Learn How to Cook" in page
    assert "Learn How to Program" in page

    page = page.click('Computer')
    page = page.click('Kochen')
    page = page.click('Wissenschaft')
    assert "Learn How to Cook" in page
    assert "Learn How to Program" in page

    # the state filter works for editors
    new = editor.get('/activities').click("Angebot erfassen")
    new.form['title'] = "Learn How to Dance"
    new.form['lead'] = "We will dance with a Python"
    new.form.submit()

    # editors see the state as a filter
    assert "Vorschau" in editor.get('/activities')

    # anonymous does not
    assert "Vorschau" not in client.get('/activities')

    page = editor.get('/activities').click('Vorschau')
    assert "Learn How to Cook" not in page
    assert "Learn How to Program" not in page
    assert "Learn How to Dance" in page

    # anyone can filter by week, only weeks with activites are shown
    assert "04.01.2016 - 10.01.2016" not in page
    assert "01.01.2016 - 03.01.2016" in page

    page = editor.get('/activities').click('01.01.2016 - 03.01.2016', index=0)
    assert "Learn How to Cook" in page


def test_activity_filter_duration(client: Client, scenario: Scenario) -> None:
    scenario.add_period()

    # the retreat lasts a weekend
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
    )

    # the meeting lasts half a day
    scenario.add_activity(title="Meeting", state='accepted')
    scenario.add_occasion(
        start=datetime(2016, 10, 10, 8),
        end=datetime(2016, 10, 10, 12),
    )

    scenario.commit()

    half_day = client.get('/activities?filter=durations%3A1')
    many_day = client.get('/activities?filter=durations%3A4')

    assert "Meeting" in half_day
    assert "Retreat" not in half_day

    assert "Meeting" not in many_day
    assert "Retreat" in many_day

    # shorten the retreat
    with scenario.update():
        scenario.occasions[0].dates[0].end -= timedelta(days=1)

    full_day = client.get('/activities?filter=durations%3A2')
    many_day = client.get('/activities?filter=durations%3A4')

    assert "Retreat" in full_day
    assert "Retreat" not in many_day


def test_activity_filter_weeks(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        prebooking_start=datetime(2022, 2, 1),
        prebooking_end=datetime(2022, 2, 28),
        booking_start=datetime(2022, 3, 1),
        booking_end=datetime(2022, 3, 31),
        execution_start=datetime(2022, 4, 1),
        execution_end=datetime(2022, 4, 30)
    )

    scenario.add_activity(title="Camping", state='accepted')
    scenario.add_occasion(
        start=datetime(2022, 4, 4, 8),
        end=datetime(2022, 4, 21, 12),
    )

    scenario.commit()

    page = client.get('/activities')

    # test if all weeks are in the filter, not just the first
    assert "04.04.2022 - 10.04.2022" in page
    assert "11.04.2022 - 17.04.2022" in page
    assert "18.04.2022 - 24.04.2022" in page


def test_activity_filter_age_ranges(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period()

    # the retreat is for really young kids
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion(age=(0, 10))

    # the meeting is for young to teenage kids
    scenario.add_activity(title="Meeting", state='accepted')
    scenario.add_occasion(age=(5, 15))

    scenario.commit()

    preschool = client.get('/activities?filter=age_ranges%3A5-5')
    highschool = client.get('/activities?filter=age_ranges%3A15-15')

    assert "Retreat" in preschool
    assert "Meeting" in preschool

    assert "Retreat" not in highschool
    assert "Meeting" in highschool

    # change the meeting age
    with scenario.update():
        scenario.occasions[1].age = NumericRange(15, 20)  # type: ignore[assignment]

    preschool = client.get('/activities?filter=age_ranges%3A5-5')

    assert "Retreat" in preschool
    assert "Meeting" not in preschool


def test_organiser_info(client: Client, scenario: Scenario) -> None:

    admin = client.spawn()
    admin.login_admin()

    editor = client.spawn()
    editor.login_editor()

    scenario.add_period()
    scenario.add_activity(
        title="Play with Legos",
        state='accepted',
        username='editor@example.org'
    )
    scenario.add_activity(
        title="Play with Playmobil",
        state='accepted',
        username='admin@example.org'
    )
    scenario.commit()

    # by default no information is shown
    for id in ('play-with-legos', 'play-with-playmobil'):
        # except the name, which is already set in the test scenario
        assert len(editor.get(f'/activity/{id}').pyquery('.organiser li')) == 1
        assert len(admin.get(f'/activity/{id}').pyquery('.organiser li')) == 1

    # owner changes are reflected on the activity
    contact = editor.get('/userprofile')
    contact.form['salutation'] = 'mr'
    contact.form['first_name'] = 'Ed'
    contact.form['last_name'] = 'Itor'
    contact.form['organisation'] = 'Editors Association'
    contact.form['address'] = 'K Street'
    contact.form['zip_code'] = '20001'
    contact.form['place'] = 'Washington'
    contact.form['email'] = 'editors-association@example.org'
    contact.form['phone'] = '+41234567890'
    contact.form['website'] = 'https://www.example.org'
    contact.form['emergency'] = '+01 234 56 78 (Peter)'
    contact.form.submit()

    activity = editor.get('/activity/play-with-legos')

    assert "Editors Association" in activity
    assert "Ed\u00A0Itor" in activity
    assert "Washington" not in activity
    assert "20001" not in activity
    assert "K Street" not in activity
    assert "editors-association@example.org" not in activity
    assert "+41 23 456 789" not in activity
    assert "https://www.example.org" in activity

    # admin changes are reflected on the activity
    contact = (
        admin.get('/usermanagement')
        .click('Veranstalter')
        .click('Ansicht')
        .click('Bearbeiten')
    )

    contact.form['organisation'] = 'Admins Association'
    contact.form.submit()

    activity = editor.get('/activity/play-with-legos')

    assert "Admins Association" in activity

    # we can show/hide information individually
    def with_public_organiser_data(values: list[str]) -> ExtendedResponse:
        page = admin.get('/feriennet-settings')
        page.form['public_organiser_data'] = values
        page.form.submit()

        return editor.get('/activity/play-with-legos')

    page = with_public_organiser_data([])
    assert 'Veranstalter' not in page

    page = with_public_organiser_data(['name'])
    assert "Admins Association" in page
    assert "Washington" not in page
    assert "editors-association@example.org" not in page
    assert "+41 23 456 789" not in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['address'])
    assert "Admins Association" not in page
    assert "Washington" in page
    assert "editors-association@example.org" not in page
    assert "+41 23 456 78 90" not in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['email'])
    assert "Admins Association" not in page
    assert "Washington" not in page
    assert "editors-association@example.org" in page
    assert "+41 23 456 78 90" not in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['phone'])
    assert "Admins Association" not in page
    assert "Washington" not in page
    assert "editors-association@example.org" not in page
    assert "+41 23 456 78 90" in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['website'])
    assert "Admins Association" not in page
    assert "Washington" not in page
    assert "editors-association@example.org" not in page
    assert "+41 23 456 78 90" not in page
    assert "https://www.example.org" in page


def test_occasions_form(client: Client, scenario: Scenario) -> None:

    editor = client.spawn()
    editor.login_editor()

    admin = client.spawn()
    admin.login_admin()

    scenario.add_period(
        prebooking_start=date(2016, 9, 1),
        prebooking_end=date(2016, 9, 30),
        booking_start=date(2016, 9, 30),
        booking_end=date(2016, 9, 30),
        execution_start=date(2016, 10, 1),
        execution_end=date(2016, 10, 31),
    )

    scenario.add_activity(
        title="Play with Legos",
        username='editor@example.org'
    )

    scenario.commit()

    activity = editor.get('/activities').click("Play with Legos")
    assert "keine Durchführungen" in activity

    occasion = activity.click("Neue Durchführung")
    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-10-04 10:00:00',
            'end': '2016-10-04 12:00:00'
        }]
    })
    # test submitting empty, form ensurances must cope with missing data
    occasion.form.submit()

    occasion.form['meeting_point'] = "Franz Karl Weber"
    occasion.form['note'] = "No griefers"
    occasion.form['min_age'] = 10
    occasion.form['max_age'] = 20
    occasion.form['min_spots'] = 30
    occasion.form['max_spots'] = 40
    activity = occasion.form.submit().follow()

    assert "keine Durchführungen" not in activity
    assert "4. Oktober 10:00 - 12:00" in activity
    assert "10 - 20 Jahre" in activity
    assert "30 - 40 Teilnehmende" in activity
    assert "Franz Karl Weber" in activity
    assert "No griefers" in activity

    occasion = activity.click("Bearbeiten", index=1)
    occasion.form['min_age'] = 15
    activity = occasion.form.submit().follow()
    assert "15 - 20 Jahre" in activity

    occasion = activity.click("Duplizieren")
    occasion.form['min_age'] = 10
    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-10-04 13:00:00',
            'end': '2016-10-04 15:00:00'
        }]
    })
    activity = occasion.form.submit().follow()
    assert "15 - 20 Jahre" in activity
    assert "10 - 20 Jahre" in activity

    activity.click("Löschen", index=0)
    activity.click("Löschen", index=1)

    assert "keine Durchführungen" in editor.get('/activity/play-with-legos')


def test_multiple_dates_occasion(client: Client, scenario: Scenario) -> None:

    editor = client.spawn()
    editor.login_editor()

    admin = client.spawn()
    admin.login_admin()

    scenario.add_period(
        prebooking_start=date(2016, 9, 1),
        prebooking_end=date(2016, 9, 30),
        booking_start=date(2016, 9, 30),
        booking_end=date(2016, 9, 30),
        execution_start=date(2016, 10, 1),
        execution_end=date(2016, 10, 31),
    )

    scenario.add_activity(
        title="Play with Legos",
        username='editor@example.org'
    )

    scenario.commit()

    activity = editor.get('/activities').click("Play with Legos")
    assert "keine Durchführungen" in activity

    occasion = activity.click("Neue Durchführung")
    occasion.form['meeting_point'] = "Franz Karl Weber"
    occasion.form['note'] = "No griefers"
    occasion.form['min_age'] = 10
    occasion.form['max_age'] = 20
    occasion.form['min_spots'] = 30
    occasion.form['max_spots'] = 40

    occasion.form['dates'] = ""
    assert "mindestens ein Datum" in occasion.form.submit()

    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-10-04 10:00:00',
            'end': '2016-10-04 12:00:00'
        }, {
            'start': '2016-10-04 10:00:00',
            'end': '2016-10-04 12:00:00'
        }]
    })
    assert "mit einem anderen Datum" in occasion.form.submit()

    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-10-01 10:00:00',
            'end': '2016-10-01 12:00:00'
        }, {
            'start': '2016-10-02 10:00:00',
            'end': '2016-10-02 12:00:00'
        }]
    })

    activity = occasion.form.submit().follow()
    assert "1. Oktober 10:00" in activity
    assert "2. Oktober 10:00" in activity


def test_execution_period(client: Client, scenario: Scenario) -> None:

    admin = client.spawn()
    admin.login_admin()

    scenario.add_period(
        prebooking_start=date(2016, 9, 1),
        prebooking_end=date(2016, 9, 30),
        booking_start=date(2016, 9, 30),
        booking_end=date(2016, 9, 30),
        execution_start=date(2016, 10, 1),
        execution_end=date(2016, 10, 1),
    )

    scenario.add_activity(
        title="Play with Lego",
        username='editor@example.org'
    )

    scenario.commit()

    occasion = admin.get('/activity/play-with-lego').click("Neue Durchführung")
    occasion.form['min_age'] = 10
    occasion.form['max_age'] = 20
    occasion.form['min_spots'] = 30
    occasion.form['max_spots'] = 40
    occasion.form['meeting_point'] = 'At the venue'

    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-10-01 00:00:00',
            'end': '2016-10-02 23:59:59'
        }]
    })
    assert "Datum liegt ausserhalb" in occasion.form.submit()

    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-09-30 00:00:00',
            'end': '2016-10-01 23:59:59'
        }]
    })
    assert "Datum liegt ausserhalb" in occasion.form.submit()

    occasion.form['dates'] = json.dumps({
        'values': [{
            'start': '2016-10-01 00:00:00',
            'end': '2016-10-01 23:59:59'
        }]
    })
    assert "Änderungen wurden gespeichert" in occasion.form.submit().follow()

    period = admin.get('/periods').click("Bearbeiten")
    period.form['execution_start'] = '2016-10-02'
    period.form['execution_end'] = '2016-10-02'
    period = period.form.submit()

    assert "in Konflikt" in period
    assert "Play with Lego" in period

    period.form['execution_start'] = '2016-10-01'
    period.form['execution_end'] = '2016-10-01'
    periods = period.form.submit().follow()

    assert "gespeichert" in periods


@pytest.mark.skip_night_hours
def test_enroll_child(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        prebooking_end=scenario.date_offset(0)
    )
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion()
    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=False
    )
    scenario.commit()

    activity = client.get('/activity/retreat')

    login = activity.click("Anmelden", index=1)
    login.form['username'] = 'member@example.org'
    login.form['password'] = 'hunter2'
    enroll = login.form.submit().follow()
    assert "Ihr Benutzerprofil ist unvollständig" in enroll

    # now that we're logged in, the login link automatically skips ahead
    enroll = activity.click("Anmelden", index=1).follow()
    assert "Teilnehmende anmelden" in enroll

    # the link changes, but the result stays the same
    enroll = client.get('/activity/retreat').click("Anmelden")
    assert "Teilnehmende anmelden" in enroll

    enroll.form['first_name'] = "Tom"
    enroll.form['last_name'] = "Sawyer"
    enroll.form['birth_date'] = "2012-01-01"
    enroll.form['gender'] = 'male'
    enroll = enroll.form.submit()

    # before continuing, the user needs to fill his profile
    assert "Ihr Benutzerprofil ist unvollständig" in enroll
    client.fill_out_profile()

    activity = enroll.form.submit().follow()
    assert "zu Tom\u00A0Sawyers Wunschliste hinzugefügt" in activity

    # prevent double-subscriptions
    enroll = activity.click("Anmelden")
    assert "Tom\u00A0Sawyer hat sich bereits für diese Durchführung" in (
        enroll.form.submit())

    enroll.form['attendee'] = 'other'
    enroll.form['first_name'] = "Tom"
    enroll.form['last_name'] = "Sawyer"
    enroll.form['birth_date'] = "2011-01-01"
    enroll.form['gender'] = 'male'

    # prevent adding two kids with the same name
    assert "Sie haben bereits eine Person mit diesem Namen erfasst" in (
        enroll.form.submit())

    # prevent enrollment for inactive periods
    assert scenario.latest_period is not None
    with scenario.update():
        scenario.latest_period.active = False

    enroll.form['first_name'] = "Huckleberry"
    enroll.form['last_name'] = "Finn"
    assert "Diese Durchführung liegt ausserhalb des aktiven Zeitraums" in (
        enroll.form.submit())

    # prevent enrollment outside of prebooking
    with scenario.update():
        scenario.latest_period.active = True
        scenario.latest_period.prebooking_start -= timedelta(days=10)
        scenario.latest_period.prebooking_end -= timedelta(days=10)

    assert "nur während der Wunschphase" in enroll.form.submit()

    # set the record straight again and test it on the edge
    with scenario.update():
        scenario.latest_period.prebooking_start += timedelta(days=10)
        scenario.latest_period.prebooking_end += timedelta(days=10)

    enroll.form['first_name'] = "Huckleberry"
    enroll.form['last_name'] = "Finn"
    activity = enroll.form.submit().follow()

    assert "zu Huckleberry\u00A0Finns Wunschliste hinzugefügt" in activity

    # prevent booking over the limit
    with scenario.update():
        scenario.latest_period.all_inclusive = True
        scenario.latest_period.max_bookings_per_attendee = 1
        scenario.latest_period.confirm_and_start_booking_phase()

        scenario.add_activity(title="Another Retreat", state='accepted')
        scenario.add_occasion()

    enroll = client.get('/activity/another-retreat').click("Anmelden")
    enroll.form.submit()

    assert "maximale Anzahl von 1 Buchungen" in enroll.form.submit()


def test_enroll_age_mismatch(client: Client, scenario: Scenario) -> None:
    scenario.add_period()
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion(age=(5, 10))
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()
    admin.fill_out_profile()

    page = admin.get('/activity/retreat').click("Anmelden")
    page.form['first_name'] = "Tom"
    page.form['last_name'] = "Sawyer"
    page.form['gender'] = 'male'

    page.form['birth_date'] = "1900-01-01"
    assert "zu alt" in page.form.submit()

    page.form['birth_date'] = f"{date.today().year - 3}-01-01"
    assert "zu jung" in page.form.submit()

    page.form['ignore_age'] = True
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()


def test_enroll_after_wishlist_phase(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period()
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion()
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()
    admin.fill_out_profile()

    page = admin.get('/activity/retreat').click("Anmelden")
    page.form['first_name'] = "Tom"
    page.form['last_name'] = "Sawyer"
    page.form['gender'] = 'male'
    page.form['birth_date'] = "2015-01-01"
    page.form['ignore_age'] = True

    with freeze_time(datetime.now() + timedelta(days=2)):
        assert "nur während der Wunschphase" in page.form.submit()


def test_booking_view(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="2017", active=False)
    scenario.add_period(title="2016", active=True)

    for i in range(4):
        scenario.add_activity(title=f"A {i}", state='accepted')
        scenario.add_occasion()

    scenario.add_user(username='m1@example.org', role='member', realname="Tom")
    scenario.add_attendee(
        name="Dustin",
        birth_date=date(2000, 1, 1)
    )

    scenario.add_user(username='m2@example.org', role='member', realname="Doc")
    scenario.add_attendee(
        name="Mike",
        birth_date=date(2000, 1, 1)
    )

    # sign Dustin up for all courses
    for occasion in scenario.occasions:
        scenario.add_booking(
            occasion=occasion,
            user=scenario.users[0],
            attendee=scenario.attendees[0]
        )

    # sign Mike up for one course only for the permission check
    scenario.add_booking(
        occasion=scenario.occasions[0],
        user=scenario.users[1],
        attendee=scenario.attendees[1]
    )

    scenario.commit()

    c1 = client.spawn()
    c1.login('m1@example.org', 'hunter2')

    c2 = client.spawn()
    c2.login('m2@example.org', 'hunter2')

    # make sure the bookings count is correct
    assert 'data-count="4"' in c1.get('/')
    assert 'data-count="1"' in c2.get('/')

    # make sure the bookings show up under my view
    def count(page: ExtendedResponse) -> int:
        return len(page.pyquery('.attendee-bookings .booking'))

    c1_bookings = c1.get('/').click('Wunschliste')
    c2_bookings = c2.get('/').click('Wunschliste')

    assert count(c1_bookings) == 4
    assert count(c2_bookings) == 1

    # make sure each user only has access to their own bookings
    def star_url(page: ExtendedResponse, index: int) -> str:
        return page.pyquery(
            page.pyquery('a[ic-post-to]')[index]).attr['ic-post-to']

    assert c1.post(star_url(c2_bookings, 0), status=403)
    assert c2.post(star_url(c1_bookings, 0), status=403)

    # star three bookings - the last one should fail
    result = c1.post(star_url(c1_bookings, 0))
    assert result.headers.get('X-IC-Trigger') is None

    result = c1.post(star_url(c1_bookings, 1))
    assert result.headers.get('X-IC-Trigger') is None

    result = c1.post(star_url(c1_bookings, 2))
    assert result.headers.get('X-IC-Trigger') is None

    result = c1.post(star_url(c1_bookings, 3))
    assert result.headers.get('X-IC-Trigger') == 'show-alert'
    assert "maximal drei Favoriten" in result.headers['X-IC-Trigger-Data']

    # users may switch between other periods
    url = c1_bookings.pyquery('select option:first').val()
    assert "Noch keine Buchungen" in c1.get(url)

    # admins may switch between other users
    admin = client.spawn()
    admin.login_admin()

    page = admin.get('/').click('Wunschliste')
    url = page.pyquery('select:last option[value*="m1"]').val()

    m1_bookings = admin.get(url)

    assert count(m1_bookings) == 4


def test_confirmed_booking_view(client: Client, scenario: Scenario) -> None:
    scenario.add_period()
    scenario.add_activity()
    scenario.add_occasion()
    scenario.add_attendee(name='Dustin', birth_date=date(2000, 1, 1))
    scenario.add_booking()
    scenario.commit()

    client.login_admin()

    # When the period is unconfirmed, no storno is available, and the
    # state is always "open"
    with scenario.update():
        assert scenario.latest_period is not None
        scenario.latest_period.confirmed = False
        assert scenario.latest_booking is not None
        scenario.latest_booking.state = 'accepted'

    page = client.get('/my-bookings')
    assert "Offen" in page
    assert "Buchung stornieren" not in page
    assert "Wunsch entfernen" in page
    assert "Gebucht" not in page

    # Related contacts are hidden at this point
    page = client.get('/feriennet-settings')
    page.form['show_related_contacts'] = True
    page.form.submit()

    page = client.get('/my-bookings')
    assert not page.pyquery('.attendees-toggle')
    assert "Elternteil" not in page

    # When the period is confirmed, the state is shown
    with scenario.update():
        scenario.latest_period.confirm_and_start_booking_phase()

    page = client.get('/my-bookings')
    assert "Gebucht" in page
    assert "Buchung stornieren" in page
    assert "Wunsch entfernen" not in page
    assert "Buchung entfernen" not in page
    assert "nicht genügend Anmeldungen" not in page

    # Related contacts are now visible
    assert page.pyquery('.attendees-toggle').text() == '1 Teilnehmende'
    assert "Elternteil" in page

    # Unless that option was disabled
    page = client.get('/feriennet-settings')
    page.form['show_related_contacts'] = False
    page.form.submit()

    page = client.get('/my-bookings')
    assert not page.pyquery('.attendees-toggle')
    assert "Elternteil" not in page

    # Other states are shown too
    states: list[tuple[BookingState, str]] = [
        ('cancelled', "Storniert"),
        ('denied', "Abgelehnt"),
        ('blocked', "Blockiert")
    ]

    for state, text in states:
        with scenario.update():
            scenario.latest_booking.state = state

        assert text in client.get('/my-bookings')

    # If there are not enough attendees, show a warning
    with scenario.update():
        scenario.latest_period.confirmed = True
        scenario.latest_booking.state = 'accepted'
        assert scenario.latest_occasion is not None
        scenario.latest_occasion.spots = NumericRange(2, 5)  # type: ignore[assignment]

    page = client.get('/my-bookings')
    assert "nicht genügend Anmeldungen" in page


def test_booking_mail(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        title="2019",
        phase='booking',
        confirmed=True,
    )
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(spots=(0, 1))
    scenario.add_user(username='member@example.org', role='member')
    scenario.add_attendee(
        name="Dustin",
        birth_date=date(2008, 1, 1),
        username='admin@example.org'
    )
    scenario.commit()

    client = client.spawn()
    client.login_admin()
    client.fill_out_profile("Scrooge", "McDuck")

    # Add cancellation conditions to the ferienpass
    page = client.get('/feriennet-settings')
    page.form['cancellation_conditions'] = "Do not cancel"
    page.form.submit()

    page = client.get('/activity/foobar').click('Anmelden')
    page = page.form.submit().follow()

    # Check mail
    assert len(os.listdir(client.app.maildir)) == 1
    message_1 = client.get_email(0, 0)
    assert "Do not cancel" in message_1['TextBody']


def test_direct_booking_and_storno(client: Client, scenario: Scenario) -> None:
    scenario.add_period(confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(spots=(0, 1))
    scenario.add_user(username='member@example.org', role='member')
    scenario.add_attendee(
        name="Dustin",
        birth_date=date(2008, 1, 1),
        username='admin@example.org'
    )
    scenario.add_attendee(
        name="Mike",
        birth_date=date(2008, 1, 1),
        username='member@example.org'
    )
    scenario.commit()

    client = client.spawn()
    client.login_admin()
    client.fill_out_profile("Scrooge", "McDuck")

    member = client.spawn()
    member.login('member@example.org', 'hunter2')
    member.fill_out_profile("Zak", "McKracken")

    # in a confirmed period parents can book directly
    page = client.get('/activity/foobar')
    assert "1 Plätze frei" in page
    assert "Eine Buchung kostet CHF pro Kind" not in page

    other = member.get('/activity/foobar').click('Anmelden')

    page = page.click('Anmelden')
    booked = page.form.submit().follow()
    assert "Ausgebucht" in booked
    assert "Dustin" in booked

    other = other.form.submit()
    assert "ist bereits ausgebucht" in other

    page = page.form.submit()
    assert "bereits für diese Durchführung angemeldet" in page

    # cancel the booking
    client.get('/my-bookings').click("Buchung stornieren")

    page = client.get('/activity/foobar')
    assert "1 Plätze frei" in page

    # admins may do this for other members
    options = page.click('Anmelden').pyquery('select option')
    url = next(
        o.attrib['value'] for o in options if 'member' in o.attrib['value'])
    page = client.get(url)

    other_url = page.request.url
    assert "Mike" in page
    assert "Für <strong>Zak McKracken</strong>" in page

    # members may not (simply ignores the other user)
    page = member.get('/activity/foobar').click('Anmelden')
    assert "admin@example.org" not in page

    page = member.get(other_url.replace('member@', 'admin@'))
    assert "Für <strong>admin@example.org</strong>" not in page
    assert "Mike" in page


def test_cancel_occasion(client: Client, scenario: Scenario) -> None:
    scenario.add_period(confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(age=(0, 100))
    scenario.add_attendee(birth_date=date.today() - timedelta(days=10 * 360))
    scenario.commit()

    client.login_admin()
    client.fill_out_profile()

    page = client.get('/activity/foobar')
    assert "Löschen" in page
    assert "Absagen" not in page
    assert "Reaktivieren" not in page

    page = page.click('Anmelden').form.submit()
    assert "Gebucht" in client.get('/my-bookings')

    page = client.get('/activity/foobar')
    assert "Löschen" not in page
    assert "Absagen" in page
    assert "Reaktivieren" not in page

    page.click("Absagen")
    assert "Storniert" in client.get('/my-bookings')

    page = client.get('/activity/foobar')
    assert "Löschen" not in page
    assert "Absagen" not in page
    assert "Reaktivieren" in page

    page.click("Reaktivieren")
    assert "Storniert" in client.get('/my-bookings')

    page = client.get('/activity/foobar')
    assert "Löschen" not in page
    assert "Absagen" in page
    assert "Reaktivieren" not in page

    client.get('/my-bookings').click("Buchung entfernen")
    page = client.get('/activity/foobar')
    assert "Löschen" in page
    assert "Absagen" not in page
    assert "Reaktivieren" not in page

    page.click("Löschen")


def test_reactivate_cancelled_booking(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period()
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(
        age=(0, 10),
        spots=(0, 2),
        cost=100
    )
    scenario.add_attendee(
        name="Dustin",
        birth_date=(datetime.today() - timedelta(days=5 * 360))
    )
    scenario.commit()

    client.login_admin()
    client.fill_out_profile()

    # by default we block conflicting bookings
    page = client.get('/activity/foobar').click('Anmelden')
    page = page.form.submit().follow()

    assert "Wunschliste hinzugefügt" in page

    page = client.get('/activity/foobar').click('Anmelden')
    assert "bereits für diese Durchführung angemeldet" in page.form.submit()

    # unless they are cancelled
    scenario.c.bookings.query().first().state = 'cancelled'  # type: ignore[union-attr]
    scenario.commit()  # can be done by cancelling the whole event in UI

    page = client.get('/activity/foobar').click('Anmelden')
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()

    # this also works between multiple occasions of the same activity
    scenario.c.bookings.query().first().state = 'cancelled'  # type: ignore[union-attr]
    scenario.commit()  # can be done by cancelling the whole event in UI

    page = client.get('/activity/foobar').click('Anmelden')
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()

    # including denied bookings
    scenario.c.bookings.query().first().state = 'denied'  # type: ignore[union-attr]
    scenario.commit()  # can be done by cancelling the whole event in UI

    page = client.get('/activity/foobar').click('Anmelden')
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()

    # and even if we confirm the period
    page = client.get('/activities').click('Zuteilung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page.form.submit()

    with scenario.update():
        assert scenario.latest_period is not None
        scenario.latest_period.confirm_and_start_booking_phase()

    client.get('/my-bookings').click("Buchung stornieren")
    page = client.get('/activity/foobar').click('Anmelden')
    assert "war erfolgreich" in page.form.submit().follow()


def test_occasion_attendance_collection(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period()

    scenario.add_activity(
        title="Foo",
        username='admin@example.org',
        state='accepted'
    )
    scenario.add_occasion()
    scenario.add_attendee(name="Dustin", username='admin@example.org')
    scenario.add_booking(username='admin@example.org', state='accepted')

    scenario.add_activity(
        title="Bar",
        username='editor@example.org',
        state='accepted'
    )
    scenario.add_occasion()
    scenario.add_attendee(name="Mike", username='editor@example.org')
    scenario.add_booking(username='admin@example.org', state='accepted')

    scenario.commit()

    # anonymous has no access
    assert client.get('/attendees/foo', status=403)
    assert client.get('/attendees/bar', status=403)

    # if the period is unconfirmed the attendees are not shown
    admin = client.spawn()
    admin.login_admin()

    for id in ('foo', 'bar'):
        page = admin.get(f'/attendees/{id}')
        assert "noch keine Zuteilung" in page
        assert "Dustin" not in page

    # organisers only see their own occasions
    with scenario.update():
        assert scenario.latest_period is not None
        scenario.latest_period.confirmed = True

    editor = client.spawn()
    editor.login_editor()

    page = editor.get('/attendees/foo')
    assert "Dustin" not in page

    page = editor.get('/attendees/bar')
    assert "Mike" in page

    # admins seel all the occasions
    page = admin.get('/attendees/foo')
    assert "Dustin" in page

    page = admin.get('/attendees/bar')
    assert "Mike" in page

    # if the emergency info is given, it is shown
    page = admin.get('/userprofile')
    page.form['salutation'] = 'mr'
    page.form['first_name'] = 'foo'
    page.form['last_name'] = 'bar'
    page.form['zip_code'] = '123'
    page.form['place'] = 'abc'
    page.form['address'] = 'abc'
    page.form['emergency'] = '123456789 Admin'
    page.form.submit()

    assert "123456789 Admin" in admin.get('/attendees/foo')
    assert "123456789 Admin" in admin.get('/attendees/bar')


def test_send_email(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="Ferienpass 2015", active=False)
    scenario.add_period(title="Ferienpass 2016")
    scenario.commit()

    client.login_admin()

    page = client.get('/notifications').click('Neue Mitteilungs-Vorlage')
    page.form['subject'] = '[Zeitraum] subject'
    page.form['text'] = '[Zeitraum] body'
    page = page.form.submit().follow()

    page = page.click('Vorlage verwenden')
    page.form['no_spam'] = True
    assert 'selected="False"' not in page
    assert "Ferienpass 2016 subject" in page
    assert "Ferienpass 2016 body" in page
    assert "keine Empfänger gefunden" in page.form.submit()

    page.form['roles'] = ['admin', 'editor']
    assert "an 2 Empfänger gesendet" in page.form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 1

    message_1 = client.get_email(0, 0)
    assert "Ferienpass 2016 subject" in message_1['Subject']
    assert "Ferienpass 2016 body" in message_1['TextBody']

    message_2 = client.get_email(0, 1)
    assert "Ferienpass 2016 subject" in message_2['Subject']
    assert "Ferienpass 2016 body" in message_2['TextBody']

    recipients = message_1['To'] + message_2['To']
    assert "editor@example.org" in recipients
    assert "admin@example.org" in recipients


def test_create_duplicate_notification(client: Client) -> None:
    client.login_admin()

    page = client.get('/notifications').click('Neue Mitteilungs-Vorlage')
    page.form['subject'] = 'Foo'
    page.form['text'] = 'Bar'

    page.form.submit().follow()
    assert "existiert bereits" in page.form.submit()


def test_import_account_statement(client: Client, scenario: Scenario) -> None:
    scenario.add_user(username='member@example.org', role='member')
    scenario.add_period(confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(cost=150)
    scenario.add_attendee(name="Julian")
    scenario.add_booking(
        username='editor@example.org',
        state='accepted', cost=150)
    scenario.add_attendee(name="Yannick")
    scenario.add_booking(
        username='member@example.org',
        state='accepted', cost=100)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(
        username='admin@example.org',
        state='accepted', cost=100)
    scenario.add_attendee(name="Austin")
    scenario.add_booking(
        username='admin@example.org',
        state='accepted', cost=100)
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()

    # Fakturierung
    page = admin.get('/').click('Fakturierung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page = page.form.submit()

    # No IBAN yet
    page = page.click('Kontoauszug importieren')
    assert "kein Bankkonto" in page

    settings = page.click('Einstellungen', index=1).click('Feriennet', index=0)
    settings.form['bank_account'] = 'CH6309000000250097798'
    settings.form['bank_beneficiary'] = 'Initech'
    settings.form.submit()

    # Prepare two payments
    bookings_query = scenario.session.query(ActivityInvoiceItem)
    bookings = bookings_query.order_by(ActivityInvoiceItem.group).all()
    assert not all(booking.payment_date for booking in bookings)
    assert not all(booking.tid for booking in bookings)

    code_1 = 'Zahlungszweck {}'.format(
        bookings[3].invoice.references[0].readable)
    code_2 = 'Zahlungszweck {}'.format(
        bookings[0].invoice.references[0].readable)
    xml = generate_xml([
        dict(amount='200.00 CHF', note='no match', valdat='2020-04-23'),
        dict(amount='100.00 CHF', note=code_1, valdat='2020-03-22', tid='TX1'),
        dict(amount='200.00 CHF', note=code_2, valdat='2020-03-05', tid='TX2'),
        dict(amount='200.00 CHF', note='no match', valdat='2020-05-23'),
        dict(amount='100.00 CHF', note='no match', valdat='2020-05-12')
    ])

    # Import payments
    page = page.click('Rechnungen')
    page = page.click('Fakturierung').click('Kontoauszug importieren')
    page.form['xml'] = Upload(
        'account.xml',
        xml.encode('utf-8'),
        'application/xml'
    )
    page = page.form.submit()

    assert "2 Zahlungen importieren" in page
    page = page.click("2 Zahlungen importieren")
    page = admin.get('/my-bills')
    assert "2 Zahlungen wurden importiert" in page

    # Check dates and transaction IDs
    booking1 = scenario.session.query(ActivityInvoiceItem).filter(
        ActivityInvoiceItem.payment_date == date(2020, 3, 22)
    ).one()
    assert booking1.tid == 'TX1'

    booking2 = scenario.session.query(ActivityInvoiceItem).filter(
        ActivityInvoiceItem.payment_date == date(2020, 3, 5)
    ).all()
    assert [b.tid for b in booking2] == ['TX2', 'TX2']

    # Re-run import
    page = page.click('Fakturierung').click('Kontoauszug importieren')
    page.form['xml'] = Upload(
        'account.xml',
        xml.encode('utf-8'),
        'application/xml'
    )
    page = page.form.submit()

    assert "0 Zahlungen importieren" in page


def test_deadline(client: Client, scenario: Scenario) -> None:
    scenario.add_period()
    scenario.add_activity(title="Foo", state='accepted')
    scenario.add_occasion()
    scenario.commit()
    scenario.refresh()

    # Test visibility of booking button right after day change
    period = scenario.latest_period
    assert period is not None
    prebook_midnight = period.as_local_datetime(period.prebooking_start)

    with freeze_time(prebook_midnight + timedelta(minutes=30)):
        assert period.wishlist_phase
        assert period.is_prebooking_in_past is False
        page = client.get('/activity/foo')
        assert 'Anmelden' in page.pyquery('.enroll a')[0].text

    with freeze_time(prebook_midnight - timedelta(minutes=30)):
        period = period  # undo mypy narrowing
        assert not period.wishlist_phase
        assert period.is_prebooking_in_past is False
        page = client.get('/activity/foo')
        assert not page.pyquery('.enroll')

    with freeze_time(period.booking_end + timedelta(days=1)):

        # show no 'enroll' for ordinary users past the deadline
        # (there are two login links in the header and footer, for the
        # ordinary login)
        assert str(client.get('/activity/foo')).count("Anmelden") == 2

        # do show it for admins though and allow signups
        admin = client.spawn()
        admin.login_admin()

        # the ordinary login link vanishes
        assert str(admin.get('/activity/foo')).count("Abmelden") == 1
        assert str(admin.get('/activity/foo')).count("Anmelden") == 1

        page = admin.get('/activity/foo').click("Anmelden")
        assert "Der Anmeldeschluss wurde erreicht" not in page.form.submit()

        # stop others, even if they get to the form
        editor = client.spawn()
        editor.login_editor()

        page = editor.get(page.request.url.replace('http://localhost', ''))
        assert "Der Anmeldeschluss wurde erreicht" in page.form.submit()


def test_cancellation_deadline(client: Client, scenario: Scenario) -> None:
    scenario.add_period(confirmed=True)
    scenario.add_activity(title="Foo", state='accepted')
    scenario.add_occasion()
    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=True
    )
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted', cost=100)
    scenario.commit()

    # without a deadline, no cancellation
    client.login('member@example.org', 'hunter2')
    assert "Buchung stornieren" not in client.get('/my-bookings')

    # before the deadline, cancellation
    with scenario.update():
        assert scenario.latest_period is not None
        scenario.latest_period.cancellation_date = (
            utcnow().date() + timedelta(days=1))

    page = client.get('/my-bookings')
    assert "Buchung stornieren" in page

    cancel = page.pyquery(
        'a:contains("Buchung stornieren")').attr('ic-post-to')

    # after the deadline, no cancellation
    with scenario.update():
        scenario.latest_period.cancellation_date = (
            utcnow().date() - timedelta(days=1))

    assert "Buchung stornieren" not in client.get('/my-bookings')

    # even if one knows the link
    client.post(cancel)
    assert "Nur Administratoren" in client.get('/my-bookings')

    # which succeeds if the deadline is changed
    with scenario.update():
        scenario.latest_period.cancellation_date\
            = utcnow().date() + timedelta(days=1)

    client.post(cancel)
    assert "Buchung wurde erfolgreich abgesagt" in client.get('/my-bookings')


def test_userprofile_login(client: Client) -> None:
    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'hunter2'
    page = page.form.submit().follow()

    assert "Ihr Benutzerprofil ist unvollständig" in page
    page.form['salutation'] = 'mr'
    page.form['first_name'] = 'Scrooge'
    page.form['last_name'] = 'McDuck'
    page.form['zip_code'] = '1234'
    page.form['place'] = 'Duckburg'
    page.form['address'] = 'Foobar'
    page.form['emergency'] = '0123 456 789 (Scrooge McDuck)'
    page = page.form.submit().follow()

    assert 'settings' in page.request.url

    client = client.spawn()

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'hunter2'
    page = page.form.submit().follow()

    assert 'settings' in page.request.url


def test_provide_activity_again(client: Client, scenario: Scenario) -> None:
    scenario.add_period()
    scenario.add_activity(title="Learn How to Program")
    scenario.add_occasion()
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()

    assert "Erneut anbieten" not in admin.get('/activities')

    with scenario.update():
        activity = scenario.latest_activity
        assert activity is not None
        activity.state = 'archived'

    assert "Erneut anbieten" in admin.get('/activities')

    editor = client.spawn()
    editor.login_editor()

    editor.post('/activity/learn-how-to-program/offer-again', status=404)
    scenario.refresh()
    assert activity.state == 'archived'

    admin.post('/activity/learn-how-to-program/offer-again')
    scenario.refresh()
    activity = activity  # undo mypy narrowing
    assert activity.state == 'preview'


def test_online_payment(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="Ferienpass 2017", confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted', cost=100)

    scenario.c.payment_providers.add(
        type='stripe_connect', default=True, meta={
            'publishable_key': '0xdeadbeef',
            'access_token': 'foobar'
        }
    )

    scenario.commit()

    client.login_admin()

    assert 'checkout-button' not in client.get('/my-bills')

    page = client.get('/').click('Fakturierung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page = page.form.submit()

    page = client.get('/my-bills')
    assert 'checkout-button' in page
    assert "Jetzt online bezahlen" in page

    # pay online
    with requests_mock.Mocker() as m:
        charge = {
            'id': '123456'
        }

        m.post('https://api.stripe.com/v1/charges', json=charge)
        m.get('https://api.stripe.com/v1/charges/123456', json=charge)
        m.post('https://api.stripe.com/v1/charges/123456/capture', json=charge)

        page.form['payment_token'] = 'foobar'
        page.form.submit().follow()

    # sync the charges
    with requests_mock.Mocker() as m:
        page = client.get('/payments')
        assert ">Offen<" in page

        m.get('https://api.stripe.com/v1/charges?limit=100', json={
            "object": "list",
            "url": "/v1/charges",
            "has_more": False,
            "data": [
                {
                    'id': '123456',
                    'captured': True,
                    'refunded': False,
                    'paid': True,
                    'status': 'foobar',
                    'metadata': {
                        'payment_id':
                        scenario.session.query(Payment).one().id.hex
                    }
                }
            ]
        })

        m.get('https://api.stripe.com/v1/payouts?limit=100&status=paid', json={
            "object": "list",
            "url": "/v1/payouts",
            "has_more": False,
        })

        page = client.get('/billing?expand=1')
        page = page.click('Online Zahlungen synchronisieren').follow()

        assert "Synchronisierung erfolgreich" in page
        assert ">Bezahlt<" in page

        page = client.get('/payments')
        assert "Offen" not in page.pyquery('tbody tr').text()
        assert "Bezahlt" in page.pyquery('tbody tr').text()

    page = client.get('/payments')
    assert "Ferienpass 2017" in page
    assert "Stripe Connect" in page
    assert "96.80" in page
    assert "3.20" in page

    page = client.get('/billing?state=all')
    page = page.click('Online Zahlungen anzeigen').follow()
    assert "96.80" in page
    assert "3.20" in page

    # refund the charge
    with requests_mock.Mocker() as m:
        charge = {
            'id': '123456'
        }
        m.post('https://api.stripe.com/v1/refunds', json=charge)
        page.click("Zahlung rückerstatten")
        # client.post(get_post_url(page, 'payment-refund'))

    page = client.get('/billing?expand=1&state=all')
    assert "Unbezahlt" in page.pyquery('tbody tr').text()

    page = client.get('/payments')
    assert "Rückerstattet" in page.pyquery('tbody tr').text()

    page = client.get('/my-bills')
    assert 'checkout-button' in page
    assert "Jetzt online bezahlen" in page

    with freeze_time('2018-01-01'):
        # it should be possible to change the payment state again
        client.get('/billing?state=all').click(
            "Rechnung als bezahlt markieren")

        # check if paid and payment date is set
        assert scenario.session.query(  # type: ignore[union-attr]
            ActivityInvoiceItem
        ).first().payment_date == date(2018, 1, 1)

    client.get('/billing?state=all').click("Rechnung als unbezahlt markieren")

    # pay again (leading to a refunded and an open charge)
    with requests_mock.Mocker() as m:
        charge = {
            'id': '654321'
        }

        m.post('https://api.stripe.com/v1/charges', json=charge)
        m.get('https://api.stripe.com/v1/charges/654321', json=charge)
        m.post('https://api.stripe.com/v1/charges/654321/capture', json=charge)

        page.form['payment_token'] = 'barfoo'
        page.form.submit().follow()

    page = client.get('/payments')

    assert "Offen" in page.pyquery('tbody tr').text()
    assert "Rückerstattet" in page.pyquery('tbody tr').text()


def test_icalendar_subscription(client: Client, scenario: Scenario) -> None:
    scenario.add_period()
    scenario.add_activity(title="Fishing")
    scenario.add_occasion(
        start=datetime(2016, 11, 25, 8),
        end=datetime(2016, 11, 25, 16),
        note="Children might get wet"
    )
    scenario.add_attendee()
    scenario.add_booking()
    scenario.commit()

    client.login_admin()

    # When the period is unconfirmed, the events are not shown in the calendar
    with scenario.update():
        assert scenario.latest_period is not None
        scenario.latest_period.confirmed = False
        assert scenario.latest_booking is not None
        scenario.latest_booking.state = 'accepted'

    page = client.get('/my-bookings')

    url = page.pyquery('.calendar-add-icon').attr('href')
    url = url.replace('webcal', 'http')

    calendar = client.get(url).text
    assert 'VEVENT' not in calendar

    # Once the period is confirmed, the state has to be accepted as well
    with scenario.update():
        scenario.latest_period.confirmed = True
        scenario.latest_booking.state = 'open'

    calendar = client.get(url).text
    assert 'VEVENT' not in calendar

    # Only with a confirmed period and accepted booking are we getting anything
    with scenario.update():
        scenario.latest_period.confirmed = True
        scenario.latest_booking.state = 'accepted'

    calendar = client.get(url).text
    assert 'VEVENT' in calendar

    assert 'SUMMARY:Fishing' in calendar
    assert 'DESCRIPTION:Children might get wet' in calendar
    assert 'DTSTART:20161125T070000Z' in calendar
    assert 'DTEND:20161125T150000Z' in calendar


def test_fill_out_contact_form(client: Client) -> None:
    page = client.get('/form/kontakt')
    page.form['vorname'] = 'Foo'
    page.form['nachname'] = 'Bar'
    page.form['telefon'] = '1234'
    page.form['e_mail'] = 'info@example.org'
    page.form['mitteilung'] = 'Hello'

    page = page.form.submit().follow()
    assert "Abschliessen" in page

    page = page.form.submit().follow()
    assert "Anfrage eingereicht" in page

    assert len(os.listdir(client.app.maildir)) == 1


def test_occasion_number(client: Client, scenario: Scenario) -> None:
    period = scenario.add_period()

    scenario.add_activity(name='fishing', state='accepted')

    scenario.add_occasion(
        start=datetime.combine(period.execution_start, time(10, 0)),
        end=datetime.combine(period.execution_start, time(11, 0))
    )
    scenario.add_occasion(
        start=datetime.combine(period.execution_start, time(11, 0)),
        end=datetime.combine(period.execution_start, time(12, 0))
    )

    scenario.commit()

    client.login_admin()
    client.fill_out_profile()

    page = client.get('/activity/fishing')

    assert "1. Durchführung" in page
    assert "2. Durchführung" in page

    assert page.text.find("1. Durch") < page.text.find("2. Durch")

    assert "1. Durchführung" in page.click('Anmelden', index=0)
    assert "2. Durchführung" in page.click('Anmelden', index=1)


def test_main_views_without_period(client: Client) -> None:
    client.login_admin()

    # 99.9% of the time, there's a period for the following views -
    # if there isn't we must be sure to not show an exeption (this happens
    # because we tend to be very optimistic about periods being there)
    assert client.get('/activities').status_code == 200
    assert client.get('/activities/json').status_code == 200
    assert client.get('/my-bookings').status_code == 200
    assert client.get('/notifications').status_code == 200

    assert client.get('/matching', expect_errors=True).status_code == 404
    assert client.get('/billing', expect_errors=True).status_code == 404


def test_book_alternate_occasion_regression(
    client: Client,
    scenario: Scenario
) -> None:
    scenario.add_period(title="Ferienpass", confirmed=True)
    scenario.add_attendee(birth_date=date.today() - timedelta(days=8 * 360))

    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion()
    scenario.add_booking(state='accepted')

    scenario.add_activity(title="Hunting", state='accepted')
    scenario.add_occasion()
    scenario.add_booking(state='blocked')

    scenario.commit()
    scenario.refresh()

    client.login_admin()
    client.fill_out_profile()

    client.get('/my-bookings').click("Buchung stornieren")

    page = client.get('/activity/hunting').click("Anmelden")
    page = page.form.submit()

    assert 'bereits für diese Durchführung' not in page


def test_view_archived_occasions(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        title="Yesteryear",
        confirmed=True,
        finalized=True,
        archived=True
    )

    scenario.add_activity(title="Fishing", state='archived')
    scenario.add_occasion()
    scenario.commit()

    # anonymous doesn't see archived occasions
    client.get('/activity/fishing', status=404)

    # editors don't see archived occasions, unless they own them
    client.login_editor()
    client.get('/activity/fishing', status=404)

    scenario.refresh()
    assert scenario.latest_activity is not None
    scenario.latest_activity.username = 'editor@example.org'
    scenario.commit()

    assert '1. Durchführung' in client.get('/activity/fishing')

    # they do not get any action links however
    assert 'Duplizieren' not in client.get('/activity/fishing')

    # admins see archived occasions, but get no links either
    client = client.spawn()
    client.login_admin()

    assert '1. Durchführung' in client.get('/activity/fishing')
    assert 'Duplizieren' in client.get('/activity/fishing')


def test_no_new_activites_without_active_period(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(
        title="2017",
        confirmed=True,
        finalized=True,
        archived=True,
        active=False
    )

    scenario.add_activity(title="Fishing", state='archived')
    scenario.add_occasion()

    scenario.add_period(
        title="2018",
        confirmed=True,
        finalized=True,
        archived=True,
        active=True
    )

    scenario.commit()

    client.login_admin()

    page = client.get('/activities')
    assert "Angebot erneut anbieten" in page
    assert "Angebot erfassen" in page

    page = client.get('/activity/fishing')
    assert "Erneut anbieten" in page

    scenario.refresh()
    assert scenario.latest_period is not None
    scenario.latest_period.active = False
    scenario.commit()

    page = client.get('/activities')
    assert "Angebot erneut anbieten" not in page
    assert "Angebot erfassen" not in page

    page = client.get('/activity/fishing')
    assert "Erneut anbieten" not in page


def test_no_state_before_wishlist_phase_starts(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(
        title="Ferienpass",
        prebooking_start=scenario.date_offset(+1),
        prebooking_end=scenario.date_offset(+2),
        execution_start=scenario.date_offset(+3),
        execution_end=scenario.date_offset(+4),
    )
    scenario.add_activity(title="Marathon", state='accepted')
    scenario.add_occasion()
    scenario.commit()

    page = client.get('/activity/marathon')
    assert 'Plätze frei' not in page
    assert not page.pyquery('.state')


def test_invoice_references(client: Client, scenario: Scenario) -> None:

    scenario.add_period(title="2019", confirmed=True, finalized=False)
    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted', cost=100)
    scenario.commit()

    client.login_admin()

    settings = client.get('/feriennet-settings')
    settings.form['bank_account'] = 'CH6309000000250097798'
    settings.form['bank_beneficiary'] = 'Initech'
    settings.form.submit()

    page = client.get('/billing')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page.form.submit()

    def reference() -> str:
        return client.get('/my-bills').pyquery(
            '.reference-number').text().strip()

    default_reference = reference()
    assert re.match(r'Q-[0-9A-Z]{5}-[0-9A-Z]{5}', default_reference)

    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'esr-v1'
    settings.form['bank_esr_participant_number'] = '1337'
    settings.form.submit()

    # each change of schema/config leads to new references
    esr_reference = reference()
    assert re.match(r'[0-9 ]+', esr_reference)

    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'raiffeisen-v1'
    settings.form['bank_esr_identification_number'] = '999999'
    page = settings.form.submit()

    raiffeisen_reference_1 = reference()
    assert re.match(r'99 9999[0-9 ]+', raiffeisen_reference_1)

    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'raiffeisen-v1'
    settings.form['bank_esr_identification_number'] = '111111'
    settings.form.submit()

    raiffeisen_reference_2 = reference()
    assert re.match(r'11 1111[0-9 ]+', raiffeisen_reference_2)

    # returning to old schemas doesn't result in new references
    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'esr-v1'
    settings.form.submit()

    assert reference() == esr_reference

    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'raiffeisen-v1'
    settings.form.submit()

    assert reference() == raiffeisen_reference_2

    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'raiffeisen-v1'
    settings.form['bank_esr_identification_number'] = '999999'
    settings.form.submit()

    assert reference() == raiffeisen_reference_1

    settings = client.get('/feriennet-settings')
    settings.form['bank_reference_schema'] = 'feriennet-v1'
    settings.form.submit()

    assert reference() == default_reference


def test_group_codes(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="2019", confirmed=False)
    scenario.add_activity(title="Fishing", state='accepted')

    # an occasion with two spots
    scenario.add_occasion(spots=(0, 2), age=(0, 99999))

    # first user
    scenario.add_user(
        username='foobar@example.org',
        role='member',
        complete_profile=True
    )

    # an attendee without a booking
    scenario.add_attendee(name="Foo")

    # an attendee with a booking
    scenario.add_attendee(name="Bar")
    scenario.add_booking(state='open')

    # second user
    scenario.add_user(
        username='qux@example.org',
        role='member',
        complete_profile=True
    )

    # an attendee without a booking
    scenario.add_attendee(name="Qux")

    scenario.commit()
    scenario.refresh()

    # the first user opens the group sharing section
    usr1 = client.spawn()
    usr1.login('foobar@example.org', 'hunter2')

    page = usr1.get('/my-bookings').click("Gspänli einladen").follow()
    group_url = page.request.url

    # bar is in the group as it was the target of aboves link
    assert "Bar" in page.pyquery('.own-children').text()
    assert "Foo" not in page.pyquery('.own-children').text()
    assert "Bar" not in page.pyquery('#add-possible').text()
    assert "Foo" in page.pyquery('#add-possible').text()

    # we can sign-up Foo
    page = page.click("zur Gruppe hinzufügen").form.submit().follow()

    # we end up at the group view again, where Foo is in the group now
    assert "Bar" in page.pyquery('.own-children').text()
    assert "Foo" in page.pyquery('.own-children').text()

    # we can remove Bar from the group
    page = page.click("aus Gruppe entfernen", index=0)
    page = usr1.get(group_url)

    assert "Bar" not in page.pyquery('.own-children').text()
    assert "Foo" in page.pyquery('.own-children').text()

    # we can add a new attendee that is added to the group automatically
    page = page.click("Neues eigenes Kind anmelden")
    page.form['first_name'] = "Tom"
    page.form['last_name'] = "Sawyer"
    page.form['birth_date'] = "2017-01-01"
    page.form['gender'] = 'male'
    page = page.form.submit().follow()

    assert "Sawyer" in page.pyquery('.own-children').text()

    page = page.click("aus Gruppe entfernen", index=1)

    # other users can see the group view, but cannot execute actions and
    # they only see the active attendees
    usr2 = client.spawn()

    page = usr2.get(group_url)
    assert "Foo" in page
    assert "Bar" not in page
    assert "aus Gruppe entfernen" not in page.pyquery('a').text()
    assert "zur Gruppe hinzufügen" not in page.pyquery('a').text()

    usr2.login('qux@example.org', 'hunter2')

    page = usr2.get(group_url)
    assert "Foo" in page
    assert "Bar" not in page

    # the second user's child should be listed now
    assert "Qux" in page.pyquery('#add-possible').text()

    # let's join the group
    page = page.click("zur Gruppe hinzufügen").form.submit().follow()

    # now we can do the matching, and we should have Foo and Qux in the group
    admin = client.spawn()
    admin.login_admin()

    page = admin.get('/activities').click('Zuteilung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page = page.form.submit()

    bookings = scenario.session.query(Booking).all()
    bookings.sort(key=lambda b: b.attendee.name)

    b1, b2, b3, b4 = bookings

    assert b1.attendee.name == 'Bar'
    assert b1.state == 'denied'

    assert b2.attendee.name == 'Foo'
    assert b2.state == 'accepted'

    assert b3.attendee.name == 'Qux'
    assert b3.state == 'accepted'

    assert b4.attendee.name == 'Tom\xa0Sawyer'
    assert b4.state == 'denied'


def test_needs(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="2019", confirmed=False)
    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(spots=(0, 2), age=(0, 99999))
    scenario.commit()

    assert "Bedarf" not in client.get('/activity/fishing')

    client.login_admin()
    page = client.get('/activity/fishing')

    assert "Bedarf" in page
    assert "Behalten Sie die Übersicht" in page

    page = page.click("Bedarf erfassen")
    page.form['name'] = "Chaperones"
    page.form['description'] = "Watch children for their own safety"
    page.form['min_number'] = 5
    page.form['max_number'] = 10
    page = page.form.submit().follow().follow()

    assert "Bedarf" in page
    assert "Behalten Sie die Übersicht" not in page
    assert "Chaperones" in page
    assert "5 - 10" in page
    assert "Watch children for their own safety" in page

    page = page.click("Bearbeiten", index=2)
    page.form['description'] = ""
    page = page.form.submit().follow().follow()

    assert "Chaperones" in page
    assert "Watch children for their own safety" not in page

    page = client.get('/export/bedarf')
    page.form['file_format'] = 'json'
    data = page.form.submit().json

    assert data[0]['Bedarf Anzahl'] == '5 - 10'
    assert data[0]['Bedarf Name'] == 'Chaperones'

    page = client.get('/activity/fishing')
    page = page.click("Löschen", index=1)

    page = client.get('/activity/fishing')
    assert "Chaperones" not in page
    assert "Behalten Sie die Übersicht" in page

    page = client.get('/export/bedarf')
    page.form['file_format'] = 'json'
    data = page.form.submit().json

    assert data == []


def test_needs_export_by_period(client: Client, scenario: Scenario) -> None:
    scenario.add_activity(title="Fishing", state='accepted')

    scenario.add_period(title="2018", confirmed=False, active=False)
    scenario.add_occasion(spots=(0, 2), age=(0, 99999))

    scenario.add_period(title="2019", confirmed=False, active=False)
    scenario.add_occasion(spots=(0, 2), age=(0, 99999))

    scenario.commit()

    client.login_admin()

    page = client.get('/activity/fishing').click("Bedarf erfassen", index=0)
    page.form['name'] = "Foo"
    page.form['min_number'] = 1
    page.form['max_number'] = 1
    page.form.submit().follow()

    page = client.get('/activity/fishing').click("Bedarf erfassen", index=1)
    page.form['name'] = "Foo"
    page.form['min_number'] = 2
    page.form['max_number'] = 2
    page.form.submit().follow()

    scenario.refresh()

    page = client.get('/export/bedarf')
    page.form['period'] = scenario.periods[0].id.hex
    page.form['file_format'] = 'json'
    one = page.form.submit().json

    page = client.get('/export/bedarf')
    page.form['period'] = scenario.periods[1].id.hex
    page.form['file_format'] = 'json'
    two = page.form.submit().json

    assert len(one) == 1
    assert len(two) == 1

    assert one[0]['Bedarf Anzahl'] == '1 - 1'
    assert two[0]['Bedarf Anzahl'] == '2 - 2'


def test_send_email_with_link_and_attachment(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(title="Ferienpass 2016")
    scenario.commit()

    client.login_admin()

    page = client.get('/files')
    page.form['file'] = [Upload('Test.txt', b'File content.')]
    page.form.submit()

    file_id = FileCollection(scenario.session).query().one().id

    page = client.get('/notifications').click('Neue Mitteilungs-Vorlage')
    page.form['subject'] = 'File und Link'
    page.form['text'] = (f'<p>http://localhost/storage/{file_id}</p>'
                         f'<p><a href="www.google.ch">Google</a></p>')
    page = page.form.submit().follow()

    page = page.click('Vorlage verwenden')
    assert "File und Link" in page
    assert "Test.txt" not in page
    assert "Google" in page
    page.form['roles'] = ['member', 'editor']
    page.form['no_spam'] = True
    page.form.submit().follow()

    # Plaintext version
    email_1 = client.get_email(0, 0)
    assert f'/storage/{file_id}' in email_1['TextBody']
    assert '[Google](www.google.ch)' in email_1['TextBody']

    # HTML version
    assert f'/storage/{file_id}' in email_1['HtmlBody']
    assert '<a href="www.google.ch">Google</a>' in email_1['HtmlBody']

    # Test if user gets an email, even if he is not in the recipient list
    email_2 = client.get_email(0, 1)
    assert email_2['To'] == 'admin@example.org'


def test_max_age_exact(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        title="2018",
        confirmed=False,
        active=True,
        prebooking_start=date(2018, 1, 1),
        prebooking_end=date(2018, 1, 31),
        execution_start=date(2018, 2, 1),
        execution_end=date(2018, 2, 28),
        age_barrier_type='exact',
    )

    scenario.add_activity(title="Fishing", state='accepted')

    scenario.add_occasion(
        age=(5, 10),
        start=datetime(2018, 1, 1, 10),
        end=datetime(2018, 1, 1, 12)
    )

    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=False
    )

    scenario.commit()

    client.login('member@example.org', 'hunter2')

    with freeze_time('2018-01-01'):
        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2013-01-02"
        page.form['gender'] = 'male'
        assert "zu jung" in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2013-01-01"
        page.form['gender'] = 'male'
        assert "zu jung" not in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['attendee'] = 'other'
        page.form['first_name'] = "Huckleberry"
        page.form['last_name'] = "Finn"
        page.form['birth_date'] = "2007-01-01"
        page.form['gender'] = 'male'
        assert "zu alt" in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['attendee'] = 'other'
        page.form['first_name'] = "Huckleberry"
        page.form['last_name'] = "Finn"
        page.form['birth_date'] = "2007-01-02"
        page.form['gender'] = 'male'
        assert "zu alt" not in page.form.submit()


def test_max_age_year(client: Client, scenario: Scenario) -> None:
    scenario.add_period(
        title="2018",
        confirmed=False,
        active=True,
        prebooking_start=date(2018, 5, 1),
        prebooking_end=date(2018, 5, 31),
        execution_start=date(2018, 6, 1),
        execution_end=date(2018, 6, 30),
        age_barrier_type='year',
    )

    scenario.add_activity(title="Fishing", state='accepted')

    scenario.add_occasion(
        age=(5, 10),
        start=datetime(2018, 5, 1, 10),
        end=datetime(2018, 5, 1, 12)
    )

    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=False
    )

    scenario.commit()

    client.login('member@example.org', 'hunter2')

    with freeze_time('2018-05-01'):
        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2014-01-01"
        page.form['gender'] = 'male'
        assert "zu jung" in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2014-12-31"
        page.form['gender'] = 'male'
        assert "zu jung" in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2013-01-01"
        page.form['gender'] = 'male'
        assert "zu jung" not in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2013-12-31"
        page.form['gender'] = 'male'
        assert "zu jung" not in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"
        page.form['birth_date'] = "2006-12-31"
        page.form['gender'] = 'male'
        assert "zu alt" in page.form.submit()

        page = client.get('/activity/fishing').click("Anmelden")
        page.form['first_name'] = "Tom"
        page.form['last_name'] = "Sawyer"

        # Allow even if child has the max age couple of hours in occasion year
        page.form['birth_date'] = "2007-01-01"
        page.form['gender'] = 'male'
        assert "zu alt" not in page.form.submit()


def test_accept_tos(client: Client, scenario: Scenario) -> None:
    scenario.add_period(confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(age=(0, 100))
    scenario.add_attendee(birth_date=date.today() - timedelta(days=10 * 360))
    scenario.commit()

    client.login_admin()
    client.fill_out_profile()

    page = client.get('/activity/foobar').click("Anmelden")
    assert "AGB" not in page

    page = client.get('/feriennet-settings')
    page.form['tos_url'] = 'https://example.org/tos'
    page.form.submit()

    page = client.get('/activity/foobar').click("Anmelden")
    assert "AGB"

    page = page.form.submit()
    assert "Die AGB müssen akzeptiert werden" in page

    page.form['accept_tos'] = True
    page = page.form.submit().follow()

    assert "AGB" not in page
    assert "erfolgreich" in page

    page = client.get('/activity/foobar').click("Anmelden")
    assert "AGB" not in page

    page = client.get('/export/benutzer')
    page.form['file_format'] = 'json'
    data = page.form.submit().json
    assert data[0]['Benutzer AGB akzeptiert']
    assert not data[1]['Benutzer AGB akzeptiert']


def test_donations(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="2019", confirmed=True, finalized=False)
    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted', cost=100)
    scenario.commit()

    client.login_admin()

    # toggle donations
    page = client.get('/billing')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page = page.form.submit()

    assert "Jetzt spenden" in client.get('/my-bills')

    page = client.get('/feriennet-settings')
    page.form['donation'] = False
    page.form.submit()

    assert "Jetzt spenden" not in client.get('/my-bills')

    page = client.get('/feriennet-settings')
    page.form['donation'] = True
    page.form.submit()

    # try a donation
    page = client.get('/my-bills')

    assert "Ich möchte einen zusätzlichen Betrag" in page

    page = page.click('Jetzt spenden')
    page.form['amount'] = '10.00'
    page = page.form.submit().follow()

    assert "Vielen Dank" in page
    assert "Ihre Spende" in page
    assert "10" in page

    # try to adjust it
    page = page.click('Anpassen')
    page.form['amount'] = '30.00'
    page = page.form.submit().follow()

    assert "Vielen Dank" in page
    assert "Ihre Spende" in page
    assert "30" in page

    # mark it as paid to disable changes
    for item in scenario.session.query(ActivityInvoiceItem):
        item.paid = True

    transaction.commit()

    # this should lead to an error now
    page.click("Entfernen")
    assert "Die Spende wurde bereits bezahlt" in client.get('/my-bills')

    # until we mark it as unpaid again
    for item in scenario.session.query(ActivityInvoiceItem):
        item.paid = False

    transaction.commit()

    client.get('/my-bills').click("Entfernen")
    assert "Ihre Spende wurde entfernt" in client.get('/my-bills')

    # the link should no longer show up
    assert "Entfernen" not in client.get('/my-bills')


def test_booking_after_finalization_all_inclusive(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(
        title="2019",
        confirmed=True,
        finalized=True,
        all_inclusive=True,
        pay_organiser_directly=False,
        booking_cost=100,
    )

    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(cost=10)
    scenario.add_activity(title="Hunting", state='accepted')
    scenario.add_occasion(cost=10)

    scenario.add_attendee(name="Beavis")
    scenario.add_attendee(name="Butthead")

    scenario.commit()

    # this is only possible as an Admin
    client.login_editor()
    client.fill_out_profile()
    assert "Anmelden" not in client.get('/activity/fishing')
    assert "Anmelden" not in client.get('/activity/hunting')

    client.login_admin()
    client.fill_out_profile()
    assert "Anmelden" in client.get('/activity/fishing')
    assert "Anmelden" in client.get('/activity/hunting')

    # adding Beavis should result in a new invoice with the all inclusive
    # price, as well as the activity-specific price
    page = client.get('/activity/fishing').click("Anmelden")
    page.select_radio('attendee', "Beavis")
    page.form.submit().follow()

    page = client.get('/my-bills')
    assert str(page).count('110.00 Ausstehend') == 1
    help = [e.text.strip() for e in page.pyquery('.item-text')[:-2]]
    assert help == [
        'Ferienpass',
        'Fishing',
    ]

    # adding Butthead will incur an additional all-inclusive charge
    page = client.get('/activity/fishing').click("Anmelden")
    page.select_radio('attendee', "Butthead")
    page.form.submit()

    page = client.get('/my-bills')
    assert str(page).count('220.00 Ausstehend') == 1
    assert [e.text.strip() for e in page.pyquery('.item-text')[:-2]] == [
        'Ferienpass',
        'Fishing',
        'Ferienpass',
        'Fishing',
    ]

    # rename Beavis
    page = client.get('/my-bookings')
    page = page.click('Bearbeiten', index=0)
    page.form['last_name'] = 'Judge'
    page.form.submit()

    # adding Beavis to a second activity this way should not result in
    # an additional all-inclusive charge
    page = client.get('/activity/hunting').click("Anmelden")
    page.select_radio('attendee', "Beavis")
    page.form.submit()

    page = client.get('/my-bills')
    assert str(page).count('220.00 Ausstehend') == 0
    assert str(page).count('230.00 Ausstehend') == 1
    assert [e.text.strip() for e in page.pyquery('.item-text')[:-2]] == [
        'Ferienpass',
        'Fishing',
        'Hunting',
        'Ferienpass',
        'Fishing',
    ]

    # the name change should have changed the name on the invoce too
    assert [e.text.strip() for e in page.pyquery('.item-group strong')[:-1]
            ] == [
        'Beavis\xa0Judge',
        'Butthead'
    ]

    # none of this should have produced more than one invoice
    assert client.app.session().query(BookingPeriodInvoice).count() == 1


def test_booking_after_finalization_itemized(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(
        title="2019",
        confirmed=True,
        finalized=True,
        all_inclusive=False,
        booking_cost=5,
    )

    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(cost=95)
    scenario.add_activity(title="Hunting", state='accepted')
    scenario.add_occasion(cost=45)

    scenario.add_attendee(name="Beavis")
    scenario.add_attendee(name="Butthead")

    scenario.commit()

    # this is only possible as an Admin
    client.login_editor()
    client.fill_out_profile()
    assert "Anmelden" not in client.get('/activity/fishing')
    assert "Anmelden" not in client.get('/activity/hunting')

    client.login_admin()
    client.fill_out_profile()
    assert "Anmelden" in client.get('/activity/fishing')
    assert "Anmelden" in client.get('/activity/hunting')

    # adding Beavis should result in a new invoice with the cost of the
    # booking, plus the period booking cost
    page = client.get('/activity/fishing').click("Anmelden")
    page.select_radio('attendee', "Beavis")
    page.form.submit().follow()

    page = client.get('/my-bills')
    assert str(page).count('100.00 Ausstehend') == 1
    assert [e.text.strip() for e in page.pyquery('.item-text')[:-2]] == [
        'Fishing',
    ]

    # adding Beavis to a second booking, should do the same
    page = client.get('/activity/hunting').click("Anmelden")
    page.select_radio('attendee', "Beavis")
    page.form.submit().follow()

    page = client.get('/my-bills')
    assert str(page).count('150.00 Ausstehend') == 1
    assert [e.text.strip() for e in page.pyquery('.item-text')[:-2]] == [
        'Fishing',
        'Hunting',
    ]

    # adding Butthead should also result in a new invoice item
    page = client.get('/activity/fishing').click("Anmelden")
    page.select_radio('attendee', "Butthead")
    page.form.submit().follow()

    page = client.get('/my-bills')
    assert str(page).count('250.00 Ausstehend') == 1
    assert [e.text.strip() for e in page.pyquery('.item-text')[:-2]] == [
        'Fishing',
        'Hunting',
        'Fishing',
    ]

    # none of this should have produced more than one invoice
    assert client.app.session().query(BookingPeriodInvoice).count() == 1


def test_booking_after_finalization_for_anonymous(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(
        title="2019",
        phase='booking',
        confirmed=True,
        finalized=True,
        book_finalized=True,
        all_inclusive=False,
        deadline_days=1,
        booking_cost=5,
    )

    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(cost=95)
    scenario.add_activity(title="Hunting", state='accepted')
    scenario.add_occasion(cost=45)

    scenario.commit()

    # "Anmelden" is there three times, twice for ogc-login and once for the
    # occasion
    assert client.get('/activity/fishing').body.count(b"Anmelden") == 3
    assert client.get('/activity/hunting').body.count(b"Anmelden") == 3

    client.login_editor()
    assert client.get('/activity/fishing').body.count(b"Anmelden") == 1
    assert client.get('/activity/hunting').body.count(b"Anmelden") == 1

    client.login_admin()
    assert client.get('/activity/fishing').body.count(b"Anmelden") == 1
    assert client.get('/activity/hunting').body.count(b"Anmelden") == 1


@pytest.mark.parametrize('attendee_owner', [
    'anna.frisch@example.org',
    'admin@example.org'
])
def test_attendee_view(
    client: Client,
    scenario: Scenario,
    attendee_owner: str
) -> None:

    # Edit an attendee as administrator
    if not attendee_owner.startswith('admin'):
        scenario.add_user(username='anna.frisch@example.org')
    scenario.add_attendee(
        username=attendee_owner,
        name=f'Max{NAME_SEPARATOR}Frisch',
        birth_date=datetime(2020, 1, 1)
    )
    scenario.add_attendee(
        username=attendee_owner,
        name=f'Bruno{NAME_SEPARATOR}Frisch',
        birth_date=datetime(2020, 2, 1)
    )
    scenario.commit()
    scenario.refresh()
    client.login_admin()

    assert scenario.latest_attendee is not None
    page = client.get(f'/attendee/{scenario.latest_attendee.id}')
    # Unique Child is not in the row of first_name
    assert page.form['first_name'].value == 'Bruno'
    assert page.form['last_name'].value == 'Frisch'
    page.form['first_name'] = 'Max'
    page = page.form.submit()
    assert "Sie haben bereits eine Person mit diesem Namen erfasst" in page


def test_registration(client: Client) -> None:
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    assert 'volljährige Person eröffnet werden' not in register

    client.login_admin()
    page = client.get('/feriennet-settings')
    page.form['require_full_age_for_registration'] = True
    page.form.submit()
    client.logout()

    register = client.get('/auth/register')
    assert 'volljährige Person eröffnet werden' in register
    register.form['username'] = 'user@example.org'
    register.form['password'] = 'known_very_secure_password'
    register.form['confirm'] = 'known_very_secure_password'

    assert "Vielen Dank" in register.form.submit().follow()

    message = client.get_email(0)['HtmlBody']
    assert "Anmeldung bestätigen" in message

    expr = r'href="[^"]+">Anmeldung bestätigen</a>'
    url = re.search(expr, message).group()  # type: ignore[union-attr]
    url = client.extract_href(url)

    assert "Konto wurde aktiviert" in client.get(url).follow()
    assert "Konto wurde bereits aktiviert" in client.get(url).follow()

    logged_in = client.login(
        'user@example.org', 'known_very_secure_password').follow()
    assert "Ihr Benutzerprofil ist unvollständig" in logged_in


def test_view_qrbill(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="Ferienpass 2017", confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_attendee(name="Dustin", username='admin@example.org')
    scenario.add_booking(
        state='accepted', cost=100, username='admin@example.org'
    )
    scenario.commit()

    client.login_admin()

    page = client.get('/').click('Fakturierung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page.form.submit()

    page = client.get('/userprofile')
    page.form['salutation'] = 'mr'
    page.form['first_name'] = 'foo'
    page.form['last_name'] = 'bar'
    page.form['zip_code'] = '123'
    page.form['place'] = 'abc'
    page.form['address'] = 'abc'
    page.form['emergency'] = '123456789 Admin'
    page.form.submit()

    page = client.get('/feriennet-settings')
    page.form['bank_qr_bill'] = True
    page.form['bank_account'] = 'CH5604835012345678009'
    page.form['bank_beneficiary'] = (
        'Ferienpass Musterlingen, Bahnhofstr. 2, 1234 Beispiel'
    )
    page.form.submit()

    page = client.get('/my-bills?username=admin@example.org')
    assert '<img class="qr-bill" src="data:image/svg+xml;base64,' in page


@freeze_time("2022-05-01 18:00")
def test_activities_json(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="Ferienpass 2022", confirmed=True)
    activity = scenario.add_activity(
        title='Backen',
        lead='Backen mit Johann.',
        state='accepted',
        location='Bäckerei Govikon, Rathausplatz, 4001 Govikon',
        tags=['Farm', 'Adventure'],
        content={}
    )
    activity.coordinates = Coordinates(1.1, 2.2)
    occasion = scenario.add_occasion(
        age=(1, 11),
        cost=None,
        spots=(4, 5),
    )
    start_date = occasion.dates[0].localized_start.date().isoformat()
    scenario.add_occasion(
        age=(10, 15),
        cost=100,
        spots=(0, 10),
    )
    scenario.commit()

    assert client.get('/activities/json').json == {
        'period_name': 'Ferienpass 2022',
        'wish_phase_start': scenario.date_offset(-1).isoformat(),
        'wish_phase_end': date.today().isoformat(),
        'booking_phase_start': date.today().isoformat(),
        'booking_phase_end': scenario.date_offset(+10).isoformat(),
        'deadline_days': None,
        'activities': [{
            'age': {'min': 1, 'max': 15},
            'coordinate': {'lat': 1.1, 'lon': 2.2},
            'cost': {'min': 0.0, 'max': 100.0},
            'dates': [
                {
                    'start_date': start_date,
                    'start_time': '00:00:00',
                    'end_date': start_date,
                    'end_time': '01:00:00'
                },
                {
                    'start_date': start_date,
                    'start_time': '01:00:00',
                    'end_date': start_date,
                    'end_time': '02:00:00'
                },
            ],
            'image': {'thumbnail': None, 'full': None},
            'lead': 'Backen mit Johann.',
            'location': 'Bäckerei Govikon, Rathausplatz, 4001 Govikon',
            'provider': 'Govikon',
            'spots': 15,
            'tags': ['Abenteuer', 'Bauernhof', 'Halbtägig'],
            'title': 'Backen',
            'url': 'http://localhost/activity/backen',
            'zip_code': 4001
        }]
    }


def test_billing_with_date(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="2019", confirmed=True, finalized=False)
    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted', cost=100)
    scenario.commit()

    client.login_admin()

    settings = client.get('/feriennet-settings')
    settings.form['bank_account'] = 'CH6309000000250097798'
    settings.form['bank_beneficiary'] = 'Initech'
    settings.form.submit()

    page = client.get('/billing')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page.form.submit()

    page = client.get('/billing')
    assert 'Keine Rechnungen gefunden' not in page

    date = scenario.date_offset(+10).isoformat()
    form = page.click('Als bezahlt markieren mit bestimmten Datum')
    assert 'auf bezahlt setzen' in form
    form.form['payment_date'] = date
    form.form.submit()

    page = client.get('/billing?state=unpaid')
    assert 'Keine Rechnungen gefunden.' in page

    form = client.get('/export/rechnungspositionen')
    form.form['file_format'] = 'json'
    json_data = form.form.submit().json
    assert json_data[0]['Rechnungsposition Bezahlt'] == True
    assert json_data[0]['Zahlungsdatum'] == date


def test_mails_on_registration_and_cancellation(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(title="2019", confirmed=True, finalized=False,
                        phase="booking")
    scenario.add_activity(title="Drawing", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.commit()

    client.login_admin()

    page = client.get('/userprofile')
    page.form['salutation'] = 'mr'
    page.form['first_name'] = 'foo'
    page.form['last_name'] = 'bar'
    page.form['zip_code'] = '123'
    page.form['place'] = 'abc'
    page.form['address'] = 'abc'
    page.form['emergency'] = '123456789 Admin'
    page.form.submit()

    page = client.get('/activities')
    page = page.click('Drawing')
    form = page.click('Anmelden')
    form.form['attendee'] = 'other'
    form.form['first_name'] = 'Susan'
    form.form['last_name'] = 'Golding'
    form.form['birth_date'] = date.today() - timedelta(weeks=-12 * 52)
    form.form['gender'] = 'female'
    form.form['ignore_age'] = 'y'
    page = form.form.submit().follow()
    assert "war erfolgreich" in page

    page = client.get('/my-bookings')
    page = page.click('Buchung stornieren')

    mails = [client.get_email(i) for i in range(2)]
    confirmation = mails[0]
    text = "Vielen Dank!\n\nWir haben Ihre Buchung für Susan Golding erhalten."
    assert text in confirmation['TextBody']

    cancelation = mails[1]
    text = "Wir haben Ihre Abmeldung für Susan Golding erhalten."
    assert text in cancelation['TextBody']


def test_add_child_with_differing_address(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(title="2019", confirmed=True, finalized=False,
                        phase="booking")
    scenario.add_activity(title="Drawing", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.commit()

    client.login_admin()

    settings = client.get('/feriennet-settings')
    settings.form['show_political_municipality'] = 'y'
    settings.form.submit()

    client.fill_out_profile()

    page = client.get('/activities')
    page = page.click('Drawing')
    form = page.click('Anmelden')
    form.form['attendee'] = 'other'
    form.form['first_name'] = 'Susan'
    form.form['last_name'] = 'Golding'
    form.form['birth_date'] = date.today() - timedelta(weeks=-12 * 52)
    form.form['gender'] = 'female'
    form.form['differing_address'] = 'y'
    form.form['address'] = '31 St. Davids Hill'
    form.form['zip_code'] = '1212'
    form.form['place'] = 'Exeter'
    form.form['political_municipality'] = 'London'
    form.form['ignore_age'] = 'y'
    page = form.form.submit().follow()
    assert "war erfolgreich" in page

    page = client.get('/billing')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page.form.submit()

    form = client.get('/export/rechnungspositionen')
    form.form['file_format'] = 'json'
    json_data = form.form.submit().json
    assert json_data[0]['Teilnehmeradresse'] == '31 St. Davids Hill'
    assert json_data[0]['Teilnehmer PLZ'] == '1212'
    assert json_data[0]['Teilnehmer Ort'] == 'Exeter'
    assert json_data[0]['Teilnehmer Politische Gemeinde'] == 'London'


def test_add_child_without_political_municipality(
    client: Client,
    scenario: Scenario
) -> None:

    scenario.add_period(title="2023", confirmed=True, finalized=False,
                        phase='booking')
    scenario.add_activity(title="Skating", state='accepted')
    scenario.add_occasion(cost=1)
    scenario.commit()

    client.login_admin()
    client.fill_out_profile()
    page = client.get('/feriennet-settings')
    page.form['show_political_municipality'] = False
    page.form.submit()

    page = client.get('/activity/skating').click('Anmelden')
    # with differing address
    page.form['first_name'] = "Tom"
    page.form['last_name'] = "Sawyer"
    page.form['birth_date'] = "2017-01-01"
    page.form['gender'] = 'male'
    page.form['differing_address'] = True
    page.form['address'] = 'Somestreet'
    page.form['zip_code'] = '4052'
    page.form['place'] = 'Somecity'
    page = page.form.submit().follow()
    assert 'war erfolgreich' in page

    # without differing address
    page = client.get('/activity/skating').click('Anmelden')
    page.form['attendee'] = 'other'  # Neue Person erfassen
    page.form['first_name'] = "Lisa"
    page.form['last_name'] = "Sawyer"
    page.form['birth_date'] = "2019-01-01"
    page.form['gender'] = 'female'
    page.form['differing_address'] = False
    page.form['ignore_age'] = True
    page = page.form.submit().follow()
    assert 'war erfolgreich' in page


def test_view_dashboard(client: Client, scenario: Scenario) -> None:
    scenario.add_period(title="2019", confirmed=True, finalized=False)
    scenario.add_activity(title="Pet Zoo", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_occasion(cost=200)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted')

    # Activities and occasions with state 'preview' will not appear
    # on the dashboard
    scenario.add_activity(title="Cooking", state='preview')
    scenario.add_occasion(cost=50)
    scenario.add_occasion(cost=60)
    scenario.commit()

    client.login_admin()

    page = client.get('/dashboard')
    assert page.pyquery('.activities .facts tr:first-child').text(
        ) == "1\nAngebote"
    assert page.pyquery('.activities .facts tr:nth-child(2)').text(
        ) == "2\nDurchführungen"
    assert page.pyquery('.activities .facts tr:nth-child(5)').text(
        ) == "1\ndurchführbar"
    assert page.pyquery('.activities .facts tr:nth-child(7)').text(
        ) == "1\nunbelegt"

    # ensure only feriennet boardlets are shown
    assert len(page.pyquery('.boardlet')) == 6
