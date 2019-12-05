from datetime import datetime

from sedate import utcnow

from onegov.fsi.models import CourseEvent


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


def test_add_course_event(client):
    view = '/fsi/events/add'
    client.login_editor()
    client.get(view, status=403)
    client.login_admin()
    client.get(view)


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


def test_delete_course_event(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    assert not event.reservation.count()
    view = f'/fsi/event/{event.id}'
    client.login_admin()

    # csrf protected url must be used
    client.delete(view, status=403)
    page = client.get(view)
    page = page.click('Löschen')
    client.get(view, status=404)


def test_register_for_course_event(client_with_db):
    client = client_with_db
    session = client.app.session()
    event = session.query(CourseEvent).filter_by(
        location='Empty'
    ).one()
    assert not event.is_past
    client.login_member()
    page = client.get(f'/fsi/event/{event.id}').click('Anmelden')
    page = client.get(f'/fsi/event/{event.id}')
    assert 'Angemeldet' in page
