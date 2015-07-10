import random

from onegov.ticket.model import Ticket


class TicketCollection(object):

    def __init__(self, session):
        self.session = session

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

    def open_ticket(self, handler_code, **handler_data):
        """ Opens a new ticket using the given handler. """

        ticket = Ticket()
        ticket.number = self.issue_unique_ticket_number(handler_code)
        ticket.handler_code = handler_code
        ticket.handler_data = handler_data
        ticket.handler.refresh()

        self.session.add(ticket)
        self.session.flush()

        return ticket

    def by_handler_code(self, handler_code):
        return self.query().filter(Ticket.handler_code == handler_code).all()

    def by_id(self, id, ensure_handler_code=None):
        query = self.query().filter(Ticket.id == id)

        if ensure_handler_code:
            query = query.filter(Ticket.handler_code == ensure_handler_code)

        return query.first()
