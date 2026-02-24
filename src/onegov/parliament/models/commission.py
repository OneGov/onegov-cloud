from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.parliament import _
from onegov.core.orm import observes
from uuid import uuid4
from uuid import UUID
from sqlalchemy import Enum
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias

    from onegov.parliament.models import CommissionMembership


CommissionType: TypeAlias = Literal[
    'normal',
    'intercantonal',
    'official',
]

TYPES: dict[CommissionType, str] = {
    'normal': _('normal'),
    'intercantonal': _('intercantonal'),
    'official': _('official mission'),
}


class Commission(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'par_commissions'

    poly_type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': poly_type,
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

    #: The type value
    type: Mapped[CommissionType] = mapped_column(
        Enum(
            *TYPES.keys(),
            name='commission_type'
        ),
        default='normal'
    )

    #: The type as translated text
    @property
    def type_label(self) -> str:
        return TYPES.get(self.type, '')

    #: The description
    description = dict_markup_property('content')

    #: A commission may have n parliamentarians
    memberships: Mapped[list[CommissionMembership]] = relationship(
        cascade='all, delete-orphan',
        back_populates='commission'
    )

    @observes('end')
    def end_observer(self, end: date | None) -> None:
        if end:
            for membership in self.memberships:
                if not membership.end:
                    membership.end = end

    def __repr__(self) -> str:
        return f'<Commission {self.name}>'
