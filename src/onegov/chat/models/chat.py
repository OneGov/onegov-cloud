from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import Any


class Chat(Base, TimestampMixin):
    """ A chat. """

    __tablename__ = 'chats'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the unique id, part of the url
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id'))
    user: Mapped[User | None] = relationship()

    customer_name: Mapped[str]
    email: Mapped[str]
    topic: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
    chat_history: Mapped[list[dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSONB),
        default=list
    )
