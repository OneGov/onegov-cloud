from __future__ import annotations

from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from .translator import Translator


class TranslatorTimeReport(Base, TimestampMixin):
    """Records time reports for translator deployments/assignments."""

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

    assignment_type: Column[str | None] = Column(Text)

    #: The duration in minutes
    duration: Column[int] = Column(Integer, nullable=False)

    case_number: Column[str | None] = Column(Text)

    assignment_date: Column[date] = Column(Date, nullable=False)

    hourly_rate: Column[float] = Column(
        Float,  # type:ignore[arg-type]
        nullable=False,
    )

    surcharge_percentage: Column[float] = Column(
        Float,  # type:ignore[arg-type]
        nullable=False,
        default=0.0,
    )

    travel_compensation: Column[float] = Column(
        Float,  # type:ignore[arg-type]
        nullable=False,
        default=0.0,
    )

    total_compensation: Column[float] = Column(
        Float,  # type:ignore[arg-type]
        nullable=False,
    )

    notes: Column[str | None] = Column(Text)

    @property
    def duration_hours(self) -> float:
        """Return duration in hours for display."""
        return self.duration / 60.0

    @property
    def base_compensation(self) -> float:
        """Calculate compensation without travel."""
        return (
            self.hourly_rate
            * self.duration_hours
            * (1 + self.surcharge_percentage / 100)
        )

    @property
    def title(self) -> str:
        """Return a readable title for this time report."""
        date_str = self.assignment_date.strftime('%Y-%m-%d')
        if self.assignment_type:
            return f'{self.assignment_type} - {date_str}'
        return f'Time Report - {date_str}'
