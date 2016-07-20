from depot.fields.sqlalchemy import UploadedFileField as UploadedFileFieldBase
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.file.filters import OnlyIfImage, WithThumbnailFilter
from onegov.file.attachments import ProcessedUploadedFile
from sqlalchemy import Column, Text
from sqlalchemy_utils import observes


class UploadedFileField(UploadedFileFieldBase):
    """ A customized version of Depot's uploaded file field. This version
    stores its data in an unlimited text field, whereas the original uses
    a limited varchar field.

    We probably won't hit the 4000 character limit any time soon, but to
    avoid any chance of this happening, we use Text instead.

    """

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(Text())


class File(Base, TimestampMixin):
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

    @observes('reference')
    def reference_observer(self, reference):
        self.checksum = self.reference.get('checksum')

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
