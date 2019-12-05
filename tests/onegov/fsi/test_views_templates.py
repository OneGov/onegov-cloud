import pytest

from onegov.fsi.models.course_notification_template import InfoTemplate


@pytest.mark.skip('Test runs endlessly in mirakuru package')
def test_send_template(client_with_es_db):
    client = client_with_es_db
    session = client.app.session()
    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/send'
    client.login_editor()
    client.get(view)
    # page = page.form.submit().follow()
    # assert "an 2 Empfänger gesendet" in page.form.submit().follow()
    # assert len(client.app.smtp.outbox) == 2
    # email = client.get_email(0)


def test_embed_template(client_with_db):
    client = client_with_db
    session = client.app.session()
    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/embed'
    client.login_editor()
    client.get(view, status=403)
    client.login_admin()
    client.get(view)

