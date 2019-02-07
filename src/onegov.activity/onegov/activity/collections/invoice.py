from cached_property import cached_property
from decimal import Decimal
from onegov.activity.models import Invoice, InvoiceItem
from onegov.core.collection import GenericCollection
from onegov.activity.utils import random_invoice_code
from sqlalchemy import func, and_, not_
from onegov.user import User


class InvoiceCollection(GenericCollection):

    def __init__(self, session, period_id=None, user_id=None):
        super().__init__(session)
        self.user_id = user_id
        self.period_id = period_id

    def query(self):
        q = super().query()

        if self.user_id:
            q = q.filter_by(user_id=self.user_id)

        if self.period_id is not None:
            q = q.filter_by(period_id=self.period_id)

        return q

    def query_items(self):
        return self.session.query(InvoiceItem)\
            .filter(InvoiceItem.invoice_id.in_(
                self.query().with_entities(Invoice.id).subquery()
            ))

    def for_user_id(self, user_id):
        return self.__class__(self.session, self.period_id, user_id)

    def for_period_id(self, period_id):
        return self.__class__(self.session, period_id, self.user_id)

    @cached_property
    def invoice(self):
        # XXX used for compatibility with legacy implementation in Feriennet
        return self.period_id and self.period_id.hex or None

    @cached_property
    def username(self):
        # XXX used for compatibility with legacy implementation in Feriennet
        if self.user_id:
            user = self.session.query(User)\
                .with_entities(User.username)\
                .filter_by(id=self.user_id)\
                .first()

            return user and user.username or None

    @property
    def model_class(self):
        return Invoice

    def _invoice_ids(self):
        return self.query().with_entities(Invoice.id).subquery()

    def _sum(self, condition):
        q = self.session.query(func.sum(InvoiceItem.amount).label('amount'))
        q = q.filter(condition)

        return Decimal(q.scalar() or 0.0)

    @property
    def total_amount(self):
        return self._sum(InvoiceItem.invoice_id.in_(self._invoice_ids()))

    @property
    def outstanding_amount(self):
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == False
        ))

    @property
    def paid_amount(self):
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == True
        ))

    def unpaid_count(self, excluded_period_ids=None):
        q = self.query().with_entities(func.count(Invoice.id))

        if excluded_period_ids:
            q = q.filter(not_(Invoice.period_id.in_(excluded_period_ids)))

        q = q.filter(Invoice.paid == False)

        return q.scalar() or 0

    def sync(self):
        for invoice in self.query():
            invoice.sync()

    def add(self, period_id=None, user_id=None, code=None):
        period_id = period_id or self.period_id
        user_id = user_id or self.user_id
        code = code or random_invoice_code()

        invoice = Invoice(period_id=period_id, user_id=user_id, code=code)
        self.session.add(invoice)
        self.session.flush()

        return invoice
