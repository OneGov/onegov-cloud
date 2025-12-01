from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from sqlalchemy import ARRAY, Column, Date, Enum, Float, ForeignKey, Integer
from sqlalchemy import Numeric, Text
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import uuid
    from datetime import date, datetime
    from sqlalchemy.orm import Session
    from .translator import Translator
    from onegov.user import User
    from .ticket import TimeReportTicket

TimeReportStatus = Literal['pending', 'confirmed']
SurchargeType = Literal['night_work', 'weekend_holiday', 'urgent']


class TranslatorTimeReport(Base, TimestampMixin):

    __tablename__ = 'translator_time_reports'

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4,
    )

    translator_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('translators.id', ondelete='CASCADE'),
        nullable=False,
    )

    translator: relationship[Translator] = relationship(
        'Translator', back_populates='time_reports'
    )

    created_by_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )

    created_by: relationship[User | None] = relationship('User')

    assignment_type: Column[str | None] = Column(Text)

    assignment_location: Column[str | None] = Column(
        Text,
        nullable=True,
        comment='Key of selected assignment location for on-site work'
    )

    #: The duration in minutes (total work time excluding breaks)
    duration: Column[int] = Column(Integer, nullable=False)

    #: Break time in minutes
    break_time: Column[int] = Column(Integer, nullable=False, default=0)

    #: Night work duration in MINUTES (20:00-06:00)
    night_minutes: Column[int] = Column(Integer, nullable=False, default=0)

    #: Weekend/holiday work duration in MINUTES
    weekend_holiday_minutes: Column[int] = Column(
        Integer, nullable=False, default=0
    )

    case_number: Column[str | None] = Column(Text)

    assignment_date: Column[date] = Column(Date, nullable=False)

    start: Column[datetime | None] = Column(UTCDateTime)

    end: Column[datetime | None] = Column(UTCDateTime)

    hourly_rate: Column[Decimal] = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )

    surcharge_types: Column[list[str] | None] = Column(
        ARRAY(Text),
        nullable=True,
        default=list,
    )

    travel_compensation: Column[Decimal] = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
        default=0,
    )

    travel_distance: Column[float | None] = Column(
        Float(precision=2),  # type:ignore[arg-type]
        nullable=True,
        comment='One-way travel distance in km'
    )

    total_compensation: Column[Decimal] = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )

    notes: Column[str | None] = Column(Text)

    status: Column[TimeReportStatus] = Column(
        Enum('pending', 'confirmed', name='time_report_status'),  # type: ignore[arg-type]
        nullable=False,
        default='pending',
    )

    SURCHARGE_RATES: dict[str, Decimal] = {
        'night_work': Decimal('50'),
        'weekend_holiday': Decimal('25'),
        'urgent': Decimal('25'),
    }

    @property
    def duration_hours(self) -> Decimal:
        """Return duration in hours for display."""
        return Decimal(self.duration) / Decimal(60)

    @property
    def break_time_hours(self) -> Decimal:
        """Return break time in hours for display."""
        return Decimal(self.break_time) / Decimal(60)

    @property
    def night_hours_decimal(self) -> Decimal:
        """Return night hours in decimal format for calculations."""
        return Decimal(self.night_minutes) / Decimal(60)

    @property
    def weekend_holiday_hours_decimal(self) -> Decimal:
        """Return weekend/holiday hours in decimal format for calculations."""
        return Decimal(self.weekend_holiday_minutes) / Decimal(60)

    @property
    def day_hours_decimal(self) -> Decimal:
        """Return day hours (total - night) in decimal format."""
        day_hours = self.duration_hours - self.night_hours_decimal
        # Ensure non-negative (handle rounding edge cases)
        return max(day_hours, Decimal('0'))

    @property
    def night_hourly_rate(self) -> Decimal:
        """Return night hourly rate (base rate + 50% surcharge)."""
        return self.hourly_rate * (
            1 + self.SURCHARGE_RATES['night_work'] / 100
        )

    def calculate_compensation_breakdown(self) -> dict[str, Decimal]:
        """Calculate detailed compensation breakdown.

        Returns a dictionary with all compensation components:
        - day_pay: Payment for day hours (base rate)
        - night_pay: Payment for night hours (base rate + 50% surcharge)
        - night_surcharge: Just the surcharge portion for night hours
        - weekend_surcharge: Weekend surcharge (only on non-night hours)
        - urgent_surcharge: Urgent surcharge (25% on top of everything)
        - total_surcharges: Sum of all surcharges
        - subtotal: Total work compensation (before break
          deduction/travel/meal)
        - break_deduction: Break time deduction at normal hourly rate
        - adjusted_subtotal: Subtotal minus break deduction
        - travel: Travel compensation
        - meal: Meal allowance
        - total: Final total compensation (including break deduction)
        """
        hourly_rate = self.hourly_rate
        total_hours = self.duration_hours
        night_hours = self.night_hours_decimal
        surcharge_types = self.surcharge_types or []

        # Initialize all surcharge values
        night_pay = Decimal('0')
        night_surcharge = Decimal('0')
        weekend_surcharge = Decimal('0')
        urgent_surcharge = Decimal('0')

        # Calculate day/night pay
        if night_hours > 0:
            # We have night work - split into day and night
            day_hours = total_hours - night_hours
            day_pay = hourly_rate * day_hours
            night_pay = self.night_hourly_rate * night_hours
            # Just the extra 50% portion
            night_surcharge = night_pay - (hourly_rate * night_hours)
        else:
            # No night work - all hours are day hours
            day_pay = hourly_rate * total_hours

        # Weekend/holiday surcharge (only on non-night hours)
        if 'weekend_holiday' in surcharge_types:
            weekend_holiday_hours = self.weekend_holiday_hours_decimal
            # Weekend surcharge only applies to hours that aren't night hours
            weekend_non_night_hours = weekend_holiday_hours - min(
                weekend_holiday_hours, night_hours
            )
            rate = self.SURCHARGE_RATES['weekend_holiday'] / 100
            weekend_surcharge = (hourly_rate * weekend_non_night_hours) * rate

        # Urgent surcharge stacks on top of actual work compensation
        if 'urgent' in surcharge_types:
            actual_work_pay = day_pay + night_pay + weekend_surcharge
            rate = self.SURCHARGE_RATES['urgent'] / 100
            urgent_surcharge = actual_work_pay * rate

        # Calculate break deduction
        break_hours = self.break_time_hours
        break_deduction = hourly_rate * break_hours

        # Totals
        total_surcharges = (
            night_surcharge + weekend_surcharge + urgent_surcharge
        )
        subtotal = day_pay + night_pay + weekend_surcharge + urgent_surcharge
        adjusted_subtotal = subtotal - break_deduction
        travel = self.travel_compensation
        meal = self.meal_allowance
        total = adjusted_subtotal + travel + meal

        return {
            'day_pay': day_pay,
            'night_pay': night_pay,
            'night_surcharge': night_surcharge,
            'weekend_surcharge': weekend_surcharge,
            'urgent_surcharge': urgent_surcharge,
            'total_surcharges': total_surcharges,
            'subtotal': subtotal,
            'break_deduction': break_deduction,
            'adjusted_subtotal': adjusted_subtotal,
            'travel': travel,
            'meal': meal,
            'total': total,
        }

    @property
    def meal_allowance(self) -> Decimal:
        """Return meal allowance if duration >= 6 hours."""
        return Decimal('40.0') if self.duration_hours >= 6 else Decimal('0')

    @property
    def title(self) -> str:
        """Return a readable title for this time report."""
        date_str = self.assignment_date.strftime('%Y-%m-%d')
        if self.assignment_type:
            return f'{self.assignment_type} - {date_str}'
        return f'Time Report - {date_str}'

    def get_ticket(self, session: Session) -> TimeReportTicket | None:
        """Get the ticket associated with this time report."""
        from onegov.translator_directory.models.ticket import TimeReportTicket

        return (
            session.query(TimeReportTicket)
            .filter(
                TimeReportTicket.handler_data['handler_data'][
                    'time_report_id'
                ].astext
                == str(self.id)
            )
            .first()
        )
