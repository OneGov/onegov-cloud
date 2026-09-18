""" Imports directories scraped by ogi-scraper into onegov directories. """
from __future__ import annotations

import json
import os

import click
import transaction

from onegov.core.cli import command_group
from onegov.core.utils import Bunch, normalize_for_url
from onegov.directory import DirectoryCollection
from onegov.directory.types import DirectoryConfiguration

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest


cli = command_group()


@cli.command('import-from-ogi-scraper')
@click.argument('file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, default=False)
def import_directory_from_ogi_scraper(
    file: str,
    dry_run: bool,
) -> Callable[[CoreRequest, Framework], None]:
    r""" Imports a directory from a self-describing ogi-scraper JSON export.

    The file carries both the directory spec and its entries::

        {
          "directory": {
            "title": "Vereine",
            "structure": "Name *= ___\\n...",       # onegov formcode
            "configuration": { ... },                # DirectoryConfiguration
            "fields": { "<field_id>": "<record_key>", ... }
          },
          "entries": [ { ...record... }, ... ]
        }

    The scraper is the source that knows the target shape, so this command
    needs no per-directory knowledge. The directory is created if missing and
    entries are matched by name and updated in place, so the import is
    idempotent.

    Example:

        onegov-directory --select /onegov_town6/malters \\
            import-from-ogi-scraper vereinsliste.json

    """

    def _import(request: CoreRequest, app: Framework) -> None:
        with open(file, encoding='utf-8') as f:
            payload = json.load(f)

        if not isinstance(payload, dict) or 'directory' not in payload:
            click.secho(
                'Expected a self-describing export with a "directory" spec '
                'and "entries" (this file is not importable as a directory).',
                fg='red')
            return

        spec = payload['directory']
        entries = payload.get('entries', [])
        title = spec['title']
        mapping = spec.get('fields', {})

        session = app.session()
        directories: DirectoryCollection[Any] = DirectoryCollection(
            session, type='extended')

        configuration = DirectoryConfiguration(**spec.get('configuration', {}))
        directory = directories.by_name(normalize_for_url(title))
        if directory is None:
            directory = directories.add(
                title=title,
                structure=spec['structure'],
                configuration=configuration,
            )
            click.secho(f'Created directory {title!r}', fg='green')
        else:
            # keep structure and configuration in sync with the spec
            directory.structure = spec['structure']
            directory.configuration = configuration
            click.secho(f'Using existing directory {title!r}', fg='yellow')

        field_ids = [f.id for f in directory.basic_fields]
        file_field_ids = [f.id for f in directory.file_fields]
        existing = {entry.name: entry for entry in directory.entries}
        # image paths in the export are relative to the json file's directory
        base_dir = os.path.dirname(os.path.abspath(file))

        def file_value(rec: dict[str, Any], fid: str) -> Any:
            """A Bunch(file, filename) for an image field, or {} if none."""
            rel = rec.get(mapping.get(fid, ''), '')
            if not rel:
                return {}
            path = os.path.join(base_dir, rel)
            if not os.path.exists(path):
                click.secho(f'  missing image {rel}', fg='red')
                return {}
            return Bunch(data=object(), file=open(path, 'rb'),  # noqa: SIM115
                         filename=os.path.basename(path))

        created = 0
        updated = 0
        skipped = 0
        for rec in entries:
            values: dict[str, Any] = {fid: '' for fid in field_ids}
            for fid, key in mapping.items():
                if fid in values:
                    values[fid] = rec.get(key) or ''
            for fid in file_field_ids:
                values[fid] = file_value(rec, fid)

            entry_title = directory.configuration.extract_title(values)
            if not entry_title:
                skipped += 1
                continue

            entry = existing.get(normalize_for_url(entry_title))
            if entry is None:
                directory.add(values)
                created += 1
            else:
                directory.update(entry, values)
                updated += 1

        if dry_run:
            transaction.abort()
            click.secho(
                f'Dry run: would create {created} and update {updated} '
                f'entry/entries ({skipped} skipped)', fg='yellow')
        else:
            click.secho(
                f'Imported {created} new and updated {updated} entry/entries '
                f'({skipped} skipped)', fg='green')

    return _import
