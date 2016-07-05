from depot.fields.sqlalchemy import UploadedFileField as UploadedFileFieldBase
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Text
from uuid import uuid4


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
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the name of the file, incl. extension (not used for public links)
    name = Column(Text, nullable=False)

    #: the type of the file, this can be used to create custom polymorphic
    #: subclasses. See `<http://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    #:
    #: not to be confused with the the actual filetype which is stored
    #: on the :attr:`reference`!
    type = Column(Text, nullable=True)

    #: the reference to the actual file, uses depot to point to a file on
    #: the local file system or somewhere else (e.g. S3)
    reference = Column(UploadedFileField)
