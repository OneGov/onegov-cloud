""" Contains the models describing the files. """

import base64
import magic

from onegov.core.filestorage import FilestorageFile
from webob.exc import HTTPUnsupportedMediaType


class FileCollection(object):
    """ Defines the collection of files uploaded to the site. Currently
    this is done without any ORM backing (and therefore without any
    special features like tagging, metadata and so on).

    Instead it's simply a list of files in a directory.

    This can be made more powerful (and complicated) once we have sufficent
    time to do it.

    """

    allowed_mime = {
        'application/msword',
        'application/pdf',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-'
        'officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/zip',
        'text/plain',
    }

    def __init__(self, app):
        assert app.has_filestorage

        self.path_prefix = 'files/'
        self.file_storage = app.filestorage.makeopendir('files')

    @property
    def files(self):
        """ Returns the :class:`~onegov.town.model.File` instances in this
        collection.

        """
        files = self.file_storage.ilistdirinfo(files_only=True)
        files = sorted(files, key=lambda i: i[1]['created_time'])

        for filename, info in files:
            yield File(filename, info)

    def store_file(self, file_, filename):
        """ Stores an file (a file with a ``read()`` method) with the given
        filename. Note that these files are public, so the filename *should*
        be random.

        See :func:`onegov.core.filestorage.random_filename`.

        """

        file_data = file_.read()

        mimetype_by_introspection = magic.from_buffer(file_data, mime=True)
        mimetype_by_introspection = mimetype_by_introspection.decode('utf-8')

        if mimetype_by_introspection not in self.allowed_mime:
            raise HTTPUnsupportedMediaType()

        self.file_storage.setcontents(filename, file_data)

        return self.get_file_by_filename(filename)

    def get_file_by_filename(self, filename):
        """ Returns the :class:`~onegov.town.model.File` instance with the
        given name, or None if not found.

        """
        if self.file_storage.exists(filename):
            return File(filename)

    def delete_file_by_filename(self, filename):
        """ Deletes the file of the given filename. """

        if self.file_storage.exists(filename):
            self.file_storage.remove(filename)


class File(FilestorageFile):
    """ A filestorage file that points to an uploaded image or file. """

    def __init__(self, filename, info=None):
        self.filename = filename
        self.info = info or {}

    @property
    def date(self):
        if 'date' in self.info:
            return self.info['created_time'].date()

    @property
    def path(self):
        return 'files/' + self.filename

    @property
    def original_name(self):
        if '-' in self.filename:
            name = str(self.filename.split('-')[0])
            return base64.urlsafe_b64decode(name).strip()

    @classmethod
    def from_url(cls, url):
        return cls(url.split('/')[-1])
