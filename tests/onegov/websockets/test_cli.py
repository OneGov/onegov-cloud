from __future__ import annotations

import pytest

from click.testing import CliRunner
from onegov.websockets.cli import cli
from os import path
from unittest.mock import patch
from yaml import dump


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from unittest.mock import MagicMock


@pytest.fixture(scope='function')
def cfg_path(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str,
    websocket_config: dict[str, Any]
) -> str:
    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': (
                    'tests.onegov.websockets.conftest.WebsocketsTestApp'
                ),
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'identity_secret': 'much-secret',
                    'websockets': {
                        'client_url': websocket_config['url'],
                        'manage_url': websocket_config['url'],
                        'manage_token': websocket_config['token']
                    }
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


@patch('onegov.websockets.cli.init_sentry')
@patch('onegov.websockets.cli.main')
def test_cli_serve(
    main: MagicMock,
    init_sentry: MagicMock,
    cfg_path: str,
    websocket_config: dict[str, Any]
) -> None:

    runner = CliRunner()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'serve'
    ])
    assert result.exit_code == 0
    assert init_sentry.call_count == 0
    assert main.call_count == 1
    assert main.call_args[0][0] == '127.0.0.1'
    assert main.call_args[0][1] == websocket_config['port']
    assert main.call_args[0][2] == 'super-super-secret-token'

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'serve',
        '--host', '127.0.0.2',
        '--port', '8887',
        '--token', 'not-so-secret-token',
        '--sentry-dsn', 'https://sentry.io/foo-bar',
        '--sentry-environment', 'foo-bar',
        '--sentry-release', '1.0'
    ])
    assert result.exit_code == 0
    assert init_sentry.call_count == 1
    assert init_sentry.call_args[1] == {
        'dsn': 'https://sentry.io/foo-bar',
        'environment': 'foo-bar',
        'release': '1.0',
    }

    assert main.call_count == 2
    assert main.call_args[0][0] == '127.0.0.2'
    assert main.call_args[0][1] == 8887
    assert main.call_args[0][2] == 'not-so-secret-token'


@patch('onegov.websockets.cli.connect')
@patch('onegov.websockets.cli.authenticate')
@patch('onegov.websockets.cli.get_status', return_value='XYZ')
def test_cli_status(
    status: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    cfg_path: str,
    websocket_config: dict[str, Any]
) -> None:

    runner = CliRunner()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'status'
    ])
    assert result.exit_code == 0
    assert connect.call_count == 1
    assert connect.call_args[0][0] == websocket_config['url']
    assert authenticate.call_count == 1
    assert authenticate.call_args[0][1] == 'super-super-secret-token'
    assert status.call_count == 1
    assert 'XYZ' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'status',
        '--url', 'wss://govikon.org/ws',
        '--token', 'not-so-secret-token'
    ])
    assert result.exit_code == 0
    assert connect.call_count == 2
    assert connect.call_args[0][0] == 'wss://govikon.org/ws'
    assert authenticate.call_count == 2
    assert authenticate.call_args[0][1] == 'not-so-secret-token'
    assert status.call_count == 2
    assert 'XYZ' in result.output


@patch('onegov.websockets.cli.connect')
@patch('onegov.websockets.cli.authenticate')
@patch('onegov.websockets.cli.broadast_message', return_value='XYZ')
def test_cli_broadcast(
    broadcast: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    cfg_path: str,
    websocket_config: dict[str, Any]
) -> None:

    runner = CliRunner()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'broadcast',
        '{"a": "b"}'
    ])
    assert result.exit_code == 0
    assert connect.call_count == 1
    assert connect.call_args[0][0] == websocket_config['url']
    assert authenticate.call_count == 1
    assert authenticate.call_args[0][1] == 'super-super-secret-token'
    assert broadcast.call_count == 1
    assert broadcast.call_args[0][1] == 'foo-bar'
    assert broadcast.call_args[0][2] is None
    assert broadcast.call_args[0][3] == {'a': 'b'}
    assert '{"a": "b"} sent to foo-bar' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'broadcast',
        '--url', 'wss://govikon.org/ws',
        '--schema', 'foo-baz',
        '--channel', 'one',
        '--token', 'not-so-secret-token',
        '{"a": "b"}'
    ])
    assert result.exit_code == 0
    assert connect.call_count == 2
    assert connect.call_args[0][0] == 'wss://govikon.org/ws'
    assert authenticate.call_count == 2
    assert authenticate.call_args[0][1] == 'not-so-secret-token'
    assert broadcast.call_count == 2
    assert broadcast.call_args[0][1] == 'foo-baz'
    assert broadcast.call_args[0][2] == 'one'
    assert broadcast.call_args[0][3] == {'a': 'b'}
    assert '{"a": "b"} sent to foo-baz-one' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'broadcast',
        '--private',
        '{"a": "b"}'
    ])
    assert result.exit_code == 0
    assert connect.call_count == 3
    assert connect.call_args[0][0] == websocket_config['url']
    assert authenticate.call_count == 3
    assert authenticate.call_args[0][1] == 'super-super-secret-token'
    # NOTE: undo mypy narrowing of call_args
    broadcast2 = broadcast
    assert broadcast2.call_count == 3
    assert broadcast2.call_args[0][1] == 'foo-bar'
    assert broadcast2.call_args[0][2]
    assert broadcast2.call_args[0][3] == {'a': 'b'}
    assert f'foo-bar-{broadcast2.call_args[0][2]}' in result.output


@patch('onegov.websockets.cli.connect')
@patch('onegov.websockets.cli.register')
def test_cli_listen(
    register: MagicMock,
    connect: MagicMock,
    cfg_path: str,
    websocket_config: dict[str, Any]
) -> None:

    runner = CliRunner()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'listen',
    ])
    assert result.exit_code == 0
    assert connect.call_count == 1
    assert connect.call_args[0][0] == websocket_config['url']
    assert register.call_count == 1
    assert register.call_args[0][1] == 'foo-bar'
    assert register.call_args[0][2] is None
    assert f'Listing on {websocket_config["url"]} @ foo-bar' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'listen',
        '--url', 'wss://govikon.org/ws',
        '--schema', 'foo-baz',
        '--channel', 'one',
    ])
    assert result.exit_code == 0
    assert connect.call_count == 2
    assert connect.call_args[0][0] == 'wss://govikon.org/ws'
    assert register.call_count == 2
    assert register.call_args[0][1] == 'foo-baz'
    assert register.call_args[0][2] == 'one'
    assert 'Listing on wss://govikon.org/ws @ foo-baz-one' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'listen',
        '--private',
    ])
    assert result.exit_code == 0
    assert connect.call_count == 3
    assert connect.call_args[0][0] == websocket_config['url']
    # NOTE: undo mypy narrowing of call_args
    register2 = register
    assert register2.call_count == 3
    assert register2.call_args[0][1] == 'foo-bar'
    assert register2.call_args[0][2]
    assert f'foo-bar-{register2.call_args[0][2]}' in result.output
