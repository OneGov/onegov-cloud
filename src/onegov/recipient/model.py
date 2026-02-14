from __future__ import annotations

from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.utils import normalize_for_url
from sqlalchemy import Enum
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID


from typing import Literal, TypeAlias

Medium: TypeAlias = Literal['phone', 'email', 'http']


class GenericRecipient(Base, ContentMixin, TimestampMixin):
    """ A generic recipient class with polymorphic support. """

    __tablename__ = 'generic_recipients'

    #: the internal id of the recipient
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the recipient name
    name: Mapped[str]

    #: the order of the records (set to the normalized name + medium)
    order: Mapped[str] = mapped_column(index=True)

    #: the medium over which notifications are sent
    medium: Mapped[Medium] = mapped_column(
        Enum(
            'phone',
            'email',
            'http',
            name='recipient_medium'
        )
    )

    #: the phone number, e-mail, url, etc. of the recipient (matches medium)
    address: Mapped[str]

    #: extra information associated with the address (say POST/GET for http)
    extra: Mapped[str | None]

    #: the polymorphic recipient type
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    @observes('name')
    def name_observer(self, name: str) -> None:
        self.order = normalize_for_url(name)
