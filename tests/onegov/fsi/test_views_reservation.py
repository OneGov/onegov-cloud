from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.models import CourseSubscription, CourseAttendee, CourseEvent, \
    Course
from onegov.user import User


def test_locked_course_event_reservations(client_with_db):
    client = client_with_db
    client.login_admin()
    session = client.app.session()
    course = session.query(Course).first()

    # Add a new course event
    page = client.get(f'/fsi/events/add?course_id={course.id}')
    page.form['presenter_name'] = 'Presenter'
    page.form['presenter_company'] = 'Presenter'
    page.form['presenter_email'] = 'presenter@example.org'
    page.form['locked_for_subscriptions'] = True
    page.form['start'] = '2050-10-04 10:00:00'
    page.form['end'] = '2050-10-04 12:00:00'
    page.form['location'] = 'location'
    page.form['max_attendees'] = 20
    # goes to the event created
    new = page.form.submit().follow()
    assert 'Eine neue Durchführung wurde hinzugefügt' in new

    client.login_editor()
    # Hinzufügen - Teilnehmer als editor
    add_subscription = new.click('Teilnehmer', href='reservations', index=0)
    page = add_subscription.form.submit()
    assert 'Diese Durchführung kann (nicht) mehr gebucht werden.' in page

    client.login_admin()
    add_subscription = new.click('Teilnehmer', href='reservations', index=0)
    page = add_subscription.form.submit().follow()
    assert 'Neue Anmeldung wurde hinzugefügt' in page
    assert 'Diese Durchführung kann (nicht) mehr gebucht werden.' not in page


def test_reservation_collection_view(client_with_db):
    view = '/fsi/reservations'
    client = client_with_db
    client.get(view, status=403)

    client.login_member(to=view)
    # is the current attendee registered for two courses
    page = client.get(view)
    assert 'Meine Kursanmeldungen' in page
    assert 'Course' in page
    assert '01.01.2050' in page
    assert '01.01.1950' in page


def test_reservation_details(client_with_db):
    client = client_with_db
    session = client.app.session()
    attendee = session.query(CourseAttendee).first()
    subscription = attendee.subscriptions.first()

    view = f'/fsi/reservation/{subscription.id}'
    # This view has just the delete method
    client.get(view, status=405)


def test_edit_reservation(client_with_db):
    client = client_with_db
    session = client.app.session()
    subscription = session.query(CourseSubscription).filter(
        CourseSubscription.attendee_id != None).first()

    placeholder = session.query(CourseSubscription).filter(
        CourseSubscription.attendee_id == None).first()

    events = session.query(CourseEvent).all()
    assert events[1].id != subscription.course_event_id

    # --- Test edit a placeholder --
    client.login_admin()
    view = f'/fsi/reservation/{placeholder.id}/edit-placeholder'
    page = client.get(view)
    assert page.form['course_event_id'].value == str(
        placeholder.course_event_id)

    # The default dummy desc will be set in the view
    assert page.form['dummy_desc'].value == 'Placeholder'
    page.form['dummy_desc'] = ''
    page = page.form.submit().maybe_follow()
    assert 'Platzhalter aktualisiert' in page
    page = client.get(view)
    # check if empty placeholder is replaced by default
    assert page.form['dummy_desc'].value == 'Platzhalter-Reservation'

    # --- Test a normal subscription ---
    view = f'/fsi/reservation/{subscription.id}/edit'
    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    edit = client.get(view)
    assert 'Anmeldung bearbeiten' in edit
    assert edit.form['course_event_id'].value == str(
        subscription.course_event_id)
    assert edit.form['attendee_id'].value == str(subscription.attendee_id)
    options = [opt[2] for opt in edit.form['attendee_id'].options]
    # Returns event.possible_subscribers, tested elsewhere
    # Planner (admin) and attendee have subscription, not editor_attendee (PE)
    # L, F is the normal attendee
    assert options == ['L, F', 'PE, PE']

    # course must be fixed
    options = [opt[2] for opt in edit.form['course_event_id'].options]
    assert options == ['Course - 01.01.1950 01:00']

    new_id = edit.form['attendee_id'].options[1][0]
    edit.form['attendee_id'] = new_id
    page = edit.form.submit().maybe_follow()
    assert 'Anmeldung wurde aktualisert' in page
    page = client.get(view)
    assert page.form['attendee_id'].value == new_id


def test_own_reservations(client_with_db):
    client = client_with_db
    client.login_editor()
    page = client.get('/topics/informationen')

    # check if the management bar shows the correct number of subscriptions
    res_count = page.pyquery('a.open-tickets').attr('data-count')
    assert res_count == '1'
    page = page.click('Kursanmeldung', href='attendee_id')
    assert 'Keine Einträge gefunden' not in page


def test_create_delete_reservation(client_with_db):
    client = client_with_db
    session = client.app.session()

    attendee = session.query(CourseAttendee).first()
    att_res = attendee.subscriptions.all()
    assert len(att_res) == 2

    # Lazy loading not possible
    member = session.query(User).filter_by(role='member').first()
    coll = CourseEventCollection(session, upcoming_only=True)
    events = coll.query().all()
    # one of the three is past
    assert len(events) == 2

    assert events[0].start.year == 2050     # ascending order, other is 2060
    assert events[1].id not in [e.course_event_id for e in att_res]

    assert attendee.user_id == member.id
    assert attendee.organisation == 'ORG'
    view = f'/fsi/reservations/add'

    client.login_editor()

    # Check filtering down the courses when the attendee is given
    page = client.get(f'/fsi/reservations/add?attendee_id={attendee.id}')
    options = [opt[2] for opt in page.form['course_event_id'].options]
    assert options == [
        'Course - 01.01.2060 01:00'
    ]

    client.get(view)

    # Add - Subscription as editor having the permissions to see one attendee
    new = client.get(view).click('Anmeldung')

    assert new.form['attendee_id'].options[0] == (
        str(attendee.id), False, str(attendee))

    # the fixture also provides a past event which should not be an option
    options = [opt[2] for opt in new.form['course_event_id'].options]
    print(options)
    assert options == [
        'Course - 01.01.2050 01:00',
        'Course - 01.01.2060 01:00'
    ]
    # select course_id where there is no registration done (2060)
    new.form['course_event_id'] = str(events[1].id)
    page = new.form.submit().maybe_follow()
    assert 'Alle Kursanmeldungen' in page
    assert 'Course' in page
    assert '01.01.2060' in page

    page = client.get(view).form.submit()
    msg = 'Für dieses Jahr gibt es bereits andere Anmeldungen für diesen Kurs'
    assert msg in page

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
    new = client.get(view)
    options = [opt[2] for opt in new.form['course_event_id'].options]
    # must asscending order from newest to oldest, past events excluded
    assert options == ['Course - 01.01.2050 01:00', 'Course - 01.01.2060 01:00']
    new.form['dummy_desc'] = 'Safe!'
    page = new.form.submit().follow()
    assert 'Safe!' in page
    page.click('Safe!').click('Löschen')
    page = client.get('/fsi/reservations')
    assert 'Safe!' not in page
