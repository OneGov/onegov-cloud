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


def sync_invoice_items(items, capture=True):
    for item in (i for i in items if i.payments):
        if capture:
            for payment in item.payments:

                # though it should be fairly rare, it's possible for
                # charges not to be captured yet
                if payment.state == 'open':
                    payment.charge.capture()
                    payment.sync()

        # the last payment is the relevant one
        item.paid = item.payments[-1].state == 'paid'


class Invoice(Base, TimestampMixin):
    """ A grouping of invoice items. """

    __tablename__ = 'invoices'

    #: the public id of the invoice
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the period to which this invoice belongs to
    period_id = Column(UUID, ForeignKey('periods.id'), nullable=False)
    period = relationship(Period, backref='invoices')

    #: the user to which the invoice belongs
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    user = relationship(User, backref='invoices')

    #: the specific items linked with this invoice
    items = relationship(InvoiceItem, backref='invoice')

    @property
    def price(self):
        return Price(self.outstanding_amount, 'CHF')

    @property
    def has_donation(self):
        for item in self.items:
            if item.group == 'donation':
                return True

    def readable_by_bucket(self, bucket):
        for ref in self.references:
            if ref.bucket == bucket:
                return ref.readable

        return None

    def sync(self, capture=True):
        items = object_session(self).query(InvoiceItem).filter(and_(
            InvoiceItem.source != None,
            InvoiceItem.source != 'xml'
        )).options(joinedload(InvoiceItem.payments))

        sync_invoice_items(items, capture=capture)

    def add(self, group, text, unit, quantity, flush=True, **kwargs):
        item = InvoiceItem(
            group=group,
            text=text,
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
    def discourage_changes(self):
        return self.discourage_changes_for_items(self.items)

    @hybrid_property
    def disable_changes(self):
        return self.disable_changes_for_items(self.items)

    @hybrid_property
    def has_online_payments(self):
        return self.has_online_payments_for_items(self.items)

    def discourage_changes_for_items(self, items):
        for item in items:
            if item.source == 'xml':
                return True

        return False

    def disable_changes_for_items(self, items):
        for item in items:
            if not item.source:
                continue

            if item.source == 'xml':
                continue

            states = {p.state for p in item.payments}

            if 'open' in states or 'paid' in states:
                return True

    def has_online_payments_for_items(self, items):
        for item in items:
            if not item.source or item.source == 'xml':
                continue

            return True

    # paid or not
    @hybrid_property
    def paid(self):
        return self.outstanding_amount <= 0

    # paid + unpaid
    @hybrid_property
    def total_amount(self):
        return self.outstanding_amount + self.paid_amount

    @total_amount.expression
    def total_amount(cls):
        return select([func.sum(InvoiceItem.amount)]).\
            where(InvoiceItem.invoice_id == cls.id).\
            label('total_amount')

    # paid only
    @hybrid_property
    def outstanding_amount(self):
        return round(
            sum(item.amount for item in self.items if not item.paid),
            SCALE
        )

    @outstanding_amount.expression
    def outstanding_amount(cls):
        return select([func.sum(InvoiceItem.amount)]).\
            where(and_(
                InvoiceItem.invoice_id == cls.id,
                InvoiceItem.paid == False
            )).label('outstanding_amount')

    # unpaid only
    @hybrid_property
    def paid_amount(self):
        return round(
            sum(item.amount for item in self.items if item.paid),
            SCALE
        )

    @paid_amount.expression
    def paid_amount(cls):
        return select([func.sum(InvoiceItem.amount)]).\
            where(and_(
                InvoiceItem.invoice_id == cls.id,
                InvoiceItem.paid == True
            )).label('paid_amount')
