from __future__ import annotations

from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from sqlalchemy import Column, ForeignKey, Table, Text
from sqlalchemy.orm import mapped_column, relationship, Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .file import File


# many to many relationship between File and FileSets
file_to_set_associations = Table(
    'file_to_set_associations', Base.metadata,
    Column('file_id', Text, ForeignKey('files.id')),
    Column('fileset_id', Text, ForeignKey('filesets.id'))
)


class FileSet(Base, ContentMixin, TimestampMixin):
    """ A set of files that belong together. Each file may be part of
    none, one or many sets. Each set may containe none, one or many files.

    The fileset uses uuids for public urls instead of a readable url-safe
    name, because files are meant to be always public with an unguessable url,
    and so the filesets containing files must also have the same property.

    Otherwise we might not be able to guess the name the of the file, but we
    will be able to guess the name of a fileset containing files.

    """

    __tablename__ = 'filesets'

    #: the unique, public id of the fileset
    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=random_token
    )

    #: the title of the fileset (not usable in url)
    title: Mapped[str]

    #: the type of the fileset, this can be used to create custom polymorphic
    #: subclasses. See `<https://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    #:
    #: this is independent from the :attr:`onegov.file.models.File.type`
    #: attribute on the :class:`~onegov.file.models.File`.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    files: Mapped[list[File]] = relationship(
        secondary=file_to_set_associations,
        back_populates='filesets',
        order_by='desc(File.last_change)'
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }
