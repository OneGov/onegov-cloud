from onegov.core import utils
from onegov.core.collection import GenericCollection, Pagination
from onegov.chat.models import Chat


class ChatCollection(GenericCollection, Pagination):
    """ Manages a list of chats.

    Use it like this::

        from onegov.people import ChatCollection
        chats = ChatCollection(session)

    """

    @property
    def model_class(self) -> Chat:
        return Chat

    def add(self, customer_name, email):
        chat = self.model_class(
            customer_name=customer_name,
            email=email,
        )

        self.session.add(chat)
        self.session.flush()

        return chat

    def by_id(self, id) -> Chat:
        if utils.is_uuid(id):
            return self.query().filter(self.model_class.id == id).first()
