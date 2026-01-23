from __future__ import annotations

import sedate

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.types import JSON, UTCDateTime
from onegov.file import File
from sqlalchemy import Column, Text
from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.ext.hybrid import hybrid_property
from ulid import ULID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.chat.collections import MessageCollection
    from onegov.core.request import CoreRequest
    from sqlalchemy.orm import Session
    from typing import Self


class MessageFile(File):
    __mapper_args__ = {'polymorphic_identity': 'messagefile'}


class Message(Base):
    """ A single chat message bound to channel. """

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    __tablename__ = 'messages'

    #: the public id of the message - uses ulid for absolute ordering
    id: Column[str] = Column(
        Text,
        primary_key=True,
        default=lambda: str(ULID())
    )

    #: channel to which this message belongs -> this might one day be
    #: linked to an actual channel record - for now it's just a string that
    #: binds all messages with the same string together
    channel_id: Column[str] = Column(Text, index=True, nullable=False)

    #: optional owner of the message -> this is just an identifier, it isn't
    #: necessarily linked to the user table
    owner: Column[str | None] = Column(Text, nullable=True)

    #: the polymorphic type of the message
    type: Column[str] = Column(Text, nullable=False, default='generic')

    #: meta information specific to this message and maybe its type -> we
    #: don't use the meta/content mixin yet as we might not need the content
    #: property
    meta: Column[dict[str, Any]] = Column(JSON, nullable=False, default=dict)

    #: the text of the message, maybe None for certain use cases (say if the
    # content of the message is generated from the meta property)
    text: Column[str | None] = Column(Text, nullable=True)

    #: the time this message was created - not taken from the timestamp mixin
    #: because here we don't want it to be deferred
    created: Column[datetime] = Column(UTCDateTime, default=sedate.utcnow)

    #: the time this message was modified - not taken from the timestamp mixin
    #: because here we don't want it to be deferred
    modified: Column[datetime | None] = Column(
        UTCDateTime,
        onupdate=sedate.utcnow
    )

    #: a single optional file associated with this message
    file = associated(File, 'file', 'one-to-one')

    # we need to override __hash__ and __eq__ to establish the equivalence of
    # polymorphic subclasses that differ - we need to compare the base class
    # with subclasses to work around a limitation of the association proxy
    # (see backref in onegov.core.orm.abstract.associable.associated)
    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: object) -> bool:
        if (
            isinstance(other, self.__class__)
            and self.id == other.id
            and self.channel_id == other.channel_id
        ):
            return True

        return super().__eq__(other)

    @property
    def subtype(self) -> str | None:
        """ An optional subtype for this message used for separating messages
        of a type further (currently for UI).

        Should be made unique, but there's no guarantee.

        """
        return None

    def get(self, request: CoreRequest) -> str | None:
        """ Code rendering a message should call this method to get the
        actual text of the message. It might be rendered from meta or it
        might be returned directly from the text column.

        How this is done is up to the polymorphic Message.

        """
        return self.text

    if TYPE_CHECKING:
        # workaround for sqlalchemy-stubs
        edited: Column[bool]
    else:
        @hybrid_property
        def edited(self) -> bool:
            # use != instead of "is None" as we want this translated into SQL
            return self.modified != None

    @classmethod
    def bound_messages(cls, session: Session) -> MessageCollection[Self]:
        """ A message collection bound to the polymorphic identity of this
        message.

        """
        from onegov.chat import MessageCollection  # XXX circular import

        return MessageCollection(
            session=session,
            type=inspect(cls).polymorphic_identity
        )


@event.listens_for(Message, 'init')  # type:ignore[untyped-decorator]
def init(
    target: Message,
    args: tuple[Any, ...],
    kwargs: dict[str, Any]
) -> None:
    """ Ensures that the message id is created upon instantiation. This helps
    to ensure that each message is ordered according to it's creation.

    Note that messages created within a millisecond of each other are ordered
    randomly.

    """
    target.id = str(ULID())
