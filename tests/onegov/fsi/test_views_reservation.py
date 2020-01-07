from datetime import datetime

from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.models import CourseReservation, CourseAttendee, CourseEvent
from onegov.user import User


def test_reservation_collection_view(client):
    view = '/fsi/reservations'
    client.get(view, status=403)

    client.login_member(to=view)
    client.get(view)


def test_reservation_details(client_with_db):
    client = client_with_db
    session = client.app.session()
    attendee = session.query(CourseAttendee).first()
    reservation = attendee.reservations.first()

    view = f'/fsi/reservation/{reservation.id}'
    # This view has just the delete method
    client.get(view, status=405)

def test_edit_reservation(client_with_db):
    client = client_with_db
    session = client.app.session()
    reservation = session.query(CourseReservation).filter(
        CourseReservation.attendee_id != None).first()

    view = f'/fsi/reservation/{reservation.id}/edit'
    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    edit = client.get(view)
    assert edit.form['course_event_id'].value == str(
        reservation.course_event_id)
    assert edit.form['attendee_id'].value == str(reservation.attendee_id)


def test_create_delete_reservation(client_with_db):
    client = client_with_db
    session = client.app.session()

    attendee = session.query(CourseAttendee).first()
    att_res = attendee.reservations.all()
    assert len(att_res) == 2

    # Lazy loading not possible
    member = session.query(User).filter_by(role='member').first()
    coll = CourseEventCollection(session, upcoming_only=True)
    events = coll.query().all()
    # one of the three is past
    assert len(events) == 2

    assert events[0].start.year == 2060
    assert events[0].id not in [e.course_event_id for e in att_res]

    assert attendee.user_id == member.id
    assert attendee.organisation == 'ORG'
    view = f'/fsi/reservations/add'

    client.login_editor()

    # Check filtering down the courses when the attendee is given
    page = client.get(f'/fsi/reservations/add?attendee_id={attendee.id}')
    options = [opt[2] for opt in page.form['course_event_id'].options]
    assert options == [
        'Course - 01.01.2060'
    ]

    client.get(view)

    # Add - Subscription as editor having the permissions to see one attendee
    new = client.get(view).click('Anmeldung')

    assert new.form['attendee_id'].options[0] == (
        str(attendee.id), False,  str(attendee))

    # the fixture also provides a past event which should not be an option
    options = [opt[2] for opt in new.form['course_event_id'].options]
    assert options == [
        'Course - 01.01.2060',
        'Course - 01.01.2050'
    ]
    # select course_id where there is no registration done
    assert new.form['course_event_id'].value == str(events[0].id)
    page = new.form.submit().maybe_follow()
    assert 'Alle Kursanmeldungen' in page
    assert 'Course' in page
    assert '01.01.2060' in page

    page = client.get(view).form.submit().follow()
    assert 'Anmeldung existiert bereits' in page

    # Settings the attendee id should filter down to events the attendee
    # hasn't any subscription
    page = client.get(f'/fsi/reservations/add?attendee_id={attendee.id}')
    options = [opt[2] for opt in page.form['course_event_id'].options]
    assert options == [
        'Keine'
    ]

    # Test adding placeholder with editor not allowed
    view = '/fsi/reservations/add-placeholder'
    client.get(view, status=403)

    client.login_admin()
    #
    new = client.get(view).click('Platzhalter')
    new.form['dummy_desc'] = 'Safe!'
    page = new.form.submit().follow()
    assert 'Safe!' in page
    page.click('Safe!').click('Löschen')
    page = client.get('/fsi/reservations')
    assert 'Safe!' not in page
