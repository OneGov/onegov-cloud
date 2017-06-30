from onegov.chat.models import Message
from onegov.core.collection import GenericCollection


class MessageCollection(GenericCollection):

    @property
    def model_class(self):
        return Message.get_polymorphic_class(self.type, Message)
