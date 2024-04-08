from click.testing import CliRunner

from onegov.translator_directory.cli import cli
from tests.onegov.translator_directory.shared import create_translator


def test_migrate_command(
    cfg_path, session_manager, translator_app
):

    local = 'bar'

    session_manager.set_current_schema(f'translator_directory-{local}')
    create_translator(
        translator_app, email='james@memo.com', last_name='Z', gender='M'
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            '--config',
            cfg_path,
            '--select',
            f'/translator_directory/{local}',
            'migrate-hometown',
            '--dry-run',
        ],
    )
    assert 'Total count of items to be migrated: 0' in result.output
    assert result.exit_code == 0
