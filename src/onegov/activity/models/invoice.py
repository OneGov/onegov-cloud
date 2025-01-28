from __future__ import annotations

from onegov.activity.models.invoice_item import InvoiceItem, SCALE
from onegov.activity.models.period import Period
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay import Price
from onegov.user import User
from sqlalchemy import and_
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session, relationship, joinedload
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable
    from decimal import Decimal
    from onegov.activity.models import InvoiceReference
    from sqlalchemy.sql import ColumnElement


def sync_invoice_items(
    items: Iterable[InvoiceItem],
    capture: bool = True
) -> None:

    for item in items:
        if not item.payments:
            continue

        if capture:
            for payment in item.payments:

                # though it should be fairly rare, it's possible for
                # charges not to be captured yet
                if payment.state == 'open':
                    # FIXME: This only works for StripePayment, should we
                    #        check that we got a StripePayment?
                    payment.charge.capture()  # type:ignore[attr-defined]
                    payment.sync()

        # the last payment is the relevant one
        item.paid = item.payments[-1].state == 'paid'


class Invoice(Base, TimestampMixin):
    """ A grouping of invoice items. """

    __tablename__ = 'invoices'

    #: the public id of the invoice
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the period to which this invoice belongs to
    period_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('periods.id'),
        nullable=False
    )
    period: relationship[Period] = relationship(
        Period,
        back_populates='invoices'
    )

    #: the user to which the invoice belongs
    user_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('users.id'),
        nullable=False
    )
    # FIXME: Do we need this backref? It's across module boundaries, so
    #        not the best for proper module isolation
    user: relationship[User] = relationship(User, backref='invoices')

    #: the specific items linked with this invoice
    items: relationship[list[InvoiceItem]] = relationship(
        InvoiceItem,
        back_populates='invoice'
    )

    #: the references pointing to this invoice
    references: relationship[list[InvoiceReference]] = relationship(
        'InvoiceReference',
        back_populates='invoice',
        cascade='all, delete-orphan'
    )

    @property
    def price(self) -> Price:
        return Price(self.outstanding_amount, 'CHF')

    @property
    def has_donation(self) -> bool:
        for item in self.items:
            if item.group == 'donation':
                return True
        return False

    def readable_by_bucket(self, bucket: str) -> str | None:
        for ref in self.references:
            if ref.bucket == bucket:
                return ref.readable

        return None

    def sync(self, capture: bool = True) -> None:
        items = object_session(self).query(InvoiceItem).filter(and_(
            InvoiceItem.source != None,
            InvoiceItem.source != 'xml'
        )).options(joinedload(InvoiceItem.payments))

        sync_invoice_items(items, capture=capture)

    def add(
        self,
        group: str,
        text: str,
        unit: Decimal,
        quantity: Decimal,
        organizer: str = '',
        attendee_id: uuid.UUID | None = None,
        flush: bool = True,
        **kwargs: Any  # FIXME: type safety for optional arguments
    ) -> InvoiceItem:

        item = InvoiceItem(
            group=group,
            attendee_id=attendee_id,
            text=text,
            organizer=organizer,
            unit=unit,
            quantity=quantity,
            invoice_id=self.id,
            **kwargs
        )

        self.items.append(item)

        if flush:
            object_session(self).flush()

        return item

    @hybrid_property
    def discourage_changes(self) -> bool:
        return self.discourage_changes_for_items(self.items)

    @hybrid_property
    def disable_changes(self) -> bool:
        return self.disable_changes_for_items(self.items)

    @hybrid_property
    def has_online_payments(self) -> bool:
        return self.has_online_payments_for_items(self.items)

    def discourage_changes_for_items(
        self,
        items: Iterable[InvoiceItem]
    ) -> bool:
        for item in items:
            if item.source == 'xml':
                return True

        return False

    def disable_changes_for_items(
        self,
        items: Iterable[InvoiceItem]
    ) -> bool:
        for item in items:
            if not item.source:
                continue

            if item.source == 'xml':
                continue

            states = {p.state for p in item.payments}

            if 'open' in states or 'paid' in states:
                return True
        return False

    def has_online_payments_for_items(
        self,
        items: Iterable[InvoiceItem]
    ) -> bool:
        for item in items:
            if not item.source or item.source == 'xml':
                continue

            return True
        return False

    if TYPE_CHECKING:
        paid: Column[bool]
        total_amount: Column[Decimal]
        outstanding_amount: Column[Decimal]
        paid_amount: Column[Decimal]

    # paid or not
    @hybrid_property  # type:ignore[no-redef]
    def paid(self) -> bool:
        return self.outstanding_amount <= 0

    # paid + unpaid
    @hybrid_property  # type:ignore[no-redef]
    def total_amount(self) -> Decimal:
        return self.outstanding_amount + self.paid_amount

    @total_amount.expression  # type:ignore[no-redef]
    def total_amount(cls) -> ColumnElement[Decimal]:
        return select([func.sum(InvoiceItem.amount)]).where(
            InvoiceItem.invoice_id == cls.id
        ).label('total_amount')

    # paid only
    @hybrid_property  # type:ignore[no-redef]
    def outstanding_amount(self):
        return round(
            sum(item.amount for item in self.items if not item.paid),
            SCALE
        )

    @outstanding_amount.expression  # type:ignore[no-redef]
    def outstanding_amount(cls):
        return select([func.sum(InvoiceItem.amount)]).where(
            and_(
                InvoiceItem.invoice_id == cls.id,
                InvoiceItem.paid == False
            )
        ).label('outstanding_amount')

    # unpaid only
    @hybrid_property  # type:ignore[no-redef]
    def paid_amount(self) -> Decimal:
        return round(
            sum(item.amount for item in self.items if item.paid),
            SCALE
        )

    @paid_amount.expression  # type:ignore[no-redef]
    def paid_amount(cls) -> ColumnElement[Decimal]:
        return select([func.sum(InvoiceItem.amount)]).where(
            and_(
                InvoiceItem.invoice_id == cls.id,
                InvoiceItem.paid == True
            )
        ).label('paid_amount')
