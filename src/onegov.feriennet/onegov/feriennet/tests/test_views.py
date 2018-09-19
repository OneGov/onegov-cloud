import onegov.feriennet
import requests_mock

from datetime import datetime, timedelta, date, time
from freezegun import freeze_time
from onegov.activity.utils import generate_xml
from onegov.core.custom import json
from onegov.pay import Payment
from onegov_testing import utils
from psycopg2.extras import NumericRange
from webtest import Upload


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.feriennet, onegov.feriennet.FeriennetApp)


def test_activity_permissions(client, scenario):
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
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)

    editor.get(url).click("Publikation beantragen")

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket.click("Veröffentlichen")

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert editor.get(url, status=200)
    assert anon.get(url, status=200)
    assert admin.get(url, status=200)

    ticket = admin.get(ticket.request.url)
    ticket.click("Archivieren")

    assert "Learn How to Program" in editor.get('/activities')
    assert "Learn How to Program" not in anon.get('/activities')
    assert "Learn How to Program" in admin.get('/activities')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)


def test_activity_communication(client, scenario):
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

    assert len(client.app.smtp.outbox) == 1
    assert "Ein neues Ticket" in admin.get_email(0)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Learn Python" in ticket

    ticket.click("Veröffentlichen")
    assert len(client.app.smtp.outbox) == 2

    message = admin.get_email(1)
    assert "wurde veröffentlicht" in message
    assert "Learn Python" in message
    assert "Using a Raspberry Pi we will learn Python" in message


def test_activity_search(client_with_es, scenario):
    client = client_with_es

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
    client.app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' not in admin.get('/search?q=Learn')
    assert 'search-result-vacation' not in editor.get('/search?q=Learn')
    assert 'search-result-vacation' not in client.get('/search?q=Learn')

    url = '/activity/learn-how-to-program'
    editor.get(url).click("Publikation beantragen")

    # once proposed, activities can be found by the admin only
    client.app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/search?q=Learn')
    assert 'search-result-vacation' not in editor.get('/search?q=Learn')
    assert 'search-result-vacation' not in client.get('/search?q=Learn')

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    ticket.click("Veröffentlichen")

    # once accepted, activities can be found by anyone
    client.app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/search?q=Learn')
    assert 'search-result-vacation' in editor.get('/search?q=Learn')
    assert 'search-result-vacation' in client.get('/search?q=Learn')

    ticket = admin.get(ticket.request.url)
    ticket.click("Archivieren")

    # archived the search will fail again, except for admins
    client.app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/search?q=Learn')
    assert 'search-result-vacation' not in editor.get('/search?q=Learn')
    assert 'search-result-vacation' not in client.get('/search?q=Learn')


def test_activity_filter_tags(client, scenario):
    scenario.add_period(
        prebooking_start=datetime(2015, 1, 1),
        prebooking_end=datetime(2015, 12, 31),
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

    page = page.click('Computer')
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


def test_activity_filter_duration(client, scenario):
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

    half_day = client.get('/activities').click('Halbtägig')
    many_day = client.get('/activities').click('Mehrtägig')

    assert "Meeting" in half_day
    assert "Retreat" not in half_day

    assert "Meeting" not in many_day
    assert "Retreat" in many_day

    # shorten the retreat
    with scenario.update():
        scenario.occasions[0].dates[0].end -= timedelta(days=1)

    full_day = client.get('/activities').click('Ganztägig')
    many_day = client.get('/activities').click('Mehrtägig')

    assert "Retreat" in full_day
    assert "Retreat" not in many_day


def test_activity_filter_age_ranges(client, scenario):
    scenario.add_period()

    # the retreat is for really young kids
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion(age=(0, 10))

    # the meeting is for young to teenage kids
    scenario.add_activity(title="Meeting", state='accepted')
    scenario.add_occasion(age=(5, 15))

    scenario.commit()

    preschool = client.get('/activities').click('3 - 6 Jahre')
    highschool = client.get('/activities').click('14 - 17 Jahre')

    assert "Retreat" in preschool
    assert "Meeting" in preschool

    assert "Retreat" not in highschool
    assert "Meeting" in highschool

    # change the meeting age
    with scenario.update():
        scenario.occasions[1].age = NumericRange(15, 20)

    preschool = client.get('/activities').click('3 - 6 Jahre')

    assert "Retreat" in preschool
    assert "Meeting" not in preschool


def test_organiser_info(client, scenario):

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
        assert not editor.get(f'/activity/{id}').pyquery('.organiser li')
        assert not admin.get(f'/activity/{id}').pyquery('.organiser li')

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
    contact.form['phone'] = '+41 23 456 789'
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
    contact = admin.get('/usermanagement')\
        .click('editor@example.org')\
        .click('Bearbeiten')

    contact.form['organisation'] = 'Admins Association'
    contact.form.submit()

    activity = editor.get('/activity/play-with-legos')

    assert "Admins Association" in activity

    # we can show/hide information individually
    def with_public_organiser_data(values):
        page = admin.get('/settings')
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
    assert "+41 23 456 789" not in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['email'])
    assert "Admins Association" not in page
    assert "Washington" not in page
    assert "editors-association@example.org" in page
    assert "+41 23 456 789" not in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['phone'])
    assert "Admins Association" not in page
    assert "Washington" not in page
    assert "editors-association@example.org" not in page
    assert "+41 23 456 789" in page
    assert "https://www.example.org" not in page

    page = with_public_organiser_data(['website'])
    assert "Admins Association" not in page
    assert "Washington" not in page
    assert "editors-association@example.org" not in page
    assert "+41 23 456 789" not in page
    assert "https://www.example.org" in page


def test_occasions_form(client, scenario):

    editor = client.spawn()
    editor.login_editor()

    admin = client.spawn()
    admin.login_admin()

    scenario.add_period(
        prebooking_start=date(2016, 9, 1),
        prebooking_end=date(2016, 9, 30),
        execution_start=date(2016, 10, 1),
        execution_end=date(2016, 10, 31),
        deadline_date=date(2016, 10, 1)
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
    assert "30 - 40 Teilnehmer" in activity
    assert "Franz Karl Weber" in activity
    assert "No griefers" in activity

    occasion = activity.click("Bearbeiten", index=1)
    occasion.form['min_age'] = 15
    activity = occasion.form.submit().follow()
    assert "15 - 20 Jahre" in activity

    occasion = activity.click("Duplizieren")
    occasion.form['min_age'] = 10
    activity = occasion.form.submit().follow()
    assert "15 - 20 Jahre" in activity
    assert "10 - 20 Jahre" in activity

    activity.click("Löschen", index=0)
    activity.click("Löschen", index=1)

    assert "keine Durchführungen" in editor.get('/activity/play-with-legos')


def test_multiple_dates_occasion(client, scenario):

    editor = client.spawn()
    editor.login_editor()

    admin = client.spawn()
    admin.login_admin()

    scenario.add_period(
        prebooking_start=date(2016, 9, 1),
        prebooking_end=date(2016, 9, 30),
        execution_start=date(2016, 10, 1),
        execution_end=date(2016, 10, 31),
        deadline_date=date(2016, 10, 1)
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


def test_execution_period(client, scenario):

    admin = client.spawn()
    admin.login_admin()

    scenario.add_period(
        prebooking_start=date(2016, 9, 1),
        prebooking_end=date(2016, 9, 30),
        execution_start=date(2016, 10, 1),
        execution_end=date(2016, 10, 1),
        deadline_date=date(2016, 10, 1)
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


def test_enroll_child(client, scenario):
    scenario.add_period()
    scenario.add_activity(title="Retreat", state='accepted')
    scenario.add_occasion()
    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=False
    )
    scenario.commit()

    activity = client.get('/activity/retreat')

    login = activity.click("Anmelden")
    assert "Login" in login

    login.form['username'] = 'member@example.org'
    login.form['password'] = 'hunter2'
    enroll = login.form.submit().follow()
    assert "Ihr Benutzerprofil ist unvollständig" in enroll

    # now that we're logged in, the login link automatically skips ahead
    enroll = activity.click("Anmelden").follow()
    assert "Teilnehmer anmelden" in enroll

    # the link changes, but the result stays the same
    enroll = client.get('/activity/retreat').click("Anmelden")
    assert "Teilnehmer anmelden" in enroll

    enroll.form['first_name'] = "Tom"
    enroll.form['last_name'] = "Sawyer"
    enroll.form['birth_date'] = "2012-01-01"
    enroll.form['gender'] = 'male'
    enroll = enroll.form.submit()

    # before continuing, the user needs to fill his profile
    assert "Ihr Benutzerprofil ist unvollständig" in enroll
    client.fill_out_profile()

    activity = enroll.form.submit().follow()
    assert "zu Tom\u00A0Sawyer's Wunschliste hinzugefügt" in activity

    # prevent double-subscriptions
    enroll = activity.click("Anmelden")
    assert "Tom\u00A0Sawyer hat sich bereits für diese Durchführung"\
        in enroll.form.submit()

    enroll.form['attendee'] = 'other'
    enroll.form['first_name'] = "Tom"
    enroll.form['last_name'] = "Sawyer"
    enroll.form['birth_date'] = "2011-01-01"
    enroll.form['gender'] = 'male'

    # prevent adding two kids with the same name
    assert "Sie haben bereits ein Kind mit diesem Namen eingegeben"\
        in enroll.form.submit()

    # prevent enrollment for inactive periods
    with scenario.update():
        scenario.latest_period.active = False

    enroll.form['first_name'] = "Huckleberry"
    enroll.form['last_name'] = "Finn"
    assert "Diese Durchführung liegt ausserhalb des aktiven Zeitraums"\
        in enroll.form.submit()

    # prevent enrollment outside of prebooking
    with scenario.update():
        scenario.latest_period.active = True
        scenario.latest_period.prebooking_start -= timedelta(days=10)
        scenario.latest_period.prebooking_end -= timedelta(days=10)

    assert "nur während der Wunschphase" in enroll.form.submit()

    # set the record straight again
    with scenario.update():
        scenario.latest_period.prebooking_start += timedelta(days=10)
        scenario.latest_period.prebooking_end += timedelta(days=10)

    enroll.form['first_name'] = "Huckleberry"
    enroll.form['last_name'] = "Finn"
    activity = enroll.form.submit().follow()

    assert "zu Huckleberry\u00A0Finn's Wunschliste hinzugefügt" in activity

    # prevent booking over the limit
    with scenario.update():
        scenario.latest_period.all_inclusive = True
        scenario.latest_period.confirmed = True
        scenario.latest_period.max_bookings_per_attendee = 1

        scenario.add_activity(title="Another Retreat", state='accepted')
        scenario.add_occasion()

    enroll = client.get('/activity/another-retreat').click("Anmelden")
    enroll.form.submit()

    assert "maximale Anzahl von 1 Buchungen" in enroll.form.submit()

    # prevent booking one activity more than once
    with scenario.update():
        scenario.latest_period.all_inclusive = False
        scenario.latest_period.max_bookings_per_attendee = None
        scenario.latest_period.confirmed = False
        scenario.add_occasion()

    enroll = client.get('/activity/another-retreat').click("Anmelden", index=0)
    enroll = enroll.form.submit()

    enroll = client.get('/activity/another-retreat').click("Anmelden", index=1)
    enroll = enroll.form.submit()

    assert "bereits eine andere Durchführung dieses Angebots gebucht" in enroll


def test_enroll_age_mismatch(client, scenario):
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


def test_enroll_after_wishlist_phase(client, scenario):
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


def test_booking_view(client, scenario):
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
    def count(page):
        return len(page.pyquery('.attendee-bookings .booking'))

    c1_bookings = c1.get('/').click('Wunschliste')
    c2_bookings = c2.get('/').click('Wunschliste')

    assert count(c1_bookings) == 4
    assert count(c2_bookings) == 1

    # make sure each user only has access to their own bookings
    def star_url(page, index):
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
    assert "maximal drei Favoriten" in result.headers.get('X-IC-Trigger-Data')

    # users may switch between other periods
    url = c1_bookings.pyquery('select option:first').val()
    assert "Noch keine Buchungen" in c1.get(url)

    # admins may switch between other users
    admin = client.spawn()
    admin.login_admin()

    page = admin.get('/').click('Wunschliste')
    url = page.pyquery('select:last option:nth-child(3)').val()

    m1_bookings = admin.get(url)

    assert count(m1_bookings) == 4


def test_confirmed_booking_view(scenario, client):
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
        scenario.latest_period.confirmed = False
        scenario.latest_booking.state = 'accepted'

    page = client.get('/my-bookings')
    assert "Offen" in page
    assert "Stornieren" not in page
    assert "Entfernen" in page
    assert "Gebucht" not in page

    # Related contacts are hidden at this point
    page = client.get('/settings')
    page.form['show_related_contacts'] = True
    page.form.submit()

    page = client.get('/my-bookings')
    assert not page.pyquery('.attendees-toggle')
    assert "Elternteil" not in page

    # When the period is confirmed, the state is shown
    with scenario.update():
        scenario.latest_period.confirmed = True

    page = client.get('/my-bookings')
    assert "Gebucht" in page
    assert "Stornieren" in page
    assert "Entfernen" not in page
    assert "nicht genügend Teilnehmer" not in page

    # Related contacts are now visible
    assert page.pyquery('.attendees-toggle').text() == '1 Teilnehmer'
    assert "Elternteil" in page

    # Unless that option was disabled
    page = client.get('/settings')
    page.form['show_related_contacts'] = False
    page.form.submit()

    page = client.get('/my-bookings')
    assert not page.pyquery('.attendees-toggle')
    assert "Elternteil" not in page

    # Other states are shown too
    states = [
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
        scenario.latest_occasion.spots = NumericRange(2, 5)

    page = client.get('/my-bookings')
    assert "nicht genügend Teilnehmer" in page


def test_direct_booking_and_storno(client, scenario):
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
    client.get('/my-bookings').click("Stornieren")

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


def test_cancel_occasion(client, scenario):
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

    client.get('/my-bookings').click("Entfernen")
    page = client.get('/activity/foobar')
    assert "Löschen" in page
    assert "Absagen" not in page
    assert "Reaktivieren" not in page

    page.click("Löschen")


def test_reactivate_cancelled_booking(client, scenario):
    scenario.add_period()
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(
        age=(0, 10),
        spots=(0, 2),
        cost=100
    )
    scenario.add_occasion(
        age=(0, 10),
        spots=(0, 2),
        cost=1000
    )
    scenario.add_attendee(
        name="Dustin",
        birth_date=(datetime.today() - timedelta(days=5 * 360))
    )
    scenario.commit()

    client.login_admin()
    client.fill_out_profile()

    # by default we block conflicting bookings
    page = client.get('/activity/foobar').click('Anmelden', index=0)
    page = page.form.submit().follow()

    assert "Wunschliste hinzugefügt" in page

    page = client.get('/activity/foobar').click('Anmelden', index=0)
    assert "bereits für diese Durchführung angemeldet" in page.form.submit()

    page = client.get('/activity/foobar').click('Anmelden', index=1)
    assert "eine andere Durchführung" in page.form.submit()

    # unless they are cancelled
    scenario.c.bookings.query().first().state = 'cancelled'
    scenario.commit()  # can be done by cancelling the whole event in UI

    page = client.get('/activity/foobar').click('Anmelden', index=0)
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()

    # this also works between multiple occasions of the same activity
    scenario.c.bookings.query().first().state = 'cancelled'
    scenario.commit()  # can be done by cancelling the whole event in UI

    page = client.get('/activity/foobar').click('Anmelden', index=1)
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()

    # including denied bookings
    scenario.c.bookings.query().first().state = 'denied'
    scenario.commit()  # can be done by cancelling the whole event in UI

    page = client.get('/activity/foobar').click('Anmelden', index=1)
    assert "Wunschliste hinzugefügt" in page.form.submit().follow()

    # and even if we confirm the period
    page = client.get('/activities').click('Zuteilung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page.form.submit()

    client.get('/my-bookings').click("Stornieren")
    page = client.get('/activity/foobar').click('Anmelden', index=0)
    assert "war erfolgreich" in page.form.submit().follow()

    page = client.get('/my-bookings').click("Stornieren")
    page = client.get('/activity/foobar').click('Anmelden', index=1)
    assert "war erfolgreich" in page.form.submit().follow()


def test_occasion_attendance_collection(client, scenario):
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


def test_send_email(client, scenario):
    scenario.add_period(title="Ferienpass 2016")
    scenario.commit()

    client.login_admin()

    page = client.get('/notifications').click('Neue Mitteilungs-Vorlage')
    page.form['subject'] = '[Zeitraum] subject'
    page.form['text'] = '[Zeitraum] body'
    page = page.form.submit().follow()

    page = page.click('Versand')
    assert "Ferienpass 2016 subject" in page
    assert "Ferienpass 2016 body" in page
    assert "keine Empfänger gefunden" in page.form.submit()

    page.form['roles'] = ['admin', 'editor']
    assert "an 2 Empfänger gesendet" in page.form.submit().follow()
    assert len(client.app.smtp.outbox) == 2

    message = client.get_email(0)
    assert "Ferienpass 2016 subject" in client.app.smtp.outbox[0]['subject']
    assert "Ferienpass 2016 body" in message


def test_create_duplicate_notification(client):
    client.login_admin()

    page = client.get('/notifications').click('Neue Mitteilungs-Vorlage')
    page.form['subject'] = 'Foo'
    page.form['text'] = 'Bar'

    page.form.submit().follow()
    assert "existiert bereits" in page.form.submit()


def test_import_account_statement(client, scenario):
    scenario.add_period(confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(state='accepted', cost=100)
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()

    page = admin.get('/').click('Fakturierung')
    page.form['confirm'] = 'yes'
    page.form['sure'] = 'yes'
    page = page.form.submit()

    page = page.click('Kontoauszug importieren')
    assert "kein Bankkonto" in page

    settings = page.click('Einstellungen', index=1)
    settings.form['bank_account'] = 'CH6309000000250097798'
    settings.form['bank_beneficiary'] = 'Initech'
    settings = settings.form.submit()

    page = page.click('Rechnungen')
    code = page.pyquery('.invoice-items-payment li:last').text()

    page = page.click('Fakturierung').click('Kontoauszug importieren')
    assert "kein Bankkonto" not in page

    xml = generate_xml([
        dict(amount='100.00 CHF', note=code)
    ])

    page.form['xml'] = Upload(
        'account.xml',
        xml.encode('utf-8'),
        'application/xml'
    )

    page = page.form.submit()

    assert "1 Zahlungen importieren" in page
    page.click("1 Zahlungen importieren")

    page = admin.get('/my-bills')
    assert "1 Zahlungen wurden importiert" in page
    assert "unpaid" not in page

    page = page.click('Fakturierung').click('Kontoauszug importieren')
    page.form['xml'] = Upload(
        'account.xml',
        xml.encode('utf-8'),
        'application/xml'
    )
    page = page.form.submit()

    assert "0 Zahlungen importieren" in page


def test_deadline(client, scenario):
    deadline = datetime.utcnow().date() - timedelta(days=1)

    scenario.add_period(deadline_date=deadline)
    scenario.add_activity(title="Foo", state='accepted')
    scenario.add_occasion()
    scenario.commit()

    # show no 'enroll' for ordinary users past the deadline
    assert "Anmelden" not in client.get('/activity/foo')

    # do show it for admins though and allow signups
    admin = client.spawn()
    admin.login_admin()

    assert "Anmelden" in admin.get('/activity/foo')

    page = admin.get('/activity/foo').click("Anmelden")
    assert "Der Anmeldeschluss wurde erreicht" not in page.form.submit()

    # stop others, even if they get to the form
    editor = client.spawn()
    editor.login_editor()

    page = editor.get(page.request.url.replace('http://localhost', ''))
    assert "Der Anmeldeschluss wurde erreicht" in page.form.submit()


def test_userprofile_login(client):
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


def test_provide_activity_again(client, scenario):
    scenario.add_period()
    scenario.add_activity(title="Learn How to Program")
    scenario.add_occasion()
    scenario.commit()

    admin = client.spawn()
    admin.login_admin()

    assert "Erneut anbieten" not in admin.get('/activities')

    with scenario.update():
        scenario.latest_activity.state = 'archived'

    assert "Erneut anbieten" in admin.get('/activities')

    editor = client.spawn()
    editor.login_editor()

    editor.post('/activity/learn-how-to-program/offer-again', status=404)
    scenario.refresh()
    assert scenario.latest_activity.state == 'archived'

    admin.post('/activity/learn-how-to-program/offer-again')
    scenario.refresh()
    assert scenario.latest_activity.state == 'preview'


def test_online_payment(client, scenario):
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

        m.get('https://api.stripe.com/v1/charges?limit=50', json={
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

        m.get('https://api.stripe.com/v1/payouts?limit=50&status=paid', json={
            "object": "list",
            "url": "/v1/payouts",
            "has_more": False,
        })

        page = client.get('/billing?expand=1')
        page = page.click('Online Zahlungen synchronisieren').follow()

        assert "Synchronisierung erfolgreich" in page
        assert ">Bezahlt<" in page

        page = client.get('/payments')
        assert ">Offen<" not in page
        assert ">Bezahlt<" in page

    page = client.get('/payments')
    assert "Ferienpass 2017" in page
    assert "Stripe Connect" in page
    assert "96.80" in page
    assert "3.20" in page

    page = client.get('/billing')
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

    page = client.get('/billing?expand=1')
    assert ">Unbezahlt<" in page

    page = client.get('/payments')
    assert ">Rückerstattet<" in page

    page = client.get('/my-bills')
    assert 'checkout-button' in page
    assert "Jetzt online bezahlen" in page

    # it should be possible to change the payment state again
    client.get('/billing').click("Rechnung als bezahlt markieren")
    client.get('/billing').click("Rechnung als unbezahlt markieren")

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
    assert ">Offen<" in page
    assert ">Rückerstattet<" in page


def test_icalendar_subscription(client, scenario):
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
        scenario.latest_period.confirmed = False
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
    assert 'DTSTART;VALUE=DATE-TIME:20161125T070000Z' in calendar
    assert 'DTEND;VALUE=DATE-TIME:20161125T150000Z' in calendar


def test_fill_out_contact_form(client):
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

    assert len(client.app.smtp.outbox) == 1


def test_book_alternate_occasion(client, scenario):
    scenario.add_period(title="Ferienpass 2018")
    scenario.add_activity(title="Fishing", state='accepted')
    scenario.add_occasion()
    scenario.add_attendee(birth_date=date.today() - timedelta(days=8 * 360))
    scenario.add_booking(state='blocked')
    scenario.add_occasion()
    scenario.commit()

    scenario.refresh()
    assert scenario.latest_booking.occasion == scenario.occasions[0]

    client.login_admin()
    client.fill_out_profile()

    # before period confirmation, the blocked booking must remain
    page = client.get('/activity/fishing').click('Anmelden', index=1)
    page = page.form.submit()

    assert "bereits eine andere Durchführung dieses Angebots" in page

    with scenario.update():
        scenario.latest_period.confirmed = True

    # we should be able to directly book occasion two,
    # which should remove occasion one's booking
    page = client.get('/activity/fishing').click('Anmelden', index=1)
    page = page.form.submit().follow()

    assert "bereits eine andere Durchführung dieses Angebots" not in page

    scenario.refresh()
    assert scenario.latest_booking.occasion == scenario.occasions[1]


def test_occasion_number(client, scenario):
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


def test_main_views_without_period(client):
    client.login_admin()

    # 99.9% of the time, there's a period for the following views -
    # if there isn't we must be sure to not show an exeption (this happens
    # because we tend to be very optimistic about periods being there)
    assert client.get('/activities').status_code == 200
    assert client.get('/my-bookings').status_code == 200
    assert client.get('/notifications').status_code == 200

    assert client.get('/matching', expect_errors=True).status_code == 404
    assert client.get('/billing', expect_errors=True).status_code == 404


def test_book_alternate_occasion_regression(client, scenario):
    scenario.add_period(title="Ferienpass", phase='booking', confirmed=True)
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

    client.get('/my-bookings').click("Stornieren")

    page = client.get('/activity/hunting').click("Anmelden")
    page = page.form.submit()

    assert 'bereits für diese Durchführung' not in page


def test_view_archived_occasions(client, scenario):
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
    scenario.latest_activity.username = 'editor@example.org'
    scenario.commit()

    assert '1. Durchführung' in client.get('/activity/fishing')

    # they do not get any action links however
    assert 'Duplizieren' not in client.get('/activity/fishing')

    # admins see archived occasions
    client = client.spawn()
    client.login_admin()

    assert '1. Durchführung' in client.get('/activity/fishing')
    assert 'Duplizieren' in client.get('/activity/fishing')


def test_no_new_activites_without_active_period(client, scenario):
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
    scenario.latest_period.active = False
    scenario.commit()

    page = client.get('/activities')
    assert "Angebot erneut anbieten" not in page
    assert "Angebot erfassen" not in page

    page = client.get('/activity/fishing')
    assert "Erneut anbieten" not in page


def test_no_state_before_wishlist_phase_starts(client, scenario):

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
