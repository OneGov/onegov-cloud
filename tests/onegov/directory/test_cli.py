from __future__ import annotations

import json

from click.testing import CliRunner
from onegov.directory import DirectoryCollection
from onegov.directory.cli import cli
from pathlib import Path


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager


def _export(title: str = 'Vereine') -> dict[str, Any]:
    # self-describing ogi-scraper export: directory spec + entries
    return {
        'directory': {
            'title': title,
            'structure': 'Name *= ___\nContact = ___',
            'configuration': {
                'title': '[name]',
                'order': ['name'],
                'searchable': ['name', 'contact'],
            },
            'fields': {'name': 'name', 'contact': 'contact'},
        },
        'entries': [
            {'name': 'Turnverein Govikon', 'contact': 'a@example.org'},
            {'name': 'Musikgesellschaft Govikon', 'contact': 'b@example.org'},
        ],
    }


def test_import_from_ogi_scraper(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    path = Path(temporary_directory) / 'vereine.json'
    path.write_text(json.dumps(_export()), encoding='utf-8')

    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')

    # Import: directory is created, entries added
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'Created directory' in result.output
    assert 'Imported 2 new and updated 0' in result.output

    session.expunge_all()
    directory = directories.by_name('vereine')
    assert directory is not None
    assert {e.name for e in directory.entries} == {
        'turnverein-govikon', 'musikgesellschaft-govikon'}

    # Re-run is idempotent: matched by name and updated in place
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'Using existing directory' in result.output
    assert 'Imported 0 new and updated 2' in result.output
    session.expunge_all()
    assert directories.by_name('vereine') is not None
    assert len(directories.by_name('vereine').entries) == 2  # type: ignore[union-attr]


def test_import_dry_run(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    path = Path(temporary_directory) / 'vereine.json'
    path.write_text(json.dumps(_export()), encoding='utf-8')

    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path), '--dry-run'
    ])
    assert result.exit_code == 0
    assert 'Dry run: would create 2 and update 0' in result.output

    session.expunge_all()
    assert directories.by_name('vereine') is None, 'dry-run must not commit'


def test_import_rejects_non_directory_export(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    path = Path(temporary_directory) / 'bad.json'
    # a plain list of records, not a self-describing export
    path.write_text(json.dumps([{'name': 'x'}]), encoding='utf-8')

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'not importable as a directory' in result.output

    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    assert directories.query().count() == 0


def test_import_skips_entry_without_title(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    export = _export()
    # an entry whose title field is empty is skipped
    export['entries'].append({'name': '', 'contact': 'c@example.org'})
    path = Path(temporary_directory) / 'vereine.json'
    path.write_text(json.dumps(export), encoding='utf-8')

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'Imported 2 new and updated 0 entry/entries (1 skipped)' \
        in result.output


def _file_export(
    doc_field: str = 'Document = *.txt',
    field_id: str = 'document',
) -> dict[str, Any]:
    # export whose doc field is a (text, single- or multiple-file) field;
    # the record key 'doc' is mapped onto the formcode field id
    return {
        'directory': {
            'title': 'Firmen',
            'structure': f'Name *= ___\n{doc_field}',
            'configuration': {
                'title': '[name]',
                'order': ['name'],
                'searchable': ['name'],
            },
            'fields': {'name': 'name', field_id: 'doc'},
        },
        'entries': [],
    }


def test_import_rejects_incompatible_structure_without_recreate(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    path = Path(temporary_directory) / 'firmen.json'

    # create a directory whose 'doc' field is a plain text field
    export = _file_export(doc_field='Document = ___')
    export['entries'] = [{'name': 'Acme', 'doc': 'hello'}]
    path.write_text(json.dumps(export), encoding='utf-8')
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'Created directory' in result.output

    # now 'doc' becomes a file field: text -> file cannot migrate in place
    export = _file_export(doc_field='Document = *.txt')
    export['entries'] = [{'name': 'Acme', 'doc': ''}]
    path.write_text(json.dumps(export), encoding='utf-8')
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'changed' in result.output and 'Re-run with --recreate' \
        in result.output

    # the directory structure was left untouched (still a text field)
    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('firmen')
    assert directory is not None
    assert {f.id for f in directory.basic_fields} >= {'name', 'document'}


def test_import_recreate(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    path = Path(temporary_directory) / 'firmen.json'

    # seed a text-field directory with one entry
    export = _file_export(doc_field='Document = ___')
    export['entries'] = [{'name': 'Acme', 'doc': 'hello'}]
    path.write_text(json.dumps(export), encoding='utf-8')
    runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])

    # --recreate drops the directory (and its entry) and re-imports with the
    # incompatible file-field structure
    export = _file_export(doc_field='Document = *.txt')
    export['entries'] = [{'name': 'Beta', 'doc': ''}]
    path.write_text(json.dumps(export), encoding='utf-8')
    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path), '--recreate'
    ])
    assert result.exit_code == 0
    assert 'Recreating directory' in result.output
    assert 'dropping 1 existing' in result.output
    assert 'Imported 1 new' in result.output

    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('firmen')
    assert directory is not None
    # old entry gone, new structure now has a file field
    assert {e.name for e in directory.entries} == {'beta'}
    assert {f.id for f in directory.file_fields} == {'document'}


def test_import_attaches_files(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()
    base = Path(temporary_directory)
    (base / 'documents').mkdir(exist_ok=True)
    (base / 'documents' / 'report.txt').write_text('hi', encoding='utf-8')

    export = _file_export(doc_field='Document = *.txt')
    export['entries'] = [
        # a real file on disk is attached
        {'name': 'Acme', 'doc': 'documents/report.txt'},
        # a missing path is skipped (with a warning), entry still imported
        {'name': 'Beta', 'doc': 'documents/gone.txt'},
        # a URL value is not a local file -> no attachment
        {'name': 'Gamma', 'doc': 'https://example.org/x.txt'},
    ]
    path = base / 'firmen.json'
    path.write_text(json.dumps(export), encoding='utf-8')

    result = runner.invoke(cli, [
        '--config', cfg_path, '--select', '/foo/bar',
        'import-from-ogi-scraper', str(path)
    ])
    assert result.exit_code == 0
    assert 'missing file, skipped: documents/gone.txt' in result.output
    assert 'Imported 3 new' in result.output

    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('firmen')
    assert directory is not None
    acme = next(e for e in directory.entries if e.name == 'acme')
    assert 'report.txt' in str(acme.values.get('document'))
    beta = next(e for e in directory.entries if e.name == 'beta')
    assert not beta.values.get('document')
