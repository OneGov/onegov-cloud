from click.testing import CliRunner
from onegov.town.cli import cli


def test_add_town(postgres_dsn):

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-town',
        'add', 'Govikon'
    ])

    assert result.exit_code == 0
    assert 'Govikon was added to the test-add-town schema' in result.output

    result = runner.invoke(cli, [
        '--dsn', postgres_dsn,
        '--schema', 'test-add-town',
        'add', 'Govikon'
    ])

    assert result.exit_code == 1
    assert 'The schema test-add-town already contains a town' in result.output
