import random

from collections import namedtuple
from onegov.core.collection import Pagination
from onegov.ticket import handlers as global_handlers
from onegov.ticket.model import Ticket
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload, undefer


class TicketCollectionPagination(Pagination):

    def __init__(self, session, page=0, state='open', handler='ALL',
                 extra_parameters=None):
        self.session = session
        self.page = page
        self.state = state
        self.handler = handler
        self.handlers = global_handlers

        if self.handler != 'ALL':
            self.extra_parameters = extra_parameters or {}
        else:
            self.extra_parameters = {}

    def __eq__(self, other):
        return self.state == other.state and self.page == other.page

    def subset(self):
        query = self.query()
        query = query.order_by(desc(Ticket.created))
        query = query.options(joinedload(Ticket.user))
        query = query.options(undefer(Ticket.created))

        if self.state != 'all':
            query = query.filter(Ticket.state == self.state)

        if self.handler != 'ALL':
            query = query.filter(Ticket.handler_code == self.handler)

            if self.extra_parameters:
                handler_class = self.handlers.get(self.handler)
                query = handler_class.handle_extra_parameters(
                    self.session, query, self.extra_parameters
                )

        return query

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, index, self.state, self.handler,
            self.extra_parameters
        )

    def for_state(self, state):
        return self.__class__(
            self.session, 0, state, self.handler, self.extra_parameters)

    def for_handler(self, handler):
        return self.__class__(
            self.session, 0, self.state, handler, self.extra_parameters)


TicketCount = namedtuple('TicketCount', ['open', 'pending', 'closed'])


class TicketCollection(TicketCollectionPagination):

    def query(self):
        return self.session.query(Ticket)

    def random_number(self, length):
        range_start = 10 ** (length - 1)
        range_end = 10 ** length - 1

        return random.randint(range_start, range_end)

    def random_ticket_number(self, handler_code):
        number = str(self.random_number(length=8))
        return '{}-{}-{}'.format(handler_code, number[:4], number[4:])

    def is_existing_ticket_number(self, ticket_number):
        query = self.query().with_entities(Ticket.number)
        return bool(query.filter(Ticket.number == ticket_number).first())

    def issue_unique_ticket_number(self, handler_code):
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

    def open_ticket(self, handler_code, handler_id, **handler_data):
        """ Opens a new ticket using the given handler. """

        ticket = Ticket()
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

    def by_handler_code(self, handler_code):
        return self.query().filter(Ticket.handler_code == handler_code).all()

    def by_id(self, id, ensure_handler_code=None):
        query = self.query().filter(Ticket.id == id)

        if ensure_handler_code:
            query = query.filter(Ticket.handler_code == ensure_handler_code)

        return query.first()

    def by_handler_id(self, handler_id):
        return self.query().filter(Ticket.handler_id == handler_id).first()

    def get_count(self):
        query = self.query()
        query = query.with_entities(Ticket.state, func.count(Ticket.state))
        query = query.group_by(Ticket.state)

        count = {r[0]: r[1] for r in query.all()}
        count.setdefault('open', 0)
        count.setdefault('pending', 0)
        count.setdefault('closed', 0)

        return TicketCount(**count)
