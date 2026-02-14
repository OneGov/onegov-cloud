from __future__ import annotations

from datetime import date
from decimal import Decimal
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.pay.models.payable import PayableManyTimes
from onegov.pay.constants import PRECISION, SCALE
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.orm import validates
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay.models import Invoice
    from sqlalchemy.sql import ColumnElement


class InvoiceItem(Base, TimestampMixin, PayableManyTimes):
    """ An item in an invoice. """

    __tablename__ = 'invoice_items'

    #: the polymorphic type of the invoice item
    type: Mapped[str] = mapped_column(default=lambda: 'generic')
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    #: the public id of the invoice item
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the invoice this item belongs to
    # FIXME: Shouldn't this be nullable=False?
    invoice_id: Mapped[UUID | None] = mapped_column(ForeignKey('invoices.id'))
    invoice: Mapped[Invoice] = relationship(
        'Invoice',
        back_populates='items'
    )

    #: the item group (all items with the same text are visually grouped)
    group: Mapped[str]

    #: a secondary group who is not necessarily grouped visually
    family: Mapped[str | None]

    #: the cost center / cost unit identifier of this invoice item
    cost_object: Mapped[str | None]

    #: the item text
    text: Mapped[str]

    #: true if paid
    paid: Mapped[bool] = mapped_column(default=False)

    #: the payment date
    payment_date: Mapped[date | None]

    #: the transaction id if paid through a bank or online transaction
    tid: Mapped[str | None]

    #: the source of the transaction id, e.g. stripe, xml
    source: Mapped[str | None]

    #: the unit to pay..
    # FIXME: I don't think this should be nullable
    unit: Mapped[Decimal] = mapped_column(
        Numeric(precision=PRECISION, scale=SCALE),
        nullable=True
    )

    #: ..multiplied by the quantity..
    # FIXME: and neither should this be
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=PRECISION, scale=SCALE),
        nullable=True
    )

    #: ..together form the amount
    @hybrid_property
    def amount(self) -> Decimal:
        if self.unit is None or self.quantity is None:
            return None  # type: ignore[unreachable]
        return round(
            round(self.unit, SCALE) * round(self.quantity, SCALE),
            SCALE
        )

    @amount.inplace.expression
    @classmethod
    def _amount_expression(cls) -> ColumnElement[Decimal]:
        return cls.unit * cls.quantity

    #: the VAT factor (`net_amount` times the factor yields `amount`)
    vat_factor: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=True
    )

    @property
    def vat_rate(self) -> Decimal | None:
        """ A convenience attribute to access/set the VAT rate in % """
        if self.vat_factor is None:
            return None
        return round((self.vat_factor - Decimal('1')) * Decimal('100'), 2)

    @vat_rate.setter
    def vat_rate(self, value: Decimal | None) -> None:
        if value is None:
            self.vat_factor = None
        else:
            self.vat_factor = round(
                (value + Decimal('100')) / Decimal('100'),
                4
            )

    @property
    def vat(self) -> Decimal:
        return self.amount - self.net_amount

    @property
    def net_amount(self) -> Decimal:
        if self.vat_factor is None:
            return self.amount
        return round(self.amount / self.vat_factor, SCALE)

    @validates('source')
    def validate_source(self, key: str, value: str | None) -> str | None:
        assert value in (
            None,
            'xml',
            'datatrans',
            'stripe_connect',
            'worldline_saferpay'
        )
        return value
