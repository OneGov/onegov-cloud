from __future__ import annotations

import random

from onegov.core.collection import Pagination
from onegov.core.custom import msgpack
from onegov.ticket import handlers as global_handlers
from onegov.ticket.models.ticket import Ticket
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import joinedload, undefer
from uuid import UUID


from typing import Any, Literal, NamedTuple, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket.models.ticket import TicketState
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

    def __init__(
        self,
        session: Session,
        page: int = 0,
        state: ExtendedTicketState = 'open',
        handler: str = 'ALL',
        group: str | None = None,
        owner: str = '*',
        submitter: str = '*',
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

        if self.handler != 'ALL':
            self.extra_parameters = extra_parameters or {}
        else:
            self.extra_parameters = {}

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TicketCollection)
            and self.state == other.state
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
            self.owner, self.submitter, self.extra_parameters
        )

    def available_groups(self, handler: str = '*') -> tuple[str, ...]:
        query = self.query().with_entities(distinct(Ticket.group))
        query = query.order_by(Ticket.group)

        if handler != '*':
            query = query.filter(Ticket.handler_code == handler)

        return tuple(r[0] for r in query.all())

    def for_state(self, state: ExtendedTicketState) -> Self:
        return self.__class__(
            self.session, 0, state, self.handler, self.group, self.owner,
            self.submitter, self.extra_parameters
        )

    def for_handler(self, handler: str) -> Self:
        return self.__class__(
            self.session, 0, self.state, handler, self.group, self.owner,
            self.submitter, self.extra_parameters
        )

    def for_group(self, group: str) -> Self:
        return self.__class__(
            self.session, 0, self.state, self.handler, group, self.owner,
            self.submitter, self.extra_parameters
        )

    def for_owner(self, owner: str | UUID) -> Self:
        if isinstance(owner, UUID):
            owner = owner.hex

        return self.__class__(
            self.session, 0, self.state, self.handler, self.group, owner,
            self.submitter, self.extra_parameters
        )

    def for_submitter(self, submitter: str) -> Self:
        return self.__class__(
            self.session, 0, self.state, self.handler, self.group, self.owner,
            submitter, self.extra_parameters
        )


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
        **handler_data: Any
    ) -> Ticket:
        """ Opens a new ticket using the given handler. """

        ticket = Ticket.get_polymorphic_class(handler_code, default=Ticket)()
        ticket.number = self.issue_unique_ticket_number(handler_code)

        # add it to the session before invoking the handler, who expects
        # each ticket to belong to a session already
        self.session.add(ticket)
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
            Ticket.ticket_email == ticket_email)


# FIXME: Why is this its own subclass? shouldn't this at least override
#        __init__ to pin state to 'archived'?!
class ArchivedTicketCollection(TicketCollectionPagination):
    def query(self) -> Query[Ticket]:
        return self.session.query(Ticket)
