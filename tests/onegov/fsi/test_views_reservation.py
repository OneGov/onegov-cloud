from onegov.fsi.models import CourseReservation, CourseAttendee


def test_reservation_collection(client):
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


def test_add_reservation(client):
    view = '/fsi/reservations/add'
    client.login_editor()
    client.get(view, status=403)

    view = '/fsi/reservations/add-placeholder'
    client.get(view, status=403)


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


def test_delete_reservations(client_with_db):
    client = client_with_db
    session = client.app.session()
    reservation = session.query(CourseReservation).filter(
        CourseReservation.attendee_id == None).first()

    view = f'/fsi/reservation/{reservation.id}'
    client.login_admin()

    # csrf protected url must be used
    client.delete(view, status=403)
    page = client.get(view + '/edit')
    page.click('Löschen')
