from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import CreateInvoicesForm
from onegov.wtfs.layouts import InvoiceLayout
from onegov.wtfs.models import Invoice
from onegov.wtfs.security import ViewModel


@WtfsApp.form(
    model=Invoice,
    template='invoice.pt',
    permission=ViewModel,
    form=CreateInvoicesForm
)
def import_municipality_data(self, request, form):
    """ Import municipality data. """

    layout = InvoiceLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        data, count, total = self.export()

        return {
            'layout': layout,
            'result': True,
            'count': count,
            'total': total,
            'data': data
        }

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Create invoice"),
        'cancel': layout.cancel_url
    }
