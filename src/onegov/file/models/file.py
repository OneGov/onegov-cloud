from __future__ import annotations

import fcntl
import json
import sedate
import isodate

from contextlib import contextmanager
from collections import defaultdict
from depot.fields.sqlalchemy import UploadedFileField as UploadedFileFieldBase
from onegov.core.crypto import random_token
from onegov.core.orm import Base, observes
from onegov.core.orm.abstract import Associable
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UTCDateTime
from onegov.core.utils import normalize_for_url
from onegov.file import log
from onegov.file.attachments import ProcessedUploadedFile
from onegov.file.filters import OnlyIfImage, WithThumbnailFilter
from onegov.file.filters import OnlyIfPDF, WithPDFThumbnailFilter
from onegov.file.models.fileset import file_to_set_associations
from onegov.file.utils import extension_for_content_type
from onegov.search import ORMSearchable
from pathlib import Path
from sqlalchemy import Boolean, Column, Index, Text
from sqlalchemy import case
from sqlalchemy import event
from sqlalchemy import text
from sqlalchemy import type_coerce
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.orm import object_session, Session
from sqlalchemy.orm.attributes import flag_modified
from time import monotonic


from typing import overload, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import Iterator
    from datetime import datetime
    from depot.fields.upload import UploadedFile
    from depot.io.utils import FileIntent
    from onegov.file import FileSet
    from onegov.file.types import FileStats, SignatureMetadata
    from sqlalchemy.engine import Dialect
    from sqlalchemy.orm.session import SessionTransaction
    from sqlalchemy.sql.type_api import TypeEngine

    # HACK: This column accepts FileIntent as an input, but when
    #       we ask for the value we always get an UploadedFile
    class _UploadedFileColumn(Column[UploadedFile]):
        def __set__(
            self,
            obj: object,
            value: UploadedFile | FileIntent
        ) -> None: ...


class UploadedFileField(UploadedFileFieldBase):
    """ A customized version of Depot's uploaded file field. This version
    stores its data in a JSONB field, instead of using text.

    """

    # TODO: Try switching impl to JSON, so we can use JSON operators on
    #       columns using this type, we may need to change some of the
    #       methods if we do that though
    # impl = JSON

    def load_dialect_impl(
        self,
        dialect: Dialect
    ) -> TypeEngine[UploadedFile]:
        return dialect.type_descriptor(JSON())

    def process_bind_param(  # type:ignore[override]
        self,
        value: UploadedFile | None,
        dialect: Dialect
    ) -> UploadedFile | None:
        return value if value else None

    def process_result_value(
        self,
        value: dict[str, Any] | None,
        dialect: Dialect
    ) -> UploadedFile | None:
        return self._upload_type(value) if value else None


class SearchableFile(ORMSearchable):
    """ Files are not made available for elasticsearch by default. This is
    for security reasons - files are public by default but one has to know
    the url (a very long id).

    Search might lead to a disclosure of all files, which is why files
    can only be searched if they are of a different polymorphic subclass
    and use this mixin.

    """

    fts_public = True
    fts_properties = {
        'name': {'type': 'text', 'weight': 'A'},
        'note': {'type': 'localized', 'weight': 'B'},
        'extract': {'type': 'localized', 'weight': 'C'}
    }

    if TYPE_CHECKING:
        # forward declare columns on File
        name: Column[str]
        published: Column[bool]

    @property
    def fts_suggestion(self) -> str:
        return self.name


class File(Base, Associable, TimestampMixin):
    """ A general file (image, document, pdf, etc), referenced in the database.

    Thanks to the use of `Depot <https://depot.readthedocs.io>`_ files
    can be seemingly stored in the database (with transaction guarantees),
    without actually storing it in the database.

    """

    __tablename__ = 'files'

    #: the unique, public id of the file
    id: Column[str] = Column(
        Text,
        nullable=False,
        primary_key=True,
        default=random_token
    )

    #: the name of the file, incl. extension (not used for public links)
    name: Column[str] = Column(Text, nullable=False)

    #: a short note about the file (for captions, other information)
    note: Column[str | None] = Column(Text, nullable=True)

    #: the default order of files
    order: Column[str] = Column(Text, nullable=False)

    #: true if published
    published: Column[bool] = Column(Boolean, nullable=False, default=True)

    #: the date after which this file will be made public - this controls
    #: the visibility of the object through the ``access``
    #: property which in turn is enforced by :mod:`onegov.core.security.rules`.
    #:
    #: To get a file published, be sure to call
    #: :meth:`onegov.file.collection.FileCollection.publish_files` once an
    #: hour through a cronjob (see :mod:`onegov.core.cronjobs`)!
    publish_date: Column[datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )

    #: the date up to which the file is published
    publish_end_date: Column[datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )

    #: true if marked for publication
    publication: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: true if the file was digitally signed in the onegov cloud
    #:
    #: (the file could be signed without this being true, but that would
    #: amount to a signature created outside of our platform, which is
    #: something we ignore)
    signed: Column[bool] = Column(Boolean, nullable=False, default=False)

    #: the metadata of the signature - this should include the following
    #: data::
    #:
    #:  - old_digest: The sha-256 hash before the file was signed
    #:  - new_digest: The sha-256 hash after the file was signed
    #:  - signee: The username of the user that signed the document
    #:  - timestamp: The time the document was signed in UTC
    #:  - request_id: A unique identifier by the signing service
    #:
    signature_metadata: Column[SignatureMetadata | None] = deferred(
        Column(JSON, nullable=True)
    )

    #: the type of the file, this can be used to create custom polymorphic
    #: subclasses. See `<https://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    #:
    #: not to be confused with the the actual filetype which is stored
    #: on the :attr:`reference`!
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: the reference to the actual file, uses depot to point to a file on
    #: the local file system or somewhere else (e.g. S3)
    reference: _UploadedFileColumn = Column(UploadedFileField(  # type:ignore
        upload_type=ProcessedUploadedFile,
        filters=[
            OnlyIfImage(
                # note, the thumbnail configuration should not be changed
                # anywhere but here - for consistency.
                WithThumbnailFilter(
                    name='small', size=(512, 512), format='png'
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
    checksum: Column[str | None] = Column(Text, nullable=True, index=True)

    #: the content of the given file as text, if it can be extracted
    #: (it is important that this column be loaded deferred by default, lest
    #: we load massive amounts of text on simple queries)
    extract: Column[str | None] = deferred(Column(Text, nullable=True))

    #: the languge of the file
    language: Column[str | None] = Column(Text, nullable=True)

    #: statistics around the extract (number of pages, words, etc.)
    #: those are usually set during file upload (as some information is
    #: lost afterwards)
    stats: Column[FileStats | None] = deferred(Column(JSON, nullable=True))

    #: arbitrary additional meta data, which can be used by subclasses to
    #: store additional information using e.g. `meta_property`
    meta: Column[dict[str, Any]] = Column(JSON, nullable=False, default=dict)

    filesets: relationship[list[FileSet]] = relationship(
        'FileSet',
        secondary=file_to_set_associations,
        back_populates='files'
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    __table_args__ = (
        Index('files_by_type_and_order', 'type', 'order'),
    )

    @hybrid_property
    def signature_timestamp(self) -> datetime | None:
        if self.signed:
            return sedate.replace_timezone(
                isodate.parse_datetime(self.signature_metadata['timestamp']),
                'UTC'
            )
        return None

    @signature_timestamp.expression  # type:ignore[no-redef]
    def signature_timestamp(cls):
        return type_coerce(case(
            [(
                File.signed == True,
                text("""
                    (
                        to_timestamp(
                            signature_metadata->>'timestamp',
                            'YYYY-MM-DD"T"HH24:MI:SS.US'
                        )::timestamp without time zone
                    )
                """)
            )],
            else_=text('NULL')
        ), UTCDateTime)

    # NOTE: Technically we could scope these observes to DepotApp, but
    #       then we would need to instantiate a DepotApp for testing
    #       which could get annoying
    @observes('reference')
    def reference_observer(self, reference: UploadedFile) -> None:
        if 'checksum' in self.reference:
            self.checksum = self.reference.pop('checksum')

        if 'extract' in self.reference:
            self.extract = self.reference.pop('extract')

        if 'stats' in self.reference:
            self.stats = self.reference.pop('stats')

    @observes('name')
    def name_observer(self, name: str) -> None:
        self.order = normalize_for_url(name)

    @property
    def access(self) -> str:
        return 'public' if self.published else 'private'

    @property
    def file_id(self) -> str:
        """ The file_id of the contained reference.

        If :attr:`virtual_file_id` is not None, it is returned instead.
        """

        # FIXME: Do we use this attribute...? It doesn't seem like it's
        #        defined, if it's something that is sometimes added at
        #        runtime we should probably either initalize it to None
        #        or do a getattr...
        return self.virtual_file_id or self.reference.file_id  # type:ignore

    @property
    def claimed_extension(self) -> str:
        """ Returns the extension as defined by the file name or by the
        content type (whatever is found first in this order).

        Note that this extension could therefore not be correct. It is mainly
        meant for display purposes.

        If you need to know the type of a file you should use the
        content type stored on the reference.

        """
        return extension_for_content_type(
            self.reference['content_type'], self.name)

    def get_thumbnail_id(self, size: str) -> UploadedFile | None:
        """ Returns the thumbnail id with the given size (e.g. 'small').

        """
        # make sure to always prefix the name with thumbnail_, otherwise this
        # mechanism might be used to access other files created by filters
        name = 'thumbnail_' + size

        if name not in self.reference:
            return None

        return self.reference[name]['id']

    # FIXME: We may want to restrict the arguments on the actual
    #        function rather than use overloads as a workaround
    #        but we will have to be careful about default values
    @overload
    def _update_metadata(self) -> None: ...

    @overload
    def _update_metadata(
        self,
        *,
        content_type: str = ...,
        filename: str = ...,
    ) -> None: ...

    def _update_metadata(self, **options: Any) -> None:
        """ Updates the underlying metadata with the give values. This
        operats on low-level interfaces of Depot and assumes local storage.

        You should have a good reason for using this.

        """
        assert set(options.keys()).issubset({'content_type', 'filename'})

        if not hasattr(self.reference.file, '_metadata_path'):
            raise NotImplementedError(
                'The current depot storage backend does not support '
                'in-place metadata updates'
            )

        path = Path(self.reference.file._metadata_path)

        # store the pending metadata on the session to commit them later
        session = object_session(self)

        if 'pending_metadata_changes' not in session.info:
            session.info['pending_metadata_changes'] = defaultdict(dict)

        # only support upating existing values - do not create new ones
        session.info['pending_metadata_changes'][path].update(options)

        # make sure we cause a commit here
        flag_modified(self, 'reference')


@contextmanager
def metadata_lock(
    metadata_path: StrPath,
    timeout: float = 0.0,
) -> Iterator[bool]:
    """ Locks the metadata from a ``filedepot.io.local.LocalStoredFile``.
    Tries to acquire the lock repeatedly in a spin lock until timeout
    expires, it will return whether or not it managed to acquire the lock
    """
    lock_file = f'{metadata_path}.lock'
    start_time = monotonic()
    with open(lock_file, 'wb') as fd:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                if monotonic() - start_time >= timeout:
                    yield False
                    break
            else:
                yield True
                fcntl.flock(fd, fcntl.LOCK_UN)
                break


@event.listens_for(Session, 'after_commit')  # type:ignore[misc]
def update_metadata_after_commit(session: Session) -> None:
    if 'pending_metadata_changes' not in session.info:
        return

    for path, values in session.info['pending_metadata_changes'].items():
        with metadata_lock(path, 0.5) as locked:
            if not locked:
                # FIXME: For now we just log an error but still overwrite
                #        the metadata file, in case we get a flock that
                #        never gets cleaned up properly
                log.error(
                    f'Failed to acquire lock on metadata file {path}. '
                    'Performing a potentially unsafe override of metadata.'
                )

            # we modify the file in place in rw mode
            with open(path, 'r+') as f:
                metadata = json.loads(f.read())
                metadata.update(values)

                # FIXME: This potentially still has some race conditions
                #        with LocalStoredFile loading the metadata in
                #        another process, unless the file isn't flushed
                #        until after we are done writing to it.
                f.seek(0)
                f.write(json.dumps(metadata))
                f.truncate()

    del session.info['pending_metadata_changes']


@event.listens_for(Session, 'after_soft_rollback')  # type:ignore[misc]
def discard_metadata_on_rollback(
    session: Session,
    previous_transaction: SessionTransaction
) -> None:
    if 'pending_metadata_changes' in session.info:
        del session.info['pending_metadata_changes']
