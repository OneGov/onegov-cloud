from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.pas.models.commission import Commission
from onegov.pas.models.parliamentarian import Parliamentarian
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    import datetime
    from typing import Literal
    from typing_extensions import TypeAlias

    AttendenceType: TypeAlias = Literal[
        'plenary',
        'commission',
        'study',
        'shortest',
    ]

TYPES: dict['AttendenceType', str] = {
    'plenary': _('Plenary session'),
    'commission': _('Commission meeting'),
    'study': _('File study'),
    'shortest': _('Shortest meeting'),
}


class Attendence(Base, TimestampMixin):

    __tablename__ = 'pas_attendence'

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The date
    date: 'Column[datetime.date]' = Column(
        Date,
        nullable=False
    )

    #: The duration in minutes
    duration: 'Column[int]' = Column(
        Integer,
        nullable=False
    )

    #: The type
    type: 'Column[AttendenceType]' = Column(
        Enum(
            *TYPES.keys(),  # type:ignore[arg-type]
            name='pas_attendence_type'
        ),
        nullable=False,
        default='plenary'
    )

    #: The type as translated text
    @property
    def type_label(self) -> str:
        return TYPES.get(self.type, '')

    #: The id of the parliamentarian
    parliamentarian_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_parliamentarians.id'),
        nullable=False
    )

    #: The parliamentarian
    parliamentarian: 'relationship[Parliamentarian]' = relationship(
        Parliamentarian,
        back_populates='attendences'
    )

    #: the id of the commission
    commission_id: 'Column[uuid.UUID|None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_commissions.id'),
        nullable=True
    )

    #: the related commission (which may have any number of memberships)
    commission: 'relationship[Commission|None]' = relationship(
        Commission,
        back_populates='attendences'
    )
