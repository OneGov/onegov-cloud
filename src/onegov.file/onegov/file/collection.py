from io import IOBase
from onegov.file.models import File, FileSet


class FileCollection(object):
    """ Manages files. """

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(File)

    def add(self, filename, content, type=None):
        """ Adds a file with the given filename. The content maybe either
        in bytes or a file object.

        """
        assert isinstance(content, bytes) or isinstance(content, IOBase), """
            Content must be either a bytes string or a file-like object.
        """

        if hasattr(content, 'mode'):
            assert 'b' in content.mode, "Open file in binary mode."
        else:
            assert isinstance(content, bytes), "Provide content in bytes."

        file = File.get_polymorphic_class(type, File)()
        file.name = filename
        file.type = type
        file.reference = content

        self.session.add(file)
        self.session.flush()

        return file

    def delete(self, file):
        self.session.delete(file)

    def by_id(self, file_id):
        """ Returns the file with the given id or None. """

        return self.query().filter(File.id == file_id).first()

    def by_filename(self, filename):
        """ Returns a query that matches the files with the given filename.

        Be aware that there may be multiple files with the same filename!

        """
        return self.query().filter(File.name == filename)


class FileSetCollection(object):
    """ Manages filesets. """

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(FileSet)

    def add(self, title, type=None):
        fileset = FileSet.get_polymorphic_class(type, FileSet)()
        fileset.title = title
        fileset.type = type

        self.session.add(fileset)
        self.session.flush()

        return fileset

    def delete(self, fileset):
        self.session.delete(fileset)

    def by_id(self, fileset_id):
        """ Returns the fileset with the given id or None. """

        return self.query().filter(FileSet.id == fileset_id).first()
