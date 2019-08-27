from morepath.request import Response
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import CreateInvoicesForm
from onegov.wtfs.layouts import InvoiceLayout
from onegov.wtfs.models import Invoice
from onegov.wtfs.security import ViewModel


@WtfsApp.form(
    model=Invoice,
    template='form.pt',
    permission=ViewModel,
    form=CreateInvoicesForm
)
def create_invoices(self, request, form):
    """ Create invoices and download them as CSV. """

    layout = InvoiceLayout(self, request)

    if form.submitted(request):
        form.update_model(self)

        response = Response(
            content_type='text/csv',
            content_disposition='inline; filename=rechnungen.csv'
        )
        self.export(response.body_file)
        return response

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Create invoice"),
        'cancel': layout.cancel_url
    }
