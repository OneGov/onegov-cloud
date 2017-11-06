import mimetypes
import json
import shutil
import os

from collections import OrderedDict
from onegov.core.csv import CSVFile
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.utils import Bunch, rchop, is_subpath, normalize_for_url
from onegov.directory.models import Directory, DirectoryEntry
from onegov.directory.types import DirectoryConfiguration
from onegov.file import File
from onegov.form import as_internal_id
from pathlib import Path
from sqlalchemy.orm import object_session
from tempfile import TemporaryDirectory, NamedTemporaryFile


class DirectoryArchiveReader(object):

    def read(self, target=None, skip_existing=True):
        metadata = self.read_metadata()
        records = self.read_data()

        directory = target or Directory()
        directory.title = metadata['title']
        directory.lead = metadata['lead']
        directory.name = metadata['name']
        directory.type = metadata['type']
        directory.structure = metadata['structure']
        directory.configuration = DirectoryConfiguration(
            **metadata['configuration'])

        by_human_id = {f.human_id: f for f in directory.fields}
        by_id = {f.id: f for f in directory.fields}

        if skip_existing and target:
            existing = {
                e.name for e in object_session(target).query(DirectoryEntry)
                .filter_by(directory_id=target.id)
                .with_entities(DirectoryEntry.name)
            }
        else:
            existing = set()

        unknown = object()

        def parse(key, value):
            field = by_human_id.get(key) or by_id.get(key)

            if not field:
                return unknown

            if field.type == 'fileinput':

                if value:
                    # be extra paranoid about these path values -> they could
                    # potentially be used to access files on the local system
                    assert '..' not in value
                    assert value.count('/') == 1
                    assert value.startswith(field.id + '/')

                    path = self.path / value
                    assert is_subpath(str(self.path), str(path))

                    value = Bunch(
                        data=object(),
                        file=path.open('rb'),
                        filename=value.split('/')[-1]
                    )
                else:
                    value = None
            else:
                try:
                    value = field.parse(value)
                except ValueError:
                    value = None

            return as_internal_id(key), value

        for record in records:
            values = dict(
                p for p in (parse(k, v) for k, v in record.items())
                if p is not unknown
            )

            if skip_existing:
                title = directory.configuration.extract_title(values)

                if normalize_for_url(title) in existing:
                    continue

            entry = directory.add(values)

            names = (
                ('latitude', 'longitude'),
                ('Latitude', 'Longitude')
            )
            for lat, lon in names:
                if record.get(lat) and record.get(lon):
                    entry.content['coordinates'] = {
                        'lon': record[lon],
                        'lat': record[lat]
                    }

        return directory

    def read_metadata(self):
        with (self.path / 'metadata.json').open('r') as f:
            return json.loads(f.read())

    def read_data(self):
        if (self.path / 'data.json').exists():
            return self.read_data_from_json()

        if (self.path / 'data.csv').exists():
            return self.read_data_from_csv()

        raise NotImplementedError

    def read_data_from_json(self):
        with (self.path / 'data.json').open('r') as f:
            return json.loads(f.read())

    def read_data_from_csv(self):
        with (self.path / 'data.csv').open('rb') as f:
            csv = CSVFile(f)
            csv.rowtype = dict

            return list(csv.lines)


class DirectoryArchiveWriter(object):

    def write(self, directory):
        assert self.format in ('xlsx', 'csv', 'json')

        self.write_directory_metadata(directory)
        self.write_directory_entries(directory)

    def write_directory_metadata(self, directory):
        metadata = {
            'configuration': directory.configuration.to_dict(),
            'structure': directory.structure.replace('\r\n', '\n'),
            'title': directory.title,
            'lead': directory.lead,
            'name': directory.name,
            'type': directory.type
        }
        self.write_json(self.path / 'metadata.json', metadata)

    def write_directory_entries(self, directory):
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
            data['Latitude'] = coordinates.get('lat')
            data['Longitude'] = coordinates.get('lon')

            return data

        data = tuple(as_dict(e) for e in directory.entries)

        write = getattr(self, 'write_{}'.format(self.format))
        write(self.path / 'data.{}'.format(self.format), data)

        tempfiles = []

        if paths:
            files = object_session(directory).query(File)
            files = files.filter(File.id.in_(paths))

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
                    os.link(src, dst)  # prefer links if possible
                except OSError:
                    shutil.copyfile(src, dst)

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

    def __init__(self, path, format=None, transform=None):
        self.path = Path(path)
        self.format = format
        self.transform = transform or (lambda key, value: (key, value))


class DirectoryZipArchive(object):

    format = 'zip'

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.temp = TemporaryDirectory()
        self.archive = DirectoryArchive(self.temp.name, *args, **kwargs)

    @classmethod
    def from_buffer(cls, buffer):
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
