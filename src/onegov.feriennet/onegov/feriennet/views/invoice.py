from onegov.activity import InvoiceItem, InvoiceItemCollection
from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import InvoiceLayout
from onegov.feriennet.views.shared import all_users
from sortedcontainers import SortedDict


@FeriennetApp.html(
    model=InvoiceItemCollection,
    template='invoices.pt',
    permission=Personal)
def view_my_invoices(self, request):

    q = self.query()
    q = q.order_by(
        InvoiceItem.invoice,
        InvoiceItem.group,
        InvoiceItem.text
    )

    bills = SortedDict(lambda period: period.execution_start)

    users = all_users(request)
    user = next(u for u in users if u.username == self.username)

    if request.current_username == self.username:
        title = _("Invoices")
    else:
        title = _("Invoices of ${user}", mapping={
            'user': user.title
        })

    return {
        'title': title,
        'layout': InvoiceLayout(self, request, title),
        'users': users,
        'bills': bills
    }
