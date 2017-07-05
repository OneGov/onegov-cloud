from functools import partial
from onegov.core.security import Private
from onegov.org import OrgApp, _
from onegov.org.layout import PaymentCollectionLayout
from onegov.org.models import PaymentMessage
from onegov.pay import Payment
from onegov.pay import PaymentCollection
from onegov.pay import PaymentProviderCollection
from onegov.ticket import TicketCollection


def ticket_by_link(tickets, link):
    if link.__tablename__ == 'reservations':
        return tickets.by_handler_id(link.token.hex)
    elif link.__tablename__ == 'submissions':
        return tickets.by_handler_id(link.id.hex)
    else:
        raise NotImplementedError


def create_ticket_messages(payment, request, change):
    session = request.app.session()
    tickets = TicketCollection(session)

    for link in payment.links:
        ticket = ticket_by_link(tickets, link)
        if ticket:
            PaymentMessage.create(payment, ticket, request, change)


@OrgApp.html(
    model=PaymentCollection,
    template='payments.pt',
    permission=Private)
def view_payments(self, request):
    session = request.app.session()
    tickets = TicketCollection(session)

    providers = {
        provider.id: provider
        for provider in PaymentProviderCollection(session).query()
    }

    payment_links = self.payment_links_by_batch()

    return {
        'title': _("Payments"),
        'layout': PaymentCollectionLayout(self, request),
        'payments': self.batch,
        'get_ticket': partial(ticket_by_link, tickets),
        'providers': providers,
        'payment_links': payment_links
    }


@OrgApp.view(
    model=Payment,
    name='mark-as-paid',
    request_method='POST',
    permission=Private)
def mark_as_paid(self, request):
    request.assert_valid_csrf_token()
    create_ticket_messages(self, request, 'marked-as-paid')

    assert self.source == 'manual'
    self.state = 'paid'


@OrgApp.view(
    model=Payment,
    name='mark-as-unpaid',
    request_method='POST',
    permission=Private)
def mark_as_unpaid(self, request):
    request.assert_valid_csrf_token()
    create_ticket_messages(self, request, 'marked-as-unpaid')

    assert self.source == 'manual'
    self.state = 'open'


@OrgApp.view(
    model=Payment,
    name='capture',
    request_method='POST',
    permission=Private)
def capture(self, request):
    request.assert_valid_csrf_token()
    create_ticket_messages(self, request, 'captured')

    assert self.source == 'stripe_connect'
    self.charge.capture()


@OrgApp.view(
    model=Payment,
    name='refund',
    request_method='POST',
    permission=Private)
def refund(self, request):
    request.assert_valid_csrf_token()
    create_ticket_messages(self, request, 'refunded')

    assert self.source == 'stripe_connect'
    self.refund()
