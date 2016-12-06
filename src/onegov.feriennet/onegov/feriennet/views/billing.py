from onegov.activity import Period, PeriodCollection
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.layout import BillingCollectionLayout


def all_periods(request):
    p = PeriodCollection(request.app.session()).query()
    p = p.order_by(Period.execution_start)
    return p.all()


@FeriennetApp.html(
    model=BillingCollection,
    template='billing.pt',
    permission=Secret)
def view_billing(self, request):
    layout = BillingCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': _("Billing for ${title}", mapping={
            'title': self.period.title
        }),
        'model': self,
        'period': self.period,
        'periods': all_periods(request),
    }
