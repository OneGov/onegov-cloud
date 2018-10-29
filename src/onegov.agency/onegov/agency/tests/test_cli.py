from click.testing import CliRunner
from onegov.agency.cli import cli
from onegov.core.utils import module_path
from onegov.people.models import Agency
from onegov.people.models import Person
from pytest import mark
from textwrap import dedent
from textwrap import indent
from unittest.mock import patch


@mark.parametrize("file", [
    module_path('onegov.agency', 'tests/fixtures/export-agencies.xls'),
])
def test_import_agencies(cfg_path, session_manager, file):
    runner = CliRunner()

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
            '--select', '/foo/bar',
            'import-agencies', file,
            '--visualize'
        ])
    assert result.exit_code == 0
    assert indent(expected, '  ') in result.output

    # Reimport
    with patch('onegov.agency.cli.get', return_value=DummyResponse()):
        result = runner.invoke(cli, [
            '--config', cfg_path,
            '--select', '/foo/bar',
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
            '--select', '/foo/bar',
            'import-agencies', file,
            '--visualize', '--clear', '--dry-run'
        ])
    assert result.exit_code == 0
    assert "Deleting all agencies" in result.output
    assert "Deleting all people" in result.output
    assert indent(expected, '  ') in result.output
    assert "Aborting transaction" in result.output

    # Check some additional values
    session = session_manager.session()
    agency = session.query(Agency).filter_by(title="Nationalrat").one()
    assert agency.portrait == "NR\n2016/2019"
    assert agency.portrait_html == "<p>NR<br>2016/2019</p>"
    assert agency.state == 'published'
    assert agency.export_fields == [
        'membership.title',
        'person.title',
        'person.academic_title',
        'person.political_party'
    ]
    assert agency.organigram_file.read() == b'image'

    person = session.query(Person).filter_by(last_name="Balmer").one()
    assert person.academic_title == "lic.iur."
    assert person.profession == "Rechtsanwalt"
    assert person.first_name == "Kurt"
    assert person.last_name == "Balmer"
    assert person.political_party == "CVP"
    assert person.year == "1962"
    assert person.email == "test@test.test"
    assert person.address == "Eichmatt 11"
    assert person.phone == "041 111 22 33"
    assert person.direct_phone == "041 111 22 34"
    assert person.website == "https://zg.ch"
    assert person.notes == "Kantonsrat"
    assert person.salutation == "Herr"

    membership = person.memberships.one()
    assert membership.meta['prefix'] == "xx"
    assert membership.since == "2000"
    assert membership.title == "Stimmenzähler"
