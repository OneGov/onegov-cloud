import transaction

from onegov.core.utils import Bunch
from onegov.org import OrgApp


def test_allowed_application_id(org_app):
    # little bobby tables!
    assert not org_app.is_allowed_application_id(
        "Robert'); DROP TABLE Students; --"
    )
    assert not org_app.is_allowed_application_id('foo')
    org_app.session_manager.ensure_schema_exists(org_app.namespace + '-foo')
    assert org_app.is_allowed_application_id('foo')


def test_send_email(smtp):

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
            'host': smtp.address[0],
            'port': smtp.address[1],
            'force_tls': False,
            'username': None,
            'password': None,
            'use_directory': False,
            'sender': 'mails@govikon.ch'
        },
        'transactional': {
            'host': smtp.address[0],
            'port': smtp.address[1],
            'force_tls': False,
            'username': None,
            'password': None,
            'use_directory': False,
            'sender': 'mails@govikon.ch'
        }
    }

    app.send_email(receivers=['civilian@example.org'], subject='Test')
    assert len(smtp.outbox) == 0
    transaction.abort()

    app.send_email(receivers=['civilian@example.org'], subject='Test')
    assert len(smtp.outbox) == 0
    transaction.commit()

    assert len(smtp.outbox) == 1
    mail = smtp.outbox[0]

    assert mail['Reply-To'] == 'Gemeinde Govikon <info@govikon.ch>'
    assert mail['Subject'] == 'Test'
    assert mail['Sender'] == 'Gemeinde Govikon <mails@govikon.ch>'
    assert mail['From'] == 'Gemeinde Govikon <mails@govikon.ch>'
