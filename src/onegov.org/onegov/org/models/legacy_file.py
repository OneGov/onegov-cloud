""" Contains the legacy models of files for url redirect support. Going
forward, onegov.file and onegov.org.models.file is used.

 """

import base64

from onegov.core.filestorage import FilestorageFile


class LegacyFileCollection(object):

    def __init__(self, app):
        assert app.has_filestorage

        self.path_prefix = 'files/'
        self.file_storage = app.filestorage.makeopendir('files')

    def get_file_by_filename(self, filename):
        if self.file_storage.exists(filename):
            return LegacyFile(filename)


class LegacyImageCollection(object):

    def __init__(self, app):
        assert app.has_filestorage

        self.path_prefix = 'images/'
        self.file_storage = app.filestorage.makeopendir('images')

    def get_file_by_filename(self, filename):
        if self.file_storage.exists(filename):
            return LegacyImage(filename)


class LegacyFile(FilestorageFile):
    """ A filestorage file that points to an uploaded image or file. """

    def __init__(self, filename, info=None):
        self.filename = filename
        self.info = info or {}

    @property
    def date(self):
        if 'modified_time' in self.info:
            return self.info['modified_time'].date()

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


class LegacyImage(LegacyFile):
    """ A filestorage file that points to a full image (not a thumbnail). """

    @property
    def path(self):
        return 'images/' + self.filename
