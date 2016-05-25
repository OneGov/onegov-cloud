import os.path
import transaction
import yaml

from click.testing import CliRunner
from email.header import decode_header
from email.utils import parseaddr
from onegov.core import Framework
from onegov.core.cli import cli, GroupContext, command_group
from smtplib import SMTPRecipientsRefused
from unittest.mock import patch


def test_group_context_without_schemas(postgres_dsn):
    ctx = GroupContext('/onegov_test/*', {
        'applications': [{
            'path': '/onegov_test/*',
            'application': 'onegov.core.Framework',
            'namespace': 'onegov_test',
            'configuration': {
                'dsn': postgres_dsn
            }
        }]
    })

    assert len(tuple(ctx.appcfgs)) == 1
    assert list(ctx.available_selectors) == ['/onegov_test/*']
    assert list(ctx.all_wildcard_paths) == ['/onegov_test/*']
    assert list(ctx.all_paths) == []
    assert list(ctx.matching_paths) == []


def test_group_context_with_schemas(postgres_dsn):
    class TestContext(GroupContext):

        def available_schemas(self, *args, **kwargs):
            return ['onegov_test-foo', 'onegov_test-bar']

    ctx = TestContext('/onegov_test/*', {
        'applications': [{
            'path': '/onegov_test/*',
            'application': 'onegov.core.Framework',
            'namespace': 'onegov_test',
            'configuration': {
                'dsn': postgres_dsn
            }
        }]
    })

    assert len(tuple(ctx.appcfgs)) == 1
    assert list(ctx.available_selectors) == [
        '/onegov_test/*',
        '/onegov_test/bar',
        '/onegov_test/foo'
    ]
    assert list(ctx.all_wildcard_paths) == ['/onegov_test/*']
    assert list(ctx.all_paths) == [
        '/onegov_test/foo',
        '/onegov_test/bar'
    ]
    assert list(ctx.matching_paths) == [
        '/onegov_test/foo',
        '/onegov_test/bar'
    ]

    ctx.selector = '/onegov_test/foo'
    assert list(ctx.matching_paths) == [
        '/onegov_test/foo',
    ]

    ctx.selector = '/onegov_test/b??'
    assert list(ctx.matching_paths) == [
        '/onegov_test/bar',
    ]


def create_command_fixture(temporary_directory, postgres_dsn):
    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': {
                    'dsn': postgres_dsn
                }
            }
        ]
    }

    with open(os.path.join(temporary_directory, 'onegov.yml'), 'w') as f:
        f.write(yaml.dump(cfg))

    cli = command_group()

    @cli.command(context_settings={'creates_path': True})
    def create():
        nonlocal cli
        cli.called = True

        def perform(request, app):
            cli.called_request = True

        return perform

    return cli


def test_create_command_group_single_path(temporary_directory, postgres_dsn):
    cli = create_command_fixture(temporary_directory, postgres_dsn)
    cfg = os.path.join(temporary_directory, 'onegov.yml')

    runner = CliRunner()
    schemas = ['foobar-foo', 'foobar-bar']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, ['--config', cfg, '/foobar/*', 'create'])
        assert "The selector must match a single path" in result.output


def test_create_command_group_existing_path(temporary_directory, postgres_dsn):
    cli = create_command_fixture(temporary_directory, postgres_dsn)
    cfg = os.path.join(temporary_directory, 'onegov.yml')

    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, ['--config', cfg, '/foobar/foo', 'create'])
        assert "may not reference an existing path" in result.output


def test_create_command_full_path(temporary_directory, postgres_dsn):
    cli = create_command_fixture(temporary_directory, postgres_dsn)
    cfg = os.path.join(temporary_directory, 'onegov.yml')

    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, ['--config', cfg, '/foobar', 'create'])
        assert "must reference a full path" in result.output


def test_create_command_wildcard(temporary_directory, postgres_dsn):
    cli = create_command_fixture(temporary_directory, postgres_dsn)
    cfg = os.path.join(temporary_directory, 'onegov.yml')

    runner = CliRunner()
    schemas = []

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, ['--config', cfg, '/foobar/*', 'create'])
        assert "may not contain a wildcard" in result.output


def test_create_command_request_called(temporary_directory, postgres_dsn):
    cli = create_command_fixture(temporary_directory, postgres_dsn)
    cfg = os.path.join(temporary_directory, 'onegov.yml')

    runner = CliRunner()
    schemas = []

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        runner.invoke(cli, ['--config', cfg, '/foobar/foo', 'create'])

        assert cli.called
        assert cli.called_request


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
