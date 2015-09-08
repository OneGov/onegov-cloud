# -*- coding: utf-8 -*-
import os.path
import transaction
import yaml

from click.testing import CliRunner
from email.header import decode_header
from email.utils import parseaddr
from onegov.core import Framework
from onegov.core.cli import cli


def test_sendmail(smtpserver, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': {
                    'mail_use_directory': True,
                    'mail_directory': os.path.join(
                        temporary_directory, 'mails')
                }
            }
        ]
    }

    os.makedirs(os.path.join(temporary_directory, 'mails'))
    os.makedirs(os.path.join(temporary_directory, 'mails', 'new'))
    os.makedirs(os.path.join(temporary_directory, 'mails', 'cur'))
    os.makedirs(os.path.join(temporary_directory, 'mails', 'tmp'))

    with open(os.path.join(temporary_directory, 'onegov.yml'), 'w') as f:
        f.write(yaml.dump(cfg))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtpserver.addr[0],
        '--port', smtpserver.addr[1]
    ])

    assert result.exit_code == 0
    assert len(smtpserver.outbox) == 0

    app = Framework()
    app.mail_sender = 'noreply@example.org'
    app.mail_use_directory = True
    app.mail_directory = os.path.join(temporary_directory, 'mails')

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    transaction.commit()

    assert len(smtpserver.outbox) == 0

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtpserver.addr[0],
        '--port', smtpserver.addr[1]
    ])

    assert result.exit_code == 0
    assert len(smtpserver.outbox) == 1

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtpserver.addr[0],
        '--port', smtpserver.addr[1]
    ])

    assert result.exit_code == 0
    assert len(smtpserver.outbox) == 1

    message = smtpserver.outbox[0]

    assert message['Sender'] == 'Govikon <noreply@example.org>'
    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['Reply-To'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'
    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        'VGhpcyBlLW1haWwgaXMganVzdCBhIHRlc3Q=\n'
    )


def test_sendmail_unicode(smtpserver, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': {
                    'mail_use_directory': True,
                    'mail_directory': os.path.join(
                        temporary_directory, 'mails')
                }
            }
        ]
    }

    os.makedirs(os.path.join(temporary_directory, 'mails'))
    os.makedirs(os.path.join(temporary_directory, 'mails', 'new'))
    os.makedirs(os.path.join(temporary_directory, 'mails', 'cur'))
    os.makedirs(os.path.join(temporary_directory, 'mails', 'tmp'))

    with open(os.path.join(temporary_directory, 'onegov.yml'), 'w') as f:
        f.write(yaml.dump(cfg))

    app = Framework()
    app.mail_sender = u'noreply@example.org'
    app.mail_use_directory = True
    app.mail_directory = os.path.join(temporary_directory, 'mails')

    app.send_email(
        reply_to=u'Gövikon <info@example.org>',
        receivers=[u'recipient@example.org'],
        subject=u"Test E-Mäil",
        content=u"👍"
    )

    transaction.commit()

    CliRunner().invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtpserver.addr[0],
        '--port', smtpserver.addr[1]
    ])

    message = smtpserver.outbox[0]

    def decode(header):
        name, addr = parseaddr(header)

        try:
            name = decode_header(name)[0][0].decode('utf-8')
        except AttributeError:
            pass

        return name, addr

    assert decode(message['Sender']) == (u"Gövikon", 'noreply@example.org')
    assert decode(message['From']) == (u"Gövikon", 'noreply@example.org')
    assert decode(message['Reply-To']) == (u"Gövikon", 'info@example.org')
    assert decode_header(message['Subject'])[0][0].decode('utf-8')\
        == u"Test E-Mäil"

    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        '8J+RjQ==\n'
    )
