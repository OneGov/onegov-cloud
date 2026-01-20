from __future__ import annotations

from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from sqlalchemy import Column, Enum, Text
from uuid import uuid4


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from typing import TypeAlias

    Medium: TypeAlias = Literal['phone', 'email', 'http']


class GenericRecipient(Base, ContentMixin, TimestampMixin):
    """ A generic recipient class with polymorphic support. """

    __tablename__ = 'generic_recipients'

    #: the internal id of the recipient
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the recipient name
    name: Column[str] = Column(Text, nullable=False)

    #: the order of the records (set to the normalized name + medium)
    order: Column[str] = Column(Text, nullable=False, index=True)

    #: the medium over which notifications are sent
    medium: Column[Medium] = Column(Enum(  # type:ignore[arg-type]
        'phone',
        'email',
        'http',
        name='recipient_medium'
    ), nullable=False)

    #: the phone number, e-mail, url, etc. of the recipient (matches medium)
    address: Column[str] = Column(Text, nullable=False)

    #: extra information associated with the address (say POST/GET for http)
    extra: Column[str | None] = Column(Text, nullable=True)

    #: the polymorphic recipient type
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    @observes('name')
    def name_observer(self, name: str) -> None:
        self.order = normalize_for_url(name)
