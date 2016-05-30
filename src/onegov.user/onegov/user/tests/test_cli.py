import os.path
import yaml

from click.testing import CliRunner
from onegov.user.cli import cli


def test_cli(postgres_dsn, session_manager, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')

    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

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

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'add', 'admin', 'admin@example.org',
        '--password', 'hunter2',
        '--no-prompt',
    ])

    assert result.exit_code == 1
    assert 'admin@example.org already exists' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'exists', 'admin@example.org'
    ])

    assert result.exit_code == 0
    assert 'admin@example.org exists' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-password', 'admin@example.org',
        '--password', 'hunter2'
    ])

    assert result.exit_code == 0
    assert "admin@example.org's password was changed" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'delete', 'admin@example.org'
    ])

    assert result.exit_code == 0
    assert 'admin@example.org was deleted' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'delete', 'admin@example.org'
    ])

    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'exists', 'admin@example.org'
    ])

    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'change-password', 'admin@example.org',
        '--password', 'hunter2'
    ])

    assert result.exit_code == 1
    assert 'admin@example.org does not exist' in result.output
