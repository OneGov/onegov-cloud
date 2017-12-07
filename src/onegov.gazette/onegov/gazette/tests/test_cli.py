import os
import yaml

from click.testing import CliRunner
from onegov.gazette.cli import cli
from xlsxwriter import Workbook


def write_config(path, postgres_dsn, temporary_directory):
    cfg = {
        'applications': [
            {
                'path': '/onegov_gazette/*',
                'application': 'onegov.gazette.GazetteApp',
                'namespace': 'onegov_gazette',
                'configuration': {
                    'dsn': postgres_dsn,
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


def test_add_instance(postgres_dsn, temporary_directory):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory)
    write_principal(temporary_directory, 'Govikon')

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 1
    assert "This selector may not reference an existing path" in result.output


def test_add_instance_missing_config(postgres_dsn, temporary_directory):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory)

    result = run_command(cfg_path, 'govikon1', ['add'])
    assert result.exit_code == 0
    assert "principal.yml not found" in result.output
    assert "Instance was created successfully" in result.output


def test_import_editors(postgres_dsn, temporary_directory):
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory)
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
