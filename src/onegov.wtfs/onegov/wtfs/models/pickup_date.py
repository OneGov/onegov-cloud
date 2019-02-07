from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.wtfs.models.municipality import Municipality
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class PickupDate(Base, TimestampMixin):
    """ A pick-up date. """

    __tablename__ = 'wtfs_pickup_dates'

    #: the id of the db record (only relevant internally)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the date
    date = Column(Date, nullable=False)

    #: the municipality.
    municipality_id = Column(UUID, ForeignKey(Municipality.id), nullable=False)
    municipality = relationship(
        Municipality,
        backref=backref(
            'pickup_dates',
            lazy='dynamic',
            order_by='PickupDate.date'
        )
    )
