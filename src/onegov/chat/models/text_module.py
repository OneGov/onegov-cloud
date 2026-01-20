from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import paragraphify, linkify
from onegov.user import User
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from markupsafe import Markup


class TextModule(Base, TimestampMixin):
    """ Defines a text module that can be selected and inserted at the
    cursor position when composing a message in text areas.

    These text modules can either be private or be shared across the
    entire organization to help standardize ticket responses.
    """

    __tablename__ = 'text_modules'

    #: the public id of the text module
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of the text module
    name: Column[str] = Column(Text, nullable=False)

    #: the actual text module
    text: Column[str] = Column(Text, nullable=False)

    #: the message type this text module should be available for
    message_type: Column[str | None] = Column(
        Text,
        nullable=True,
        index=True
    )

    #: the ticket handler this text module should be available for
    handler_code: Column[str | None] = Column(
        Text,
        nullable=True,
        index=True
    )

    #: for a private text module the user it belongs to
    user_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(User.id),
        nullable=True
    )
    user: relationship[User | None] = relationship(User)

    @property
    def private(self) -> bool:
        return self.user_id is not None

    @property
    def formatted_text(self) -> Markup:
        return paragraphify(linkify(self.text))

    @property
    def preview_text(self) -> str:
        lines = self.text.splitlines()
        preview = lines[0]
        if len(lines) > 1 or len(preview) > 50:
            preview = preview[:46] + ' ...'
        return preview
