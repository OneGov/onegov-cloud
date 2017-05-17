from itertools import groupby
from onegov.activity import InvoiceItem, InvoiceItemCollection
from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingDetails
from onegov.feriennet.layout import InvoiceLayout
from onegov.feriennet.views.shared import all_users
from sortedcontainers import SortedDict
from stdnum import iban


@FeriennetApp.html(
    model=InvoiceItemCollection,
    template='invoices.pt',
    permission=Personal)
def view_my_invoices(self, request):

    periods = {p.id.hex: p for p in request.app.periods if p.finalized}
    bills = SortedDict(lambda period: period.execution_start)

    if periods:
        q = self.query()
        q = q.order_by(
            InvoiceItem.invoice,
            InvoiceItem.group,
            InvoiceItem.text
        )
        q = q.filter(InvoiceItem.invoice.in_(periods.keys()))

        for period_hex, items in groupby(q, lambda i: i.invoice):
            billing_period = periods[period_hex]
            bills[billing_period] = BillingDetails(billing_period.title, items)

    users = all_users(request)
    user = next(u for u in users if u.username == self.username)

    if request.current_username == self.username:
        title = _("Invoices")
    else:
        title = _("Invoices of ${user}", mapping={
            'user': user.title
        })

    if request.app.org.bank_payment_order_type == 'esr':
        account = request.app.org.bank_esr_participant_number
    else:
        account = request.app.org.bank_account
        account = account and iban.format(account)

    beneficiary = request.app.org.bank_beneficiary

    return {
        'title': title,
        'layout': InvoiceLayout(self, request, title),
        'users': users,
        'user': user,
        'bills': bills,
        'model': self,
        'account': account,
        'beneficiary': beneficiary
    }
