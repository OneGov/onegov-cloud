import os
import yaml

from click.testing import CliRunner
from onegov.town.cli import cli


def test_manage_towns(postgres_dsn, temporary_directory):

    cfg = {
        'applications': [
            {
                'path': '/onegov_town/*',
                'application': 'onegov.town.TownApp',
                'namespace': 'onegov_town',
                'configuration': {
                    'dsn': postgres_dsn
                }
            }
        ]
    }

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')

    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_town/newyork',
        'add', 'New York'
    ])

    assert result.exit_code == 0
    assert "New York was created successfully" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_town/newyork',
        'add', 'New York'
    ])

    assert result.exit_code == 1
    assert "may not reference an existing path" in result.output

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_town/newyork', 'delete'
    ], input='y\n')

    assert result.exit_code == 0
    assert "New York was deleted successfully" in result.output
