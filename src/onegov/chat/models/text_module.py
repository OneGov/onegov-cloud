from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.utils import paragraphify, linkify
from onegov.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup


class TextModule(Base, TimestampMixin):
    """ Defines a text module that can be selected and inserted at the
    cursor position when composing a message in text areas.

    These text modules can either be private or be shared across the
    entire organization to help standardize ticket responses.
    """

    __tablename__ = 'text_modules'

    #: the public id of the text module
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the name of the text module
    name: Mapped[str]

    #: the actual text module
    text: Mapped[str]

    #: the message type this text module should be available for
    message_type: Mapped[str | None] = mapped_column(index=True)

    #: the ticket handler this text module should be available for
    handler_code: Mapped[str | None] = mapped_column(index=True)

    #: for a private text module the user it belongs to
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey(User.id))
    user: Mapped[User | None] = relationship()

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
