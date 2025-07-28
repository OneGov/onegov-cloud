from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
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
    from onegov.pas.models import PASCommission
    from onegov.pas.models import PASParliamentarian
    from typing import Literal
    from typing import TypeAlias

    AttendenceType: TypeAlias = Literal[
        'plenary',
        'commission',
        'study',
        'shortest',
    ]

TYPES: dict[AttendenceType, str] = {
    'plenary': _('Plenary session'),
    'commission': _('Commission meeting'),
    'study': _('File study'),
    'shortest': _('Shortest meeting'),
}


class Attendence(Base, TimestampMixin):

    __tablename__ = 'par_attendence'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The date
    date: Column[datetime.date] = Column(
        Date,
        nullable=False
    )

    #: The duration in minutes
    duration: Column[int] = Column(
        Integer,
        nullable=False
    )

    #: The type
    type: Column[AttendenceType] = Column(
        Enum(
            *TYPES.keys(),  # type:ignore[arg-type]
            name='par_attendence_type'
        ),
        nullable=False,
        default='plenary'
    )

    #: The type as translated text
    @property
    def type_label(self) -> str:
        return TYPES.get(self.type, '')

    #: The id of the parliamentarian
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_parliamentarians.id'),
        nullable=False
    )

    #: The parliamentarian
    parliamentarian: relationship[PASParliamentarian] = relationship(
        'PASParliamentarian',
        back_populates='attendences'
    )

    #: the id of the commission
    commission_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_commissions.id'),
        nullable=True
    )

    #: the related commission (which may have any number of memberships)
    commission: relationship[PASCommission | None] = relationship(
        'PASCommission',
        back_populates='attendences'
    )

    def calculate_value(self) -> Decimal:
        """Calculate the value (in hours) for an attendance record.

        The calculation follows these business rules:
        - Plenary sessions:
            * Always counted as 0.5 (half day), regardless of actual duration
            This is the special case!

        - Everything else is counted as actual hours:
            * First 2 hours are counted as given
            * After 2 hours, time is rounded to nearest 30-minute increment,
            * and there is another rate applied for the additional time
            * Example: 2h 40min would be calculated as 2.5 hours

        Examples:
            >>> # Plenary session
            >>> attendence.type = 'plenary'
            >>> calculate_value(attendence)
            '0.5'

            >>> # Commission meeting, 2 hours
            >>> attendence.type = 'commission'
            >>> attendence.duration = 120  # minutes
            >>> calculate_value(attendence)
            '2.0'

            >>> # Study session, 2h 40min
            >>> attendence.type = 'study'
            >>> attendence.duration = 160  # minutes
            >>> calculate_value(attendence)
            '2.5'
        """
        if self.duration < 0:
            raise ValueError('Duration cannot be negative')

        if self.type == 'plenary':
            return Decimal('0.5')

        if self.type in ('commission', 'study', 'shortest'):
            # Convert minutes to hours with Decimal for precise calculation
            duration_hours = Decimal(str(self.duration)) / Decimal('60')

            if duration_hours <= Decimal('2'):
                # Round to 1 decimal place
                return duration_hours.quantize(
                    Decimal('0.1'), rounding=ROUND_HALF_UP
                )
            else:
                base_hours = Decimal('2')
                additional_hours = (duration_hours - base_hours)
                # Round additional time to nearest 0.5
                additional_hours = (additional_hours * 2).quantize(
                    Decimal('1.0'), rounding=ROUND_HALF_UP
                ) / 2
                total_hours = base_hours + additional_hours
                return total_hours.quantize(
                    Decimal('0.1'), rounding=ROUND_HALF_UP
                )

        raise ValueError(f'Unknown attendance type: {self.type}')

    def __repr__(self) -> str:
        return f'<Attendence {self.date} {self.type}>'
