from __future__ import annotations

from collections import OrderedDict
from onegov.core.security import Private
from onegov.core.utils import append_query_param
from onegov.form import merge_forms
from onegov.org import OrgApp, _
from onegov.org.forms import DateRangeForm, ExportForm
from onegov.org.forms.payments_search_form import PaymentSearchForm
from onegov.org.layout import PaymentCollectionLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import PaymentMessage
from onegov.core.elements import Link
from sedate import align_range_to_day, standardize_date, as_datetime
from onegov.org.pdf.ticket import TicketsPdf
from onegov.pay import Payment
from onegov.pay import PaymentCollection
from onegov.pay import PaymentProviderCollection
from onegov.pay.errors import DatatransApiError, SaferpayApiError
from onegov.pay.models.payment import ManualPayment
from onegov.pay.models.payment_providers.datatrans import DatatransPayment
from onegov.pay.models.payment_providers.stripe import StripePayment
from onegov.pay.models.payment_providers.worldline_saferpay import (
    SaferpayPayment)
from onegov.ticket import Ticket
from webob.response import Response
from webob import exc, Response as WebobResponse


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest
    from onegov.pay.types import AnyPayableBase
    from sqlalchemy.orm import Session
    from typing import type_check_only
    from webob import Response

    @type_check_only
    class PaymentExportForm(DateRangeForm, ExportForm):
        pass


EMAIL_SUBJECTS = {
    'marked-as-paid': _('Your payment has been received'),
    'marked-as-unpaid': _('Your payment has been withdrawn'),
    'refunded': _('Your payment has been refunded')
}


def send_ticket_notifications(
    payment: Payment,
    request: OrgRequest,
    change: str
) -> None:

    ticket = payment.ticket

    if not ticket:
        return

    # create a notification in the chat
    PaymentMessage.create(payment, ticket, request, change)

    if change == 'captured':
        return

    # send an e-mail
    email = ticket.snapshot.get('email') or ticket.handler.email
    assert email is not None

    send_ticket_mail(
        request=request,
        template='mail_payment_change.pt',
        subject=EMAIL_SUBJECTS[change],
        receivers=(email, ),
        ticket=ticket,
        content={
            'model': ticket,
            'payment': payment,
            'change': change
        }
    )


def handle_pdf_response(
    self: PaymentCollection,
    request: OrgRequest
) -> WebobResponse:
    # Export a pdf of all invoiced, without pagination limit
    all_payments = list(self.by_state('invoiced').subset())

    if not all_payments:
        request.warning(_('No payments found for PDF generation'))
        return request.redirect(request.class_link(PaymentCollection))

    payment_ids = [p.id for p in all_payments]
    tickets = self.session.query(Ticket).filter(
        Ticket.payment_id.in_(payment_ids)
    ).all()

    if not tickets:
        request.warning(_('No tickets found for PDF generation'))
        return request.redirect(request.class_link(PaymentCollection))

    filename = 'Payments.pdf'
    multi_pdf = TicketsPdf.from_tickets(request, tickets)
    return Response(
        multi_pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}'
    )


@OrgApp.form(
    model=PaymentCollection,
    template='payments.pt',
    form=PaymentSearchForm,
    permission=Private
)
def view_payments(
    self: PaymentCollection,
    request: OrgRequest,
    form: PaymentSearchForm,
    layout: PaymentCollectionLayout | None = None
) -> RenderData | WebobResponse:
    request.include('invoicing')
    layout = layout or PaymentCollectionLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    if request.params.get('format') == 'pdf':
        return handle_pdf_response(self, request)

    providers = {
        provider.id: provider
        for provider in PaymentProviderCollection(request.session).query()
    }

    # Process reservation dates into a display-ready format
    reservation_dates = self.reservation_dates_by_batch()
    reservation_dates_formatted = {
        payment_id: (
            f"{layout.format_date(start, 'date')} - "
            f"{layout.format_date(end, 'date')}"
        ) if start != end else layout.format_date(start, 'date')
        for payment_id, (start, end) in reservation_dates.items()
    }

    return {
        'title': _('Receivables'),
        'form': form,
        'layout': layout or PaymentCollectionLayout(self, request),
        'payments': self.batch,
        'tickets': self.tickets_by_batch(),
        'reservation_dates_formatted': reservation_dates_formatted,
        'providers': providers,
        'pdf_export_link': append_query_param(request.url, 'format', 'pdf')
    }


@OrgApp.json(
    model=PaymentCollection,
    name='batch-set-payment-state',
    request_method='POST',
    permission=Private
)
def handle_batch_set_payment_state(
    self: PaymentCollection,
    request: OrgRequest
) -> JSON_ro:

    request.assert_valid_csrf_token()
    payment_ids = request.json_body.get('payment_ids', [])
    state = request.json_body.get('state')

    if state not in ('invoiced', 'paid', 'open'):
        raise exc.HTTPBadRequest()

    payments_query = self.session.query(Payment).distinct().filter(
        Payment.id.in_(payment_ids)
    )
    # State sequence is assumed to be: 'open' -> 'invoiced' - 'paid'
    updated_count = 0
    for payment in payments_query:
        if not isinstance(payment, ManualPayment):
            continue
        if payment.state != state:
            if payment.state == 'open' and state == 'invoiced':
                payment.state = state
            if payment.state == 'invoiced' and state == 'paid':
                payment.state = state
            # backwards
            if payment.state == 'invoiced' and state == 'open':
                payment.state = state
            if payment.state == 'paid' and state == 'invoiced':
                payment.state = state

        updated_count += 1

    if updated_count > 0:
        messages = {
            'invoiced': _('${count} payments marked as invoiced.',
                          mapping={'count': updated_count}),
            'paid': _('${count} payments marked as paid.',
                      mapping={'count': updated_count}),
            'open': _('${count} payments marked as unpaid.',
                      mapping={'count': updated_count}),
        }
        request.success(messages[state])

    return {'status': 'success', 'message': 'OK'}


@OrgApp.form(
    model=PaymentCollection,
    name='export',
    template='form.pt',
    permission=Private,
    form=merge_forms(DateRangeForm, ExportForm)
)
def export_payments(
    self: PaymentCollection,
    request: OrgRequest,
    form: PaymentExportForm,
    layout: PaymentCollectionLayout | None = None
) -> RenderData | Response:

    layout = layout or PaymentCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Export'), '#'))
    layout.editbar_links = None  # type:ignore[assignment]

    if form.submitted(request):
        start, end = align_range_to_day(
            standardize_date(as_datetime(form.data['start']), layout.timezone),
            standardize_date(as_datetime(form.data['end']), layout.timezone),
            layout.timezone)

        return form.as_export_response(
            run_export(
                session=request.session,
                start=start,
                end=end,
                nested=form.format == 'json',
                formatter=layout.export_formatter(form.format)
            )
        )

    return {
        'title': _('Export'),
        'layout': layout,
        'form': form
    }


def run_export(
    session: Session,
    start: datetime,
    end: datetime,
    nested: bool,
    formatter: Callable[[Any], object]
) -> Sequence[dict[str, Any]]:

    collection = PaymentCollection(session, start=start, end=end)

    payments = tuple(collection.subset())
    if not payments:
        return ()

    links = collection.payment_links_by_batch(payments)
    assert links is not None

    def transform(
        payment: Payment,
        links: list[AnyPayableBase]
    ) -> dict[str, Any]:

        r: dict[str, Any] = OrderedDict()
        r['source'] = formatter(payment.source)
        r['source_id'] = formatter(payment.remote_id)
        r['source_references'] = (
            tuple(formatter(r) for r in payment.remote_references)
            if nested
            else formatter('\n'.join(payment.remote_references))
        )
        r['state'] = formatter(payment.state)
        r['currency'] = formatter(payment.currency)
        r['gross'] = formatter(payment.amount)
        r['net'] = formatter(round(payment.net_amount, 2))
        r['fee'] = formatter(round(payment.fee, 2))
        r['payout_id'] = formatter(payment.meta.get('payout_id'))
        r['payout_date'] = formatter(payment.meta.get('payout_date'))
        r['references'] = (
            tuple(formatter(l.payable_reference) for l in links)
            if nested
            else formatter('\n'.join(l.payable_reference for l in links))
        )

        return r

    return tuple(transform(p, links[p.id]) for p in payments)


@OrgApp.view(
    model=Payment,
    name='mark-as-paid',
    request_method='POST',
    permission=Private
)
def mark_as_paid(self: Payment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'marked-as-paid')

    request.success(_('The ticket was marked as paid'))

    assert self.source == 'manual'
    self.state = 'paid'
    self.sync_invoice_items()


@OrgApp.view(
    model=Payment,
    name='mark-as-unpaid',
    request_method='POST',
    permission=Private
)
def mark_as_unpaid(self: Payment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'marked-as-unpaid')

    request.success(_('The ticket was marked as unpaid'))

    assert self.source == 'manual'
    self.state = 'open'
    self.sync_invoice_items()


@OrgApp.view(
    model=StripePayment,
    name='capture',
    request_method='POST',
    permission=Private
)
def capture_stripe(self: StripePayment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'captured')

    request.success(_('The payment was captured'))

    assert self.source == 'stripe_connect'
    self.charge.capture()
    self.sync_invoice_items()


@OrgApp.view(
    model=StripePayment,
    name='refund',
    request_method='POST',
    permission=Private
)
def refund_stripe(self: StripePayment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'refunded')

    request.success(_('The payment was refunded'))

    assert self.source == 'stripe_connect'
    self.refund()
    self.sync_invoice_items()


@OrgApp.view(
    model=DatatransPayment,
    name='capture',
    request_method='POST',
    permission=Private
)
def capture_datatrans(self: DatatransPayment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    tx = self.transaction
    if tx.status == 'settled':
        request.info(
            _('The payment is already captured but is still processing')
        )
        return
    send_ticket_notifications(self, request, 'captured')

    request.success(_('The payment was captured'))

    assert self.source == 'datatrans'
    if tx.status == 'transmitted':
        self.sync(tx)
    else:
        self.provider.client.settle(tx)
        self.sync_invoice_items()


@OrgApp.view(
    model=DatatransPayment,
    name='refund',
    request_method='POST',
    permission=Private
)
def refund_datatrans(self: DatatransPayment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    assert self.source == 'datatrans'
    try:
        self.refund()
    except DatatransApiError:
        request.alert(_('Could not refund the payment'))
    else:
        send_ticket_notifications(self, request, 'refunded')
        request.success(_('The payment was refunded'))


@OrgApp.view(
    model=SaferpayPayment,
    name='capture',
    request_method='POST',
    permission=Private
)
def capture_saferpay(self: SaferpayPayment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    tx = self.transaction
    if tx.status == 'PENDING':
        request.info(
            _('The payment is already captured but is still processing')
        )
        return

    if tx.status == 'CANCELED':
        request.alert(_('Could not capture the payment'))
    else:
        request.success(_('The payment was captured'))
        send_ticket_notifications(self, request, 'captured')

    assert self.source == 'worldline_saferpay'
    if tx.status != 'AUTHORIZED':
        self.sync(tx)
    else:
        self.provider.client.capture(tx)
        self.sync_invoice_items()


@OrgApp.view(
    model=SaferpayPayment,
    name='refund',
    request_method='POST',
    permission=Private
)
def refund_saferpay(self: SaferpayPayment, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    assert self.source == 'worldline_saferpay'
    try:
        new_refund = self.refund()
    except SaferpayApiError:
        request.alert(_('Could not refund the payment'))
    else:
        self.sync_invoice_items()
        if new_refund:
            send_ticket_notifications(self, request, 'refunded')
        request.success(_('The payment was refunded'))
