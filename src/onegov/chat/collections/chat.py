from typing import Any

from onegov.chat.models import Chat
from onegov.core.collection import GenericCollection


class ChatCollection(GenericCollection[Chat]):
    """ Manages a list of chats.

    Use it like this::

        from onegov.people import ChatCollection
        chats = ChatCollection(session)

    """

    @property
    def model_class(self) -> type[Chat]:
        return Chat

    def add(  # type: ignore
        self,
        customer_name: str,
        email: str,
        topic: str,
        **kwargs: Any
    ) -> Chat:
        chat = self.model_class(
            customer_name=customer_name,
            email=email,
            topic=topic,
        )

        self.session.add(chat)
        self.session.flush()

        return chat
