from onegov.core.collection import GenericCollection, Pagination
from onegov.pay.models import Payment
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import undefer


class PaymentCollection(GenericCollection, Pagination):
    """ Manages the payment records.

    To render a list of payments you might want to also consider the
    :class:`onegov.pay.collection.payable.Paybale` collection, which renders
    payments by loading the linked records first.

    """

    def __init__(self, session, source='*', page=0):
        super().__init__(session)
        self.source = source
        self.page = page

    @property
    def model_class(self):
        return Payment.get_polymorphic_class(self.source, Payment)

    def add(self, **kwargs):
        if self.source != '*':
            kwargs.setdefault('source', self.source)
        return super().add(**kwargs)

    def __eq__(self, other):
        return self.source == other.source and self.page == other.page

    def subset(self):
        q = self.query().order_by(desc(Payment.created))
        q = q.options(joinedload(Payment.provider))
        q = q.options(undefer(Payment.created))
        return q

    @property
    def page_index(self, page):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, self.source, index)
