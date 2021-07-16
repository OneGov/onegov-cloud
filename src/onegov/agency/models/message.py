from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin


class AgencyMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'agency_mutation'
    }

    @classmethod
    def create(cls, ticket, request, change):
        return super().create(ticket, request, change=change)


class PersonMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'person_mutation'
    }

    @classmethod
    def create(cls, ticket, request, change):
        return super().create(ticket, request, change=change)
