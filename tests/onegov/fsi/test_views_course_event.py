from __future__ import annotations

import os

from datetime import timedelta
from sedate import utcnow
from onegov.fsi.models import CourseEvent


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client, FsiScenario


def test_course_event_collection(client: Client) -> None:
    view = '/fsi/events'
    client.get(view, status=403)

    client.login_member()
    client.get(view)


def test_course_event_details(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).first()
    assert event is not None

    view = f'/fsi/event/{event.id}'
    client.get(view, status=403)

    client.login_member()
    client.get(view)


def test_edit_course_event(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()

    event = session.query(CourseEvent).first()
    assert event is not None
    view = f'/fsi/event/{event.id}/edit'

    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    new = client.get(view)
    new.form['location'] = 'New Loc'
    new.form['start'] = '2015-05-05 00:00'
    new.form['end'] = '2015-05-06 00:00'
    new.form['presenter_name'] = 'Pres'
    new.form['min_attendees'] = 2
    new.form['max_attendees'] = 3
    new.form['hidden_from_public'] = True
    new.form['locked_for_subscriptions'] = True
    page = new.form.submit().follow()

    assert 'New Loc' in page
    assert '05. Mai 2015' in page
    assert 'Pres' in page
    assert 'min. 2 max. 3' in page
    # String will not be rendered in email preview
    assert 'This course is hidden.' not in page
    # test no changes
    page = client.get(view)
    page.form.submit().follow()


def test_add_delete_course_event(client_with_db: Client) -> None:
    view = '/fsi/events/add'
    client = client_with_db
    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    page = client.get(view)
    assert page.form['course_id'].value

    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_company'] = 'Company'
    page.form['presenter_email'] = 'p@t.com'
    page.form['start'] = '2016-10-04 10:00'
    page.form['end'] = '2016-10-04 12:00'
    page.form['location'] = 'location'
    assert page.form['min_attendees'].value == '1'
    page.form['max_attendees'] = '10'
    assert page.form['status'].value == 'created'
    # Follow will not work if there are error in the form
    page = page.form.submit().follow()
    assert 'Eine neue Durchführung wurde hinzugefügt' in page

    # Test add duplicate
    page = client.get(view)
    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_company'] = 'Company'
    page.form['presenter_email'] = 'p@t.com'
    page.form['start'] = '2016-10-04 10:00'
    page.form['end'] = '2016-10-04 12:00'
    page.form['location'] = 'location'
    page.form['max_attendees'] = '10'
    page = page.form.submit()
    assert 'Ein Duplikat dieser Durchführung existiert bereits' in page

    # Delete course without subscriptions
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        presenter_email='p@t.com'
    ).one()

    assert not event.subscriptions.count()
    view = f'/fsi/event/{event.id}'

    # csrf protected url must be used
    client.delete(view, status=403)
    page = client.get(view)
    page.click('Löschen')
    # Test that course does not exist anymore
    client.get(view, status=404)


def test_duplicate_course_event(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).first()
    assert event is not None

    client.login_admin()
    view = f'/fsi/event/{event.id}/duplicate'
    dup = client.get(view)
    assert dup.form['course_id'].value == str(event.course.id)
    assert dup.form['presenter_name'].value == event.presenter_name
    assert dup.form['presenter_email'].value == event.presenter_email
    assert not dup.form['start'].value
    assert not dup.form['end'].value
    assert dup.form['location'].value == event.location
    assert dup.form['min_attendees'].value == str(event.min_attendees)
    assert dup.form['max_attendees'].value == str(event.max_attendees)


def test_cancel_course_event(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter(
        CourseEvent.start > utcnow()).first()
    assert event is not None

    wanted_count = event.attendees.count()

    view = f'/fsi/event/{event.id}'
    client.login_admin()

    # Cancel event
    page = client.get(view)
    redirect_link = page.pyquery('a.cancel-icon').attr('redirect-after')
    assert redirect_link
    client.get(view).click('Absagen')

    msg = f"Email erfolgreich an {wanted_count + 1} Empfänger gesendet"
    assert msg in client.get(redirect_link)
    assert len(os.listdir(client.app.maildir)) == 1

    for number in range(wanted_count):
        message = client.get_email(0, number)
        assert message['Subject'] == 'Absage Kursveranstaltung'


def test_register_for_course_event_member(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    assert not event.is_past
    client.login_member()
    client.get(f'/fsi/event/{event.id}').click('Anmelden')
    page = client.get(f'/fsi/event/{event.id}')
    assert 'Angemeldet' in page

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message['To'] == 'member@example.org'
    assert message['Subject'] == 'Anmeldungsbestätigung'
    text = message['TextBody']
    assert 'Sie haben sich erfolgreich für folgenden Kurs angemeldet' in text

    # Test cancellation emails upon unsubscribing
    client.login_admin()
    view = f'/fsi/reservations?course_event_id={event.id}'
    page = client.get(view)
    page.click('Löschen')
    assert len(os.listdir(client.app.maildir)) == 2
    message = client.get_email(1)
    assert message['Subject'] == 'Absage Kursveranstaltung'


def test_register_for_course_event_editor(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    client.login_editor()
    client.get(f'/fsi/event/{event.id}').click('Anmelden')
    page = client.get(f'/fsi/event/{event.id}')
    assert 'Angemeldet' in page

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)
    assert message['To'] == 'editor@example.org'


def test_register_for_course_event_admin(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    client.login_admin()
    client.get(f'/fsi/event/{event.id}').click('Anmelden')
    page = client.get(f'/fsi/event/{event.id}')
    assert 'Angemeldet' in page

    assert len(os.listdir(client.app.maildir)) == 1


def test_add_subscription_for_other_attendee(client_with_db: Client) -> None:
    client = client_with_db
    client.login_admin()
    new = client.get('/fsi/reservations').click('Anmeldung')

    # There is already a subscription for this course and attendee
    assert new.form['course_event_id'].options[0][2] == (
           'Course - 01.01.2050 01:00')
    assert new.form['course_event_id'].options[1][2] == (
           'Course - 01.01.2060 01:00')
    bookable_id = new.form['course_event_id'].options[1][0]

    # take the fist choice and fail
    page = new.form.submit()
    assert 'Für dieses Jahr gibt es bereits andere Anmeldungen' in page

    page.form['course_event_id'] = bookable_id
    page = page.form.submit().follow()
    assert "Neue Anmeldung wurde hinzugefügt" in page

    assert len(os.listdir(client.app.maildir)) == 1


def test_edit_subscription_for_other_attendee(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    client.login_admin()

    new = client.get(f'/fsi/reservations/add?course_event_id={event.id}')
    page = new.form.submit().follow()
    assert 'Neue Anmeldung wurde hinzugefügt' in page
    assert len(os.listdir(client.app.maildir)) == 1


def test_delete_subscriptions_past_present(
    client: Client,
    scenario: FsiScenario
) -> None:

    now = utcnow()
    scenario.add_course(name='Testcourse with Templates')
    scenario.add_attendee()
    scenario.commit()
    scenario.refresh()

    past_event = scenario.add_course_event(
        scenario.latest_course,
        start=now - timedelta(days=2, minutes=30),
        end=now - timedelta(days=2)
    )
    event = scenario.add_course_event(
        scenario.latest_course,
        start=now + timedelta(days=2),
        end=now + timedelta(days=2, minutes=30)
    )

    scenario.add_subscription(event, scenario.latest_attendee)
    scenario.add_subscription(past_event, scenario.latest_attendee)
    scenario.add_notification_template(event)
    scenario.add_notification_template(past_event)
    scenario.commit()
    scenario.refresh()

    client.login_admin()
    event_subscriptions = (
        f'/fsi/reservations?course_event_id={scenario.latest_event.id}')

    page = client.get(event_subscriptions)
    response = client.delete(
        page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))
    assert response.status_code == 200
    assert client.get_email(-1, flush_queue=True)

    page = client.get(event_subscriptions)
    assert 'Keine Einträge gefunden' in page

    past_event_subscriptions = (
        f'/fsi/reservations?course_event_id={scenario.course_events[-2].id}')

    page = client.get(past_event_subscriptions)
    response = client.delete(
        page.pyquery('a[ic-delete-from]').attr('ic-delete-from'))

    assert response.status_code == 200
    assert len(os.listdir(client.app.maildir)) == 0
