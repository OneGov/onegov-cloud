import mimetypes
import json
import shutil
import os

from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.utils import rchop
from onegov.file import File
from pathlib import Path
from sqlalchemy.orm import object_session
from tempfile import TemporaryDirectory, NamedTemporaryFile


class DirectoryArchiveReader(object):

    def read(self):
        raise NotImplementedError


class DirectoryArchiveWriter(object):

    def write(self, directory):
        self.write_directory_metadata(directory)
        self.write_directory_entries(directory)

    def write_directory_metadata(self, directory):
        metadata = {
            'configuration': directory.configuration.to_dict(),
            'structure': directory.structure,
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
            return {k: v for k, v in as_tuples(entry)}

        data = tuple(as_dict(e) for e in directory.entries)

        write = getattr(self, 'write_{}'.format(self.format))
        write(self.path / 'data.{}'.format(self.format), data)

        files = object_session(directory).query(File)
        files = files.filter(File.id.in_(paths))

        tempfiles = []

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

    def __init__(self, path, format, transform=None):
        assert format in ('xlsx', 'csv', 'json')

        self.path = Path(path)
        self.format = format
        self.transform = transform or (lambda key, value: (key, value))


class DirectoryZipArchive(object):

    format = 'zip'

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.temp = TemporaryDirectory()
        self.archive = DirectoryArchive(self.temp.name, *args, **kwargs)

    def write(self, directory):
        self.archive.write(directory)
        self.compress()

    def read(self):
        self.extract()
        return self.archive.read()

    def compress(self):
        # make_archive expects a path without extension
        output_file = rchop(str(self.path), '.' + self.format)
        shutil.make_archive(output_file, self.format, str(self.archive.path))

    def extract(self):
        shutil.unpack_archive(
            filename=self.archive.path,
            extract_dir=self.path,
            format=self.format)
