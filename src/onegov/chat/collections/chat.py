from onegov.core import utils
from onegov.core.collection import GenericCollection
from onegov.chat.models import Chat


class ChatCollection(GenericCollection):
    """ Manages a list of chats.

    Use it like this::

        from onegov.people import ChatCollection
        chats = ChatCollection(session)

    """

    @property
    def model_class(self):
        return Chat

    def add(self, customer_name):
        chat = self.model_class(
            customer_name=customer_name,
        )

        self.session.add(chat)
        self.session.flush()

        return chat

    def by_id(self, id):
        if utils.is_uuid(id):
            return self.query().filter(self.model_class.id == id).first()
