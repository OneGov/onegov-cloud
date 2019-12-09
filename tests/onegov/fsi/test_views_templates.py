from onegov.fsi.models.course_notification_template import InfoTemplate

from tests.onegov.org.common import get_mail


def test_send_template(client_with_db):
    client = client_with_db
    session = client.app.session()
    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/send'
    client.login_editor()
    client.get(view, status=403)
    client.login_admin()
    page = client.get(view)
    page = page.form.submit().follow()
    assert "an 2 Empfänger gesendet" in page
    assert len(client.app.smtp.outbox) == 2
    email = get_mail(client.app.smtp.outbox, 0)

    assert email['to'] == 'admin@example.org' or 'member@example.org'
    text = email['text']
    assert "Bitte beachten sie die untenstehenden Informationen." in text


def test_embed_template(client_with_db):
    client = client_with_db
    session = client.app.session()
    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/embed'
    client.login_editor()
    client.get(view, status=403)
    client.login_admin()
    client.get(view)
