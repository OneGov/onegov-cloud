from __future__ import annotations

import json
import os.path
import pytest
import transaction

from click.testing import CliRunner
from onegov.core.cli import cli, GroupContext
from unittest.mock import patch, Mock


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core import Framework
    from .conftest import SmtpApp, TestGroup


def test_group_context_without_schemas(postgres_dsn: str) -> None:
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
    assert list(ctx.all_wildcard_selectors) == ['/onegov_test/*']
    assert list(ctx.all_specific_selectors) == []
    assert list(ctx.matches) == []


def test_group_context_with_schemas(postgres_dsn: str) -> None:
    class TestContext(GroupContext):
        def available_schemas(
            self,
            *args: object,
            **kwargs: object
        ) -> list[str]:
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
    assert list(ctx.all_wildcard_selectors) == ['/onegov_test/*']
    assert list(ctx.all_specific_selectors) == [
        '/onegov_test/foo',
        '/onegov_test/bar'
    ]
    assert list(ctx.matches) == [
        '/onegov_test/foo',
        '/onegov_test/bar'
    ]

    ctx.selector = '/onegov_test/foo'
    assert list(ctx.matches) == [
        '/onegov_test/foo',
    ]

    ctx.selector = '/onegov_test/b??'
    assert list(ctx.matches) == [
        '/onegov_test/bar',
    ]


@pytest.mark.parametrize('cli', [{'singular': True}], indirect=True)
def test_create_command_group_single_path(
    cli: TestGroup,
    cli_config: str
) -> None:

    runner = CliRunner()
    schemas = ['foobar-foo', 'foobar-bar']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/*', 'create'
        ])
        assert "The selector must match a single path" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_group_existing_path(
    cli: TestGroup,
    cli_config: str
) -> None:

    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/foo', 'create'
        ])
        assert "may not reference an existing path" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_full_path(cli: TestGroup, cli_config: str) -> None:
    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar', 'create'
        ])
        assert "must reference a full path" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_wildcard(cli: TestGroup, cli_config: str) -> None:
    runner = CliRunner()

    with patch.object(GroupContext, 'available_schemas', return_value=[]):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/*', 'create'
        ])
        assert "may not contain a wildcard" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_request_called(
    cli: TestGroup,
    cli_config: str
) -> None:

    runner = CliRunner()

    with patch.object(GroupContext, 'available_schemas', return_value=[]):
        runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/foo', 'create'
        ])

        assert cli.called
        assert cli.called_request


@pytest.mark.parametrize('cli', [{'default_selector': '*'}], indirect=True)
def test_create_command_default_selector(
    cli: TestGroup,
    cli_config: str
) -> None:

    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        runner.invoke(cli, [
            '--config', cli_config, 'create'
        ])

        assert cli.called
        assert cli.called_request


def test_sendmail(
    temporary_directory: str,
    maildir_app: Framework,
    monkeypatch: pytest.MonkeyPatch
) -> None:

    mock_send = Mock(return_value=None)
    monkeypatch.setattr(
        'onegov.core.mail_processor.PostmarkMailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )
    transaction.commit()

    assert len(os.listdir(maildir)) == 1

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark'
    ])

    assert result.exit_code == 0
    assert mock_send.called
    assert len(os.listdir(maildir)) == 0

    messages = json.loads(mock_send.call_args.args[1])
    assert len(messages) == 1
    message = messages[0]
    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['ReplyTo'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'

    mock_send.reset_mock()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0
    assert not mock_send.called


def test_sendmail_invalid_queue(
    temporary_directory: str,
    maildir_app: Framework,
    monkeypatch: pytest.MonkeyPatch
) -> None:

    mock_send = Mock(return_value=None)
    monkeypatch.setattr(
        'onegov.core.mail_processor.PostmarkMailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )
    transaction.commit()

    assert len(os.listdir(maildir)) == 1

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'bogus'
    ])

    assert result.exit_code == 1
    assert len(os.listdir(maildir)) == 1


def test_sendmail_smtp(
    temporary_directory: str,
    maildir_smtp_app: SmtpApp
) -> None:

    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_smtp_app
    smtp = app.smtp

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'smtp'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0
    assert len(smtp.outbox) == 0

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )
    transaction.commit()

    assert len(os.listdir(maildir)) == 1
    assert len(smtp.outbox) == 0

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'smtp'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0
    assert len(smtp.outbox) == 1

    message = smtp.outbox[0]
    assert message['from'] == 'Govikon <noreply@example.org>'
    assert message['reply-to'] == 'Govikon <info@example.org>'
    assert message['subject'] == 'Test E-Mail'

    # clear outbox
    del smtp.outbox[:]
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'smtp'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0
    assert len(smtp.outbox) == 0


def test_sendmail_limit(
    temporary_directory: str,
    maildir_app: Framework,
    monkeypatch: pytest.MonkeyPatch
) -> None:

    mock_send = Mock(return_value=None)
    monkeypatch.setattr(
        'onegov.core.mail_processor.PostmarkMailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )

    transaction.commit()
    assert len(os.listdir(maildir)) == 3

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark',
        '--limit', '1'
    ])

    assert result.exit_code == 0
    assert mock_send.call_count == 1
    assert len(os.listdir(maildir)) == 2

    mock_send.reset_mock()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark',
        '--limit', '2'
    ])

    assert mock_send.call_count == 2
    assert len(os.listdir(maildir)) == 0

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test",
        category="transactional"
    )

    transaction.commit()

    mock_send.reset_mock()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark'
    ])

    assert mock_send.call_count == 2
    assert len(os.listdir(maildir)) == 0


def test_sendmail_exception(
    temporary_directory: str,
    maildir_app: Framework,
    monkeypatch: pytest.MonkeyPatch
) -> None:

    error = RuntimeError('Failed to send request.')
    mock_send = Mock(side_effect=error)
    monkeypatch.setattr(
        'onegov.core.mail_processor.PostmarkMailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app
    app.send_email(
        reply_to='Gövikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mäil",
        content="👍",
        category="transactional"
    )

    transaction.commit()

    result = CliRunner().invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--queue', 'postmark'
    ])

    # should contain a .sending and the actual mail
    assert len(os.listdir(maildir)) == 2
    assert result.exception == error
    assert result.exit_code == 1
