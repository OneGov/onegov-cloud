import transaction

from onegov.core.utils import Bunch
from onegov.town import TownApp


def test_send_email(smtpserver):

    class App(TownApp):

        @property
        def town(self):
            return Bunch(
                name="Gemeinde Govikon",
                meta=dict(reply_to='info@govikon.ch')
            )

    app = App()
    app.mail_host, app.mail_port = smtpserver.addr
    app.mail_sender = 'mails@govikon.ch'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False

    app.send_email(receivers=['civilian@example.org'], subject='Test')
    assert len(smtpserver.outbox) == 0
    transaction.abort()

    app.send_email(receivers=['civilian@example.org'], subject='Test')
    assert len(smtpserver.outbox) == 0
    transaction.commit()

    assert len(smtpserver.outbox) == 1
    mail = smtpserver.outbox[0]

    assert mail['Reply-To'] == 'Gemeinde Govikon <info@govikon.ch>'
    assert mail['Subject'] == 'Test'
    assert mail['Sender'] == 'Gemeinde Govikon <mails@govikon.ch>'
    assert mail['From'] == 'Gemeinde Govikon <mails@govikon.ch>'
