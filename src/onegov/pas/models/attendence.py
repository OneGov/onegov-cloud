from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.pas import _
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import PASCommission
    from onegov.pas.models import PASParliamentarian
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

    #: The polymorphic type of attendence
    poly_type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': poly_type,
        'polymorphic_identity': 'pas_attendence',
    }

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The date
    date: Mapped[datetime.date]

    #: The duration in minutes
    duration: Mapped[int]

    #: The type
    type: Mapped[AttendenceType] = mapped_column(
        Enum(
            *TYPES.keys(),
            name='par_attendence_type'
        ),
        default='plenary'
    )

    #: Tracks grouped attendance records to enable future batch
    #: modifications. Only relevant if added in bulk.
    bulk_edit_id: Mapped[UUID | None]

    #: Whether this attendance submission is closed/completed
    #: This is only relevant for commission attendance, not plenary sessions.
    #: Parliamentarians use this to signal they have recorded all their
    #: commission activities for a settlement run.
    abschluss: Mapped[bool] = mapped_column(default=False)

    #: The type as translated text
    @property
    def type_label(self) -> str:
        return TYPES.get(self.type, '')

    #: The id of the parliamentarian
    parliamentarian_id: Mapped[UUID] = mapped_column(
        ForeignKey('par_parliamentarians.id'),
    )

    #: The parliamentarian
    parliamentarian: Mapped[PASParliamentarian] = relationship(
        back_populates='attendences'
    )

    #: the id of the commission
    commission_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('par_commissions.id'),
    )

    #: the related commission (which may have any number of memberships)
    commission: Mapped[PASCommission | None] = relationship(
        back_populates='attendences'
    )

    def calculate_value(self) -> Decimal:
        """Calculate the value (in hours) for an attendance record.

        The calculation follows these business rules:
        - Plenary sessions:
            * Returns actual hours from duration field for display
            * CHF calculation is independent and always uses half-day rate
            * This allows storing actual hours while paying fixed rate

        - Everything else is counted as actual hours:
            * First 2 hours are counted as given
            * After 2 hours, time is rounded to nearest 30-minute increment,
            * and there is another rate applied for the additional time
            * Example: 2h 40min would be calculated as 2.5 hours

        Examples:
            >>> # Plenary session
            >>> attendence.type = 'plenary'
            >>> attendence.duration = 180  # 3 hours
            >>> calculate_value(attendence)
            '3.0'

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
            return Decimal(str(self.duration)) / Decimal('60')

        if self.type in ('commission', 'study', 'shortest'):
            # Convert minutes to hours with Decimal for precise calculation
            duration_hours = Decimal(str(self.duration)) / Decimal('60')

            if duration_hours <= Decimal('2'):
                # Round to 2 decimal places
                return duration_hours.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
            else:
                base_hours = Decimal('2')
                additional_hours = (duration_hours - base_hours)
                # Round additional time to nearest 0.5
                additional_hours = (additional_hours * 2).quantize(
                    Decimal('1'), rounding=ROUND_HALF_UP
                ) / 2
                total_hours = base_hours + additional_hours
                return total_hours.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )

        raise ValueError(f'Unknown attendance type: {self.type}')

    def __repr__(self) -> str:
        return f'<Attendence {self.date} {self.type}>'
