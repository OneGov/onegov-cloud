from itertools import groupby
from onegov.activity import InvoiceItem, InvoiceItemCollection
from onegov.core.security import Personal, Secret
from onegov.core.templates import render_macro
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import BillingDetails
from onegov.feriennet.layout import InvoiceLayout
from onegov.feriennet.views.shared import all_users
from onegov.pay import process_payment
from sortedcontainers import SortedDict
from stdnum import iban
from sqlalchemy import nullsfirst
from uuid import UUID


@FeriennetApp.view(
    model=InvoiceItem,
    permission=Personal,
)
def redirect_to_invoice_view(self, request):
    return request.redirect(request.link(
        InvoiceItemCollection(
            request.session, username=self.username, invoice=self.invoice
        )
    ))


@FeriennetApp.view(
    model=InvoiceItem,
    permission=Secret,
    name='online-payments'
)
def view_creditcard_payments(self, request):
    return request.redirect(request.class_link(
        BillingCollection,
        {
            'username': self.username,
            'period_id': UUID(self.invoice)
        }, name='online-payments'
    ))


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
            nullsfirst(InvoiceItem.family),
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
    payment_provider = request.app.default_payment_provider
    layout = InvoiceLayout(self, request, title)

    def payment_button(title, price):
        price = payment_provider.adjust_price(price)

        label = ': '.join((
            request.translate(_("Pay Online Now")),
            render_macro(layout.macros['price'], layout.request, {
                'layout': layout,
                'price': price,
                'show_fee': True
            })
        ))

        return request.app.checkout_button(
            button_label=label,
            title=title,
            price=price,
            email=self.username,
            locale=request.locale
        )

    return {
        'title': title,
        'layout': layout,
        'users': users,
        'user': user,
        'bills': bills,
        'model': self,
        'account': account,
        'payment_provider': payment_provider,
        'payment_button': payment_button,
        'beneficiary': beneficiary
    }


@FeriennetApp.view(
    model=InvoiceItemCollection,
    template='invoices.pt',
    permission=Personal,
    request_method='POST')
def handle_payment(self, request):
    provider = request.app.default_payment_provider
    token = request.params.get('payment_token')
    period = request.params.get('period')

    q = self.query()
    q = q.filter(InvoiceItem.invoice == period)
    q = q.filter(InvoiceItem.paid == False)

    items = tuple(q)
    bill = BillingDetails(period, items)
    price = request.app.default_payment_provider.adjust_price(bill.price)
    payment = process_payment('cc', price, provider, token)

    if not payment:
        request.alert(_("Your payment could not be processed"))
    else:

        for item in items:
            item.payments.append(payment)
            item.paid = True
            item.source = provider.type

        request.success(_("Your payment has been received. Thank you!"))

    return request.redirect(request.link(self))
