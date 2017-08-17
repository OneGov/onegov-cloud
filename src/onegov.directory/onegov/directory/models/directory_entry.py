from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from uuid import uuid4


class DirectoryEntry(Base, ContentMixin, TimestampMixin):
    """ A single entry of a directory. """

    __tablename__ = 'directory_entries'

    #: An interal id for references (not public)
    id = Column(UUID, primary_key=True, default=uuid4)

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

    __mapper_args__ = {
        'order_by': order,
        'polymorphic_on': type
    }
