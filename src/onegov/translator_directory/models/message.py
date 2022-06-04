from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin


class TranslatorMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'translator_mutation'
    }

    @classmethod
    def create(cls, ticket, request, change):
        return super().create(ticket, request, change=change)
