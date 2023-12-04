from onegov.chat.models import Chat
from onegov.core.collection import GenericCollection, Pagination

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ChatCollection(GenericCollection[Chat], Pagination[Chat]):
    """ Manages a list of chats.

    Use it like this::

        from onegov.people import ChatCollection
        chats = ChatCollection(session)

    """

    def __init__(
        self,
        session: 'Session',
        page: int = 0,
        handler: str = 'ALL',
        group: str | None = None,
        owner: str = '*',
    ):
        self.session = session
        self.page = page
        self.handler = handler
        self.group = group
        self.owner = owner

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        # return self.query().filter(Chat.active == False)
        return self.query()

    @property
    def search(self):
        return self.search_widget and self.search_widget.name

    @property
    def search_query(self):
        return self.search_widget and self.search_widget.search_query

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            page=index
        )

    @property
    def name_of_view(self) -> str:
        return 'archive'

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
