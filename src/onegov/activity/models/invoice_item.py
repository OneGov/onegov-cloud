from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay import PayableManyTimes
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from uuid import uuid4


# total digits
PRECISION = 8

# digits after the point
SCALE = 2


class InvoiceItem(Base, TimestampMixin, PayableManyTimes):
    """ An item in an invoice. """

    __tablename__ = 'invoice_items'

    #: the public id of the invoice item
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the invoice this item belongs to
    invoice_id = Column(UUID, ForeignKey('invoices.id'))

    #: the item group (all items with the same text are visually grouped)
    group = Column(Text, nullable=False)

    #: a secondary group who is not necessarily grouped visually
    family = Column(Text, nullable=True)

    #: the item text
    text = Column(Text, nullable=False)

    #: true if paid
    paid = Column(Boolean, nullable=False, default=False)

    #: the transaction id if paid through a bank or online transaction
    tid = Column(Text, nullable=True)

    #: the source of the transaction id, e.g. stripe, xml
    source = Column(Text, nullable=True)

    #: the unit to pay..
    unit = Column(Numeric(precision=PRECISION, scale=SCALE), nullable=True)

    #: ..multiplied by the quantity..
    quantity = Column(Numeric(precision=PRECISION, scale=SCALE), nullable=True)

    #: ..together form the amount
    @hybrid_property
    def amount(self):
        return round(self.unit, SCALE) * round(self.quantity, SCALE)

    @amount.expression
    def amount(cls):
        return cls.unit * cls.quantity

    @validates('source')
    def validate_source(self, key, value):
        assert value in (None, 'xml', 'stripe_connect')
        return value
