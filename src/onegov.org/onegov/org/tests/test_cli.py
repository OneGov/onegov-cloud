import os
import yaml

from click.testing import CliRunner
from onegov.org.cli import cli


def test_manage_orgs(postgres_dsn, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/onegov_org/*',
                'application': 'onegov.org.OrgApp',
                'namespace': 'onegov_org',
                'configuration': {
                    'dsn': postgres_dsn,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage'
                }
            }
        ]
    }

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')

    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/newyork',
        'add', 'New York'
    ])

    assert result.exit_code == 0
    assert "New York was created successfully" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/newyork',
        'add', 'New York'
    ])

    assert result.exit_code == 1
    assert "may not reference an existing path" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/newyork', 'delete'
    ], input='y\n')

    assert result.exit_code == 0
    assert "New York was deleted successfully" in result.output
