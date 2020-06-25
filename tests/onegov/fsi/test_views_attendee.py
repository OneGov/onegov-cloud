from onegov.user import User


def test_course_attendee_collection(client):
    view = '/fsi/attendees'
    client.get(view, status=403)
    client.login_member()
    client.get(view, status=403)


def test_attendee_details(client_with_db):
    client = client_with_db
    session = client.app.session()

    planner = session.query(User).filter_by(
        username='admin@example.org').first().attendee

    attendee = session.query(User).filter_by(
        username='member@example.org').first().attendee

    client.login_member()
    client.get(f'/fsi/attendee/{planner.id}', status=403)
    # can see his own
    client.get(f'/fsi/attendee/{attendee.id}')

    # ca see all others
    client.login_editor()
    client.get(f'/fsi/attendee/{planner.id}', status=200)


def test_edit_attendee(client_with_db):
    client = client_with_db
    session = client.app.session()

    attendee = session.query(User).filter_by(
        username='member@example.org').first().attendee

    client.login_member()
    client.get(f'/fsi/attendee/{attendee.id}', status=200)

    # Assure permission Secret
    client.login_member()
    client.get(f'/fsi/attendee/{attendee.id}/edit', status=403)

    client.login_editor()
    client.get(f'/fsi/attendee/{attendee.id}/edit', status=403)

    client.login_admin()
    new = client.get(f'/fsi/attendee/{attendee.id}/edit')
    new.form['first_name'] = 'New FN'
    new.form['last_name'] = 'New LN'
    page = new.form.submit().follow()
    assert 'New FN' in page


def test_add_external_attendee(client):
    view = '/fsi/attendees/add-external'
    client.login_member()
    client.get(view, status=403)

    client.login_editor()
    new = client.get(view)
    new.form['first_name'] = 'New FN'
    new.form['last_name'] = 'New LN'
    new.form['email'] = 'external@example.org'

    page = new.form.submit().follow()
    assert 'external@example.org' in page

    # Test adding twice
    page = client.get(view)
    page.form['first_name'] = 'Duplicate FN'
    page.form['last_name'] = 'Duplicate LN'
    page.form['email'] = 'external@example.org'
    page = page.form.submit()
    assert 'Ein Teilnehmer mit dieser E-Mail existiert bereits' in page
