from __future__ import annotations

import json
import os
import yaml

from click.testing import CliRunner
from onegov.directory import DirectoryCollection
from onegov.directory.cli import cli
from onegov.org.cli import cli as org_cli
from tests.shared.utils import create_image


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager


def write_cfg(
    postgres_dsn: str,
    temporary_directory: str,
    redis_url: str
) -> str:
    cfg = {
        'applications': [
            {
                'path': '/onegov_org/*',
                'application': 'onegov.org.OrgApp',
                'namespace': 'onegov_org',
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
                    'redis_url': redis_url,
                    'websockets': {
                        'client_url': 'ws://localhost:8766',
                        'manage_url': 'ws://localhost:8766',
                        'manage_token': 'super-super-secret-token'
                    }
                }
            }
        ]
    }
    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(yaml.dump(cfg))
    return cfg_path


def create_instance(cfg_path: str) -> None:
    result = CliRunner().invoke(org_cli, [
        '--config', cfg_path, '--select', '/onegov_org/govikon',
        'add', 'Govikon'
    ], catch_exceptions=False)
    assert result.exit_code == 0


def write_export(
    directory: str,
    spec_overrides: dict[str, Any] | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> str:
    spec: dict[str, Any] = {
        'title': 'Vereine',
        'structure': 'Name *= ___\nDescription = ___\nLogo = *.png',
        'configuration': {
            'title': '[Name]', 'order': ['Name'], 'searchable': ['Name'],
        },
        'fields': {'name': 'name', 'description': 'desc', 'logo': 'logo'},
    }
    spec.update(spec_overrides or {})
    payload = {
        'directory': spec,
        'entries': entries if entries is not None else [
            {'name': 'Verein A', 'desc': 'First', 'logo': 'a.png'},
            {'name': 'Verein B', 'desc': 'Second'},
        ],
    }
    path = os.path.join(directory, 'export.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    with open(os.path.join(directory, 'a.png'), 'wb') as f:
        f.write(create_image().read())
    return path


def run_import(cfg_path: str, file: str, *extra: str) -> Any:
    return CliRunner().invoke(cli, [
        '--config', cfg_path, '--select', '/onegov_org/govikon',
        'import-from-ogi-scraper', file, *extra
    ], catch_exceptions=False)


def test_import_from_ogi_scraper(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:
    cfg_path = write_cfg(postgres_dsn, temporary_directory, redis_url)
    create_instance(cfg_path)
    file = write_export(temporary_directory)

    result = run_import(cfg_path, file)
    assert result.exit_code == 0
    assert "Created directory 'Vereine'" in result.output
    assert 'Imported 2 new and updated 0' in result.output

    session_manager.set_current_schema('onegov_org-govikon')
    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('vereine')
    assert directory is not None
    entries = {e.name: e for e in directory.entries}
    assert set(entries) == {'verein-a', 'verein-b'}

    # the image was imported for the entry that had one
    a = entries['verein-a']
    assert a.values['logo']['data'].startswith('@')
    assert len(a.files) == 1
    assert not entries['verein-b'].files


def test_import_is_idempotent(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:
    cfg_path = write_cfg(postgres_dsn, temporary_directory, redis_url)
    create_instance(cfg_path)
    file = write_export(temporary_directory)

    run_import(cfg_path, file)
    # second run matches by name and updates in place
    result = run_import(cfg_path, file)
    assert result.exit_code == 0
    assert "Using existing directory 'Vereine'" in result.output
    assert 'Imported 0 new and updated 2' in result.output

    session_manager.set_current_schema('onegov_org-govikon')
    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('vereine')
    assert directory is not None
    assert len(directory.entries) == 2


def test_import_dry_run(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:
    cfg_path = write_cfg(postgres_dsn, temporary_directory, redis_url)
    create_instance(cfg_path)
    file = write_export(temporary_directory)

    result = run_import(cfg_path, file, '--dry-run')
    assert result.exit_code == 0
    assert 'Dry run: would create 2 and update 0' in result.output

    session_manager.set_current_schema('onegov_org-govikon')
    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    assert directories.by_name('vereine') is None


def test_import_rejects_non_directory_payload(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:
    cfg_path = write_cfg(postgres_dsn, temporary_directory, redis_url)
    create_instance(cfg_path)

    file = os.path.join(temporary_directory, 'bad.json')
    with open(file, 'w', encoding='utf-8') as f:
        json.dump({'entries': []}, f)

    result = run_import(cfg_path, file)
    assert result.exit_code == 0
    assert 'not importable as a directory' in result.output


def test_import_warns_on_missing_image(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:
    cfg_path = write_cfg(postgres_dsn, temporary_directory, redis_url)
    create_instance(cfg_path)
    file = write_export(temporary_directory, entries=[
        {'name': 'Verein A', 'desc': 'First', 'logo': 'ghost.png'},
    ])

    result = run_import(cfg_path, file)
    assert result.exit_code == 0
    assert 'missing image ghost.png' in result.output
    assert 'Imported 1 new and updated 0' in result.output

    session_manager.set_current_schema('onegov_org-govikon')
    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('vereine')
    assert directory is not None
    assert not directory.entries[0].files


def test_import_skips_entries_without_title(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> None:
    cfg_path = write_cfg(postgres_dsn, temporary_directory, redis_url)
    create_instance(cfg_path)
    file = write_export(temporary_directory, entries=[
        {'name': 'Verein A', 'desc': 'First', 'logo': 'a.png'},
        {'name': '', 'desc': 'No name'},
    ])

    result = run_import(cfg_path, file)
    assert result.exit_code == 0
    assert 'Imported 1 new and updated 0 entry/entries (1 skipped)' \
        in result.output

    session_manager.set_current_schema('onegov_org-govikon')
    session = session_manager.session()
    directories: DirectoryCollection[Any] = DirectoryCollection(
        session, type='extended')
    directory = directories.by_name('vereine')
    assert directory is not None
    assert len(directory.entries) == 1
