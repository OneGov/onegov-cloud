from __future__ import annotations

from decimal import Decimal
from datetime import date
from markupsafe import Markup
from onegov.activity import (
    ActivityInvoiceItem, BookingPeriod, BookingPeriodCollection,
    BookingPeriodInvoice, BookingPeriodInvoiceCollection)
from onegov.core.security import Personal, Secret
from onegov.core.templates import render_macro
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.forms import DonationForm
from onegov.feriennet.layout import DonationLayout
from onegov.feriennet.layout import InvoiceLayout
from onegov.feriennet.qrbill import generate_qr_bill
from onegov.feriennet.views.shared import users_for_select_element
from onegov.pay import process_payment, PaymentError, INSUFFICIENT_FUNDS
from onegov.user import User
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import case
from stdnum import iban
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from onegov.pay import Price
    from webob import Response


@FeriennetApp.view(
    model=ActivityInvoiceItem,
    permission=Personal,
)
def redirect_to_invoice_view(
    self: ActivityInvoiceItem,
    request: FeriennetRequest
) -> Response:
    return request.redirect(
        request.link(
            BookingPeriodInvoiceCollection(
                request.session,
                user_id=self.invoice.user_id,
                period_id=self.invoice.period_id
            )
        )
    )


@FeriennetApp.view(
    model=ActivityInvoiceItem,
    permission=Secret,
    name='online-payments'
)
def view_creditcard_payments(
    self: ActivityInvoiceItem,
    request: FeriennetRequest
) -> Response:
    return request.redirect(request.class_link(
        BillingCollection,
        {
            'username': self.invoice.user.username,
            'period_id': self.invoice.period_id
        }, name='online-payments'
    ))


@FeriennetApp.html(
    model=BookingPeriodInvoiceCollection,
    template='invoices.pt',
    permission=Personal)
def view_my_invoices(
    self: BookingPeriodInvoiceCollection,
    request: FeriennetRequest
) -> RenderData | Response:

    payment_provider = request.app.default_payment_provider
    if payment_provider and payment_provider.payment_via_get:
        token = payment_provider.get_token(request)
        if token:
            return handle_payment(self, request, token)

    query = BookingPeriodCollection(request.session).query()
    query = query.filter(BookingPeriod.finalized == True)
    periods = {p.id.hex: p for p in query}

    # By default, we want to see all the invoices, unless a specific one
    # is selected. This is a bit of a code-smell, because we usually would
    # want to set that through the model in the path directive.
    show_all_invoices = 'invoice' not in request.params

    q = self.query(ignore_period_id=show_all_invoices is True)
    q = q.filter(BookingPeriodInvoice.period_id.in_(periods.keys()))
    q = q.outerjoin(BookingPeriod)
    q = q.outerjoin(ActivityInvoiceItem)
    q = q.options(contains_eager(BookingPeriodInvoice.items))
    q = q.order_by(
        BookingPeriod.execution_start,
        BookingPeriodInvoice.id,
        case(
            [
                (ActivityInvoiceItem.group == 'donation', 2),
                (ActivityInvoiceItem.family != None, 1),
            ],
            else_=0
        ),
        ActivityInvoiceItem.group,
        ActivityInvoiceItem.text
    )

    invoices = tuple(q)

    users = users_for_select_element(request)
    user = request.session.query(User).filter_by(id=self.user_id).one()

    assert request.current_user is not None
    if request.current_user.id == self.user_id:
        title = _('Invoices')
    else:
        title = _('Invoices of ${user}', mapping={
            'user': user.title
        })

    # make sure the invoice is set up with the latest configured reference,
    # which may result in a new reference record being added - this is done
    # ad-hoc on an invoice to invoice basis since we do not need a new
    # reference for an invoice that is never looked at
    for invoice in invoices:
        if not invoice.paid:
            self.schema.link(request.session, invoice)

    meta = request.app.org.meta
    if self.schema.name == 'feriennet-v1' or meta.get('bank_qr_bill'):
        account = meta.get('bank_account')
        account = account and iban.format(account)
    else:
        account = meta.get('bank_esr_participant_number')

    beneficiary = meta.get('bank_beneficiary')
    qr_bill_enabled = meta.get('bank_qr_bill', False)
    layout = InvoiceLayout(self, request, title)

    def payment_button(title: str, price: Price | None) -> str | None:
        assert payment_provider is not None
        assert request.locale is not None
        price = payment_provider.adjust_price(price)

        label = ': '.join((
            request.translate(_('Pay Online Now')),
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
            complete_url=request.link(self),
            request=request,
        )

    def user_select_link(user: User) -> str:
        return request.class_link(BookingPeriodInvoiceCollection, {
            'username': user.username,
        })

    def qr_bill(invoice: BookingPeriodInvoice) -> bytes | None:
        return generate_qr_bill(self.schema.name, request, user, invoice)

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
        'invoice_bucket': request.app.invoice_bucket(),
        'qr_bill': qr_bill if qr_bill_enabled else None,
    }


@FeriennetApp.view(
    model=BookingPeriodInvoiceCollection,
    template='invoices.pt',
    permission=Personal,
    request_method='POST')
def handle_payment(
    self: BookingPeriodInvoiceCollection,
    request: FeriennetRequest,
    token: str | None = None
) -> Response:

    provider = request.app.default_payment_provider
    assert provider is not None

    if token is None:
        token = provider.get_token(request)
    # FIXME: Can period actually be omitted, i.e. are there
    #        cases where we only get a single Invoice when we
    #        omit the period?
    period = request.params.get('period')
    assert period is None or isinstance(period, str)
    period_id = UUID(period) if period else None

    invoice = (
        self.for_period_id(period_id=period_id).query()
        .outerjoin(ActivityInvoiceItem)
        .one()
    )

    price = provider.adjust_price(invoice.price)
    assert price is not None
    payment = process_payment('cc', price, provider, token)

    if payment is INSUFFICIENT_FUNDS:
        request.alert(_('Your card has insufficient funds'))
    elif payment is None or isinstance(payment, PaymentError):
        request.alert(_('Your payment could not be processed'))
    else:
        for item in invoice.items:

            if item.paid:
                continue

            item.payments.append(payment)
            item.source = provider.type
            item.payment_date = date.today()
            item.paid = True

        request.success(_('Your payment has been received. Thank you!'))

    return request.redirect(request.link(self))


@FeriennetApp.form(
    model=BookingPeriodInvoiceCollection,
    form=DonationForm,
    template='donation.pt',
    permission=Personal,
    name='donation')
def handle_donation(
    self: BookingPeriodInvoiceCollection,
    request: FeriennetRequest,
    form: DonationForm
) -> RenderData | Response:

    assert request.current_user is not None
    if not self.user_id:
        return request.redirect(request.link(
            self.for_user_id(request.current_user.id),
            name='donation'
        ))

    if not self.period_id:
        assert request.app.active_period is not None
        return request.redirect(request.link(
            self.for_period_id(request.app.active_period.id),
            name='donation'
        ))

    if request.current_user.id == self.user_id:
        title = _('Donation')
    else:
        user = request.session.query(User).filter_by(id=self.user_id).one()
        title = _('Donation of ${user}', mapping={'user': user.title})

    period = request.app.periods_by_id[self.period_id.hex]
    bills = BillingCollection(request, period)

    if form.submitted(request):

        try:
            bills.include_donation(
                user_id=self.user_id,
                amount=Decimal(form.amount.data),
                text=request.translate(_('Donation')))
        except NoResultFound:
            request.alert(_('No invoice found'))
        else:
            request.success(_('Thank you for your donation'))
            return request.redirect(request.link(self))

    elif not request.POST:

        donation = (
            request.session.query(ActivityInvoiceItem)
            .filter(ActivityInvoiceItem.group == 'donation')
            .filter(
                ActivityInvoiceItem.invoice_id.in_(
                    request.session.query(BookingPeriodInvoice.id)
                    .filter(BookingPeriodInvoice.period_id == self.period_id)
                    .filter(BookingPeriodInvoice.user_id == self.user_id)
                )
            ).first()
        )

        if donation:
            amount = f'{donation.amount:.2f}'

            for key, value in form.amount.choices:  # type:ignore[misc]
                if key == amount:
                    form.amount.data = amount
                    break

    description = request.app.org.meta.get('donation_description', '').strip()
    # NOTE: We need treat this as Markup
    # TODO: It would be cleaner if we had a proxy object
    #       with all the settings as dict_property
    description = Markup(description)  # nosec: B704

    return {
        'title': title,
        'layout': DonationLayout(self, request, title),
        'form': form,
        'button_text': _('Donate'),
        'description': description,
    }


@FeriennetApp.view(
    model=BookingPeriodInvoiceCollection,
    permission=Personal,
    name='donation',
    request_method='DELETE')
def handle_delete_donation(
    self: BookingPeriodInvoiceCollection,
    request: FeriennetRequest
) -> None:

    assert self.user_id and self.period_id
    request.assert_valid_csrf_token()

    period = request.app.periods_by_id[self.period_id.hex]
    bills = BillingCollection(request, period)

    if bills.exclude_donation(self.user_id):
        request.success(_('Your donation was removed'))
    else:
        request.alert(_('This donation has already been paid'))
