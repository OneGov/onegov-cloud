from onegov.fsi.models.course_notification_template import InfoTemplate


def test_send_template(client_with_db):
    client = client_with_db
    session = client.app.session()
    info_template = session.query(InfoTemplate).first()
    view = f'/fsi/template/{info_template.id}/send'
    client.login_editor()
    page = client.get(view)
    page.click('Send E-Mail Now')
