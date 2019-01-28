import os
import yaml

from click.testing import CliRunner
from onegov.wtfs.cli import cli


def write_config(path, postgres_dsn, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/onegov_wtfs/*',
                'application': 'onegov.wtfs.WtfsApp',
                'namespace': 'onegov_wtfs',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    },
                },
            }
        ]
    }
    with open(path, 'w') as f:
        f.write(yaml.dump(cfg))


def run_command(cfg_path, principal, commands, input=None):
    runner = CliRunner()
    return runner.invoke(
        cli,
        [
            '--config', cfg_path,
            '--select', '/onegov_wtfs/{}'.format(principal),
        ] + commands,
        input
    )


def test_add_instance(postgres_dsn, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 1
    assert "This selector may not reference an existing path" in result.output


def test_delete_instance(postgres_dsn, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['delete'], 'n')
    assert result.exit_code == 1
    assert "Deletion process aborted" in result.output

    result = run_command(cfg_path, 'govikon', ['delete'], 'y')
    assert result.exit_code == 0
    assert "Instance was deleted successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['delete'], 'y')
    assert result.exit_code == 1
    assert "Selector doesn't match any paths, aborting." in result.output
