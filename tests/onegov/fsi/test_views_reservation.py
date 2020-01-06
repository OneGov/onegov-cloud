
from onegov.fsi.models import CourseReservation, CourseAttendee


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
    view = f'/fsi/reservations/add'
    client.login_admin()

    new = client.get(view).click('Platzhalter')
    new.form['dummy_desc'] = 'Safe!'
    page = new.form.submit().follow()
    assert 'Safe!' in page
    page = page.click('Safe!').click('Löschen')
    page = client.get('/fsi/reservations')
    assert 'Safe!' not in page


def test_makeing_reservations(client_with_db):
    client = client_with_db

    # Test permissions for editor, member
    view = '/fsi/reservations/add'
    client.login_editor()
    client.get(view)
    view = '/fsi/reservations/add-placeholder'
    client.get(view, status=403)

    session = client.app.session()

    planner_editor = session.query(CourseAttendee).filter_by(
        first_name='PE').one()
    assert planner_editor.user.role == 'editor'



    # edi = editor(session)
    # att, data = attendee(session)
    # client.login_admin()
    # view = '/fsi/reservations/add'
    # page = client.get(f'/fsi/attendee/{att.id}')
    # pass
