import json

from depot.fields.sqlalchemy import UploadedFileField as UploadedFileFieldBase
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.abstract import Associable
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UTCDateTime
from onegov.core.utils import normalize_for_url
from onegov.file.attachments import ProcessedUploadedFile
from onegov.file.filters import OnlyIfImage, WithThumbnailFilter
from onegov.file.filters import OnlyIfPDF, WithPDFThumbnailFilter
from pathlib import Path
from sqlalchemy import Boolean, Column, Index, Text
from sqlalchemy import event
from sqlalchemy.orm import object_session, Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy_utils import observes


class UploadedFileField(UploadedFileFieldBase):
    """ A customized version of Depot's uploaded file field. This version
    stores its data in a JSONB field, instead of using text.

    """

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value:
            return value

    def process_result_value(self, value, dialect):
        if value:
            return self._upload_type(value)


class File(Base, Associable, TimestampMixin):
    """ A general file (image, document, pdf, etc), referenced in the database.

    Thanks to the use of `Depot <http://depot.readthedocs.io>`_ files
    can be seemingly stored in the database (with transaction guarantees),
    without actually storing it in the database.

    """

    __tablename__ = 'files'

    #: the unique, public id of the file
    id = Column(Text, nullable=False, primary_key=True, default=random_token)

    #: the name of the file, incl. extension (not used for public links)
    name = Column(Text, nullable=False)

    #: a short note about the file (for captions, other information)
    note = Column(Text, nullable=True)

    #: the default order of files
    order = Column(Text, nullable=False)

    #: true if published
    published = Column(Boolean, nullable=False, default=True)

    #: the date after which this file will be made public - this controls
    #: the visibility of the object through the ``is_hidden_from_public``
    #: property which in turn is enforced by :mod:`onegov.core.security.rules`.
    #:
    #: To get a file published, be sure to call
    #: :meth:`onegov.file.collection.FileCollection.publish_files` once an
    #: hour through a cronjob (see :mod:`onegov.core.cronjobs`)!
    publish_date = Column(UTCDateTime, nullable=True)

    #: true if the file was digitally signed in the onegov cloud
    #:
    #: (the file could be signed without this being true, but that would
    #: amount to a signature created outside of our platform, which is
    #: something we ignore)
    signed = Column(Boolean, nullable=False, default=False)

    #: the type of the file, this can be used to create custom polymorphic
    #: subclasses. See `<http://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    #:
    #: not to be confused with the the actual filetype which is stored
    #: on the :attr:`reference`!
    type = Column(Text, nullable=True)

    #: the reference to the actual file, uses depot to point to a file on
    #: the local file system or somewhere else (e.g. S3)
    reference = Column(UploadedFileField(
        upload_type=ProcessedUploadedFile,
        filters=[
            OnlyIfImage(
                # note, the thumbnail configuration should not be changed
                # anywhere but here - for consistency.
                WithThumbnailFilter(
                    name='small', size=(256, 256), format='png'
                )
            ),
            OnlyIfPDF(
                WithPDFThumbnailFilter(
                    name='medium', size=(512, 512), format='png'
                )
            )
        ]
    ), nullable=False)

    #: the md5 checksum of the file *before* it was processed by us, that is
    #: if the file was very large and we in turn made it smaller, it's the
    #: checksum of the file before it was changed by us
    #: this is useful to check if an uploaded file was already uploaded before
    #:
    #: note, this is not meant to be cryptographically secure - this is
    #: strictly a check of file duplicates, not protection against tampering
    checksum = Column(Text, nullable=True, index=True)

    __mapper_args__ = {
        'polymorphic_on': 'type'
    }

    __table_args__ = (
        Index('files_by_type_and_order', 'type', 'order'),
    )

    @observes('reference')
    def reference_observer(self, reference):
        self.checksum = self.reference.get('checksum')

    @observes('name')
    def name_observer(self, name):
        self.order = normalize_for_url(name)

    @property
    def is_hidden_from_public(self):
        return not self.published

    @property
    def file_id(self):
        """ The file_id of the contained reference.

        If :attr:`virtual_file_id` is not None, it is returned instead.
        """

        return self.virtual_file_id or self.reference.file_id

    def get_thumbnail_id(self, size):
        """ Returns the thumbnail id with the given size (e.g. 'small').

        """
        # make sure to always prefix the name with thumbnail_, otherwise this
        # mechanism might be used to access other files created by filters
        name = 'thumbnail_' + size

        if name not in self.reference:
            return None

        return self.reference[name]['id']

    def _update_metadata(self, **options):
        """ Updates the underlying metadata with the give values. This
        operats on low-level interfaces of Depot and assumes local storage.

        You should have a good reason for using this.

        """
        assert set(options.keys()).issubset({'content_type', 'filename'})

        path = Path(self.reference.file._metadata_path)

        # store the pending metadata on the session to commit them later
        session = object_session(self)

        if 'pending_metadata_changes' not in session.info:
            session.info['pending_metadata_changes'] = []

        # only support upating existing values - do not create new ones
        for key, value in options.items():
            session.info['pending_metadata_changes'].append((path, key, value))

        # make sure we cause a commit here
        flag_modified(self, 'reference')


@event.listens_for(Session, 'after_commit')
def update_metadata_after_commit(session):
    if 'pending_metadata_changes' not in session.info:
        return

    for path, key, value in session.info['pending_metadata_changes']:
        with open(path, 'r') as f:
            metadata = json.loads(f.read())

        metadata[key] = value

        with open(path, 'w') as f:
            f.write(json.dumps(metadata))

    del session.info['pending_metadata_changes']


@event.listens_for(Session, 'after_soft_rollback')
def discard_metadata_on_rollback(session):
    if 'pending_metadata_changes' in session.info:
        del session.info['pending_metadata_changes']
