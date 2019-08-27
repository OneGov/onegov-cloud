import mimetypes
import shutil
import os

from collections import OrderedDict
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.csv import convert_xls_to_csv
from onegov.core.csv import CSVFile
from onegov.core.custom import json
from onegov.core.utils import Bunch, rchop, is_subpath
from onegov.directory.errors import MissingColumnError, MissingFileError
from onegov.directory.models import Directory, DirectoryEntry
from onegov.directory.types import DirectoryConfiguration
from onegov.file import File
from onegov.form import as_internal_id
from pathlib import Path
from sqlalchemy.orm import object_session
from tempfile import TemporaryDirectory, NamedTemporaryFile


UNKNOWN_FIELD = object()


class FieldParser(object):
    """ Parses records read by the directory archive reader. """

    def __init__(self, directory, archive_path):
        self.fields_by_human_id = {f.human_id: f for f in directory.fields}
        self.fields_by_id = {f.id: f for f in directory.fields}
        self.archive_path = archive_path

    def get_field(self, key):
        return self.fields_by_human_id.get(key) or self.fields_by_id.get(key)

    def parse_fileinput(self, key, value, field):
        if not value:
            return None

        # be extra paranoid about these path values -> they could
        # potentially be used to access files on the local system
        assert '..' not in value
        assert value.count('/') == 1
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

    def parse_generic(self, key, value, field):
        return field.parse(value)

    def parse_item(self, key, value):
        field = self.get_field(key)

        if not field:
            return UNKNOWN_FIELD

        parser = getattr(self, 'parse_' + field.type, self.parse_generic)

        try:
            value = parser(key, value, field)
        except ValueError:
            value = None

        return as_internal_id(key), value

    def parse(self, record):
        return dict(
            p for p in (self.parse_item(k, v) for k, v in record.items())
            if p is not UNKNOWN_FIELD
        )


class DirectoryArchiveReader(object):
    """ Reading part of :class:`DirectoryArchive`. """

    def read(self, target=None, skip_existing=True, limit=0,
             apply_metadata=True, after_import=None):
        """ Reads the archive resulting in a dictionary and entries.

        :param target:
            Uses the given dictionary as a target for the read. Otherwise,
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

        directory = target or Directory()

        if apply_metadata:
            self.apply_metadata(directory, self.read_metadata())

        if skip_existing and target:
            existing = {
                e.name for e in object_session(target).query(DirectoryEntry)
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
            except KeyError as e:
                raise MissingColumnError(column=e.args[0])

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

    def apply_metadata(self, directory, metadata):
        """ Applies the metadata to the given directory and returns it. """

        directory.name = directory.name or metadata['name']

        directory.title = metadata['title']
        directory.lead = metadata['lead']
        directory.type = metadata['type']
        directory.structure = metadata['structure']
        directory.configuration = DirectoryConfiguration(
            **metadata['configuration']
        )

        if 'meta' in metadata:
            directory.meta = metadata['meta']

        if 'content' in metadata:
            directory.content = metadata['content']

        return directory

    def read_metadata(self):
        """ Returns the metadata as a dictionary. """

        try:
            with (self.path / 'metadata.json').open('r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            raise MissingFileError('metadata.json')

    def read_data(self):
        """ Returns the entries as a list of dictionaries. """

        if (self.path / 'data.json').exists():
            return self.read_data_from_json()

        if (self.path / 'data.csv').exists():
            return self.read_data_from_csv()

        if (self.path / 'data.xlsx').exists():
            return self.read_data_from_xlsx()

        raise NotImplementedError

    def read_data_from_json(self):
        with (self.path / 'data.json').open('r') as f:
            return json.loads(f.read())

    def read_data_from_csv(self):
        with (self.path / 'data.csv').open('rb') as f:
            return tuple(CSVFile(f, rowtype=dict).lines)

    def read_data_from_xlsx(self):
        with (self.path / 'data.xlsx').open('rb') as f:
            return tuple(CSVFile(
                convert_xls_to_csv(f), rowtype=dict, dialect='excel'
            ).lines)


class DirectoryArchiveWriter(object):
    """ Writing part of :class:`DirectoryArchive`. """

    def write(self, directory):
        """ Writes the given directory. """

        assert self.format in ('xlsx', 'csv', 'json')

        self.write_directory_metadata(directory)
        self.write_directory_entries(directory)

    def write_directory_metadata(self, directory):
        """ Writes the metadata. """

        metadata = {
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

    def write_directory_entries(self, directory):
        """ Writes the directory entries. """

        fields = directory.fields
        paths = {}

        def file_path(entry, field, value):
            return '{folder}/{name}{ext}'.format(
                folder=field.id,
                name=entry.name,
                ext=mimetypes.guess_extension(value['mimetype']) or '')

        def as_tuples(entry):
            for field in fields:
                value = entry.values.get(field.id)

                if field.type == 'fileinput':
                    if value:
                        file_id = value['data'].lstrip('@')
                        value = paths[file_id] = file_path(entry, field, value)
                    else:
                        value = None

                yield self.transform(field.human_id, value)

        def as_dict(entry):
            data = OrderedDict(as_tuples(entry))

            coordinates = entry.content.get('coordinates', {})

            if isinstance(coordinates, dict):
                data['Latitude'] = coordinates.get('lat')
                data['Longitude'] = coordinates.get('lon')
            else:
                data['Latitude'] = coordinates.lat
                data['Longitude'] = coordinates.lon

            return data

        data = tuple(as_dict(e) for e in directory.entries)

        write = getattr(self, 'write_{}'.format(self.format))
        write(self.path / 'data.{}'.format(self.format), data)

        self.write_paths(object_session(directory), paths)

    def write_paths(self, session, paths):
        """ Writes the given files to the archive path.

        :param session:
            The database session in use.

        :param paths:
            A dictionary with each key being a file id and each value
            being a path where this file id should be written to.

        """

        files = paths and session.query(File).filter(File.id.in_(paths)) or []

        # keep the temp files around so they don't get GC'd prematurely
        tempfiles = []

        try:
            for f in files:
                folder, name = paths[f.id].split('/', 1)
                folder = self.path / folder

                if not folder.exists():
                    folder.mkdir()

                # support both local files and others (memory/remote)
                if hasattr(f.reference.file, '_file_path'):
                    src = os.path.abspath(f.reference.file._file_path)
                else:
                    tmp = NamedTemporaryFile()
                    tmp.write(f.reference.file.read())
                    tempfiles.append(tmp)

                    src = tmp.name

                dst = str(folder / name)

                try:
                    os.link(src, dst)  # prefer links if possible (faster)
                except OSError:
                    shutil.copyfile(src, dst)
        finally:
            for tempfile in tempfiles:
                tempfile.close()

    def write_json(self, path, data):
        with open(str(path), 'w') as f:
            json.dump(data, f, sort_keys=True, indent=2)

    def write_xlsx(self, path, data):
        with open(str(path), 'wb') as f:
            f.write(convert_list_of_dicts_to_xlsx(data))

    def write_csv(self, path, data):
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

    def __init__(self, path, format='json', transform=None):
        """ Initialise the archive at the given path (must exist).

        :param path:
            The target path of this archive.

        :param format:
            The format of the entries (json, csv or xlsx)

        :apram transform:
            A transform function called with key and value for each entry
            that is about to be written when creating an archive. Use this
            to format values (for example datetime to string for json).

            Note that transformed fields are read by onegov.form. So if the
            transformed values cannot be parsed again by onegov.form, you
            cannot import hte resulting archive.

        """

        self.path = Path(path)
        self.format = format
        self.transform = transform or (lambda key, value: (key, value))


class DirectoryZipArchive(object):
    """ Offers the same interface as the DirectoryArchive, additionally
    zipping the folder on write and extracting the zip on read.

    """

    format = 'zip'

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.temp = TemporaryDirectory()
        self.archive = DirectoryArchive(self.temp.name, *args, **kwargs)

    @classmethod
    def from_buffer(cls, buffer):
        """ Creates a zip archive instance from a file object in memory. """

        f = NamedTemporaryFile()

        buffer.seek(0)

        while f.write(buffer.read(1024 * 1024)):
            pass

        f.flush()

        obj = cls(f.name)

        # keep the tempfile around undtil the zip archive itself is GC'd
        obj.file = f

        return obj

    def write(self, directory, *args, **kwargs):
        self.archive.write(directory, *args, **kwargs)
        self.compress()

    def read(self, *args, **kwargs):
        self.extract()
        return self.archive.read(*args, **kwargs)

    def compress(self):
        # make_archive expects a path without extension
        output_file = rchop(str(self.path), '.' + self.format)
        shutil.make_archive(output_file, self.format, str(self.archive.path))

    def extract(self):
        shutil.unpack_archive(
            filename=str(self.path),
            extract_dir=str(self.archive.path),
            format=self.format)
