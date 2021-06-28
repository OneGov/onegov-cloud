from functools import partial

from onegov.core.security import Private
from onegov.form import merge_forms
from onegov.org.forms import DateRangeForm, ExportForm
from onegov.org import _, OrgApp

from onegov.org.exports.base import OrgExport
from onegov.ticket import TicketCollection
from onegov.town6.layout import DefaultLayout
from onegov.pay import PaymentCollection, PaymentProviderCollection
from sedate import align_range_to_day, standardize_date, as_datetime


def ticket_by_link(tickets, link):
    if link.__tablename__ == 'reservations':
        return tickets.by_handler_id(link.token.hex)
    elif link.__tablename__ == 'submissions':
        return tickets.by_handler_id(link.id.hex)


def ticket_for_payment(ticket_collection):
    return partial(ticket_by_link, ticket_collection)


def provider_title(payment, providers):
    if not payment.provider_id:
        return _('Manual')
    return providers[payment.provider_id].title


@OrgApp.export(
    id='payments',
    form_class=merge_forms(DateRangeForm, ExportForm),
    permission=Private,
    title=_("Payments"),
    explanation=_("Exports payments and tickets")
)
class PaymentsExport(OrgExport):

    def query(self, session, start, end):
        tickets = TicketCollection(session)
        coll = PaymentCollection(session, start=start, end=end)
        payments = tuple(coll.subset())

        payment_links = coll.payment_links_by_batch(payments)
        get_ticket = partial(ticket_by_link, tickets)
        pr = {
            provider.id: provider
            for provider in PaymentProviderCollection(session).query()
        }

        for p in payments:
            links = payment_links[p.id]
            if not links:
                yield p, links, None, provider_title(p, pr)
            else:
                yield (
                    p, links, get_ticket(links[0]), provider_title(p, pr)
                )

    def rows(self, session, start, end):
        for item, link, ticket, provider in self.query(session, start, end):
            yield (
                (k, v) for k, v in self.fields(item, link, ticket, provider)
            )

    def fields(self, item, links, ticket, provider):
        yield from self.ticket_item_fields(ticket)
        yield from self.payment_items_fields(item, links, provider)

    def run(self, form, session):
        timezone = DefaultLayout.timezone
        start, end = align_range_to_day(
            standardize_date(as_datetime(form.data['start']), timezone),
            standardize_date(as_datetime(form.data['end']), timezone),
            timezone)
        return self.rows(session, start, end)
