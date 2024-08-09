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


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from datetime import datetime
    from onegov.form import Form
    from onegov.pay import Payment, PaymentProvider
    from onegov.pay.types import AnyPayableBase
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session
    from uuid import UUID


def ticket_by_link(
    tickets: TicketCollection,
    link: 'AnyPayableBase'
) -> 'Ticket | None':

    if link.__tablename__ == 'reservations':
        return tickets.by_handler_id(link.token.hex)  # type:ignore
    elif link.__tablename__ == 'submissions':
        return tickets.by_handler_id(link.id.hex)  # type:ignore
    return None


def provider_title(
    payment: 'Payment',
    providers: dict['UUID', 'PaymentProvider[Any]']
) -> str:

    if not payment.provider_id:
        return _('Manual')
    return providers[payment.provider_id].title


@OrgApp.export(
    id='payments',
    form_class=merge_forms(DateRangeForm, ExportForm),
    permission=Private,
    title=_("Credit card payments"),
    explanation=_("Exports payments and tickets")
)
class PaymentsExport(OrgExport):
    # Date Paid:
    # - for manual payments, we don't know exactly, assuming the last_modified
    #   date is state is paid

    def query(
        self,
        session: 'Session',
        start: 'datetime | None',
        end: 'datetime | None'
    ) -> 'Iterator[tuple[Payment, list[AnyPayableBase], Ticket | None, str]]':

        tickets = TicketCollection(session)
        coll = PaymentCollection(session, start=start, end=end)
        payments = tuple(coll.subset())

        payment_links = coll.payment_links_by_subset(payments)
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

    def rows(
        self,
        session: 'Session',
        start: 'datetime | None',
        end: 'datetime | None'
    ) -> 'Iterator[Iterator[tuple[str, Any]]]':
        for item, link, ticket, provider in self.query(session, start, end):
            yield (
                (k, v) for k, v in self.fields(item, link, ticket, provider)
            )

    def fields(
        self,
        item: 'Payment',
        links: 'Iterable[AnyPayableBase]',
        ticket: 'Ticket | None',
        provider: str
    ) -> 'Iterator[tuple[str, Any]]':

        yield from self.ticket_item_fields(ticket)
        yield from self.payment_items_fields(item, links, provider)

    def run(
        self,
        form: 'Form',
        session: 'Session'
    ) -> 'Iterator[Iterator[tuple[str, Any]]]':

        timezone = DefaultLayout.timezone
        start, end = align_range_to_day(
            standardize_date(as_datetime(form.data['start']), timezone),
            standardize_date(as_datetime(form.data['end']), timezone),
            timezone)
        return self.rows(session, start, end)
