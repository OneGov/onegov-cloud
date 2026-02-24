from __future__ import annotations

from onegov.chat.models import Message
from onegov.core.collection import GenericCollection
from sqlalchemy import desc


from typing import overload, Any, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.chat.models import MessageFile
    from sqlalchemy.orm import Query, Session


_M = TypeVar('_M', bound=Message)


class MessageCollection(GenericCollection[_M]):

    @overload
    def __init__(
        self: MessageCollection[Message],
        session: Session,
        type: tuple[str, ...] | Literal['*'] | None = ...,
        channel_id: str = '*',
        newer_than: str | None = None,
        older_than: str | None = None,
        limit: int | None = None,
        load: Literal['older-first', 'newer-first'] = 'older-first'
    ): ...

    @overload
    def __init__(
        self,
        session: Session,
        type: str,
        channel_id: str = '*',
        newer_than: str | None = None,
        older_than: str | None = None,
        limit: int | None = None,
        load: Literal['older-first', 'newer-first'] = 'older-first'
    ): ...

    def __init__(
        self,
        session: Session,
        type: str | tuple[str, ...] | None = '*',
        channel_id: str = '*',
        newer_than: str | None = None,
        older_than: str | None = None,
        limit: int | None = None,
        load: Literal['older-first', 'newer-first'] = 'older-first'
    ):
        super().__init__(session)
        self.type = type
        self.channel_id = channel_id
        self.newer_than = newer_than
        self.older_than = older_than
        self.limit = limit
        self.load = load

        assert self.load in ('older-first', 'newer-first')

    @property
    def model_class(self) -> type[_M]:
        if not isinstance(self.type, str):
            return Message  # type:ignore[return-value]
        return Message.get_polymorphic_class(self.type, Message)  # type:ignore

    @overload
    def add(
        self,
        *,
        channel_id: str,
        owner: str | None = None,
        type: str | None = None,
        meta: dict[str, Any] = ...,
        text: str | None = None,
        created: datetime = ...,
        updated: datetime | None = ...,
        file: MessageFile | None = None,
        **kwargs: Any
    ) -> _M: ...

    @overload
    def add(self, **kwargs: Any) -> _M: ...

    def add(
        self,
        *,
        type: str | None = None,
        **kwargs: Any
    ) -> Message:

        _type: str | tuple[str, ...] | None = type
        if _type is None:
            _type = self.type or 'generic'
        if _type is not None and not isinstance(_type, str):
            raise RuntimeError(
                f'Multiple types to add a message with: {_type}'
            )

        if _type is None or _type == '*':
            _type = 'generic'

        return super().add(type=_type, **kwargs)

    def query(self) -> Query[_M]:
        """ Queries the messages with the given parameters. """

        q = self.session.query(self.model_class)

        if self.type != '*':
            if self.type is None or isinstance(self.type, str):
                q = q.filter_by(type=self.type)
            else:
                q = q.filter(self.model_class.type.in_(self.type))

        if self.channel_id != '*':
            q = q.filter_by(channel_id=self.channel_id)

        if self.newer_than is not None:
            q = q.filter(self.model_class.id > self.newer_than)

        if self.older_than is not None:
            q = q.filter(self.model_class.id < self.older_than)

        if self.load == 'older-first':
            q = q.order_by(self.model_class.id)
        else:
            q = q.order_by(desc(self.model_class.id))

        if self.limit is not None:
            q = q.limit(self.limit)

        return q

    # FIXME: This is kind of a goofball method, since it ignores
    #        almost all the parameters on the collection. It is used
    #        to ensure that the feed by default contains the 25
    #        latest messages with the oldest one first, but it will
    #        be wrong with a channel or type filter, we should probably
    #        at least apply the type and channel filters and potentially
    #        the older_than and limit filters...
    def latest_message(self, offset: int = 0) -> _M | None:
        """ Returns the latest message in descending order (newest first)."""
        q = self.session.query(self.model_class)
        q = q.order_by(desc(self.model_class.id))

        if offset:
            q = q.offset(offset)

        return q.first()
