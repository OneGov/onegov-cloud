from datetime import timedelta
from depot.io.utils import file_from_content
from onegov.chat import Message
from onegov.file.models import File, FileSet
from onegov.file.utils import as_fileintent, digest
from sedate import utcnow
from sqlalchemy import and_, text, or_


class FileCollection(object):
    """ Manages files.

    :param session:
        The SQLAlchemy db session to use.

    :param type:
        The polymorphic type to use and to filter for, or '*' for all.

    :param allow_duplicates:
        Prevents duplicates if set to false. Duplicates are detected before
        pre-processing, so already stored files may be downloaded and
        added again, as they might have changed during the upload.

        Note that this does not change existing files. It only prevents
        new duplicates from being added.

    """

    def __init__(self, session, type='*', allow_duplicates=True):
        self.session = session
        self.type = type
        self.allow_duplicates = allow_duplicates

    def query(self):
        if self.type != '*':
            model_class = File.get_polymorphic_class(self.type, File)

            if model_class is File:
                return self.session.query(File).filter_by(type=self.type)

            return self.session.query(model_class)

        return self.session.query(File)

    def add(self, filename, content, note=None, published=True,
            publish_date=None):
        """ Adds a file with the given filename. The content maybe either
        in bytes or a file object.

        """

        if not self.allow_duplicates:
            self.assert_not_duplicate(content)

        type = self.type != '*' and self.type or None

        file = File.get_polymorphic_class(type, File)()
        file.name = filename
        file.note = note
        file.type = type
        file.published = published
        file.publish_date = publish_date
        file.reference = as_fileintent(content, filename)

        self.session.add(file)
        self.session.flush()

        return file

    def replace(self, file, content):
        """ Replaces the content of the given file with the new content. """

        if not self.allow_duplicates:
            self.assert_not_duplicate(content)

        file.reference = as_fileintent(content, file.name)
        self.session.flush()

    def assert_not_duplicate(self, content):
        existing = self.by_content(content).first()

        if existing:
            raise FileExistsError(existing)

    def delete(self, file):
        self.session.delete(file)
        self.session.flush()

    def publishable_files(self, horizon=None):
        """ Yields files which may be published. """

        yield from self.query().filter(and_(
            File.published == False,
            File.publish_date != None,
            File.publish_date <= horizon
        ))

    def publish_files(self, horizon=None):
        """ Publishes unpublished files with a publish date older than the
        given horizon.

        """
        # default to a horizon slightly into the future as this method is
        # usually called by cronjob which is not perfectly on time
        horizon = horizon or (utcnow() + timedelta(seconds=90))

        for f in self.publishable_files(horizon):
            f.published = True
            f.publish_date = None

        self.session.flush()

    def by_id(self, file_id):
        """ Returns the file with the given id or None. """

        return self.query().filter(File.id == file_id).first()

    def by_filename(self, filename):
        """ Returns a query that matches the files with the given filename.

        Be aware that there may be multiple files with the same filename!

        """
        return self.query().filter(File.name == filename)

    def by_checksum(self, checksum):
        """ Returns a query that matches the given checksum (may be more than
        one record).

        """
        return self.query().filter(File.checksum == checksum)

    def by_content(self, content):
        """ Returns a query that matches the given content (may be more than
        one record).

        """
        file = file_from_content(content)

        # we need to look up two checksums, the one of the file stored and
        # possibly the one it had before signing
        #
        # XXX maybe it makes sense to combine those into a data structure
        # that holds all kinds of digests a file is known under

        # checksum
        md5 = digest(file, 'md5')

        # old_digest of signature_metadata
        sha = digest(file, 'sha256')

        return self.query().filter(or_(
            File.checksum == md5,
            File.signature_metadata['old_digest'].astext == sha
        ))

    def by_content_type(self, content_type):
        """ Returns a query that matches the given MIME content type (may be
        more than one record).

        """

        return self.query().filter(
            text("reference->>'content_type' = :content_type").bindparams(
                content_type=content_type
            )
        )

    def by_signature_digest(self, digest):
        """ Returns a query that matches the given digest in the signature
        metadata. In other words, given a digest this function will find
        signed files that match the digest - either before or after signing.

        Unsigned files are ignored.

        The digest is expected to be a SHA256 hex.

        """

        return self.query().filter_by(signed=True).filter(
            or_(
                text("signature_metadata->>'old_digest' = :digest").bindparams(
                    digest=digest
                ),
                text("signature_metadata->>'new_digest' = :digest").bindparams(
                    digest=digest
                )
            )
        )

    def locate_signature_metadata(self, digest):
        """ Looks for the given digest in the files table - if that doesn't
        work it will go through the audit trail (i.e. the chat messages) and
        see if the digest can be found there.

        If this database was ever used to sign a file with the given digest,
        or if a file that was signed had the given digest, this function
        will find it - barring manual database manipulation in the messages
        log.

        """

        match = self.by_signature_digest(digest).with_entities(
            File.signature_metadata).first()

        if match:
            return match.signature_metadata

        match = self.session.query(Message).filter_by(type='file').filter(or_(
            text(
                "meta->'action_metadata'->>'old_digest' = :digest"
            ).bindparams(digest=digest),
            text(
                "meta->'action_metadata'->>'new_digest' = :digest"
            ).bindparams(digest=digest)
        )).with_entities(Message.meta).first()

        if match:
            return match.meta['action_metadata']


class FileSetCollection(object):
    """ Manages filesets. """

    def __init__(self, session, type='*'):
        self.session = session
        self.type = type

    def query(self):
        if self.type != '*':
            model_class = FileSet.get_polymorphic_class(self.type, FileSet)

            if model_class is FileSet:
                return self.session.query(File).filter_by(type=self.type)

            return self.session.query(model_class)

        return self.session.query(FileSet)

    def add(self, title, meta=None, content=None):
        type = self.type != '*' and self.type or None

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
