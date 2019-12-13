from datetime import datetime

from sedate import utcnow

from onegov.fsi.models import CourseEvent
from tests.onegov.org.common import get_mail


def test_course_event_collection(client):
    view = '/fsi/events'
    client.get(view, status=403)

    client.login_member()
    client.get(view)


def test_course_event_details(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).first()

    view = f'/fsi/event/{event.id}'
    client.get(view, status=403)

    client.login_member()
    client.get(view)


def test_edit_course_event(client_with_db):
    client = client_with_db
    session = client.app.session()

    event = session.query(CourseEvent).first()
    view = f'/fsi/event/{event.id}/edit'

    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    new = client.get(view)
    new.form['location'] = 'New Loc'
    new.form['start'] = datetime(2015, 5, 5)
    new.form['end'] = datetime(2015, 5, 5)
    new.form['presenter_name'] = 'Pres'
    new.form['min_attendees'] = 2
    new.form['max_attendees'] = 3
    new.form['hidden_from_public'] = True
    page = new.form.submit().follow()

    assert 'New Loc' in page
    assert '05. Mai 2015' in page
    assert 'Pres' in page
    assert f'min. 2 max. 3' in page
    # String will not be rendered in email preview
    assert 'This course is hidden.' not in page


def test_add_delete_course_event(client_with_db):
    view = '/fsi/events/add'
    client = client_with_db
    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    page = client.get(view)
    assert page.form['course_id'].value
    print('course_id value: ', page.form['course_id'].value)
    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_company'] = 'Company'
    page.form['presenter_email'] = 'p@t.com'
    page.form['start'] = '2016-10-04 10:00:00'
    page.form['end'] = '2016-10-04 12:00:00'
    page.form['location'] = 'location'
    assert page.form['min_attendees'].value == '1'
    page.form['max_attendees'] = '10'
    assert page.form['status'].value == 'created'
    # Follow will not work if there are error in the form
    page = page.form.submit().follow()
    assert 'Eine neue Durchführung wurde hinzugefügt' in page

    # Delete course without reservations
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        presenter_email='p@t.com'
    ).one()

    assert not event.reservations.count()
    view = f'/fsi/event/{event.id}'

    # csrf protected url must be used
    client.delete(view, status=403)
    page = client.get(view)
    page.click('Löschen')
    # Test that course does not exist anymore
    client.get(view, status=404)


def test_duplicate_course_event(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).first()

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


def test_cancel_course_event(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter(
        CourseEvent.start > utcnow()).first()

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
    assert len(client.app.smtp.outbox) == wanted_count + 1

    message = client.app.smtp.outbox.pop()
    assert message['Subject'] == 'Absage Kursveranstaltung'


def test_register_for_course_event_member(client_with_db):
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

    assert len(client.app.smtp.outbox) == 1
    message = get_mail(client.app.smtp.outbox, 0)
    assert message['to'] == 'member@example.org'
    assert message['subject'] == '=?utf-8?q?Anmeldungsbest=C3=A4tigung?='


def test_register_for_course_event_editor(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    client.login_editor()
    client.get(f'/fsi/event/{event.id}').click('Anmelden')
    page = client.get(f'/fsi/event/{event.id}')
    assert 'Angemeldet' in page

    assert len(client.app.smtp.outbox) == 1
    message = get_mail(client.app.smtp.outbox, 0)
    assert message['to'] == 'editor@example.org'


def test_register_for_course_event_admin(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    client.login_admin()
    client.get(f'/fsi/event/{event.id}').click('Anmelden')
    page = client.get(f'/fsi/event/{event.id}')
    assert 'Angemeldet' in page

    assert len(client.app.smtp.outbox) == 1

