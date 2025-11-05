from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from .translator import Translator
    from onegov.user import User

TimeReportStatus = Literal['pending', 'confirmed']


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

    #: The duration in minutes
    duration: Column[int] = Column(Integer, nullable=False)

    case_number: Column[str | None] = Column(Text)

    assignment_date: Column[date] = Column(Date, nullable=False)

    hourly_rate: Column[Decimal] = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )

    surcharge_percentage: Column[Decimal] = Column(
        Numeric(precision=5, scale=2),
        nullable=False,
        default=0,
    )

    travel_compensation: Column[Decimal] = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
        default=0,
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

    @property
    def duration_hours(self) -> Decimal:
        """Return duration in hours for display."""
        return Decimal(self.duration) / Decimal(60)

    @property
    def base_compensation(self) -> Decimal:
        """Calculate compensation without travel."""
        return (
            self.hourly_rate
            * self.duration_hours
            * (1 + self.surcharge_percentage / Decimal(100))
        )

    @property
    def title(self) -> str:
        """Return a readable title for this time report."""
        date_str = self.assignment_date.strftime('%Y-%m-%d')
        if self.assignment_type:
            return f'{self.assignment_type} - {date_str}'
        return f'Time Report - {date_str}'
