from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
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
from uuid import uuid4


class DirectoryEntry(Base, ContentMixin, CoordinatesMixin, TimestampMixin,
                     SearchableContent, AssociatedFiles):
    """ A single entry of a directory. """

    __tablename__ = 'directory_entries'

    es_properties = {
        'keywords': {'type': 'keyword'},
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'directory_id': {'type': 'keyword'},

        # since the searchable text might include html, we remove it
        # even if there's no html -> possibly decreasing the search
        # quality a bit
        'text': {'type': 'localized_html'}
    }

    @property
    def es_public(self):
        return False  # to be overridden downstream

    #: An interal id for references (not public)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The public id of the directory entry
    name = Column(Text, nullable=False)

    #: The directory this entry belongs to
    directory_id = Column(ForeignKey('directories.id'), nullable=False)

    #: the polymorphic type of the entry
    type = Column(Text, nullable=True)

    #: The order of the entry in the directory
    order = Column(Text, nullable=False, index=True)

    #: The title of the entry
    title = Column(Text, nullable=False)

    #: Describes the entry briefly
    lead = Column(Text, nullable=True)

    #: All keywords defined for this entry (indexed)
    _keywords = Column(
        MutableDict.as_mutable(HSTORE), nullable=True, name='keywords'
    )

    __mapper_args__ = {
        'order_by': order,
        'polymorphic_on': type
    }

    __table_args__ = (
        Index('inverted_keywords', 'keywords', postgresql_using='gin'),
        Index('unique_entry_name', 'directory_id', 'name', unique=True),
    )

    @property
    def external_link(self):
        return self.directory.configuration.extract_link(self.values)

    @property
    def external_link_title(self):
        return self.directory.configuration.link_title

    @property
    def external_link_visible(self):
        return self.directory.configuration.link_visible

    @property
    def directory_name(self):
        return self.directory.name

    @property
    def keywords(self):
        return set(self._keywords.keys()) if self._keywords else set()

    @keywords.setter
    def keywords(self, value):
        self._keywords = {k: '' for k in value} if value else None

    @property
    def text(self):
        return self.directory.configuration.extract_searchable(self.values)

    @property
    def values(self):
        return self.content and self.content.get('values', {})

    @values.setter
    def values(self, values):
        self.content = self.content or {}
        self.content['values'] = values
        self.content.changed()
