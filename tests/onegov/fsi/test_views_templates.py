
from onegov.fsi.models.course_notification_template import InfoTemplate


def test_send_template(client_with_db, attendee):
    client = client_with_db
    session = client.app.session()
    attendee, data = attendee(session)

    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/send'
    client.login_admin()
    page = client.get(view)
    page = page.form.submit().follow()
    assert "an 2 Empfänger gesendet" in page
    assert len(client.app.smtp.outbox) == 2
    message = client.app.smtp.outbox.pop()
    assert message['To'] == 'admin@example.org'
    assert message['Subject'] == 'Info Mail'

    message = client.app.smtp.outbox.pop()
    assert message['To'] == 'member@example.org'

    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('utf-8')
    assert f'{attendee.first_name} {attendee.last_name}' in message
    assert 'Name' in message
    assert 'Kurslokal' in message
    assert 'Datum' in message
    assert 'Referent' in message
    assert info_template.text_html in message


def test_embed_template(client_with_db):
    client = client_with_db
    session = client.app.session()
    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/embed'
    client.login_admin()
    client.get(view)
