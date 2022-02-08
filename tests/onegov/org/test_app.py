import os
import transaction

from onegov.core.utils import Bunch
from onegov.org import OrgApp
from tests.shared import Client


def test_allowed_application_id(org_app):
    # little bobby tables!
    assert not org_app.is_allowed_application_id(
        "Robert'); DROP TABLE Students; --"
    )
    assert not org_app.is_allowed_application_id('foo')
    org_app.session_manager.ensure_schema_exists(org_app.namespace + '-foo')
    assert org_app.is_allowed_application_id('foo')


def test_send_email(maildir):

    class App(OrgApp):

        @property
        def org(self):
            return Bunch(
                name="Gemeinde Govikon",
                title="Gemeinde Govikon",
                meta=dict(reply_to='info@govikon.ch')
            )

    app = App()
    app.mail = {
        'marketing': {
            'directory': maildir,
            'sender': 'mails@govikon.ch'
        },
        'transactional': {
            'directory': maildir,
            'sender': 'mails@govikon.ch'
        }
    }
    app.maildir = maildir
    client = Client(app)

    app.send_email(
        receivers=['civilian@example.org'],
        subject='Test',
        content='Test',
        category='transactional'
    )
    assert len(os.listdir(maildir)) == 0
    transaction.abort()

    app.send_email(
        receivers=['civilian@example.org'],
        subject='Test',
        content='Test',
        category='transactional'
    )
    assert len(os.listdir(maildir)) == 0
    transaction.commit()

    assert len(os.listdir(maildir)) == 1
    mail = client.get_email(0)

    assert mail['ReplyTo'] == 'Gemeinde Govikon <info@govikon.ch>'
    assert mail['Subject'] == 'Test'
    assert mail['From'] == 'Gemeinde Govikon <mails@govikon.ch>'
