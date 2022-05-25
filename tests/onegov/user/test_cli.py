import os.path
import yaml

from click.testing import CliRunner
from onegov.core.utils import Bunch
from onegov.user import User
from onegov.user.cli import cli
from unittest.mock import patch
from transaction import commit


def test_cli(postgres_dsn, session_manager, temporary_directory, redis_url):

    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'onegov.core.Framework',
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

    def login(username):
        with patch('onegov.user.models.user.remembered'):
            with patch('onegov.user.models.user.forget'):
                session = session_manager.session()
                user = session.query(User).filter_by(username=username).one()
                number = len(user.sessions or {}) + 1
                user.save_current_session(Bunch(
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

    # Change role
    login('admin@example.org')
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
    login('admin@example.org')
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
