from __future__ import annotations

from decimal import Decimal
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay.constants import SCALE
from onegov.pay.models.invoice_item import InvoiceItem
from onegov.pay.utils import Price
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session, relationship, joinedload
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable
    from onegov.pay.models import InvoiceReference
    from sqlalchemy.sql import ColumnElement


# TODO: We may no longer need this, since `Payment.sync` should already
#       keep the invoice items updated. But we'll keep it for now just
#       in case.
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
                    payment.sync(capture=True, update_invoice_items=False)

        # the last payment is the relevant one
        item.paid = item.payments[-1].state == 'paid'


class Invoice(Base, TimestampMixin):
    """ A grouping of invoice items. """

    __tablename__ = 'invoices'

    #: the polymorphic type of the invoice
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    #: the public id of the invoice
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the entity the invoice is created for
    invoicing_party: Column[str | None] = Column(Text, nullable=True)

    #: true if invoiced
    invoiced: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

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

    # NOTE: Since period_id and user_id will exist for all polymorphic
    #       identities we need a CHECK constraint instead of NOT NULLABLE
    #       constaints on the columns.
    __table_args__ = (
        CheckConstraint(
            '(period_id IS NOT NULL AND user_id IS NOT NULL) '
            "OR type != 'booking_period'",
            name='ck_booking_period_required_columns'
        ),
    )

    @property
    def price(self) -> Price:
        return Price(self.outstanding_amount, 'CHF')

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
        *,
        type: str = 'generic',
        family: str | None = None,
        cost_object: str | None = None,
        vat_rate: Decimal | None = None,
        tid: str | None = None,
        source: str | None = None,
        flush: bool = True,
        **kwargs: Any,
    ) -> InvoiceItem:

        item = InvoiceItem.get_polymorphic_class(type)(
            group=group,
            family=family,
            cost_object=cost_object,
            text=text,
            unit=unit,
            quantity=quantity,
            invoice_id=self.id,
            **kwargs
        )
        item.vat_rate = vat_rate

        self.items.append(item)

        if flush:
            object_session(self).flush()

        return item

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
    def outstanding_amount(self) -> Decimal:
        return round(
            sum(
                (item.amount for item in self.items if not item.paid),
                start=Decimal('0')
            ),
            SCALE
        )

    @outstanding_amount.expression  # type:ignore[no-redef]
    def outstanding_amount(cls) -> ColumnElement[Decimal]:
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
            sum(
                (item.amount for item in self.items if item.paid),
                start=Decimal('0')
            ),
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

    @property
    def total_excluding_manual_entries(self) -> Decimal:
        return round(
            sum(
                (item.amount for item in self.items if item.group != 'manual'),
                start=Decimal('0')
            ),
            SCALE
        )

    @property
    def total_vat(self) -> Decimal:
        return round(
            sum(
                (item.vat for item in self.items),
                start=Decimal('0')
            ),
            SCALE
        )
