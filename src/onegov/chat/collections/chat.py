from __future__ import annotations

from onegov.chat.models import Chat
from onegov.core.collection import GenericCollection, Pagination

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session, Query
    from typing import Self


class ChatCollection(GenericCollection[Chat], Pagination[Chat]):
    """ Manages a list of chats.

    Use it like this::

        from onegov.people import ChatCollection
        chats = ChatCollection(session)

    """

    def __init__(
        self,
        session: Session,
        page: int = 0,
        state: str = 'active',
        group: str | None = None,
        owner: str = '*',
    ):
        self.session = session
        self.page = page
        self.state = state
        self.group = group
        self.owner = owner

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def subset(self) -> Query[Chat]:
        query = self.query().filter(Chat.chat_history != []).order_by(
            Chat.last_change.desc())
        if self.state == 'active':
            return query.filter(Chat.active == True)
        elif self.state == 'archived':
            return query.filter(Chat.active == False)
        else:
            return query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            state=self.state
        )

    @property
    def name_of_view(self) -> str:
        return 'archive'

    @property
    def model_class(self) -> type[Chat]:
        return Chat

    def add(  # type:ignore[override]
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
