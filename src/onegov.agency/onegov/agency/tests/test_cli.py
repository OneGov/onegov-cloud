from click.testing import CliRunner
from onegov.agency.cli import cli
from onegov.core.utils import module_path
from onegov.org.cli import cli as org_cli
from onegov.org.models import Organisation
from onegov.people.models import Agency
from onegov.people.models import Person
from pathlib import Path
from pytest import mark
from textwrap import dedent
from textwrap import indent
from unittest.mock import patch


@mark.parametrize("file", [
    module_path('onegov.agency', 'tests/fixtures/export.xls'),
])
def test_import_agencies(cfg_path, session_manager, file):
    runner = CliRunner()

    result = runner.invoke(org_cli, [
        '--config', cfg_path,
        '--select', '/agency/zug',
        'add', 'Kanton Zug'
    ])
    assert result.exit_code == 0

    expected = dedent("""
        Bundesbehörden
          Nationalrat
          * Mitglied von Zug: Aeschi Thomas
          * Mitglied von Zug: Pezzatti Bruno
          * Mitglied von Zug: Pfister Gerhard
          Ständerat
          * Mitglied von Zug: Eder Joachim
          * Mitglied von Zug: Hegglin Peter
          Bundesrat
          * Bundespräsidentin: Leuthard Doris
          * Vizepräsident: Berset Alain
          * Bundesrat: Burkhalter Didier
          * Bundesrat: Maurer Ueli
          * Bundesrat: Schneider-Ammann Johann
          * Bundesrätin: Sommaruga Simonetta
          * Bundesrat: Parmelin Guy
        Kantonale Behörden
          Kantonsrat
          * Präsident 2017/18: Burch Daniel Thomas
          * Vizepräsidentin 2017/18: Barmet Monika
          * Stimmenzählerin: Hofer Rita
          * Stimmenzähler: Balmer Kurt
          * stv. Stimmenzähler: Rüegg Richard
          * stv. Stimmenzählerin: Schriber-Neiger Hanni
          * Landschreiber: Moser Tobias
          * Stv. Landschreiberin: Spillmann Siegwart Renée
          * Protokoll: Dittli Beat
            Gemeinde Zug (19)
            * Kantonsrat: Brandenberg Manuel
            * Kantonsrat: Brunner Philip C.
            * Kantonsrat: Camenisch Philippe
            * Kantonsrat: Christen Hans
            * Kantonsrätin: Feldmann Magda
            * Kantonsrätin: Giger Susanne
            * Kantonsrätin: Gysel Barbara
            * Kantonsrätin: Landtwing Alice
            * Kantonsrat: Marti Daniel
            * Kantonsrat: Messmer Jürg
            * Kantonsrat: Raschle Urs
            * Kantonsrat: Rüegg Richard
            * Kantonsrat: Sivaganesan Rupan
            * Kantonsrat: Stadlin Daniel
            * Kantonsrätin: Stocker Cornelia
            * Kantonsrätin: Straub-Müller Vroni
            * Kantonsrätin: Thalmann Silvia
            * Kantonsrätin: Umbach Karen
            * Kantonsrat: Vollenweider Willi
            Bildungskommission
            * Präsident: Thalmann Silvia
            * Mitglied: Bieri Anna
            * Mitglied: Dzaferi Zari
            * Mitglied: Haas Esther
            * Mitglied: Häseli Barbara
            * Mitglied: Hofer Rita
            * Mitglied: Kryenbühl René
            * Mitglied: Letter Peter
            * Mitglied: Meierhans Thomas
            * Mitglied: Messmer Jürg
            * Mitglied: Riedi Beni
            * Mitglied: Sieber Beat
            * Mitglied: Umbach Karen
            * Mitglied: Unternährer Beat
            * Mitglied: Weber Monika
    """).strip()

    class DummyResponse(object):
        content = b'image'

        def raise_for_status(self):
            pass

    # Import
    with patch('onegov.agency.cli.get', return_value=DummyResponse()):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/agency/zug',
            'import-agencies', file,
            '--visualize'
        ])
    assert result.exit_code == 0
    assert indent(expected, '  ') in result.output

    # Reimport
    with patch('onegov.agency.cli.get', return_value=DummyResponse()):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/agency/zug',
            'import-agencies', file,
            '--visualize', '--clear'
        ])
    assert result.exit_code == 0
    assert "Deleting all agencies" in result.output
    assert "Deleting all people" in result.output
    assert indent(expected, '  ') in result.output

    # Reimport (dry)
    with patch('onegov.agency.cli.get', return_value=DummyResponse()):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/agency/zug',
            'import-agencies', file,
            '--visualize', '--clear', '--dry-run'
        ])
    assert result.exit_code == 0
    assert "Deleting all agencies" in result.output
    assert "Deleting all people" in result.output
    assert indent(expected, '  ') in result.output
    assert "Aborting transaction" in result.output

    # Check some additional values
    session_manager.set_current_schema('agency-zug')
    session = session_manager.session()
    agency = session.query(Agency).filter_by(title="Nationalrat").one()
    assert agency.portrait == "NR\n2016/2019"
    assert agency.portrait_html == "<p>NR<br>2016/2019</p>"
    assert agency.export_fields == [
        'membership.title',
        'person.title',
        'person.academic_title',
        'person.political_party'
    ]
    assert agency.organigram_file.read() == b'image'
    assert agency.is_hidden_from_public is True

    person = session.query(Person).filter_by(last_name="Balmer").one()
    assert person.academic_title == "lic.iur."
    assert person.profession == "Rechtsanwalt"
    assert person.first_name == "Kurt"
    assert person.last_name == "Balmer"
    assert person.political_party == "CVP"
    assert person.born == "1962"
    assert person.email == "test@test.test"
    assert person.address == "Eichmatt 11"
    assert person.phone == "041 111 22 33"
    assert person.phone_direct == "041 111 22 34"
    assert person.website == "https://zg.ch"
    assert person.notes == "Kantonsrat"
    assert person.salutation == "Herr"
    assert person.is_hidden_from_public is True

    membership = person.memberships.one()
    assert membership.title == "Stimmenzähler"
    assert membership.since == "2000"
    assert membership.addition == "yy"
    assert membership.note == "zz"
    assert membership.prefix == "xx"
    assert membership.is_hidden_from_public is None


@mark.parametrize("file", [
    module_path('onegov.agency', 'tests/fixtures/export-pdf.xls'),
])
def test_create_pdf(temporary_directory, cfg_path, file):
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

    with patch('onegov.agency.cli.get', return_value=DummyResponse()):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/agency/zug',
            'import-agencies', file
        ])
    assert result.exit_code == 0

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/agency/zug',
        'create-pdf'
    ])
    assert result.exit_code == 0
    assert "Root PDF created" in result.output
    assert "Created PDF of 'Bundesbehörden'" in result.output
    assert "Created PDF of 'Nationalrat'" in result.output
    assert "Created PDF of 'Ständerat'" in result.output

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
