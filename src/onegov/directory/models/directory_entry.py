from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.gis import CoordinatesMixin
from onegov.search import SearchableContent
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Collection
    from .directory import Directory


class DirectoryEntry(Base, ContentMixin, CoordinatesMixin, TimestampMixin,
                     SearchableContent, AssociatedFiles, UTCPublicationMixin):
    """ A single entry of a directory. """

    __tablename__ = 'directory_entries'

    fts_public = False
    fts_properties = {
        # FIXME: We may want to include the directory title, so you can
        #        find entries by the kind of directory they are in
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'},
        # FIXME: Should we move this to fts_tags?
        'keywords': {'type': 'keyword', 'weight': 'A'},

        # since the searchable text might include html, we remove it
        # even if there's no html -> possibly decreasing the search
        # quality a bit
        'text': {'type': 'localized', 'weight': 'C'}
    }

    #: An interal id for references (not public)
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The public id of the directory entry
    name: Column[str] = Column(Text, nullable=False)

    #: The directory this entry belongs to
    directory_id: Column[UUID] = Column(
        ForeignKey('directories.id'), nullable=False)

    #: the polymorphic type of the entry
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: The order of the entry in the directory
    order: Column[str] = Column(Text, nullable=False, index=True)

    #: The title of the entry
    title: Column[str] = Column(Text, nullable=False)

    #: Describes the entry briefly
    lead: Column[str | None] = Column(Text, nullable=True)

    #: All keywords defined for this entry (indexed)
    _keywords: Column[dict[str, str] | None] = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE),  # type:ignore[no-untyped-call]
        nullable=True,
        name='keywords'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    __table_args__ = (
        Index('inverted_keywords', 'keywords', postgresql_using='gin'),
        Index('unique_entry_name', 'directory_id', 'name', unique=True),
    )

    directory: relationship[Directory] = relationship(
        'Directory',
        back_populates='entries'
    )

    @property
    def external_link(self) -> str | None:
        return self.directory.configuration.extract_link(self.values)

    @property
    def external_link_title(self) -> str | None:
        return self.directory.configuration.link_title

    @property
    def external_link_visible(self) -> bool | None:
        return self.directory.configuration.link_visible

    @property
    def directory_name(self) -> str:
        return self.directory.name

    @property
    def keywords(self) -> set[str]:
        return set(self._keywords.keys()) if self._keywords else set()

    # FIXME: asymmetric properties are not supported by mypy, switch to
    #        a custom descriptor, if desired.
    @keywords.setter
    def keywords(self, value: Collection[str] | None) -> None:
        self._keywords = dict.fromkeys(value, '') if value else None

    @property
    def text(self) -> str:
        return self.directory.configuration.extract_searchable(self.values)

    @property
    def values(self) -> dict[str, Any]:
        return self.content.get('values', {}) if self.content else {}

    @values.setter
    def values(self, values: dict[str, Any]) -> None:
        self.content = self.content or {}
        self.content['values'] = values
        self.content.changed()  # type:ignore[attr-defined]
