from onegov.activity import InvoiceItemCollection, InvoiceItem
from onegov.core.security import Private
from onegov.feriennet import FeriennetApp
from onegov.pay import Payment, PaymentProviderCollection
from onegov.org.views.payment_provider import sync_payments
from onegov.org.views.payment import refund


@FeriennetApp.view(
    model=PaymentProviderCollection,
    name='sync',
    permission=Private)
def sync_payments_and_reconcile(self, request):
    result = sync_payments(self, request)

    # we keep two payment paid states, one in the invoice items table and one
    # in the payment (for online payments only).
    #
    # when synching the payment states through the provider, we reconclie
    # those two states
    #
    # the reason we don't keep this all in the payment table is mainly a
    # performance one - we don't want to load the payments when rendering
    # the potentially large list of invoice items
    InvoiceItemCollection(self.session).sync()

    return result


@FeriennetApp.view(
    model=Payment,
    name='refund',
    request_method='POST',
    permission=Private)
def refund_and_reconcile(self, request):
    result = refund(self, request)

    for link in self.links:
        if isinstance(link, InvoiceItem):
            link.paid = self.state == 'paid'

    return result
