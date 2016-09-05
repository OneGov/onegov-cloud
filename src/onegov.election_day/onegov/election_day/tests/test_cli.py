import os
import yaml

from click.testing import CliRunner
from onegov.election_day.cli import cli


def test_add_intance(postgres_dsn, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/onegov_election_day/*',
                'application': 'onegov.election_day.ElectionDayApp',
                'namespace': 'onegov_election_day',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    }
                },
            }
        ]
    }
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    principal = {
        'name': 'Govikon',
        'canton': 'be',
        'color': '#fff',
        'logo': 'canton-be.svg',
    }
    principal_path = os.path.join(
        temporary_directory, 'file-storage/onegov_election_day-govikon'
    )
    os.makedirs(principal_path)
    with open(os.path.join(principal_path, 'principal.yml'), 'w') as f:
        f.write(yaml.dump(principal, default_flow_style=False))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/govikon',
        'add',
    ])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output


def test_add_intance_missing_config(postgres_dsn, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/onegov_election_day/*',
                'application': 'onegov.election_day.ElectionDayApp',
                'namespace': 'onegov_election_day',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    }
                },
            }
        ]
    }

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_election_day/govikon',
        'add',
    ])
    assert result.exit_code == 1
    assert "principal.yml not found" in result.output
