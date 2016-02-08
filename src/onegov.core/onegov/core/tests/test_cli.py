import os.path
import transaction
import yaml

from click.testing import CliRunner
from email.header import decode_header
from email.utils import parseaddr
from onegov.core import Framework
from onegov.core.cli import cli
from smtplib import SMTPRecipientsRefused
from unittest.mock import patch


def test_sendmail(smtp, temporary_directory):

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
        '--hostname', smtp.address[0],
        '--port', smtp.address[1]
    ])

    assert result.exit_code == 0
    assert len(smtp.outbox) == 0

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

    assert len(smtp.outbox) == 0

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtp.address[0],
        '--port', smtp.address[1]
    ])

    assert result.exit_code == 0
    assert len(smtp.outbox) == 1

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtp.address[0],
        '--port', smtp.address[1]
    ])

    assert result.exit_code == 0
    assert len(smtp.outbox) == 1

    message = smtp.outbox[0]

    assert message['Sender'] == 'Govikon <noreply@example.org>'
    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['Reply-To'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'
    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/plain; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        'VGhpcyBlLW1haWwgaXMganVzdCBhIHRlc3Q=\n'
    )
    assert message.get_payload()[1].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        'VGhpcyBlLW1haWwgaXMganVzdCBhIHRlc3Q=\n'
    )


def test_sendmail_limit(smtp, temporary_directory):

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
        '--hostname', smtp.address[0],
        '--port', smtp.address[1]
    ])

    assert result.exit_code == 0
    assert len(smtp.outbox) == 0

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

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    transaction.commit()

    assert len(smtp.outbox) == 0

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtp.address[0],
        '--port', smtp.address[1],
        '--limit', 1
    ])

    assert result.exit_code == 0
    assert len(smtp.outbox) == 1

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtp.address[0],
        '--port', smtp.address[1],
        '--limit', 2
    ])

    assert len(smtp.outbox) == 3

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    transaction.commit()

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtp.address[0],
        '--port', smtp.address[1]
    ])

    assert len(smtp.outbox) == 5


def test_sendmail_unicode(smtp, temporary_directory):

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
    app.mail_sender = 'noreply@example.org'
    app.mail_use_directory = True
    app.mail_directory = os.path.join(temporary_directory, 'mails')

    app.send_email(
        reply_to='Gövikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mäil",
        content="👍"
    )

    transaction.commit()

    CliRunner().invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--hostname', smtp.address[0],
        '--port', smtp.address[1]
    ])

    message = smtp.outbox[0]

    def decode(header):
        name, addr = parseaddr(header)

        try:
            name = decode_header(name)[0][0].decode('utf-8')
        except AttributeError:
            pass

        return name, addr

    assert decode(message['Sender']) == ("Gövikon", 'noreply@example.org')
    assert decode(message['From']) == ("Gövikon", 'noreply@example.org')
    assert decode(message['Reply-To']) == ("Gövikon", 'info@example.org')
    assert decode_header(message['Subject'])[0][0].decode('utf-8')\
        == "Test E-Mäil"

    assert message.get_payload()[0].as_string() == (
        'Content-Type: text/plain; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        '8J+RjQ==\n'
    )

    assert message.get_payload()[1].as_string() == (
        'Content-Type: text/html; charset="utf-8"\n'
        'MIME-Version: 1.0\n'
        'Content-Transfer-Encoding: base64\n\n'
        '8J+RjQ==\n'
    )


def test_sender_refused(smtp, temporary_directory):

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
    app.mail_sender = 'noreply@example.org'
    app.mail_use_directory = True
    app.mail_directory = os.path.join(temporary_directory, 'mails')

    app.send_email(
        reply_to='Gövikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mäil",
        content="👍"
    )

    transaction.commit()

    def raise_error(*args, **kwargs):
        raise SMTPRecipientsRefused(recipients={'foo': 'bar'})

    with patch('smtplib.SMTP.sendmail', side_effect=raise_error):

        result = CliRunner().invoke(cli, [
            '--config', os.path.join(temporary_directory, 'onegov.yml'),
            'sendmail',
            '--hostname', smtp.address[0],
            '--port', smtp.address[1]
        ])

    assert len(smtp.outbox) == 0
    assert "Could not send e-mail: {'foo': 'bar'}" in result.output
    assert result.exit_code == 1
