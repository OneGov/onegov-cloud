import onegov.feriennet
import transaction

from datetime import datetime, timedelta, date
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.core.utils import Bunch
from onegov.org.testing import Client, get_message, select_checkbox
from onegov.testing import utils
from onegov.user import UserCollection
from psycopg2.extras import NumericRange


def get_post_url(page, css_class):
    return page.pyquery('a.{}'.format(css_class)).attr('ic-post-to')


def get_delete_link(page, index=0):
    return page.pyquery('a[ic-delete-from]')[index].attrib['ic-delete-from']


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.feriennet, onegov.feriennet.FeriennetApp)


def test_activity_permissions(es_feriennet_app):
    anon = Client(es_feriennet_app)

    admin = Client(es_feriennet_app)
    admin.login_admin()

    editor = Client(es_feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    url = '/angebot/learn-how-to-program'

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)

    editor.post(get_post_url(editor.get(url), 'request-publication'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    admin.post(get_post_url(ticket, 'accept-activity'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url, status=200)
    assert anon.get(url, status=200)
    assert admin.get(url, status=200)

    ticket = admin.get(ticket.request.url)
    admin.post(get_post_url(ticket, 'archive-activity'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url, status=200)
    assert anon.get(url, status=404)
    assert admin.get(url, status=200)


def test_activity_communication(feriennet_app):
    admin = Client(feriennet_app)
    admin.login_admin()

    editor = Client(feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn PHP"
    new.form['lead'] = "Using a Raspberry Pi we will learn PHP"
    new.form.submit()

    editor.post(get_post_url(
        editor.get('/angebot/learn-php'), 'request-publication'))

    assert len(feriennet_app.smtp.outbox) == 1
    assert "Ein neues Ticket" in get_message(feriennet_app, 0)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen", index=0).follow()
    assert "Learn PHP" in ticket

    admin.post(get_post_url(ticket, 'reject-activity'))
    assert len(feriennet_app.smtp.outbox) == 2
    message = get_message(feriennet_app, 1)
    assert "leider abgelehnt" in message
    assert "Learn PHP" in message
    assert "Using a Raspberry Pi we will learn PHP" in message

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn Python"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    editor.post(get_post_url(
        editor.get('/angebot/learn-python'), 'request-publication'))

    assert len(feriennet_app.smtp.outbox) == 3
    assert "Ein neues Ticket" in get_message(feriennet_app, 2)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Learn Python" in ticket

    admin.post(get_post_url(ticket, 'accept-activity'))
    assert len(feriennet_app.smtp.outbox) == 4
    message = get_message(feriennet_app, 3)
    assert "wurde angenommen" in message
    assert "Learn Python" in message
    assert "Using a Raspberry Pi we will learn Python" in message


def test_activity_search(es_feriennet_app):
    anon = Client(es_feriennet_app)

    admin = Client(es_feriennet_app)
    admin.login_admin()

    editor = Client(es_feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    url = '/angebot/learn-how-to-program'

    # in preview, activities can't be found
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' not in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anon.get('/suche?q=Learn')

    editor.post(get_post_url(editor.get(url), 'request-publication'))

    # once proposed, activities can be found by the admin only
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anon.get('/suche?q=Learn')

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    admin.post(get_post_url(ticket, 'accept-activity'))

    # once accepted, activities can be found by anyone
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' in anon.get('/suche?q=Learn')

    ticket = admin.get(ticket.request.url)
    admin.post(get_post_url(ticket, 'archive-activity'))

    # archived the search will fail again, except for admins
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anon.get('/suche?q=Learn')


def test_activity_filter_tags(feriennet_app):

    anon = Client(feriennet_app)

    editor = Client(feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"

    select_checkbox(new, "tags", "Computer")
    select_checkbox(new, "tags", "Wissenschaft")

    new.form.submit()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Cook"
    new.form['lead'] = "Using a Stove we will cook a Python"

    select_checkbox(new, "tags", "Kochen")
    select_checkbox(new, "tags", "Wissenschaft")

    new.form.submit()

    for activity in ActivityCollection(feriennet_app.session()).query().all():
        activity.propose().accept()

    transaction.commit()

    activities = anon.get('/angebote')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Computer')
    assert "Learn How to Cook" not in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Computer')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Kochen')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" not in activities

    activities = activities.click('Computer')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Computer')
    activities = activities.click('Kochen')
    activities = activities.click('Wissenschaft')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    # the state filter works for editors
    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Dance"
    new.form['lead'] = "We will dance with a Python"
    new.form.submit()

    # editors see the state as a filter
    assert "Vorschau" in editor.get('/angebote')

    # anonymous does not
    assert "Vorschau" not in anon.get('/angebote')

    activities = editor.get('/angebote').click('Vorschau')
    assert "Learn How to Cook" not in activities
    assert "Learn How to Program" not in activities
    assert "Learn How to Dance" in activities


def test_activity_filter_duration(feriennet_app):
    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())

    retreat = activities.add("Retreat", username='admin@example.org')
    meeting = activities.add("Meeting", username='admin@example.org')

    period = periods.add(
        title="2016",
        prebooking=(datetime(2015, 1, 1), datetime(2015, 12, 31)),
        execution=(datetime(2016, 1, 1), datetime(2016, 12, 31)),
        active=True
    )

    retreat.propose().accept()
    meeting.propose().accept()

    # the retreat lasts a weekend
    reatreat_occasion_id = occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        timezone="Europe/Zurich",
        activity=retreat,
        period=period
    ).id

    # the meeting lasts half a day
    occasions.add(
        start=datetime(2016, 10, 10, 8),
        end=datetime(2016, 10, 10, 12),
        timezone="Europe/Zurich",
        activity=meeting,
        period=period
    )

    transaction.commit()

    client = Client(feriennet_app)

    half_day = client.get('/angebote').click('Halbtägig')
    many_day = client.get('/angebote').click('Mehrtägig')

    assert "Meeting" in half_day
    assert "Retreat" not in half_day

    assert "Meeting" not in many_day
    assert "Retreat" in many_day

    # shorten the retreat
    occasions.by_id(reatreat_occasion_id).end -= timedelta(days=1)
    transaction.commit()

    full_day = client.get('/angebote').click('Ganztägig')
    many_day = client.get('/angebote').click('Mehrtägig')

    assert "Retreat" in full_day
    assert "Retreat" not in many_day


def test_activity_filter_age_ranges(feriennet_app):
    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())

    retreat = activities.add("Retreat", username='admin@example.org')
    meeting = activities.add("Meeting", username='admin@example.org')

    period = periods.add(
        title="2016",
        prebooking=(datetime(2015, 1, 1), datetime(2015, 12, 31)),
        execution=(datetime(2016, 1, 1), datetime(2016, 12, 31)),
        active=True
    )

    retreat.propose().accept()
    meeting.propose().accept()

    # the retreat lasts a weekend
    occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        age=(0, 10),
        timezone="Europe/Zurich",
        activity=retreat,
        period=period
    )

    # the meeting lasts half a day
    meeting_occasion_id = occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        age=(5, 15),
        timezone="Europe/Zurich",
        activity=meeting,
        period=period
    ).id

    transaction.commit()

    client = Client(feriennet_app)

    preschool = client.get('/angebote').click('Vorschule')
    highschool = client.get('/angebote').click('Oberstufe')

    assert "Retreat" in preschool
    assert "Meeting" in preschool

    assert "Retreat" not in highschool
    assert "Meeting" in highschool

    # change the meeting age
    occasions.by_id(meeting_occasion_id).age = NumericRange(15, 20)
    transaction.commit()

    preschool = client.get('/angebote').click('Vorschule')

    assert "Retreat" in preschool
    assert "Meeting" not in preschool


def test_organiser_info(feriennet_app):

    admin = Client(feriennet_app)
    admin.login_admin()

    editor = Client(feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Play with Legos"
    new.form['lead'] = "Like Minecraft, but in the real world"
    new.form.submit()

    new = admin.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Play with Playmobil"
    new.form['lead'] = "Like Second Life, but in the real world"
    new.form.submit()

    for activity in ActivityCollection(feriennet_app.session()).query().all():
        activity.propose().accept()

    transaction.commit()

    # by default the email address of the owner is shown
    assert 'editor@example.org' in admin.get('/angebot/play-with-legos')
    assert 'admin@example.org' in editor.get('/angebot/play-with-playmobil')

    # only the owner gets the change contact link
    assert "Kontakt ändern" in editor.get('/angebot/play-with-legos')
    assert "Kontakt ändern" not in editor.get('/angebot/play-with-playmobil')

    # admins get the change contact link as well
    assert "Kontakt ändern" in admin.get('/angebot/play-with-legos')
    assert "Kontakt ändern" in admin.get('/angebot/play-with-playmobil')

    # owner changes are reflected on the activity
    contact = editor.get('/angebot/play-with-legos').click('Kontakt ändern')
    contact.form['realname'] = 'Editors Association'
    contact.form['address'] = 'Washington'
    contact.form['email'] = 'editors-association@example.org'
    contact.form['phone'] = '+41 23 456 789'
    contact.form['website'] = 'https://www.example.org'
    contact.form.submit()

    activity = editor.get('/angebot/play-with-legos')

    assert "Editors Association" in activity
    assert "Washington" in activity
    assert "editors-association@example.org" in activity
    assert "editor@example.org" not in activity
    assert "+41 23 456 789" in activity
    assert "https://www.example.org" in activity

    # admin changes are reflected on the activity
    contact = admin.get('/angebot/play-with-legos').click('Kontakt ändern')
    contact.form['realname'] = 'Admins Association'
    contact.form.submit()

    activity = editor.get('/angebot/play-with-legos')

    assert "Admins Association" in activity


def test_occasions_form(feriennet_app):

    editor = Client(feriennet_app)
    editor.login_editor()

    admin = Client(feriennet_app)
    admin.login_admin()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Play with Legos"
    new.form['lead'] = "Like Minecraft, but in the real world"
    new.form.submit().follow()

    periods = admin.get('/angebote').click("Perioden")

    period = periods.click("Neue Periode")
    period.form['title'] = "Vacation Program 2016"
    period.form['prebooking_start'] = '2016-09-01'
    period.form['prebooking_end'] = '2016-09-30'
    period.form['execution_start'] = '2016-10-01'
    period.form['execution_end'] = '2016-10-31'
    period.form.submit()

    activity = editor.get('/angebote').click("Play with Legos")
    assert "keine Durchführungen" in activity

    occasion = activity.click("Neue Durchführung")
    occasion.form['start'] = '2016-10-04 10:00:00'
    occasion.form['end'] = '2016-10-04 12:00:00'
    occasion.form['location'] = "Franz Karl Weber"
    occasion.form['note'] = "No griefers"
    occasion.form['min_age'] = 10
    occasion.form['max_age'] = 20
    occasion.form['min_spots'] = 30
    occasion.form['max_spots'] = 40
    activity = occasion.form.submit().follow()

    assert "keine Durchführungen" not in activity
    assert "4. Oktober 10:00 - 12:00" in activity
    assert "10 - 20 Jahre alt" in activity
    assert "30 - 40 Teilnehmer" in activity
    assert "Franz Karl Weber" in activity
    assert "No griefers" in activity

    occasion = activity.click("Bearbeiten", index=1)
    occasion.form['min_age'] = 15
    activity = occasion.form.submit().follow()
    assert "15 - 20 Jahre alt" in activity

    editor.delete(get_delete_link(activity, index=1))
    assert "keine Durchführungen" in editor.get('/angebot/play-with-legos')


def test_execution_period(feriennet_app):

    admin = Client(feriennet_app)
    admin.login_admin()

    new = admin.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Play with Legos"
    new.form['lead'] = "Like Minecraft, but in the real world"
    new.form.submit().follow()

    periods = admin.get('/angebote').click("Perioden")

    period = periods.click("Neue Periode")
    period.form['title'] = "Vacation Program 2016"
    period.form['prebooking_start'] = '2016-09-01'
    period.form['prebooking_end'] = '2016-09-30'
    period.form['execution_start'] = '2016-10-01'
    period.form['execution_end'] = '2016-10-01'
    period.form.submit()

    occasion = admin.get('/angebot/play-with-legos').click("Neue Durchführung")
    occasion.form['min_age'] = 10
    occasion.form['max_age'] = 20
    occasion.form['min_spots'] = 30
    occasion.form['max_spots'] = 40

    occasion.form['start'] = '2016-10-01 00:00:00'
    occasion.form['end'] = '2016-10-02 23:59:59'
    assert "ausserhalb der gewählten Periode" in occasion.form.submit()

    occasion.form['start'] = '2016-09-30 00:00:00'
    occasion.form['end'] = '2016-10-01 23:59:59'
    assert "ausserhalb der gewählten Periode" in occasion.form.submit()

    occasion.form['start'] = '2016-10-01 00:00:00'
    occasion.form['end'] = '2016-10-01 23:59:59'
    assert "Änderungen wurden gespeichert" in occasion.form.submit().follow()

    period = admin.get('/perioden').click("Bearbeiten")
    period.form['execution_start'] = '2016-10-02'
    period.form['execution_end'] = '2016-10-02'
    period = period.form.submit()

    assert "in Konflikt" in period
    assert "Play with Legos" in period

    period.form['execution_start'] = '2016-10-01'
    period.form['execution_end'] = '2016-10-01'
    periods = period.form.submit().follow()

    assert "gespeichert" in periods


def test_enroll_child(feriennet_app):
    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())

    retreat = activities.add("Retreat", username='admin@example.org')
    retreat.propose().accept()

    prebooking = tuple(d.date() for d in (
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    ))

    execution = tuple(d.date() for d in (
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=12)
    ))

    occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        age=(0, 10),
        timezone="Europe/Zurich",
        activity=retreat,
        period=periods.add(
            title="2016",
            prebooking=prebooking,
            execution=execution,
            active=True
        )
    )

    UserCollection(feriennet_app.session()).add(
        'member@example.org', 'hunter2', 'member')

    transaction.commit()

    client = Client(feriennet_app)

    activity = client.get('/angebot/retreat')

    login = activity.click("Anmelden")
    assert "Login" in login

    login.form['username'] = 'member@example.org'
    login.form['password'] = 'hunter2'
    enroll = login.form.submit().follow()
    assert "Teilnehmer Anmelden" in enroll

    # now that we're logged in, the login link automatically skips ahead
    enroll = activity.click("Anmelden").follow()
    assert "Teilnehmer Anmelden" in enroll

    # the link changes, but the result stays the same
    enroll = client.get('/angebot/retreat').click("Anmelden")
    assert "Teilnehmer Anmelden" in enroll

    enroll.form["name"] = "Tom Sawyer"
    enroll.form["birth_date"] = "1876-01-01"
    activity = enroll.form.submit().follow()

    assert "zu Tom Sawyer's Wunschliste hinzugefügt" in activity

    # prevent double-subscriptions
    enroll = activity.click("Anmelden")
    assert "Tom Sawyer hat sich bereits für diese Durchführung angemeldet"\
        in enroll.form.submit()

    enroll.form['attendee'] = 'other'
    enroll.form['name'] = "Tom Sawyer"
    enroll.form["birth_date"] = "1876-01-01"

    # prevent adding two kids with the same name
    assert "Sie haben bereits ein Kind mit diesem Namen eingegeben"\
        in enroll.form.submit()

    # prevent enrollment for inactive periods
    periods.query().first().active = False
    transaction.commit()

    enroll.form['name'] = "Huckleberry Finn"
    assert "Diese Durchführung liegt ausserhalb der aktiven Periode"\
        in enroll.form.submit()

    # prevent enrollment outside of prebooking
    period = periods.query().first()
    period.active = True
    period.prebooking_start -= timedelta(days=10)
    period.prebooking_end -= timedelta(days=10)

    transaction.commit()

    assert "nur während der Wunschphase" in enroll.form.submit()

    # set the record straight again
    period = periods.query().first()
    period.prebooking_start += timedelta(days=10)
    period.prebooking_end += timedelta(days=10)

    transaction.commit()

    enroll.form['name'] = "Huckleberry Finn"
    activity = enroll.form.submit().follow()

    assert "zu Huckleberry Finn's Wunschliste hinzugefügt" in activity


def test_booking_view(feriennet_app):
    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    attendees = AttendeeCollection(feriennet_app.session())
    bookings = BookingCollection(feriennet_app.session())
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())
    users = UserCollection(feriennet_app.session())

    prebooking = tuple(d.date() for d in (
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    ))

    execution = tuple(d.date() for d in (
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=12)
    ))

    period = periods.add(
        title="2016",
        prebooking=prebooking,
        execution=execution,
        active=True
    )

    periods.add(
        title="2017",
        prebooking=prebooking,
        execution=execution,
        active=False
    )

    o = []

    for i in range(4):
        a = activities.add("A {}".format(i), username='admin@example.org')
        a.propose().accept()

        o.append(occasions.add(
            start=datetime(2016, 10, 8, 8),
            end=datetime(2016, 10, 9, 16),
            age=(0, 10),
            timezone="Europe/Zurich",
            activity=a,
            period=period
        ))

    m1 = users.add('m1@example.org', 'hunter2', 'member')
    m2 = users.add('m2@example.org', 'hunter2', 'member')

    a1 = attendees.add(m1, 'Dustin', date(2000, 1, 1))
    a2 = attendees.add(m2, 'Mike', date(2000, 1, 1))

    # hookup a1 with all courses
    bookings.add(m1, a1, o[0])
    bookings.add(m1, a1, o[1])
    bookings.add(m1, a1, o[2])
    bookings.add(m1, a1, o[3])

    # m2 only gets one for the permission check
    bookings.add(m2, a2, o[0])

    transaction.commit()

    c1 = Client(feriennet_app)
    c1.login('m1@example.org', 'hunter2')

    c2 = Client(feriennet_app)
    c2.login('m2@example.org', 'hunter2')

    # make sure the bookings count is correct
    assert 'data-count="4"' in c1.get('/')
    assert 'data-count="1"' in c2.get('/')

    # make sure the bookings show up under my view
    def count(page):
        return len(page.pyquery('.attendee-bookings > div > ul > li'))

    c1_bookings = c1.get('/').click('Meine Wunschliste')
    c2_bookings = c2.get('/').click('Meine Wunschliste')

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
    assert "Keine Buchungen in 2017" in c1_bookings.click('2017')

    # admins may switch between other users
    admin = Client(feriennet_app)
    admin.login_admin()

    m1_bookings = admin.get('/').click('Meine Wunschliste')\
        .click('m1@example.org')

    assert count(m1_bookings) == 4


def test_matching_view(feriennet_app):
    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    attendees = AttendeeCollection(feriennet_app.session())
    bookings = BookingCollection(feriennet_app.session())
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())

    owner = Bunch(username='admin@example.org')

    prebooking = tuple(d.date() for d in (
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    ))

    execution = tuple(d.date() for d in (
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=12)
    ))

    period = periods.add(
        title="Ferienpass 2016",
        prebooking=prebooking,
        execution=execution,
        active=True
    )

    o = []

    for i in range(2):
        a = activities.add("A {}".format(i), username='admin@example.org')
        a.propose().accept()

        o.append(occasions.add(
            start=datetime(2016, 10, 8 + i, 8),
            end=datetime(2016, 10, 8 + i, 16),
            age=(0, 10),
            spots=(2, 4),
            timezone="Europe/Zurich",
            activity=a,
            period=period
        ))

    a1 = attendees.add(owner, 'Dustin', date(2000, 1, 1))
    a2 = attendees.add(owner, 'Mike', date(2000, 1, 1))

    # the first course has enough attendees
    bookings.add(owner, a1, o[0])
    bookings.add(owner, a2, o[0])

    # the second one does not
    bookings.add(owner, a1, o[1])

    transaction.commit()

    client = Client(feriennet_app)
    client.login_admin()

    matching = client.get('/angebote').click("Zuteilung")

    # check the initial state
    assert "Ferienpass 2016" in matching
    assert "Zufriedenheit liegt bei <strong>0%</strong>" in matching
    assert "<strong>0%</strong> aller Durchführungen haben genug" in matching
    assert "0 / 4" in matching
    assert "Dustin" in matching

    # run a matching
    matching = matching.form.submit()

    assert "Zufriedenheit liegt bei <strong>100%</strong>" in matching
    assert "<strong>50%</strong> aller Durchführungen haben genug" in matching
    assert "1 / 4" in matching
    assert "2 / 4" in matching

    # reset it again
    client.post(get_post_url(matching, 'reset-matching'))
    matching = client.get('/angebote').click("Zuteilung")

    assert "Zufriedenheit liegt bei <strong>0%</strong>" in matching
    assert "<strong>0%</strong> aller Durchführungen haben genug" in matching
