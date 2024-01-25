from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay import PayableManyTimes
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from decimal import Decimal
    from onegov.activity.models import Invoice
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import ColumnElement


# total digits
PRECISION = 8

# digits after the point
SCALE = 2


class InvoiceItem(Base, TimestampMixin, PayableManyTimes):
    """ An item in an invoice. """

    __tablename__ = 'invoice_items'

    #: the public id of the invoice item
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the invoice this item belongs to
    # FIXME: Shouldn't this be nullable=False?
    invoice_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('invoices.id')
    )

    #: the attendee, if the item is connected to an attendee
    attendee_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('attendees.id'),
        nullable=True
    )

    #: the item group (all items with the same text are visually grouped)
    group: 'Column[str]' = Column(Text, nullable=False)

    #: a secondary group who is not necessarily grouped visually
    family: 'Column[str | None]' = Column(Text, nullable=True)

    #: the item text
    text: 'Column[str]' = Column(Text, nullable=False)

    #: organizer (if the item is an activity)
    organizer: 'Column[str | None]' = Column(Text, nullable=True)

    #: true if paid
    paid: 'Column[bool]' = Column(Boolean, nullable=False, default=False)

    #: the payment date
    payment_date: 'Column[date | None]' = Column(Date, nullable=True)

    #: the transaction id if paid through a bank or online transaction
    tid: 'Column[str | None]' = Column(Text, nullable=True)

    #: the source of the transaction id, e.g. stripe, xml
    source: 'Column[str | None]' = Column(Text, nullable=True)

    #: the unit to pay..
    # FIXME: I don't think this should be nullable
    unit: 'Column[Decimal | None]' = Column(
        Numeric(precision=PRECISION, scale=SCALE),
        nullable=True
    )

    #: ..multiplied by the quantity..
    # FIXME: and neither should this be
    quantity: 'Column[Decimal | None]' = Column(
        Numeric(precision=PRECISION, scale=SCALE),
        nullable=True
    )

    if TYPE_CHECKING:
        # FIXME: Use explicit backref with back_populates
        invoice: relationship[Invoice]
        amount: Column[Decimal]

    #: ..together form the amount
    @hybrid_property  # type: ignore[no-redef]
    def amount(self) -> 'Decimal | None':
        if self.unit is None or self.quantity is None:
            return None
        return round(self.unit, SCALE) * round(self.quantity, SCALE)

    @amount.expression  # type:ignore[no-redef]
    def amount(cls) -> 'ColumnElement[Decimal | None]':
        return cls.unit * cls.quantity

    @validates('source')
    def validate_source(self, key: str, value: str | None) -> str | None:
        assert value in (None, 'xml', 'stripe_connect')
        return value
