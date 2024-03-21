import decimal
from collections import OrderedDict
from decimal import Decimal
from functools import partial
from onegov.core.security import Private
from onegov.form import merge_forms
from onegov.org import OrgApp, _
from onegov.org.forms import DateRangeForm, ExportForm
from onegov.org.layout import PaymentCollectionLayout, DefaultLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import PaymentMessage, TicketMessage
from onegov.core.elements import Link
from sedate import align_range_to_day, standardize_date, as_datetime
from onegov.pay import Payment
from onegov.pay import PaymentCollection
from onegov.pay import PaymentProviderCollection
from onegov.ticket import Ticket, TicketCollection
from webob import exc


from typing import cast, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest
    from onegov.pay.models.payment_providers.stripe import StripePayment
    from onegov.pay.types import AnyPayableBase
    from sqlalchemy.orm import Session
    from typing import type_check_only
    from webob import Response

    @type_check_only
    class PaymentExportForm(DateRangeForm, ExportForm):
        pass


EMAIL_SUBJECTS = {
    'marked-as-paid': _("Your payment has been received"),
    'marked-as-unpaid': _("Your payment has been withdrawn"),
    'refunded': _("Your payment has been refunded")
}


def ticket_by_link(
    tickets: TicketCollection,
    link: Any
) -> Ticket | None:

    # FIXME: We should probably do isinstance checks so type checkers
    #        can understand that a Reservation has a token and a
    #        FormSubmission has a id...
    if link.__tablename__ == 'reservations':
        return tickets.by_handler_id(link.token.hex)
    elif link.__tablename__ == 'submissions':
        return tickets.by_handler_id(link.id.hex)
    return None


def send_ticket_notifications(
    payment: Payment,
    request: 'OrgRequest',
    change: str
) -> None:

    session = request.session
    tickets = TicketCollection(session)

    for link in payment.links:
        ticket = ticket_by_link(tickets, link)

        if not ticket:
            continue

        # create a notification in the chat
        PaymentMessage.create(payment, ticket, request, change)

        if change == 'captured':
            continue

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


@OrgApp.html(
    model=PaymentCollection,
    template='payments.pt',
    permission=Private
)
def view_payments(
    self: PaymentCollection,
    request: 'OrgRequest',
    layout: PaymentCollectionLayout | None = None
) -> 'RenderData':

    tickets = TicketCollection(request.session)

    providers = {
        provider.id: provider
        for provider in PaymentProviderCollection(request.session).query()
    }

    payment_links = self.payment_links_by_batch()

    return {
        'title': _("Payments"),
        'layout': layout or PaymentCollectionLayout(self, request),
        'payments': self.batch,
        'get_ticket': partial(ticket_by_link, tickets),
        'providers': providers,
        'payment_links': payment_links
    }


@OrgApp.form(
    model=PaymentCollection,
    name='export',
    template='form.pt',
    permission=Private,
    form=merge_forms(DateRangeForm, ExportForm)
)
def export_payments(
    self: PaymentCollection,
    request: 'OrgRequest',
    form: 'PaymentExportForm',
    layout: PaymentCollectionLayout | None = None
) -> 'RenderData | Response':

    layout = layout or PaymentCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
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
        'title': _("Export"),
        'layout': layout,
        'form': form
    }


def run_export(
    session: 'Session',
    start: 'datetime',
    end: 'datetime',
    nested: bool,
    formatter: 'Callable[[Any], object]'
) -> 'Sequence[dict[str, Any]]':

    collection = PaymentCollection(session, start=start, end=end)

    payments = tuple(collection.subset())
    if not payments:
        return ()

    links = collection.payment_links_by_batch(payments)
    assert links is not None

    def transform(
        payment: Payment,
        links: list['AnyPayableBase']
    ) -> dict[str, Any]:

        r: dict[str, Any] = OrderedDict()
        r['source'] = formatter(payment.source)
        r['source_id'] = formatter(payment.remote_id)
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


@OrgApp.json(
    model=Payment,
    name='change-net-amount',
    request_method='POST',
    permission=Private
)
def change_payment_amount(self: Payment, request: 'OrgRequest') -> 'JSON_ro':
    request.assert_valid_csrf_token()
    assert not self.paid
    format_ = DefaultLayout(self, request).format_number
    try:
        net_amount = Decimal(request.params['netAmount'])  # type:ignore
    except decimal.InvalidOperation:
        return {'net_amount': f"{format_(self.net_amount)} {self.currency}"}

    if net_amount <= 0 or (net_amount - self.fee) <= 0:
        raise exc.HTTPBadRequest("amount negative")

    links = self.links
    if links:
        tickets = TicketCollection(request.session)
        ticket = ticket_by_link(tickets, links[0])
        if ticket:
            TicketMessage.create(ticket, request, 'change-net-amount')

    self.amount = net_amount - self.fee
    return {'net_amount': f"{format_(self.net_amount)} {self.currency}"}


@OrgApp.view(
    model=Payment,
    name='mark-as-paid',
    request_method='POST',
    permission=Private
)
def mark_as_paid(self: Payment, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'marked-as-paid')

    request.success(_("The ticket was marked as paid"))

    assert self.source == 'manual'
    self.state = 'paid'


@OrgApp.view(
    model=Payment,
    name='mark-as-unpaid',
    request_method='POST',
    permission=Private
)
def mark_as_unpaid(self: Payment, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'marked-as-unpaid')

    request.success(_("The ticket was marked as unpaid"))

    assert self.source == 'manual'
    self.state = 'open'


@OrgApp.view(
    model=Payment,
    name='capture',
    request_method='POST',
    permission=Private
)
def capture(self: Payment, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'captured')

    request.success(_("The payment was captured"))

    assert self.source == 'stripe_connect'
    self = cast('StripePayment', self)
    self.charge.capture()


@OrgApp.view(
    model=Payment,
    name='refund',
    request_method='POST',
    permission=Private
)
def refund(self: Payment, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()
    send_ticket_notifications(self, request, 'refunded')

    request.success(_("The payment was refunded"))

    assert self.source == 'stripe_connect'
    self = cast('StripePayment', self)
    self.refund()
