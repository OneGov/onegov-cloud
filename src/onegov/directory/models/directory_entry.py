from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.file import AssociatedFiles
from onegov.gis import CoordinatesMixin
from onegov.search import SearchableContent
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import mapped_column, relationship, Mapped
from translationstring import TranslationString
from uuid import uuid4, UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from .directory import Directory


class DirectoryEntry(Base, ContentMixin, CoordinatesMixin, TimestampMixin,
                     SearchableContent, AssociatedFiles, UTCPublicationMixin):
    """ A single entry of a directory. """

    __tablename__ = 'directory_entries'

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString(
        'Directory entries',
        domain='onegov.org'
    )
    fts_public = False
    fts_title_property = 'title'
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
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The public id of the directory entry
    name: Mapped[str]

    #: The directory this entry belongs to
    directory_id: Mapped[UUID] = mapped_column(ForeignKey('directories.id'))

    #: the polymorphic type of the entry
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    #: The order of the entry in the directory
    order: Mapped[str] = mapped_column(index=True)

    #: The title of the entry
    title: Mapped[str]

    #: Describes the entry briefly
    lead: Mapped[str | None]

    #: All keywords defined for this entry (indexed)
    _keywords: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(HSTORE),
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

    directory: Mapped[Directory] = relationship(back_populates='entries')

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
