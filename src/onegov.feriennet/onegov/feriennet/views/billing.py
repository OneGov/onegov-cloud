from onegov.activity import Period, PeriodCollection
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.forms import BillingForm
from onegov.feriennet.layout import BillingCollectionLayout


def all_periods(request):
    p = PeriodCollection(request.app.session()).query()
    p = p.order_by(Period.execution_start)
    return p.all()


@FeriennetApp.form(
    model=BillingCollection,
    form=BillingForm,
    template='billing.pt',
    permission=Secret)
def view_billing(self, request, form):
    layout = BillingCollectionLayout(self, request)

    if form.submitted(request):
        self.create_invoices(
            all_inclusive_booking_text=request.translate(_("Passport"))
        )

    return {
        'layout': layout,
        'title': _("Billing for ${title}", mapping={
            'title': self.period.title
        }),
        'model': self,
        'period': self.period,
        'periods': all_periods(request),
        'total': self.total,
        'form': form,
        'outstanding': self.outstanding,
        'button_text': _("Create Bills")
    }
