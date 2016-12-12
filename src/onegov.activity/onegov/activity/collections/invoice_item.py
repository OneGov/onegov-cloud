from onegov.activity.models import InvoiceItem
from onegov.core.collection import GenericCollection
from sqlalchemy import func, not_


class InvoiceItemCollection(GenericCollection):

    def __init__(self, session, username=None, invoice=None):
        super().__init__(session)
        self.username = username
        self.invoice = invoice

    def query(self):
        query = super().query()

        if self.username is not None:
            query = query.filter(self.model_class.username == self.username)

        if self.invoice is not None:
            query = query.filter(self.model_class.invoice == self.invoice)

        return query

    def for_username(self, username):
        return self.__class__(self.session, username, self.invoice)

    def for_invoice(self, invoice):
        return self.__class__(self.session, self.username, invoice)

    @property
    def model_class(self):
        return InvoiceItem

    @property
    def total(self):
        q = self.query()
        q = q.with_entities(func.sum(InvoiceItem.amount))

        return q.scalar()

    @property
    def outstanding(self):
        q = self.query()
        q = q.filter(InvoiceItem.paid == False)
        q = q.with_entities(func.sum(InvoiceItem.amount))

        return q.scalar()

    def count_unpaid_invoices(self, exclude_invoices=None):
        q = self.query()
        q = q.with_entities(func.count(func.distinct(InvoiceItem.invoice)))
        q = q.filter(InvoiceItem.paid == False)

        if exclude_invoices:
            q = q.filter(not_(InvoiceItem.invoice.in_(exclude_invoices)))

        return q.scalar()

    def add(self, user, invoice, group, text, unit, quantity):
        if isinstance(user, str):
            username = user
        else:
            username = user.username

        return super().add(
            username=username,
            invoice=invoice,
            group=group,
            text=text,
            unit=unit,
            quantity=quantity
        )
