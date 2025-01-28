from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import User
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid


class Chat(Base, TimestampMixin):
    """ A chat. """

    __tablename__ = 'chats'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the unique id, part of the url
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )
    user_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('users.id'),
        nullable=True
    )
    user: relationship[User | None] = relationship(User)

    customer_name: Column[str] = Column(Text, nullable=False)
    email: Column[str] = Column(Text, nullable=False)
    topic: Column[str] = Column(Text, nullable=False)
    active: Column[bool] = Column(Boolean, nullable=False, default=True)
    chat_history: Column[list[dict[str, Any]]] = Column(
        JSONB,  # type:ignore[arg-type]
        nullable=False,
        default=list
    )
