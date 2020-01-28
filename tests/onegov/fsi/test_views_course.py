from onegov.fsi.models import Course
from tests.onegov.org.common import get_mail


def test_add_course_and_invite(client):
    view = '/fsi/courses/add'
    client.login_editor()
    client.get(view, status=403)

    # on login, admin gets his attendee
    client.login_admin()
    new = client.get(view)
    new.form['name'] = 'New Course'
    new.form['description'] = 'Desc'
    new.form.submit()

    session = client.app.session()
    course = session.query(Course).one()

    page = client.get(f'/fsi/course/{course.id}/invite')
    page.form['attendees'] = '\n'.join((
        'test1@email.com, admin@example.org',
        'member@example.org'
    ))
    page = page.form.submit().follow()

    assert len(client.app.smtp.outbox) == 1

    # member not found since the user does not have an attendee before login
    assert 'Emails sind unbekannt: test1@email.com, member@example.org' in page

    assert 'Email erfolgreich an 1 Empfänger gesendet' in page

    message = get_mail(client.app.smtp.outbox, 0)
    assert message['to'] == 'admin@example.org'
    assert message['subject'] == '=?utf-8?q?Einladung_f=C3=BCr_Kursanmeldung?='
    text = message['text']
    assert 'New Course' in text
    assert 'Verfügbare Kurstermine finden Sie unter' in text


def test_course_details(client_with_db):
    client = client_with_db
    session = client.app.session()
    course = session.query(Course).first()
    view = f'/fsi/course/{course.id}'
    client.get(view, status=403)

    client.login_member()
    page = client.get(view)

    assert course.name in page
    assert course.description in page


def test_edit_course(client_with_db):
    client = client_with_db
    session = client.app.session()
    course = session.query(Course).first()
    view = f'/fsi/course/{course.id}/edit'

    client.login_editor()
    client.get(view, status=403)

    client.login_admin()
    new = client.get(view)
    new.form['description'] = 'Changed'
    new.form['name'] = 'Changed'
    page = new.form.submit().follow()
    assert 'Changed' in page


def test_delete_course_1(client_with_db):
    client = client_with_db
    assert client.use_intercooler is True
    session = client.app.session()
    course = session.query(Course).first()
    # course_id = course.id
    view = f'/fsi/course/{course.id}'
    client.login_admin()
    assert not course.events.count()

    # csrf protected url must be used
    client.delete(view, status=403)
    page = client.get(view)
    page.click('Löschen')

    page = client.get(view)
    assert "Dieser Kurs besitzt bereits Durchführungen " \
           "und kann nicht gelöscht werden" in page


def test_course_invite(client_with_db):
    client = client_with_db
    session = client.app.session()
    course = session.query(Course).first()
    view = f'/fsi/course/{course.id}/invite'

    client.login_member()
    client.get(view, status=403)

    client.login_editor()
    client.get(view)


def test_course_collection(client):
    view = '/fsi/courses'
    client.get(view, status=403)

    client.login_member(to=view)
    client.get(view)


def test_course_1(client_with_db):
    client = client_with_db
    session = client.app.session()
    course = session.query(Course).first()
    view = f'/fsi/course/{course.id}'
    client.get(view, status=403)

    client.login_member()
    client.get(view, status=200)

    # Test if editor can view embeded email template
    client.login_editor()
    client.get(f'/fsi/course/{course.id}/embed')
