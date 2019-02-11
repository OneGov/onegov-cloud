from onegov.activity import Period, Invoice, InvoiceItem, InvoiceCollection
from onegov.core.security import Personal, Secret
from onegov.core.templates import render_macro
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.layout import InvoiceLayout
from onegov.feriennet.views.shared import users_for_select_element
from onegov.pay import process_payment
from onegov.user import User
from stdnum import iban
from sqlalchemy import nullsfirst
from sqlalchemy.orm import contains_eager


@FeriennetApp.view(
    model=InvoiceItem,
    permission=Personal,
)
def redirect_to_invoice_view(self, request):
    return request.redirect(
        request.link(
            InvoiceCollection(
                request.session,
                user_id=self.invoice.user_id,
                period_id=self.invoice.period_id
            )
        )
    )


@FeriennetApp.view(
    model=InvoiceItem,
    permission=Secret,
    name='online-payments'
)
def view_creditcard_payments(self, request):
    return request.redirect(request.class_link(
        BillingCollection,
        {
            'username': self.invoice.user.username,
            'period_id': self.invoice.period_id
        }, name='online-payments'
    ))


@FeriennetApp.html(
    model=InvoiceCollection,
    template='invoices.pt',
    permission=Personal)
def view_my_invoices(self, request):
    periods = {p.id.hex: p for p in request.app.periods if p.finalized}

    q = self.query()
    q = q.filter(Invoice.period_id.in_(periods.keys()))
    q = q.outerjoin(Period)
    q = q.outerjoin(InvoiceItem)
    q = q.options(contains_eager(Invoice.items))
    q = q.order_by(
        Period.execution_start,
        Invoice.id,
        nullsfirst(InvoiceItem.family),
        InvoiceItem.group,
        InvoiceItem.text
    )

    invoices = tuple(q)

    users = users_for_select_element(request)
    user = request.session.query(User).filter_by(id=self.user_id).first()

    if request.current_user.id == self.user_id:
        title = _("Invoices")
    else:
        title = _("Invoices of ${user}", mapping={
            'user': user.title
        })

    # make sure the invoice is set up with the latest configured reference,
    # which may result in a new reference record being added - this is done
    # ad-hoc on an invoice to invoice basis since we do not need a new
    # reference for an invoice that is never looked at
    for invoice in invoices:
        if not invoice.paid:
            self.schema.link(request.session, invoice)

    if self.schema.name == 'feriennet-v1':
        account = request.app.org.meta.get('bank_account')
        account = account and iban.format(account)
    else:
        account = request.app.org.meta.get('bank_esr_participant_number')

    beneficiary = request.app.org.meta.get('bank_beneficiary')
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
            email=user.username,
            locale=request.locale
        )

    def user_select_link(user):
        return request.class_link(InvoiceCollection, {
            'username': user.username,
        })

    return {
        'title': title,
        'layout': layout,
        'users': users,
        'user': user,
        'user_select_link': user_select_link,
        'invoices': invoices,
        'model': self,
        'account': account,
        'payment_provider': payment_provider,
        'payment_button': payment_button,
        'beneficiary': beneficiary,
        'invoice_bucket': request.app.invoice_bucket()
    }


@FeriennetApp.view(
    model=InvoiceCollection,
    template='invoices.pt',
    permission=Personal,
    request_method='POST')
def handle_payment(self, request):
    provider = request.app.default_payment_provider
    token = request.params.get('payment_token')
    period = request.params.get('period')

    invoice = self.for_period_id(period_id=period).query()\
        .outerjoin(InvoiceItem)\
        .one()

    price = request.app.default_payment_provider.adjust_price(invoice.price)
    payment = process_payment('cc', price, provider, token)

    if not payment:
        request.alert(_("Your payment could not be processed"))
    else:
        for item in invoice.items:

            if item.paid:
                continue

            item.payments.append(payment)
            item.source = provider.type
            item.paid = True

        request.success(_("Your payment has been received. Thank you!"))

    return request.redirect(request.link(self))
