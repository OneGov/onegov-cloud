from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text


class PaymentType(Base, TimestampMixin):
    """ Payment types. """

    __tablename__ = 'wtfs_payment_type'

    #: The name of the type
    name = Column(Text, primary_key=True)

    #: The price per quantity times hundred, used for invoices. Typically
    #: 700 (normal) or 850 (special).
    _price_per_quantity = Column('price_per_quantity', Integer, nullable=False)

    @property
    def price_per_quantity(self):
        return (self._price_per_quantity or 0) / 100

    @price_per_quantity.setter
    def price_per_quantity(self, value):
        self._price_per_quantity = (value or 0) * 100
