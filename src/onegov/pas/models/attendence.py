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
    from typing import TypeAlias

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

    def calculate_value(self) -> str:
        """Calculate the value (in days/hours) for an attendance record.

        The calculation follows these business rules:
        - Plenary sessions (Kantonsratsitzung):
            * Always counted as 0.5 (half day), regardless of actual duration

        - Commission meetings and file study sessions:
            * First 2 hours are counted as given
            * After 2 hours, time is rounded to nearest 30-minute increment,
            * and
            * Example: 2h 40min would be calculated as 2.5 hours

        Returns:
            str: The calculated value formatted with one decimal place:
                - '0.5' for plenary sessions
                - Actual hours (e.g., '2.5') for commission/study sessions

        Examples:
            >>> # Plenary session
            >>> attendence.type = 'plenary'
            >>> _calculate_value(attendence)
            '0.5'

            >>> # Commission meeting, 2 hours
            >>> attendence.type = 'commission'
            >>> attendence.duration = 120  # minutes
            >>> _calculate_value(attendence)
            '2.0'

            >>> # Study session, 2h 40min
            >>> attendence.type = 'study'
            >>> attendence.duration = 160  # minutes
            >>> _calculate_value(attendence)
            '2.5'
        """
        if self.type == 'plenary':
            return '0.5'  # Always half day for plenary sessions

        # For commission meetings and study sessions, calculate based on
        # duration
        if self.type in ('commission', 'study'):
            duration_hours = self.duration / 60  # Convert minutes to hours

            if duration_hours <= 2:
                return f'{duration_hours:.1f}'
            else:
                base_hours = 2
                additional_hours = (duration_hours - 2)
                # Round additional time to nearest 0.5
                additional_hours = round(additional_hours * 2) / 2
                total_hours = base_hours + additional_hours
                return f'{total_hours:.1f}'

        return '0.0'  # Default case

    def __repr__(self) -> str:
        return f'<Attendence {self.date} {self.type}>'
