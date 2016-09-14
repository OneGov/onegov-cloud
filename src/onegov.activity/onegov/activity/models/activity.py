from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    content_property,
    ContentMixin,
    meta_property,
    TimestampMixin,
)
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from uuid import uuid4


class Activity(Base, ContentMixin, TimestampMixin):
    """ Describes an activity that is made available to participants on
    certain occasions (i.e. dates).

    The activity describes the what's going on, the occasion describes when
    and with whom.

    """

    __tablename__ = 'activities'

    #: An internal id for references (not public)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: A nice id for the url, readable by humans
    name = Column(Text, nullable=False, unique=True)

    #: The title of the activity
    title = Column(Text, nullable=False)

    #: Describes the activity briefly
    lead = meta_property('lead')

    #: Describes the activity in detail
    text = content_property('text')

    #: Tags/Categories of the activity
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    #: The user id to which this activity belongs to (organiser)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': 'type'
    }
