from __future__ import annotations

import random
import sedate

from functools import cached_property
from onegov.core.collection import Pagination
from onegov.core.custom import msgpack
from onegov.core.orm.types import UUID as UUIDType
from onegov.pay.collections import InvoiceCollection
from onegov.ticket import handlers as global_handlers
from onegov.ticket.models.invoice import TicketInvoice
from onegov.ticket.models.invoice_item import TicketInvoiceItem
from onegov.ticket.models.ticket import Ticket
from sqlalchemy import and_, cast, desc, func, or_
from sqlalchemy.orm import contains_eager, joinedload, selectinload, undefer
from uuid import UUID


from typing import Any, ClassVar, Literal, NamedTuple, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date, datetime
    from onegov.ticket.models.ticket import TicketState
    from sedate.types import Direction, TzInfo
    from sqlalchemy.orm import Query, Session
    from typing import TypeAlias, TypedDict

    ExtendedTicketState: TypeAlias = TicketState | Literal['all', 'unfinished']

    class StateCountDict(TypedDict, total=False):
        open: int
        pending: int
        closed: int
        archived: int


class TicketCollectionPagination(Pagination[Ticket]):

    if TYPE_CHECKING:
        # forward declare query
        def query(self) -> Query[Ticket]: ...

    # NOTE: Indicates whether or not passing `term` to the collection
    #       has any influence on the results, the base implementation
    #       does not support search, but our subclass in onegov.org does.
    search_term_supported: ClassVar[bool] = False

    def __init__(
        self,
        session: Session,
        page: int = 0,
        state: ExtendedTicketState = 'open',
        handler: str = 'ALL',
        group: str | None = None,
        owner: str = '*',
        submitter: str = '*',
        # NOTE: Only used by subclasses which implement fulltext search
        term: str | None = None,
        extra_parameters: dict[str, Any] | None = None
    ):
        super().__init__(page)
        self.session = session
        self.state = state
        self.handler = handler
        self.handlers = global_handlers
        self.group = group
        self.owner = owner
        self.submitter = submitter
        self.term = term

        if self.handler != 'ALL':
            self.extra_parameters = extra_parameters or {}
        else:
            self.extra_parameters = {}

    @property
    def q(self) -> str | None:
        return self.term

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TicketCollection)
            and self.state == other.state
            and self.handler == other.handler
            and self.group == other.group
            and self.owner == other.owner
            and self.submitter == other.submitter
            and self.term == other.term
            and self.extra_parameters == other.extra_parameters
            and self.page == other.page
        )

    def subset(self) -> Query[Ticket]:
        query = self.query()
        query = query.order_by(desc(Ticket.created))
        query = query.options(joinedload(Ticket.user))
        query = query.options(undefer(Ticket.created))

        if self.state == 'unfinished':
            query = query.filter(
                Ticket.state != 'closed',
                Ticket.state != 'archived'
            )
        elif self.state == 'all':
            query = query.filter(Ticket.state != 'archived')
        else:
            query = query.filter(Ticket.state == self.state)

        if self.group is not None:
            query = query.filter(Ticket.group == self.group)

        if self.owner != '*':
            query = query.filter(Ticket.user_id == self.owner)

        if self.submitter != '*':
            query = query.filter(Ticket.ticket_email == self.submitter)

        if self.handler != 'ALL':
            query = query.filter(Ticket.handler_code == self.handler)

            if self.extra_parameters:
                handler_class = self.handlers.get(self.handler)
                query = handler_class.handle_extra_parameters(
                    self.session, query, self.extra_parameters
                )

        return query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session, index, self.state, self.handler, self.group,
            self.owner, self.submitter, self.term, self.extra_parameters
        )

    def for_state(self, state: ExtendedTicketState) -> Self:
        return self.__class__(
            self.session, 0, state, self.handler, self.group, self.owner,
            self.submitter, self.term, self.extra_parameters
        )

    def for_handler(self, handler: str) -> Self:
        return self.__class__(
            self.session, 0, self.state, handler, self.group, self.owner,
            self.submitter, self.term, self.extra_parameters
        )

    def for_group(self, group: str) -> Self:
        return self.__class__(
            self.session, 0, self.state, self.handler, group, self.owner,
            self.submitter, self.term, self.extra_parameters
        )

    def for_owner(self, owner: str | UUID) -> Self:
        if isinstance(owner, UUID):
            owner = owner.hex

        return self.__class__(
            self.session, 0, self.state, self.handler, self.group, owner,
            self.submitter, self.term, self.extra_parameters
        )

    def for_submitter(self, submitter: str) -> Self:
        return self.__class__(
            self.session, 0, self.state, self.handler, self.group,
            self.owner, submitter, self.term, self.extra_parameters
        )

    def groups_by_handler_code(self) -> Query[tuple[str, list[str]]]:
        return self.query().with_entities(
            Ticket.handler_code,
            func.array_agg(Ticket.group.distinct())
        ).group_by(Ticket.handler_code)


@msgpack.make_serializable(tag=60)
class TicketCount(NamedTuple):
    open: int = 0
    pending: int = 0
    closed: int = 0
    archived: int = 0


class TicketCollection(TicketCollectionPagination):

    def query(self) -> Query[Ticket]:
        return self.session.query(Ticket)

    def random_number(self, length: int) -> int:
        range_start = 10 ** (length - 1)
        range_end = 10 ** length - 1

        return random.randint(range_start, range_end)  # nosec B311

    def random_ticket_number(self, handler_code: str) -> str:
        number = str(self.random_number(length=8))
        return f'{handler_code}-{number[:4]}-{number[4:]}'

    def is_existing_ticket_number(self, ticket_number: str) -> bool:
        query = self.query().filter(Ticket.number == ticket_number)
        return self.session.query(query.exists()).scalar()

    def issue_unique_ticket_number(self, handler_code: str) -> str:
        """ Randomly generates a new ticket number, ensuring it is unique
        for the given handler_code.

        The resulting code is of the following form::

            XXX-0000-1111

        Where ``XXX`` is the handler_code and the rest is a 12 character
        sequence of random numbers separated by dashes.

        This gives us 10^8 or 100 million ticket numbers for each handler.

        Though we'll never reach that limit, there is an increasing chance
        of conflict with existing ticket numbers, so we have to check
        against the database.

        Still, this number is not unguessable (say in an URL) - there we have
        to rely on the internal ticket id, which is a uuid.

        In a social engineering setting, where we don't have the abilty to
        quickly try out thousands of numbers, the ticket number should
        be pretty unguessable however.

        """

        # usually we won't have any conflict, so we just run queries
        # against the existing database, even if this means to run more than
        # one query once in forever

        while True:
            candidate = self.random_ticket_number(handler_code)

            if not self.is_existing_ticket_number(candidate):
                return candidate

    def open_ticket(
        self,
        handler_code: str,
        handler_id: str,
        order_id: UUID | None = None,
        **handler_data: Any
    ) -> Ticket:
        """ Opens a new ticket using the given handler. """

        ticket = Ticket.get_polymorphic_class(handler_code, default=Ticket)()
        ticket.number = self.issue_unique_ticket_number(handler_code)

        # add it to the session before invoking the handler, who expects
        # each ticket to belong to a session already
        self.session.add(ticket)
        ticket.order_id = order_id
        ticket.handler_id = handler_id
        ticket.handler_code = handler_code
        ticket.handler_data = handler_data
        ticket.handler.refresh()

        self.session.flush()

        return ticket

    # FIXME: It seems better to return a query here...
    def by_handler_code(self, handler_code: str) -> list[Ticket]:
        return self.query().filter(Ticket.handler_code == handler_code).all()

    def by_id(
        self,
        id: UUID,
        ensure_handler_code: str | None = None
    ) -> Ticket | None:

        query = self.query().filter(Ticket.id == id)

        if ensure_handler_code:
            query = query.filter(Ticket.handler_code == ensure_handler_code)

        return query.first()

    def by_handler_id(self, handler_id: str) -> Ticket | None:
        return self.query().filter(Ticket.handler_id == handler_id).first()

    def get_count(self, excl_archived: bool = True) -> TicketCount:
        query: Query[tuple[str, int]] = self.query().with_entities(
            Ticket.state, func.count(Ticket.state)
        )

        if excl_archived:
            query = query.filter(Ticket.state != 'archived')

        query = query.group_by(Ticket.state)

        return TicketCount(**dict(query))

    def by_handler_data_id(
        self,
        handler_data_id: str | UUID
    ) -> Query[Ticket]:
        return self.query().filter(
            Ticket.handler_data['handler_data']['id'] == str(handler_data_id))

    def by_ticket_email(self, ticket_email: str) -> Query[Ticket]:
        return self.query().filter(
            func.lower(Ticket.ticket_email) == ticket_email.lower())

    def by_order(self, order_id: UUID) -> Query[Ticket]:
        return self.query().filter(Ticket.order_id == order_id)


# FIXME: Why is this its own subclass? shouldn't this at least override
#        __init__ to pin state to 'archived'?!
class ArchivedTicketCollection(TicketCollectionPagination):
    def query(self) -> Query[Ticket]:
        return self.session.query(Ticket)


class TicketInvoiceCollection(
    Pagination[TicketInvoice],
    InvoiceCollection[TicketInvoice, TicketInvoiceItem]
):

    batch_size = 50

    def __init__(
        self,
        session: Session,
        page: int = 0,
        ticket_group: list[str] | None = None,
        ticket_start: date | None = None,
        ticket_end: date | None = None,
        reservation_start: date | None = None,
        reservation_end: date | None = None,
        reservation_reference_date: Literal['final', 'any'] | None = None,
        has_payment: bool | None = None,
        invoiced: bool | None = None,
    ) -> None:
        Pagination.__init__(self, page)
        self.session = session
        self.has_payment = has_payment
        self.invoiced = invoiced
        self.ticket_group = ticket_group or []
        self.ticket_start = ticket_start
        self.ticket_end = ticket_end
        self.reservation_start = reservation_start
        self.reservation_end = reservation_end
        self.reservation_reference_date = reservation_reference_date or 'final'

    @property
    def model_class(self) -> type[TicketInvoice]:
        return TicketInvoice

    @property
    def item_model_class(self) -> type[TicketInvoiceItem]:
        return TicketInvoiceItem

    def query(self) -> Query[TicketInvoice]:
        return self.session.query(TicketInvoice)

    @cached_property
    def tzinfo(self) -> TzInfo:
        return sedate.ensure_timezone('Europe/Zurich')

    def align_date(self, value: date, direction: Direction) -> datetime:
        return sedate.align_date_to_day(
            sedate.replace_timezone(sedate.as_datetime(value), self.tzinfo),
            self.tzinfo,
            direction
        )

    def subset(self) -> Query[TicketInvoice]:
        query = self.query()

        query = query.join(TicketInvoice.ticket)

        query = query.options(
            selectinload(TicketInvoice.items),
            contains_eager(TicketInvoice.ticket)
        )

        if self.has_payment is True:
            query = query.filter(Ticket.payment_id.isnot(None))
        elif self.has_payment is False:
            query = query.filter(Ticket.payment_id.is_(None))

        if self.invoiced is not None:
            query = query.filter(TicketInvoice.invoiced == self.invoiced)

        if self.ticket_group:
            conditions = []
            for group in self.ticket_group:
                handler_code, *remainder = group.split('-', 1)
                condition = Ticket.handler_code == handler_code
                if remainder:
                    group, = remainder
                    condition = and_(condition, Ticket.group == group)
                conditions.append(condition)

            query = query.filter(or_(*conditions))

        # Filter payments by each associated ticket creation date
        if self.ticket_start is not None:
            query = query.filter(Ticket.created >= self.align_date(
                self.ticket_start,
                'down'
            ))

        if self.ticket_end is not None:
            query = query.filter(Ticket.created <= self.align_date(
                self.ticket_end,
                'up'
            ))

        # Filter payments by the reservation dates it belongs to
        if self.reservation_start or self.reservation_end:
            from onegov.reservation import Reservation

            if self.reservation_reference_date == 'any':
                subquery = self.session.query(Reservation.token)
                token_col = Reservation.token
                start_col = Reservation.start
                end_col = Reservation.end
            else:
                reservations = self.session.query(
                    func.max(Reservation.end).label('reference_date'),
                    Reservation.token,
                ).group_by(
                    Reservation.token
                ).subquery()

                subquery = self.session.query(reservations.c.token)
                token_col = reservations.c.token
                start_col = reservations.c.reference_date
                end_col = reservations.c.reference_date

            subquery = subquery.filter(
                token_col == cast(Ticket.handler_id, UUIDType)
            )
            if self.reservation_start is not None:
                subquery = subquery.filter(end_col >= self.align_date(
                    self.reservation_start,
                    'down'
                ))
            if self.reservation_end is not None:
                subquery = subquery.filter(start_col <= self.align_date(
                    self.reservation_end,
                    'up'
                ))

            query = query.filter(subquery.exists())

        return query.order_by(Ticket.created.desc())

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            ticket_group=self.ticket_group,
            ticket_start=self.ticket_start,
            ticket_end=self.ticket_end,
            reservation_start=self.reservation_start,
            reservation_end=self.reservation_end,
            reservation_reference_date=self.reservation_reference_date,
            has_payment=self.has_payment,
            invoiced=self.invoiced
        )

    def reservation_dates_by_batch(self) -> dict[UUID, tuple[date, date]]:
        if not self.batch:
            return {}
        from onegov.reservation import Reservation
        return {
            invoice_id: (
                sedate.to_timezone(start, self.tzinfo).date(),
                sedate.to_timezone(end, self.tzinfo).date()
            )
            for invoice_id, start, end in self.session.query(Reservation)
            .join(
                Ticket,
                cast(Ticket.handler_id, UUIDType) == Reservation.token
            )
            .filter(Ticket.invoice_id.in_([el.id for el in self.batch]))
            .group_by(Ticket.invoice_id)
            .with_entities(
                Ticket.invoice_id,
                func.min(Reservation.start),
                func.max(Reservation.end)
            )
        }

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TicketInvoiceCollection)
            and self.page == other.page
            and self.has_payment is other.has_payment
            and self.invoiced is other.invoiced
            and self.ticket_group == other.ticket_group
            and self.ticket_start == other.ticket_start
            and self.ticket_end == other.ticket_end
            and self.reservation_start == other.reservation_start
            and self.reservation_end == other.reservation_end
            and self.reservation_reference_date
                == other.reservation_reference_date
        )

    def by_invoiced(self, invoiced: bool | None) -> Self:
        return self.__class__(
            self.session,
            page=0,
            ticket_group=self.ticket_group,
            ticket_start=self.ticket_start,
            ticket_end=self.ticket_end,
            reservation_start=self.reservation_start,
            reservation_end=self.reservation_end,
            reservation_reference_date=self.reservation_reference_date,
            has_payment=self.has_payment,
            invoiced=invoiced,
        )
