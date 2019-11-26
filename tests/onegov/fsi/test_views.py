def test_view_homepage(client):
    homepage = client.get('/')

    assert "Informationen" in homepage
    assert "Kursverwaltung" in homepage


def test_view_courses(client):
    page = client.get('/events')
    assert 'Keine Einträge gefunden' in page


def test_view_courses_new(client):
    page = client.get('/events/add')
    assert page
    # page.form['domain'] = 'federation'
    # page.form.submit()


def test_course_collection_permission(fsi_app, client):
    view = '/fsi/courses'
    client.get(view, status=403)


def test_course_permission():
    view = '/fsi/course/{id}'


def test_reservation_collection_permission():
    pass


def test_reservation_permission():
    pass


def test_course_attendee_collection_permissions():
    pass


def test_course_attendee_permissions():
    pass


def test_notifications_collection_permissions():
    pass


def test_notifcation_permission():
    pass


def test_editor_only_accessible(fsi_app, client):
    viewname = '/fsi/attendees'
    client.login_editor()
    client.get(viewname, status=200)


def test_personal_accessible():
    pass


def test_attendee_permission_as_member():
    # Test if the attendee can see their own profile

    # Test that he cant see any other profile
    pass


def test_not_visible_for_public():
    views = ['/fsi/courses', '/fsi/events', '/fsi/reservations']

