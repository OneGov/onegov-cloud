import json
import os.path
import pytest
import transaction
import yaml

from click.testing import CliRunner
from onegov.core.framework import Framework
from onegov.core.cli import cli, GroupContext
from unittest.mock import patch, Mock


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
    assert list(ctx.all_wildcard_selectors) == ['/onegov_test/*']
    assert list(ctx.all_specific_selectors) == []
    assert list(ctx.matches) == []


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
def test_create_command_group_single_path(cli, cli_config):
    runner = CliRunner()
    schemas = ['foobar-foo', 'foobar-bar']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/*', 'create'
        ])
        assert "The selector must match a single path" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_group_existing_path(cli, cli_config):
    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/foo', 'create'
        ])
        assert "may not reference an existing path" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_full_path(cli, cli_config):
    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar', 'create'
        ])
        assert "must reference a full path" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_wildcard(cli, cli_config):

    runner = CliRunner()
    schemas = []

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        result = runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/*', 'create'
        ])
        assert "may not contain a wildcard" in result.output


@pytest.mark.parametrize('cli', [{'creates_path': True}], indirect=True)
def test_create_command_request_called(cli, cli_config):

    runner = CliRunner()
    schemas = []

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        runner.invoke(cli, [
            '--config', cli_config, '--select', '/foobar/foo', 'create'
        ])

        assert cli.called
        assert cli.called_request


@pytest.mark.parametrize('cli', [{'default_selector': '*'}], indirect=True)
def test_create_command_default_selector(cli, cli_config):

    runner = CliRunner()
    schemas = ['foobar-foo']

    with patch.object(GroupContext, 'available_schemas', return_value=schemas):
        runner.invoke(cli, [
            '--config', cli_config, 'create'
        ])

        assert cli.called
        assert cli.called_request


def test_sendmail(temporary_directory, maildir_app, monkeypatch):
    mock_send = Mock(return_value=None)
    monkeypatch.setattr(
        'onegov.core.mail_processor.MailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token',
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0

    app.send_email(
        reply_to='Govikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mail",
        content="This e-mail is just a test"
    )

    transaction.commit()

    assert len(os.listdir(maildir)) == 1

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token',
    ])

    assert result.exit_code == 0
    assert mock_send.called
    assert len(os.listdir(maildir)) == 0

    messages = json.loads(mock_send.call_args.args[0])
    assert len(messages) == 1
    message = messages[0]
    assert message['From'] == 'Govikon <noreply@example.org>'
    assert message['ReplyTo'] == 'Govikon <info@example.org>'
    assert message['Subject'] == 'Test E-Mail'

    mock_send.reset_mock()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token',
    ])

    assert result.exit_code == 0
    assert not mock_send.called
    assert len(os.listdir(maildir)) == 0


def test_sendmail_limit(temporary_directory, maildir_app, monkeypatch):
    mock_send = Mock(return_value=None)
    monkeypatch.setattr(
        'onegov.core.mail_processor.MailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token'
    ])

    assert result.exit_code == 0
    assert len(os.listdir(maildir)) == 0

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
    assert len(os.listdir(maildir)) == 3

    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token',
        '--limit', 1
    ])

    assert result.exit_code == 0
    assert mock_send.call_count == 1
    assert len(os.listdir(maildir)) == 2

    mock_send.reset_mock()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token',
        '--limit', 2
    ])

    assert mock_send.call_count == 2
    assert len(os.listdir(maildir)) == 0

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

    mock_send.reset_mock()
    result = runner.invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token'
    ])

    assert mock_send.call_count == 2
    assert len(os.listdir(maildir)) == 0


def test_sendmail_exception(temporary_directory, maildir_app, monkeypatch):
    error = RuntimeError('Failed to send request.')
    mock_send = Mock(side_effect=error)
    monkeypatch.setattr(
        'onegov.core.mail_processor.MailQueueProcessor.send',
        mock_send
    )
    maildir = os.path.join(temporary_directory, 'mails')
    app = maildir_app
    app.send_email(
        reply_to='Gövikon <info@example.org>',
        receivers=['recipient@example.org'],
        subject="Test E-Mäil",
        content="👍"
    )

    transaction.commit()

    result = CliRunner().invoke(cli, [
        '--config', os.path.join(temporary_directory, 'onegov.yml'),
        'sendmail',
        '--token', 'token',
    ])

    # should contain a .sending and the actual mail
    assert len(os.listdir(maildir)) == 2
    assert result.exception == error
    assert result.exit_code == 1
