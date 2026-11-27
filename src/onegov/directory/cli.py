""" Imports directories scraped by ogi-scraper into onegov directories. """
import json
import os
import re

import click
import transaction

from onegov.core.cli import command_group
from onegov.core.utils import normalize_for_url
from onegov.directory import DirectoryCollection
from onegov.directory.types import DirectoryConfiguration
from onegov.form.parser import ParsedForm

from typing import Any, BinaryIO, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest


cli = command_group()


class _FileUpload:
    """A minimal upload object for a directory file field.

    ``DirectoryCollection.update`` handles a ``fileinput`` field by reading
    ``.file`` (a binary stream) and ``.filename`` off the submitted value and
    building the stored file itself (sniffing the content type from the bytes).
    This stands in for the web form's ``FieldStorage`` so the CLI can attach a
    file straight from disk.
    """

    def __init__(self, file: BinaryIO, filename: str) -> None:
        self.file = file
        self.filename = filename
        # ``update`` inspects ``.data`` on an existing entry's file value to
        # decide whether to replace it; a non-None value means "replace"
        self.data = {'added': True}


def _file_upload(value: object, base_dir: str) -> _FileUpload | str:
    """Turn a record's file-field value into an upload, or '' if there is none.

    The value is a path to the file relative to the export JSON (as the
    scraper writes it, e.g. ``documents/123.pdf`` or ``images/abc.jpg``). A
    missing value, a URL (not a local file) or a path that does not exist
    yields ``''``, which ``update`` treats as "no file".
    """
    if not value or not isinstance(value, str):
        return ''
    if re.match(r'(?i)^https?://', value):
        return ''  # a URL, not a local file
    path = value if os.path.isabs(value) else os.path.join(base_dir, value)
    if not os.path.exists(path):
        click.secho(f'  missing file, skipped: {value}', fg='yellow')
        return ''
    return _FileUpload(open(path, 'rb'), os.path.basename(path))


@cli.command('import-from-ogi-scraper')
@click.argument('file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--recreate', is_flag=True, default=False,
              help='Drop and recreate the directory before importing. Needed '
                   'when the structure changed incompatibly (e.g. a field '
                   'became a file field), which cannot be migrated in place.')
def import_directory_from_ogi_scraper(
    file: str,
    dry_run: bool,
    recreate: bool,
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

        if directory is not None and not recreate:
            # a field changing type (e.g. text -> file) cannot be migrated in
            # place; detect that up front and ask for --recreate rather than
            # letting the structure assignment blow up later at flush time
            migration = directory.migration(
                ParsedForm.from_formcode(spec['structure']), configuration)
            if not migration.possible:
                click.secho(
                    f'The structure of {title!r} changed '
                    f'incompatibly (a field type changed, e.g. to a '
                    f'file field), which cannot be migrated in place. '
                    f'Re-run with --recreate to drop and recreate the '
                    f'directory (its entries are re-imported from this '
                    f'file).', fg='red')
                return

        if directory is not None and recreate:
            click.secho(
                f'Recreating directory {title!r} (dropping '
                f'{len(directory.entries)} existing entry/entries)',
                fg='yellow')
            # delete entries (and unlink files) before the directory itself,
            # otherwise the entries' directory_id is nulled instead of removed
            if hasattr(directory, 'files'):
                directory.files = []
                session.flush()
            for entry in list(directory.entries):
                session.delete(entry)
            directories.delete(directory)
            session.flush()
            directory = None

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

        # file fields carry a path (relative to the export) that is read from
        # disk and attached; basic fields carry plain strings
        file_fields = {f.id: f for f in directory.file_fields}
        field_ids = [f.id for f in directory.basic_fields] + list(file_fields)
        base_dir = os.path.dirname(os.path.abspath(file))
        existing = {entry.name: entry for entry in directory.entries}

        created = 0
        updated = 0
        skipped = 0
        for rec in entries:
            values: dict[str, Any] = {fid: '' for fid in field_ids}
            for fid, key in mapping.items():
                if fid not in values:
                    continue
                if fid in file_fields:
                    # NOTE: only single-file fields are supported; a multiple
                    # file field would need a list value, which update() reads
                    # as pre-stored file dicts (and crashes on an upload)
                    upload = _file_upload(rec.get(key), base_dir)
                    if upload and file_fields[fid].type == 'multiplefileinput':
                        values[fid] = [upload]
                    else:
                        values[fid] = upload
                else:
                    values[fid] = rec.get(key) or ''

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
