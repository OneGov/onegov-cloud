from __future__ import annotations

from onegov.core.security import Private
from onegov.form import merge_forms
from onegov.org.views.payment import generate_payments_pdf, handle_batch_mark_payments_invoiced
from onegov.org.views.payment import view_payments
from onegov.org.views.payment import export_payments
from onegov.town6 import TownApp
from onegov.org.forms.payments_search_form import PaymentSearchForm
from onegov.org.forms import DateRangeForm, ExportForm

from onegov.pay import PaymentCollection
from onegov.town6.layout import PaymentCollectionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.views.payment import PaymentExportForm
    from onegov.server.types import JSON_ro
    from onegov.town6.request import TownRequest
    from webob import Response


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
) -> RenderData:
    return view_payments(self, request, form,
                         PaymentCollectionLayout(self, request))


@TownApp.json(
    model=PaymentCollection,
    name='batch-mark-invoiced',
    request_method='POST',
    permission=Private
)
def town_handle_batch_mark_payments_invoiced(
    self: PaymentCollection,
    request: TownRequest
) -> JSON_ro:
    return handle_batch_mark_payments_invoiced(self, request)


@TownApp.view(
    model=PaymentCollection,
    name='generate-payments-pdf',
    permission=Private
)
def town_generate_payments_pdf(
    self: PaymentCollection,
    request: TownRequest
) -> Response:
    return generate_payments_pdf(self, request)


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
