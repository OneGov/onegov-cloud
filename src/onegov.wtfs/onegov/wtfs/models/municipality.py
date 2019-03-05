from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import UserGroup
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class Municipality(Base, TimestampMixin):
    """ A municipality """

    __tablename__ = 'wtfs_municipalities'

    #: the id of the db record (only relevant internally)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The name of the municipality.
    name = Column(Text, nullable=False)

    #: The name of the municipality.
    bfs_number = Column(Integer, nullable=False)

    #: The group that holds all users of this municipality.
    group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=False)
    group = relationship(
        UserGroup, backref=backref('municipality', uselist=False)
    )

    #: The address supplement, used for invoices.
    address_supplement = Column(Text, nullable=True)

    #: The GPN number, used for invoices.
    gpn_number = Column(Integer, nullable=True)

    #: The price per quantity times hundred, used for invoices. Typically
    #: 700 (normal) or 850 (special).
    _price_per_quantity = Column(
        'price_per_quantity', Integer, nullable=False, server_default='700'
    )

    @property
    def price_per_quantity(self):
        return (self._price_per_quantity or 0) / 100

    @price_per_quantity.setter
    def price_per_quantity(self, value):
        self._price_per_quantity = (value or 0) * 100

    @property
    def has_data(self):
        if self.pickup_dates.first() or self.scan_jobs.first():
            return True
        return False
