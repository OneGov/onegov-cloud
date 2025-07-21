from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.parliament import _
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from onegov.core.orm import observes
from uuid import uuid4
from sqlalchemy import Enum
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from typing import Literal
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

    poly_type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': poly_type,
        'polymorphic_identity': 'generic',
    }

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: External ID
    external_kub_id: Column[uuid.UUID | None] = Column(
        UUID,   # type:ignore[arg-type]
        nullable=True,
        default=uuid4,
        unique=True
    )

    #: the name
    name: Column[str] = Column(
        Text,
        nullable=False
    )

    #: The start date
    start: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The type value
    type: Column[CommissionType] = Column(
        Enum(
            *TYPES.keys(),  # type:ignore[arg-type]
            name='commission_type'
        ),
        nullable=False,
        default='normal'
    )

    #: The type as translated text
    @property
    def type_label(self) -> str:
        return TYPES.get(self.type, '')

    #: The description
    description = dict_markup_property('content')

    #: A commission may have n parliamentarians
    memberships: relationship[list[CommissionMembership]]
    memberships = relationship(
        'CommissionMembership',
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
