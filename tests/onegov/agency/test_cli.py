from click.testing import CliRunner
from onegov.agency.cli import cli
from onegov.org.cli import cli as org_cli
from onegov.org.models import Organisation
from pathlib import Path


def test_create_pdf(temporary_directory, cfg_path):
    runner = CliRunner()

    class DummyResponse(object):
        content = b'image'

        def raise_for_status(self):
            pass

    result = runner.invoke(org_cli, [
        '--config', cfg_path,
        '--select', '/agency/zug',
        'add', 'Kanton Zug'
    ])
    assert result.exit_code == 0

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/agency/zug',
        'create-pdf'
    ])
    assert result.exit_code == 0
    assert "Root PDF created" in result.output

    assert (
        Path(temporary_directory) / 'file-storage' / 'agency-zug' / 'root.pdf'
    ).exists()


def test_enable_yubikey(temporary_directory, cfg_path, session_manager):
    runner = CliRunner()

    result = runner.invoke(org_cli, [
        '--config', cfg_path,
        '--select', '/agency/govikon',
        'add', 'Govikon'
    ])
    assert result.exit_code == 0

    session_manager.set_current_schema('agency-govikon')
    session = session_manager.session()
    assert 'enable_yubikey' not in session.query(Organisation).one().meta

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/agency/govikon',
        'enable-yubikey'
    ])
    assert result.exit_code == 0
    assert "YubiKey enabled" in result.output
    assert session.query(Organisation).one().meta['enable_yubikey'] is True

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/agency/govikon',
        'disable-yubikey'
    ])
    assert result.exit_code == 0
    assert "YubiKey disabled" in result.output
    assert session.query(Organisation).one().meta['enable_yubikey'] is False
