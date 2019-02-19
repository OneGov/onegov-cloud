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
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, object_session, relationship
from sqlalchemy.schema import FetchedValue
from uuid import uuid4


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

    #: deprecated reference field -> remove in Feriennet 1.6
    code = deferred(Column(Text, FetchedValue(), nullable=True))

    #: the specific items linked with this invoice
    items = relationship(InvoiceItem, backref='invoice')

    @property
    def price(self):
        return Price(self.outstanding_amount, 'CHF')

    def readable_by_bucket(self, bucket):
        for ref in self.references:
            if ref.bucket == bucket:
                return ref.readable

        return None

    def sync(self):
        items = object_session(self).query(InvoiceItem).filter(and_(
            InvoiceItem.source != None,
            InvoiceItem.source != 'xml'
        )).join(InvoiceItem.payments)

        for item in (i for i in items if i.payments):
            for payment in item.payments:

                # though it should be fairly rare, it's possible for
                # charges not to be captured yet
                if payment.state == 'open':
                    payment.charge.capture()
                    payment.sync()

            # the last payment is the relevant one
            item.paid = item.payments[-1].state == 'paid'

    def add(self, group, text, unit, quantity, **kwargs):
        item = InvoiceItem(
            group=group,
            text=text,
            unit=unit,
            quantity=quantity,
            invoice_id=self.id,
            **kwargs
        )

        self.items.append(item)
        object_session(self).flush()

        return item

    @hybrid_property
    def discourage_changes(self):
        for item in self.items:
            if item.source == 'xml':
                return True

        return False

    @hybrid_property
    def disable_changes(self):
        for item in self.items:
            if not item.source:
                continue

            if item.source == 'xml':
                continue

            states = {p.state for p in item.payments}

            if 'open' in states or 'paid' in states:
                return True

    @hybrid_property
    def has_online_payments(self):
        for item in self.items:
            if not item.source or item.source == 'xml':
                continue

            True

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
