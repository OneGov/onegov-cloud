from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.parliament.models import ParliamentarianRole


class ParliamentaryGroup(Base, ContentMixin, TimestampMixin):
    """ Fraktion """

    __tablename__ = 'par_parliamentary_groups'

    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: External ID
    external_kub_id: Mapped[UUID | None] = mapped_column(
        default=uuid4,
        unique=True
    )

    #: the name
    name: Mapped[str]

    #: The start date
    start: Mapped[date | None]

    #: The end date
    end: Mapped[date | None]

    #: The description
    description = dict_markup_property('content')

    #: A parliamentary group may have n roles
    roles: Mapped[list[ParliamentarianRole]] = relationship(
        cascade='all, delete-orphan',
        back_populates='parliamentary_group'
    )

    def __repr__(self) -> str:
        return f'<ParliamentaryGroup {self.name}>'
