import os
import yaml

from click.testing import CliRunner
from datetime import date
from datetime import datetime
from onegov.gazette.cli import cli
from unittest.mock import patch
from xlsxwriter import Workbook


def write_config(path, postgres_dsn, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/onegov_gazette/*',
                'application': 'onegov.gazette.GazetteApp',
                'namespace': 'onegov_gazette',
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


def write_principal(temporary_directory, principal, params=None):
    params = params or {}
    params.update({
        'name': principal,
        'color': '#fff',
        'logo': 'logo.svg'
    })
    path = os.path.join(
        temporary_directory,
        'file-storage/onegov_gazette-{}'.format(principal.lower())
    )
    os.makedirs(path)
    with open(os.path.join(path, 'principal.yml'), 'w') as f:
        f.write(
            yaml.dump(params, default_flow_style=False)
        )


def run_command(cfg_path, principal, commands):
    runner = CliRunner()
    return runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/onegov_gazette/{}'.format(principal),
    ] + commands)


def test_add_instance(postgres_dsn, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 1
    assert "This selector may not reference an existing path" in result.output


def test_add_instance_missing_config(postgres_dsn, temporary_directory,
                                     redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon1', ['add'])
    assert result.exit_code == 0
    assert "principal.yml not found" in result.output
    assert "Instance was created successfully" in result.output


def test_import_editors(temporary_directory, redis_url, session_manager):
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    path = os.path.join(temporary_directory, 'benutzer.xlsx')
    workbook = Workbook(path)
    worksheet = workbook.add_worksheet('Redaktoren')

    worksheet.write('A1', 'Gruppe')
    worksheet.write('B1', 'Name')
    worksheet.write('C1', 'E-Mail')

    worksheet.write('A2', 'abc')
    worksheet.write('B2', 'Lisa Friedmann')
    worksheet.write('C2', 'lisa@friedmann.com')

    worksheet.write('A3', 'abc')
    worksheet.write('B3', 'Martina Wolf')
    worksheet.write('C3', 'martina@wolf.com')

    worksheet.write('A4', 'abc')
    worksheet.write('B4', 'Eric Krueger')
    worksheet.write('C4', 'eric@krueger.com')

    worksheet.write('A5', 'xyz')
    worksheet.write('B5', 'Dominik Gärtner')
    worksheet.write('C5', 'dominik@gertner.com')

    worksheet.write('A6', '')
    worksheet.write('B6', 'Vanessa Trommler')
    worksheet.write('C6', 'vanessa@trommler.com')
    workbook.close()

    result = run_command(
        cfg_path, 'govikon', ['import-editors', path, '--dry-run']
    )
    assert result.exit_code == 0
    assert '3 group(s) imported' in result.output
    assert '5 editor(s) imported'in result.output

    result = run_command(cfg_path, 'govikon', ['import-editors', path])
    assert result.exit_code == 0
    assert '3 group(s) imported' in result.output
    assert '5 editor(s) imported'in result.output

    result = run_command(cfg_path, 'govikon', ['import-editors', path])
    assert result.exit_code != 0

    result = run_command(
        cfg_path, 'govikon', ['import-editors', path, '--clear']
    )
    assert result.exit_code == 0
    assert 'Deleting all editors' in result.output
    assert 'Deleting all groups' in result.output
    assert '3 group(s) imported' in result.output
    assert '5 editor(s) imported'in result.output

    users = session_manager.session().execute("""
        SELECT users.username, users.realname, users.role, groups.name
        FROM "onegov_gazette-govikon".users as users
        LEFT JOIN "onegov_gazette-govikon".groups as groups
          ON users.group_id = groups.id
        ORDER BY users.username ASC
    """).fetchall()
    users = [
        [user.username, user.realname, user.role, user.name]
        for user in users
    ]
    assert users == [
        ['dominik@gertner.com', 'Dominik Gärtner', 'member', 'xyz'],
        ['eric@krueger.com', 'Eric Krueger', 'member', 'abc'],
        ['lisa@friedmann.com', 'Lisa Friedmann', 'member', 'abc'],
        ['martina@wolf.com', 'Martina Wolf', 'member', 'abc'],
        ['vanessa@trommler.com', 'Vanessa Trommler', 'member', None]
    ]


def test_import_issues(temporary_directory, redis_url, session_manager):
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    path = os.path.join(temporary_directory, 'ausgaben.xlsx')
    workbook = Workbook(path, {
        'default_date_format': 'dd.mm.yy hh:mm'
    })
    worksheet = workbook.add_worksheet('Ausgaben')

    worksheet.write('A1', 'Nummer')
    worksheet.write('B1', 'Datum')
    worksheet.write('C1', 'Eingabeschluss')

    worksheet.write('A2', 1)
    worksheet.write('B2', date(2017, 1, 10))
    worksheet.write('C2', datetime(2017, 1, 9, 12, ))

    worksheet.write('A3', 2)
    worksheet.write('B3', date(2017, 7, 17))
    worksheet.write('C3', datetime(2017, 7, 16, 12, ))

    worksheet.write('A4', 3)
    worksheet.write('B4', date(2017, 11, 24))
    worksheet.write('C4', datetime(2017, 11, 23, 12, ))

    workbook.close()

    result = run_command(
        cfg_path, 'govikon', ['import-issues', path, '--dry-run']
    )
    assert result.exit_code == 0
    assert '3 categorie(s) imported' in result.output

    result = run_command(cfg_path, 'govikon', ['import-issues', path])
    assert result.exit_code == 0
    assert '3 categorie(s) imported' in result.output

    # we don't check for duplicates
    result = run_command(cfg_path, 'govikon', ['import-issues', path])
    assert result.exit_code == 0
    assert '3 categorie(s) imported' in result.output

    result = run_command(
        cfg_path, 'govikon', ['import-issues', path, '--clear']
    )
    assert result.exit_code == 0
    assert 'Deleting issues' in result.output
    assert '3 categorie(s) imported' in result.output

    issues = session_manager.session().execute("""
        SELECT *
        FROM "onegov_gazette-govikon".gazette_issues
        ORDER BY date ASC
    """).fetchall()
    issues = [
        [issue.name, issue.number, issue.date, issue.deadline]
        for issue in issues
    ]
    assert issues == [
        ['2017-1', 1, date(2017, 1, 10), datetime(2017, 1, 9, 11, 0)],
        ['2017-2', 2, date(2017, 7, 17), datetime(2017, 7, 16, 10, 0)],
        ['2017-3', 3, date(2017, 11, 24), datetime(2017, 11, 23, 11, 0)]
    ]


def test_import_categories(temporary_directory, redis_url, session_manager):
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    path = os.path.join(temporary_directory, 'rubriken.xlsx')
    workbook = Workbook(path)
    worksheet = workbook.add_worksheet('Rubriken')

    worksheet.write('A1', 'ID')
    worksheet.write('B1', 'Name')
    worksheet.write('C1', 'Titel')
    worksheet.write('D1', 'Aktiv')

    worksheet.write('A2', 1)
    worksheet.write('B2', '10')
    worksheet.write('C2', 'Complaints')
    worksheet.write('D2', 0)

    worksheet.write('A3', 2)
    worksheet.write('B3', '11')
    worksheet.write('C3', 'Education')
    worksheet.write('D3', 1)

    worksheet.write('A4', 3)
    worksheet.write('B4', '12')
    worksheet.write('C4', 'Submissions')
    worksheet.write('D4', 1)

    worksheet.write('A5', 4)
    worksheet.write('B5', '13')
    worksheet.write('C5', 'Commercial Register')
    worksheet.write('D5', 1)

    workbook.close()

    result = run_command(
        cfg_path, 'govikon', ['import-categories', path, '--dry-run']
    )
    assert result.exit_code == 0
    assert '4 categorie(s) imported' in result.output

    result = run_command(cfg_path, 'govikon', ['import-categories', path])
    assert result.exit_code == 0
    assert '4 categorie(s) imported' in result.output

    result = run_command(cfg_path, 'govikon', ['import-categories', path])
    assert result.exit_code == 1

    result = run_command(
        cfg_path, 'govikon', ['import-categories', path, '--clear']
    )
    assert result.exit_code == 0
    assert 'Deleting categories' in result.output
    assert '4 categorie(s) imported' in result.output

    categories = session_manager.session().execute("""
        SELECT *
        FROM "onegov_gazette-govikon".gazette_categories
        ORDER BY id ASC
    """).fetchall()
    categories = [
        [category.id, category.name, category.title, category.active]
        for category in categories
    ]
    assert categories == [
        [1, '10', 'Complaints', False],
        [2, '11', 'Education', True],
        [3, '12', 'Submissions', True],
        [4, '13', 'Commercial Register', True]
    ]


def test_import_organizations(temporary_directory, redis_url, session_manager):
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon')
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    path = os.path.join(temporary_directory, 'organisationen.xlsx')
    workbook = Workbook(path)
    worksheet = workbook.add_worksheet('Organisationen')

    worksheet.write('A1', 'ID')
    worksheet.write('B1', 'Name')
    worksheet.write('C1', 'Titel')
    worksheet.write('D1', 'Aktiv')
    worksheet.write('E1', 'Externe ID')
    worksheet.write('F1', 'Übergeordnete Organisation')

    worksheet.write('A2', 1)
    worksheet.write('B2', '100')
    worksheet.write('C2', 'State Chancellery')
    worksheet.write('D2', 1)
    worksheet.write('E2', '10')
    worksheet.write('F2', '')

    worksheet.write('A3', 2)
    worksheet.write('B3', '200')
    worksheet.write('C3', 'Civic Community')
    worksheet.write('D3', 1)
    worksheet.write('E3', '')
    worksheet.write('F3', '')

    worksheet.write('A4', 3)
    worksheet.write('B4', '300')
    worksheet.write('C4', 'Municipality')
    worksheet.write('D4', 1)
    worksheet.write('E4', '30')
    worksheet.write('F4', '')

    worksheet.write('A5', 4)
    worksheet.write('B5', '400')
    worksheet.write('C5', 'Churches')
    worksheet.write('D5', 1)
    worksheet.write('E5', '40')
    worksheet.write('F5', '')

    worksheet.write('A6', 5)
    worksheet.write('B6', '410')
    worksheet.write('C6', 'Reformed')
    worksheet.write('D6', 1)
    worksheet.write('E6', '40')
    worksheet.write('F6', 4)

    worksheet.write('A7', 6)
    worksheet.write('B7', '420')
    worksheet.write('C7', 'Sikh')
    worksheet.write('D7', 0)
    worksheet.write('E7', '40')
    worksheet.write('F7', 4)

    workbook.close()

    result = run_command(
        cfg_path, 'govikon', ['import-organizations', path, '--dry-run']
    )
    assert result.exit_code == 0
    assert '6 organization(s) imported' in result.output

    result = run_command(cfg_path, 'govikon', ['import-organizations', path])
    assert result.exit_code == 0
    assert '6 organization(s) imported' in result.output

    result = run_command(cfg_path, 'govikon', ['import-organizations', path])
    assert result.exit_code == 1

    result = run_command(
        cfg_path, 'govikon', ['import-organizations', path, '--clear']
    )
    assert result.exit_code == 0
    assert 'Deleting organizations' in result.output
    assert '6 organization(s) imported' in result.output

    organizations = session_manager.session().execute("""
        SELECT *
        FROM "onegov_gazette-govikon".gazette_organizations
        ORDER BY id ASC
    """).fetchall()
    organizations = [
        [org.id, org.name, org.title, org.active, org.meta, org.parent_id]
        for org in organizations
    ]
    assert organizations == [
        [1, '100', 'State Chancellery', True, {'external_name': '10'}, None],
        [2, '200', 'Civic Community', True, {'external_name': ''}, None],
        [3, '300', 'Municipality', True, {'external_name': '30'}, None],
        [4, '400', 'Churches', True, {'external_name': '40'}, None],
        [5, '410', 'Reformed', True, {'external_name': '40'}, 4],
        [6, '420', 'Sikh', False, {'external_name': '40'}, 4]
    ]


def test_import_sogc(temporary_directory, redis_url, session_manager):
    params = {
        'canton': 'tg',
        'sogc_import': {
            'endpoint': 'https://localhost',
            'username': 'user',
            'password': 'pass',
            'category': 190,
            'organization': 200,
        }
    }
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)
    write_principal(temporary_directory, 'Govikon', params)
    assert run_command(cfg_path, 'govikon', ['add']).exit_code == 0

    with patch('onegov.gazette.cli.SogcImporter') as importer:
        importer.return_value = lambda: 0
        result = run_command(cfg_path, 'govikon', ['import-sogc', '--dry-run'])
        assert result.exit_code == 0
        assert '0 notice(s) imported' in result.output
        assert 'Aborting transaction' in result.output

    with patch('onegov.gazette.cli.SogcImporter') as importer:
        importer.return_value = lambda: 10
        result = run_command(cfg_path, 'govikon', ['import-sogc'])
        assert result.exit_code == 0
        assert '10 notice(s) imported' in result.output
        assert 'Aborting transaction' not in result.output
