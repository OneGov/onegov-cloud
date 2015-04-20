from click.testing import CliRunner
from onegov.user.cli import cli


def test_cli(postgres_dsn):

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'add', 'admin', 'admin@example.org',
        '--password', 'hunter2'
    ])

    assert result.exit_code == 0
    assert 'The user admin@example.org was added' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'add', 'admin', 'admin@example.org',
        '--password', 'hunter2'
    ])

    assert result.exit_code == 1
    assert 'The user admin@example.org already exists' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'exists', 'admin@example.org'
    ])

    assert result.exit_code == 0
    assert 'The user admin@example.org exists' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'change-password', 'admin@example.org',
        '--password', 'hunter2'
    ])

    assert result.exit_code == 0
    assert 'The password for admin@example.org was changed' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'delete', 'admin@example.org'
    ])

    assert result.exit_code == 0
    assert 'The user admin@example.org was deleted' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'delete', 'admin@example.org'
    ])

    assert result.exit_code == 1
    assert 'The user admin@example.org does not exist' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'exists', 'admin@example.org'
    ])

    assert result.exit_code == 1
    assert 'The user admin@example.org does not exist' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-user',
        'change-password', 'admin@example.org',
        '--password', 'hunter2'
    ])

    assert result.exit_code == 1
    assert 'The user admin@example.org does not exist' in result.output
