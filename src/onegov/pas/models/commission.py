from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.search import ORMSearchable
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
    from onegov.pas.models.attendence import Attendence
    from onegov.pas.models.commission_membership import CommissionMembership
    from typing import Literal
    from typing import TypeAlias

    CommissionType: TypeAlias = Literal[
        'normal',
        'intercantonal',
        'official',
    ]


TYPES: dict['CommissionType', str] = {
    'normal': _('normal'),
    'intercantonal': _('intercantonal'),
    'official': _('official mission'),
}


class Commission(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_commissions'

    es_public = False
    es_properties = {'name': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name
    name: 'Column[str]' = Column(
        Text,
        nullable=False
    )

    #: The start date
    start: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The type value
    type: 'Column[CommissionType]' = Column(
        Enum(
            *TYPES.keys(),  # type:ignore[arg-type]
            name='pas_commission_type'
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
    memberships: 'relationship[list[CommissionMembership]]'
    memberships = relationship(
        'CommissionMembership',
        cascade='all, delete-orphan',
        back_populates='commission'
    )

    #: A commission may hold meetings
    attendences: 'relationship[list[Attendence]]' = relationship(
        'Attendence',
        cascade='all, delete-orphan',
        back_populates='commission'
    )

    @observes('end')
    def end_observer(self, end: 'date | None') -> None:
        if end:
            for membership in self.memberships:
                if not membership.end:
                    membership.end = end
