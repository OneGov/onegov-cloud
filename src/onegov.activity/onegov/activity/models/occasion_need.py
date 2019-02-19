from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import INT4RANGE
from uuid import uuid4


class OccasionNeed(Base, TimestampMixin):
    """ Defines a required resource on an occasion. """

    __tablename__ = 'occasion_needs'

    #: the public id of this occasion resource
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the name of the occasion resource
    name = Column(Text, nullable=False)

    #: a description of the occasion resource
    description = Column(Text, nullable=True)

    #: the required range of resources
    number = Column(INT4RANGE, nullable=False)

    #: The associated occasion
    occasion_id = Column(UUID, ForeignKey('occasions.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'name', 'occasion_id', name='unique_need_per_occasion'),
    )
