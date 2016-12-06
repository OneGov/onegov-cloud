from decimal import Decimal
from onegov.activity import InvoiceItemCollection


class BillingCollection(object):

    def __init__(self, session, period):
        self.session = session
        self.period = period

        self.invoice_items = InvoiceItemCollection(
            session=session,
            invoice=self.period.id.hex
        )

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period)

    @property
    def bills(self):
        return []

    @property
    def total(self):
        return self.invoice_items.total or Decimal("0.00")

    @property
    def outstanding(self):
        return self.invoice_items.outstanding or Decimal("0.00")
