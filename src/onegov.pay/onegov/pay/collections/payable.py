from onegov.core.collection import Pagination
from onegov.pay import Payment
from onegov.pay.utils import QueryChain
from sqlalchemy.orm import joinedload


class PayableCollection(Pagination):
    """ Provides a collection of all payable models. This collection is
    meant to be read-only, so there's no add/delete methods.

    To add payments to payable models just use the payment property and
    directly assign a new or an existing payment.

    """

    def __init__(self, session, cls='*', page=0):
        self.session = session
        self.cls = cls
        self.page = page

    @property
    def classes(self):
        if self.cls != '*':
            return (self.cls, )

        return tuple(link.cls for link in Payment.registered_links.values())

    def query(self):
        return QueryChain((
            self.session.query(cls).options(
                joinedload(cls.payment)
            )
            for cls in self.classes
        ))

    def __eq__(self, other):
        return self.cls == other.cls and self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, self.cls, index)
