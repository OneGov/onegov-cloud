from __future__ import annotations

from sqlalchemy import Column, Date, Enum, Text
from sqlalchemy.orm import relationship
from uuid import uuid4

from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import dict_markup_property, ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.ris import _
from onegov.search import ORMSearchable


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from typing import Literal
    from typing import TypeAlias

    from onegov.ris.models.membership import RISCommissionMembership

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


class RISCommission(Base, TimestampMixin, ContentMixin, ORMSearchable):

    __tablename__ = 'ris_commissions'

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
        'description': {'type': 'localized_html'}
    }

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
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
            name='ris_commission_type'
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
    memberships: relationship[list[RISCommissionMembership]]
    memberships = relationship(
        'RISCommissionMembership',
        cascade='all, delete-orphan',
        back_populates='commission',
        order_by='Commission.name'
    )

    @observes('end')
    def end_observer(self, end: date | None) -> None:
        if end:
            for membership in self.memberships:
                if not membership.end:
                    membership.end = end

    def __repr__(self) -> str:
        return f'<Commission {self.name}>'
