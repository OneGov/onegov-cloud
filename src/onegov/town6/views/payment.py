from __future__ import annotations

from onegov.core.security import Private
from onegov.form import merge_forms
from onegov.org.views.payment import (
    export_payments, handle_batch_set_payment_state,
    view_invoices, view_payments)
from onegov.org.forms import (
    DateRangeForm, ExportForm, PaymentSearchForm, TicketInvoiceSearchForm)
from onegov.pay import PaymentCollection
from onegov.ticket import TicketInvoiceCollection
from onegov.town6 import TownApp
from onegov.town6.layout import (
    PaymentCollectionLayout, TicketInvoiceCollectionLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response
    from onegov.core.types import RenderData
    from onegov.org.views.payment import PaymentExportForm
    from onegov.server.types import JSON_ro
    from onegov.town6.request import TownRequest


@TownApp.form(
    model=PaymentCollection,
    template='payments.pt',
    form=PaymentSearchForm,
    permission=Private
)
def town_view_payments(
    self: PaymentCollection,
    request: TownRequest,
    form: PaymentSearchForm
) -> RenderData | Response:
    layout = PaymentCollectionLayout(self, request)
    return view_payments(self, request, form, layout)


@TownApp.form(
    model=TicketInvoiceCollection,
    template='invoices.pt',
    form=TicketInvoiceSearchForm,
    permission=Private
)
def town_view_invoices(
    self: TicketInvoiceCollection,
    request: TownRequest,
    form: TicketInvoiceSearchForm
) -> RenderData | Response:
    layout = TicketInvoiceCollectionLayout(self, request)
    return view_invoices(self, request, form, layout)


@TownApp.json(
    model=PaymentCollection,
    name='batch-set-payment-state',
    request_method='POST',
    permission=Private
)
def town_handle_batch_set_payment_state(
    self: PaymentCollection,
    request: TownRequest
) -> JSON_ro:
    return handle_batch_set_payment_state(self, request)


@TownApp.form(
    model=PaymentCollection,
    name='export',
    template='form.pt',
    permission=Private,
    form=merge_forms(DateRangeForm, ExportForm)
)
def town_export_payments(
    self: PaymentCollection,
    request: TownRequest,
    form: PaymentExportForm
) -> RenderData | Response:
    return export_payments(
        self, request, form, PaymentCollectionLayout(self, request))
