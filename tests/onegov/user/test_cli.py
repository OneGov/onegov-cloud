from __future__ import annotations

import os.path
import yaml

from click.testing import CliRunner
from onegov.core.framework import Framework
from onegov.core.utils import Bunch
from onegov.user import User
from onegov.user.cli import cli
from onegov.user.integration import UserApp
from unittest.mock import patch
from transaction import commit


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager


class TestApp(Framework, UserApp):
    __test__ = False


def test_cli(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:

    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'tests.onegov.user.test_cli.TestApp',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')

    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    def login(
        username: str,
        yubikey: str | None = None,
        phone_number: str | None = None,
        totp: str | None = None
    ) -> None:
        with patch('onegov.user.models.user.remembered'):
            with patch('onegov.user.models.user.forget'):
                session = session_manager.session()
                user = session.query(User).filter_by(username=username).one()
                if yubikey:
                    assert user.second_factor is not None
                    assert user.second_factor['type'] == 'yubikey'
                    assert user.second_factor['data'] == yubikey
                elif phone_number:
                    assert user.second_factor is not None
                    assert user.second_factor['type'] == 'mtan'
                    assert user.second_factor['data'] == phone_number
                elif totp:
                    assert user.second_factor is not None
                    assert user.second_factor['type'] == 'totp'
                    assert user.second_factor['data'] == totp
                else:
                    assert not user.second_factor

                number = len(user.sessions or {}) + 1
                user.save_current_session(Bunch(  # type: ignore[arg-type]
                    browser_session=Bunch(_token=f'session-{number}'),
                    client_addr=f'127.0.0.{number}',
                    user_agent='CLI',
                    app=None
                ))
        commit()

    # Add user
    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'admin', 'admin@example.org',
        '--password', 'hunter2',
        '--no-prompt',
    ])
    assert result.exit_code == 0
    assert 'Adding admin@example.org to foo/bar' in result.output
    assert 'admin@example.org was added' in result.output

    # List all users
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' in result.output
    assert '✔︎' in result.output

    # Login and list all sessions
    login('admin@example.org')
    login('admin@example.org')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' in result.output
    assert '127.0.0.1' in result.output
    assert '127.0.0.2' in result.output

    # Logout user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'logout',
        'admin@example.org'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Login again and list all sessions
    login('admin@example.org')
    login('admin@example.org')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' in result.output
    assert '127.0.0.1' in result.output
    assert '127.0.0.2' in result.output

    # Logout all
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'logout-all',
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Try to re-add user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'admin', 'admin@example.org',
        '--password', 'hunter2',
        '--no-prompt',
    ])
    assert result.exit_code == 1
    assert 'admin@example.org already exists' in result.output

    # Check if user exists
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'exists', 'admin@example.org'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org exists' in result.output

    # Change password
    login('admin@example.org')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-password', 'admin@example.org',
        '--password', 'hunter2'
    ])
    assert result.exit_code == 0
    assert "admin@example.org's password was changed" in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Change username
    login('admin@example.org')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-username', 'admin@example.org',
        'admin2@example.org'
    ])
    assert result.exit_code == 0
    assert "admin@example.org was changed to admin2@" in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin2@example.org' not in result.output

    # Change username back
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-username', 'admin2@example.org',
        'admin@example.org'
    ])
    assert result.exit_code == 0
    assert "admin2@example.org was changed to admin@" in result.output

    # Add a second user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'editor', 'editor@example.org',
        '--password', 'hunter2',
        '--no-prompt',
    ])
    assert result.exit_code == 0
    assert 'Adding editor@example.org to foo/bar' in result.output
    assert 'editor@example.org was added' in result.output

    # Try to change username to existing username
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-username', 'admin@example.org',
        'editor@example.org'
    ])
    assert result.exit_code == 1
    assert "editor@example.org already exists" in result.output

    # Change yubikey
    login('admin@example.org')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-yubikey', 'admin@example.org',
        '--yubikey', 'cccccccdefgh'
    ])
    assert result.exit_code == 0
    assert "admin@example.org's yubikey was changed" in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Create new user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'member', 'member@example.org',
        '--password', 'hunter2',
        '--no-prompt',
    ])
    assert result.exit_code == 0
    assert 'Adding member@example.org to foo/bar' in result.output
    assert 'member@example.org was added' in result.output

    # Transfer yubikey
    login('admin@example.org', yubikey='cccccccdefgh')
    login('member@example.org')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'transfer-yubikey', 'admin@example.org', 'member@example.org'
    ])
    assert result.exit_code == 0
    assert (
        "yubikey was transferred from admin@example.org to member@example.org"
    ) in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output
    assert 'member@example.org' not in result.output

    # Check if changed
    login('admin@example.org')
    login('member@example.org', yubikey='cccccccdefgh')

    # Try to set bogus number for mTAN login
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-mtan', 'admin@example.org',
        '--phone-number', 'bogus'
    ])
    assert result.exit_code == 1
    assert "Failed to parse bogus as a phone number" in result.output

    # Try to set invalid number for mTAN login
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-mtan', 'admin@example.org',
        '--phone-number', '+417811122333'
    ])
    assert result.exit_code == 1
    assert "+417811122333 is not a valid phone number" in result.output

    # Change number for mTAN login
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-mtan', 'admin@example.org',
        '--phone-number', '+41781112233'
    ])
    assert result.exit_code == 0
    assert "admin@example.org's phone number was changed" in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Check if mtan login is set up
    login('admin@example.org', phone_number='+41781112233')

    # Change secret for TOTP login
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-totp', 'admin@example.org',
        '--secret', 'very_secret'
    ])
    assert result.exit_code == 0
    assert "admin@example.org's TOTP secret was changed" in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Check if totp login is set up
    login('admin@example.org', totp='very_secret')

    # Change role
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-role', 'admin@example.org',
        'editor'
    ])
    assert result.exit_code == 0
    assert "admin@example.org's role was changed" in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # List users, check if role has changed
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list'
    ])
    assert result.exit_code == 0
    assert '[admin]' not in result.output
    assert '[editor]' in result.output

    # Deactivate user
    login('admin@example.org', totp='very_secret')
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'deactivate', 'admin@example.org',
    ])

    # List all users, check if deactivated
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' in result.output
    assert '✘' in result.output

    # List all sessions, check if logged-out
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list-sessions'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Delete user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'delete', 'admin@example.org'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org was deleted' in result.output

    # List users, check if deleted
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'list'
    ])
    assert result.exit_code == 0
    assert 'admin@example.org' not in result.output

    # Check if deleted user exists
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'exists', 'admin@example.org'
    ])

    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    # Try to re-delete user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'delete', 'admin@example.org'
    ])
    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    # Try to change password of deleted user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-password', 'admin@example.org',
        '--password', 'hunter2'
    ])
    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    # Try to change yubikey of deleted user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-yubikey', 'admin@example.org',
        '--yubikey', 'cccccccdefgh'
    ])
    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    # Try to transfer yubikey of deleted user
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'transfer-yubikey', 'admin@example.org', 'member@example.org'
    ])
    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    # Try to add realname and phone
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'admin', 'admin@example.org',
        '--password', 'hunter2',
        '--no-prompt',
        '--realname', 'Jane Doe',
        '--phone_number', '0411234567'
    ])

    assert result.exit_code == 0
    assert 'admin@example.org was added' in result.output

    with patch('onegov.user.models.user.forget'):
        session = session_manager.session()
        username = 'admin@example.org'
        user = session.query(User).filter_by(username=username).one()
        assert user.realname == 'Jane Doe'
        assert user.phone_number == '0411234567'


def test_cli_exists_recursive(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:

    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'tests.onegov.user.test_cli.TestApp',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')
    session_manager.ensure_schema_exists('foo-zar')

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')

    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    # Add user to bar
    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'admin', 'admin@bar.org',
        '--password', 'hunterb',
        '--no-prompt',
    ])
    assert result.exit_code == 0
    assert 'Adding admin@bar.org to foo/bar' in result.output
    assert 'admin@bar.org was added' in result.output

    # add user to zar
    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/zar',
        'add', 'admin', 'admin@zar.org',
        '--password', 'hunterz',
        '--no-prompt',
    ])
    assert result.exit_code == 0
    assert 'Adding admin@zar.org to foo/zar' in result.output
    assert 'admin@zar.org was added' in result.output

    # use exits to check if user exists in bar
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'exists', 'admin@bar.org'
    ])
    assert result.exit_code == 0
    assert 'foo-bar admin@bar.org exists' in result.output
    assert 'foo-zar admin@zar exists' not in result.output

    # use exits to check if user exists in zar
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/zar',
        'exists', 'admin@zar.org'
    ])
    assert result.exit_code == 0
    assert 'foo-zar admin@zar.org exists' in result.output
    assert 'foo-bar admin@bar exists' not in result.output

    # use recursive exists
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/*',
        'exists', 'admin@bar.org', '-r'
    ])
    assert result.exit_code == 0
    assert 'foo-bar admin@bar.org exists' in result.output
    assert 'foo-zar admin@bar.org does not exist' in result.output
