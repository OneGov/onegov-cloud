from __future__ import annotations

from onegov.activity import ActivityInvoiceItem
from onegov.activity import BookingPeriodInvoiceCollection
from onegov.core.security import Private
from onegov.feriennet import FeriennetApp
from onegov.pay import PaymentProviderCollection
from onegov.pay.models.payment_providers.datatrans import DatatransPayment
from onegov.pay.models.payment_providers.stripe import StripePayment
from onegov.org.views.payment_provider import sync_payments
from onegov.org.views.payment import refund_datatrans, refund_stripe


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


@FeriennetApp.view(
    model=PaymentProviderCollection,
    name='sync',
    permission=Private)
def sync_payments_and_reconcile(
    self: PaymentProviderCollection,
    request: FeriennetRequest
) -> Response:

    result = sync_payments(self, request)

    # we keep two payment paid states, one in the invoice items table and one
    # in the payment (for online payments only).
    #
    # when syncing the payment states through the provider, we reconcile
    # those two states
    #
    # the reason we don't keep this all in the payment table is mainly a
    # performance one - we don't want to load the payments when rendering
    # the potentially large list of invoice items
    BookingPeriodInvoiceCollection(self.session).sync()

    return result


@FeriennetApp.view(
    model=StripePayment,
    name='refund',
    request_method='POST',
    permission=Private)
def refund_and_reconcile_stripe(
    self: StripePayment,
    request: FeriennetRequest
) -> None:

    result = refund_stripe(self, request)
    for link in self.links:
        if isinstance(link, ActivityInvoiceItem):
            link.paid = self.state == 'paid'

    return result


@FeriennetApp.view(
    model=DatatransPayment,
    name='refund',
    request_method='POST',
    permission=Private)
def refund_and_reconcile_datatrans(
    self: DatatransPayment,
    request: FeriennetRequest
) -> None:

    result = refund_datatrans(self, request)
    for link in self.links:
        if isinstance(link, ActivityInvoiceItem):
            link.paid = self.state == 'paid'

    return result
