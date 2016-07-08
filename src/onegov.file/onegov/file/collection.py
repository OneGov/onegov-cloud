from onegov.file.models import File, FileSet
from onegov.file.utils import as_fileintent


class FileCollection(object):
    """ Manages files. """

    def __init__(self, session, type='*'):
        self.session = session
        self.type = type

    def query(self):
        query = self.session.query(File)

        if self.type != '*':
            query = query.filter(File.type == self.type)

        return query

    def add(self, filename, content, note=None):
        """ Adds a file with the given filename. The content maybe either
        in bytes or a file object.

        """

        type = self.type != '*' and self.type or None

        file = File.get_polymorphic_class(type, File)()
        file.name = filename
        file.note = note
        file.type = type
        file.reference = as_fileintent(content, filename)

        self.session.add(file)
        self.session.flush()

        return file

    def replace(self, file, content):
        """ Replaces the content of the given file with the new content. """
        file.reference = as_fileintent(content, file.name)
        self.session.flush()

    def delete(self, file):
        self.session.delete(file)
        self.session.flush()

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

    def add(self, title, meta=None, content=None, type=None):
        fileset = FileSet.get_polymorphic_class(type, FileSet)()
        fileset.title = title
        fileset.type = type
        fileset.meta = meta
        fileset.content = content

        self.session.add(fileset)
        self.session.flush()

        return fileset

    def delete(self, fileset):
        self.session.delete(fileset)

    def by_id(self, fileset_id):
        """ Returns the fileset with the given id or None. """

        return self.query().filter(FileSet.id == fileset_id).first()
