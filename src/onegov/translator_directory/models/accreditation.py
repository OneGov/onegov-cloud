from cached_property import cached_property
from datetime import date
from onegov.translator_directory.models.translator import Translator


class Accreditation:

    def __init__(self, session, target_id, ticket_id):
        self.session = session
        self.target_id = target_id
        self.ticket_id = ticket_id

    @cached_property
    def target(self):
        return self.session.query(Translator).filter_by(
            id=self.target_id
        ).first()

    @cached_property
    def ticket(self):
        from onegov.ticket import TicketCollection
        return TicketCollection(self.session).by_id(self.ticket_id)

    def accept(self):
        self.ticket.handler_data['state'] = 'accepted'
        self.target.state = 'published'
        self.target.date_of_decision = date.today()

    def deny(self):
        self.ticket.handler_data['state'] = 'denied'
        self.session.delete(self.target)
