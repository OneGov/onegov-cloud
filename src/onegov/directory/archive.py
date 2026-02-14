from __future__ import annotations

import mimetypes
import shutil
import os

from collections import OrderedDict
from enum import Enum
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.csv import convert_excel_to_csv
from onegov.core.csv import CSVFile
from onegov.core.custom import json
from onegov.core.utils import Bunch, is_subpath
from onegov.directory.errors import MissingColumnError, MissingFileError
from onegov.directory.models import Directory, DirectoryEntry
from onegov.directory.types import DirectoryConfiguration
from onegov.file import File
from onegov.form import as_internal_id
from pathlib import Path
from sqlalchemy.orm import object_session
from tempfile import TemporaryDirectory, NamedTemporaryFile


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath, SupportsItems, SupportsRead
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from onegov.core.types import JSON_ro
    from onegov.form.parser.core import FileinputField
    from onegov.form.parser.core import MultipleFileinputField
    from onegov.form.parser.core import ParsedField
    from sqlalchemy.orm import Query, Session
    from typing import Protocol, Self, TypeAlias

    UnknownFieldType: TypeAlias = 'Literal[_Sentinel.UNKNOWN_FIELD]'
    DirectoryEntryFilter: TypeAlias = Callable[
        [Iterable[DirectoryEntry]],
        Iterable[DirectoryEntry]
    ]
    FieldValueTransform: TypeAlias = Callable[
        [str, Any],
        tuple[str, Any | None]
    ]

    class SupportsReadAndSeek(SupportsRead[bytes], Protocol):
        def seek(self, offset: int, /) -> object: ...


class _Sentinel(Enum):
    UNKNOWN_FIELD = object()


UNKNOWN_FIELD = _Sentinel.UNKNOWN_FIELD


class DirectoryFileNotFound(FileNotFoundError):
    def __init__(self, file_id: str, entry_name: str, filename: str) -> None:
        self.file_id = file_id
        self.entry_name = entry_name
        self.filename = filename


class FieldParser:
    """ Parses records read by the directory archive reader. """

    def __init__(self, directory: Directory, archive_path: Path) -> None:
        self.fields_by_human_id = {f.human_id: f for f in directory.fields}
        self.fields_by_id = {f.id: f for f in directory.fields}
        self.archive_path = archive_path

    def get_field(self, key: str) -> ParsedField | None:
        """
        CSV Files header parsing is inconsistent with the the internal id (
        field.id) of the field. The headers are lovercased, so that the first
        will not yield the field, the second will also not success because
        characters like ( are not replaced by underscores.
        """
        return (
            self.fields_by_human_id.get(key)
            or self.fields_by_id.get(key)
            or self.fields_by_id.get(as_internal_id(key))
        )

    def parse_fileinput(
        self,
        key: str,
        value: str,
        field: FileinputField
    ) -> Bunch | None:  # FIXME: Use NamedTuple

        if not value:
            return None

        # be extra paranoid about these path values -> they could
        # potentially be used to access files on the local system
        assert '..' not in value
        assert value.count('/') == 1, f'{value} not allowed'
        assert not value.startswith('/')

        path = self.archive_path / value
        assert is_subpath(str(self.archive_path), str(path))

        if not path.exists():
            raise MissingFileError(value)

        return Bunch(
            data=object(),
            file=path.open('rb'),
            filename=value.split('/')[-1]
        )

    def parse_multiplefileinput(
        self,
        key: str,
        value: str,
        field: MultipleFileinputField
    ) -> tuple[Bunch, ...]:  # FIXME: Use NamedTuple

        if not value:
            return ()

        def iter_files() -> Iterator[Bunch]:
            for val in value.split(os.pathsep):
                # be extra paranoid about these path values -> they could
                # potentially be used to access files on the local system
                assert '..' not in val
                assert val.count('/') == 1, f'{val} not allowed'
                assert not val.startswith('/')

                path = self.archive_path / val
                assert is_subpath(str(self.archive_path), str(path))

                if not path.exists():
                    raise MissingFileError(val)

                yield Bunch(
                    data=object(),
                    file=path.open('rb'),
                    filename=val.split('/')[-1]
                )

        return tuple(iter_files())

    def parse_generic(
        self,
        key: str,
        value: str,
        field: ParsedField
    ) -> object:
        return field.parse(value)

    def parse_item(
        self,
        key: str,
        value: str
    ) -> tuple[str, Any | None] | UnknownFieldType:

        field = self.get_field(key)

        if not field:
            return UNKNOWN_FIELD

        parser = getattr(self, 'parse_' + field.type, self.parse_generic)

        try:
            result = parser(key, value, field)
        except ValueError:
            result = None

        return as_internal_id(key), result

    def parse(
        self,
        record: SupportsItems[str, str]
    ) -> dict[str, Any | None]:

        return dict(
            parsed
            for k, v in record.items()
            if (parsed := self.parse_item(k, v)) is not UNKNOWN_FIELD
        )


class DirectoryArchiveReader:
    """ Reading part of :class:`DirectoryArchive`. """

    path: Path

    def read(
        self,
        target: Directory | None = None,
        skip_existing: bool = True,
        limit: int = 0,
        apply_metadata: bool = True,
        after_import: Callable[[DirectoryEntry], Any] | None = None
    ) -> Directory:
        """ Reads the archive resulting in a dictionary and entries.

        :param target:
            Uses the given directory as a target for the read. Otherwise,
            a new directory is created in memory (default).

        :param skip_existing:
            Excludes already existing entries from being added to the
            directory. Only applies if target is not None.

        :param limit:
            Limits the number of records which are imported. If the limit
            is reached, the read process silently ignores all extra items.

        :param apply_metadata:
            True if the metadata found in the archive should be applied
            to the directory.

        :param after_import:
            Called with the newly added entry, right after it has been added.

        """
        meta_data = self.read_metadata()
        directory = target or Directory.get_polymorphic_class(
            meta_data.get('type', 'generic'),
            Directory
        )()

        if apply_metadata:
            directory = self.apply_metadata(directory, meta_data)

        if skip_existing and target:
            session = object_session(target)
            assert session is not None
            existing = {
                entry_name
                for entry_name, in session.query(DirectoryEntry)
                .filter_by(directory_id=target.id)
                .with_entities(DirectoryEntry.name)
            }
        else:
            existing = set()

        parser = FieldParser(directory, self.path)
        amount = 0

        for record in self.read_data():

            if limit and amount >= limit:
                break

            values = parser.parse(record)

            if skip_existing:
                name = directory.configuration.extract_name(values)

                if name in existing:
                    continue

                existing.add(name)
            try:
                entry = directory.add(values)
            except KeyError as exception:
                raise MissingColumnError(
                    column=exception.args[0]
                ) from exception

            names = (
                ('latitude', 'longitude'),
                ('Latitude', 'Longitude')
            )
            for lat, lon in names:
                if record.get(lat) and record.get(lon):
                    entry.content['coordinates'] = {
                        'lon': record[lon],
                        'lat': record[lat],
                        'zoom': None
                    }

            amount += 1

            if after_import is not None:
                after_import(entry)

        return directory

    def apply_metadata(
        self,
        directory: Directory,
        metadata: dict[str, Any]  # FIXME: Use a TypedDict?
    ) -> Directory:
        """ Applies the metadata to the given directory and returns it. """

        directory.name = directory.name or metadata['name']

        directory.title = metadata['title']
        directory.lead = metadata['lead']
        directory.structure = metadata['structure']
        directory.configuration = DirectoryConfiguration(
            **metadata['configuration']
        )

        if 'meta' in metadata:
            directory.meta = metadata['meta']

        if 'content' in metadata:
            directory.content = metadata['content']

        return directory

    def read_metadata(self) -> dict[str, Any]:
        """ Returns the metadata as a dictionary. """

        try:
            with (self.path / 'metadata.json').open('r') as f:
                return json.loads(f.read())
        except FileNotFoundError as exception:
            raise MissingFileError('metadata.json') from exception

    def read_data(self) -> Sequence[dict[str, Any]]:
        """ Returns the entries as a sequence of dictionaries. """

        if (self.path / 'data.json').exists():
            return self.read_data_from_json()

        if (self.path / 'data.csv').exists():
            return self.read_data_from_csv()

        if (self.path / 'data.xlsx').exists():
            return self.read_data_from_xlsx()

        raise NotImplementedError

    def read_data_from_json(self) -> list[dict[str, Any]]:
        with (self.path / 'data.json').open('r') as f:
            return json.loads(f.read())

    def read_data_from_csv(self) -> tuple[dict[str, Any], ...]:
        with (self.path / 'data.csv').open('rb') as f:
            rows = tuple(CSVFile(f, rowtype=dict).lines)
            return tuple(row for row in rows if any(row.values()))

    def read_data_from_xlsx(self) -> tuple[dict[str, Any], ...]:
        with (self.path / 'data.xlsx').open('rb') as f:
            return tuple(CSVFile(
                convert_excel_to_csv(f), rowtype=dict, dialect='excel'
            ).lines)


class DirectoryArchiveWriter:
    """ Writing part of :class:`DirectoryArchive`. """

    path: Path
    format: Literal['json', 'csv', 'xlsx']
    transform: FieldValueTransform

    def write(
        self,
        directory: Directory,
        *args: Any,
        entry_filter: DirectoryEntryFilter | None = None,
        query: Query[DirectoryEntry] | None = None,
        **kwargs: Any
    ) -> None:
        """ Writes the given directory. """
        assert self.format in ('xlsx', 'csv', 'json')

        self.write_directory_metadata(directory)
        self.write_directory_entries(directory, entry_filter, query)

    def write_directory_metadata(self, directory: Directory) -> None:
        """ Writes the metadata. """

        metadata: JSON_ro = {
            'configuration': directory.configuration.to_dict(),
            'structure': directory.structure.replace('\r\n', '\n'),
            'title': directory.title,
            'lead': directory.lead,
            'name': directory.name,
            'type': directory.type,
            'meta': directory.meta,
            'content': directory.content,
        }
        self.write_json(self.path / 'metadata.json', metadata)

    def write_directory_entries(
        self,
        directory: Directory,
        entry_filter: DirectoryEntryFilter | None = None,
        query: Query[DirectoryEntry] | None = None
    ) -> None:
        """ Writes the directory entries. Allows filtering with custom
        entry_filter function as well as passing a query object """

        fields = directory.fields
        paths: dict[str, str] = {}
        fid_to_entry = {}

        def file_path(
            entry: DirectoryEntry,
            field: ParsedField,
            value: dict[str, Any],
            suffix: str = ''
        ) -> str:

            return '{folder}/{name}{suffix}{ext}'.format(
                folder=field.id,
                name=entry.name,
                suffix=suffix,
                ext=mimetypes.guess_extension(value['mimetype']) or '')

        def as_tuples(
            entry: DirectoryEntry
        ) -> Iterator[tuple[str, Any | None]]:

            for field in fields:
                value = entry.values.get(field.id)

                if field.type == 'fileinput':
                    if value:
                        file_id = value['data'].lstrip('@')
                        value = paths[file_id] = file_path(entry, field, value)
                        fid_to_entry[file_id] = entry.name
                    else:
                        value = None
                elif field.type == 'multiplefileinput':
                    if value:
                        for idx, val in enumerate(value):
                            file_id = val['data'].lstrip('@')
                            value[idx] = paths[file_id] = file_path(
                                entry,
                                field,
                                val,
                                f'_{idx + 1}'
                            )
                            fid_to_entry[file_id] = entry.name
                        # turn it into a scalar value
                        value = os.pathsep.join(value)
                    else:
                        value = None

                yield self.transform(field.human_id, value)

        def as_dict(entry: DirectoryEntry) -> dict[str, Any | None]:
            data = OrderedDict(as_tuples(entry))

            coordinates = entry.content.get('coordinates', {})

            if isinstance(coordinates, dict):
                data['Latitude'] = coordinates.get('lat')
                data['Longitude'] = coordinates.get('lon')
            else:
                data['Latitude'] = coordinates.lat
                data['Longitude'] = coordinates.lon

            return data

        entries: Iterable[DirectoryEntry]
        entries = query.all() if query else directory.entries
        if entry_filter:
            entries = entry_filter(entries)

        data = tuple(as_dict(e) for e in entries)

        write = getattr(self, f'write_{self.format}')
        write(self.path / f'data.{self.format}', data)

        session = object_session(directory)
        assert session is not None
        self.write_paths(session, paths, fid_to_entry)

    def write_paths(
        self,
        session: Session,
        paths: dict[str, str],
        fid_to_entry: dict[str, str] | None = None
    ) -> None:
        """ Writes the given files to the archive path.

        :param session:
            The database session in use.

        :param paths:
            A dictionary with each key being a file id and each value
            being a path where this file id should be written to.
        :param fid_to_entry:
            A dictionary with the mapping of the file id to the entry name
        """

        files: Iterable[File]
        if paths:
            files = session.query(File).filter(File.id.in_(paths))
        else:
            files = ()

        # keep the temp files around so they don't get GC'd prematurely
        tempfiles = []

        try:
            for f in files:
                relfolder, name = paths[f.id].split('/', 1)
                folder = self.path / relfolder

                if not folder.exists():
                    folder.mkdir()

                # support both local files and others (memory/remote)
                try:
                    if hasattr(f.reference.file, '_file_path'):
                        src = os.path.abspath(f.reference.file._file_path)
                    else:
                        tmp = NamedTemporaryFile()  # noqa: SIM115
                        tmp.write(f.reference.file.read())
                        tempfiles.append(tmp)
                        src = tmp.name

                except OSError as exception:
                    if fid_to_entry is None:
                        entry_name = 'unknown'
                    else:
                        entry_name = fid_to_entry[f.id]
                    raise DirectoryFileNotFound(
                        file_id=f.id,
                        entry_name=entry_name,
                        filename=name
                    ) from exception

                dst = str(folder / name)

                try:
                    os.link(src, dst)  # prefer links if possible (faster)
                except OSError:
                    shutil.copyfile(src, dst)
        finally:
            for tempfile in tempfiles:
                tempfile.close()

    def write_json(self, path: Path, data: JSON_ro) -> None:
        with open(str(path), 'wb') as f:
            json.dump_bytes(data, f, sort_keys=True, indent=2)

    def write_xlsx(self, path: Path, data: Iterable[dict[str, Any]]) -> None:
        with open(str(path), 'wb') as f:
            f.write(convert_list_of_dicts_to_xlsx(data))

    def write_csv(self, path: Path, data: Iterable[dict[str, Any]]) -> None:
        with open(str(path), 'w') as f:
            f.write(convert_list_of_dicts_to_csv(data))


class DirectoryArchive(DirectoryArchiveReader, DirectoryArchiveWriter):
    """ Offers the ability to read/write a directory and its entries to a
    folder.

    Usage::

        archive = DirectoryArchive('/tmp/directory')
        archive.write()

        archive = DirectoryArchive('/tmp/directory')
        archive.read()

    The archive content is as follows:

    - metadata.json (contains the directory data)
    - data.json/data.csv/data.xlsx (contains the directory entries)
    - ./<field_id>/<entry_id>.<ext> (files referenced by the directory entries)

    The directory entries are stored as json, csv or xlsx. Json is preferred.

    """

    def __init__(
        self,
        path: StrPath,
        format: Literal['json', 'csv', 'xlsx'] = 'json',
        transform: FieldValueTransform | None = None
    ):
        """ Initialise the archive at the given path (must exist).

        :param path:
            The target path of this archive.

        :param format:
            The format of the entries (json, csv or xlsx)

        :param transform:
            A transform function called with key and value for each entry
            that is about to be written when creating an archive. Use this
            to format values (for example datetime to string for json).

            Note that transformed fields are read by onegov.form. So if the
            transformed values cannot be parsed again by onegov.form, you
            cannot import the resulting archive.

        """

        self.path = Path(path)
        self.format = format
        self.transform = transform or (lambda key, value: (key, value))


class DirectoryZipArchive:
    """ Offers the same interface as the DirectoryArchive, additionally
    zipping the folder on write and extracting the zip on read.

    """

    format: Literal['zip'] = 'zip'

    def __init__(
        self,
        path: StrPath,
        *args: Any,
        **kwargs: Any
    ):
        self.path = path
        self.temp = TemporaryDirectory()
        self.archive = DirectoryArchive(self.temp.name, *args, **kwargs)

    @classmethod
    def from_buffer(cls, buffer: SupportsReadAndSeek) -> Self:
        """ Creates a zip archive instance from a file object in memory. """

        f = NamedTemporaryFile()  # noqa: SIM115

        buffer.seek(0)

        while f.write(buffer.read(1024 * 1024)):
            pass

        f.flush()

        obj = cls(f.name)

        # keep the tempfile around undtil the zip archive itself is GC'd
        obj.file = f  # type:ignore[attr-defined]

        return obj

    def write(self, directory: Directory, *args: Any, **kwargs: Any) -> None:
        self.archive.write(directory, *args, **kwargs)
        self.compress()

    def read(self, *args: Any, **kwargs: Any) -> Directory:
        self.extract()
        return self.archive.read(*args, **kwargs)

    def compress(self) -> None:
        # make_archive expects a path without extension
        output_file = str(self.path).removesuffix('.' + self.format)
        shutil.make_archive(output_file, self.format, str(self.archive.path))

    def extract(self) -> None:
        shutil.unpack_archive(
            filename=str(self.path),
            extract_dir=str(self.archive.path),
            format=self.format
        )

        top_level_dir = next(
            (
                entry.path
                for entry in os.scandir(self.archive.path)
                if entry.is_dir() and 'metadata.json' in os.listdir(entry.path)
            ), None,
        )
        if top_level_dir:
            # flatten structure by moving all files to the top level
            shutil.copytree(top_level_dir, str(self.archive.path),
                            dirs_exist_ok=True)
            shutil.rmtree(top_level_dir)
