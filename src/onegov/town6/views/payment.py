from onegov.core.security import Private
from onegov.form import merge_forms
from onegov.org.views.payment import view_payments, export_payments
from onegov.town6 import TownApp
from onegov.org.forms import DateRangeForm, ExportForm

from onegov.pay import PaymentCollection
from onegov.town6.layout import PaymentCollectionLayout


@TownApp.html(
    model=PaymentCollection,
    template='payments.pt',
    permission=Private)
def town_view_payments(self, request):
    return view_payments(self, request, PaymentCollectionLayout(self, request))


@TownApp.form(
    model=PaymentCollection,
    name='export',
    template='form.pt',
    permission=Private,
    form=merge_forms(DateRangeForm, ExportForm))
def town_export_payments(self, request, form):
    return export_payments(
        self, request, form, PaymentCollectionLayout(self, request))
