from collections import defaultdict
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

    def payment_links_by_batch(self, batch=None):
        """ A more efficient way of loading all links of the given batch
        (compared to loading payment.links one by one).

        """

        batch = batch or self.batch

        if not batch:
            return None

        payment_links = defaultdict(list)

        for link in Payment.registered_links.values():
            targets = self.session.query(
                getattr(link.table.columns, link.key)
            ).filter(
                link.table.columns.payment_id.in_(tuple(
                    p.id for p in self.batch
                ))
            )

            q = self.session.query(link.cls)
            q = q.filter(link.cls.id.in_(targets.subquery()))
            q = q.options(joinedload(link.cls.payment))

            for link in q:
                payment_links[link.payment.id].append(link)

        return payment_links
