from __future__ import annotations

from onegov.activity.models import BookingPeriod
from onegov.core.collection import GenericCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date


class BookingPeriodCollection(GenericCollection[BookingPeriod]):

    @property
    def model_class(self) -> type[BookingPeriod]:
        return BookingPeriod

    def add(  # type:ignore[override]
        self,
        title: str,
        prebooking: tuple[date | None, date | None],
        booking: tuple[date, date],
        execution: tuple[date, date],
        active: bool = False,
        minutes_between: int | None = 0,
        deadline_days: int | None = None,
        cancellation_date: date | None = None,
        cancellation_days: int | None = None,
        finalizable: bool = True,
        confirmable: bool = True
    ) -> BookingPeriod:

        if not confirmable:
            prebooking = (booking[0], booking[0])

        period = super().add(
            title=title,
            prebooking_start=prebooking[0],
            prebooking_end=prebooking[1],
            booking_start=booking[0],
            booking_end=booking[1],
            execution_start=execution[0],
            execution_end=execution[1],
            minutes_between=minutes_between,
            active=active,
            deadline_days=deadline_days,
            cancellation_date=cancellation_date,
            cancellation_days=cancellation_days,
            finalizable=finalizable,
            confirmable=confirmable,
        )

        if not confirmable:
            period.confirmed = True

        return period

    def active(self) -> BookingPeriod | None:
        return self.query().filter(BookingPeriod.active == True).first()
