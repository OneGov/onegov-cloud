from __future__ import annotations

from decimal import Decimal
from onegov.activity.models import Occasion, OccasionDate
from onegov.activity.types import BoundedIntegerRange
from onegov.core.collection import GenericCollection
from sedate import standardize_date


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from onegov.activity.models import Activity, BookingPeriod


class OccasionCollection(GenericCollection[Occasion]):

    @property
    def model_class(self) -> type[Occasion]:
        return Occasion

    @staticmethod
    def to_half_open_interval(lower: int, upper: int) -> BoundedIntegerRange:
        """ Postgres coerces ranges internally to be half-open in an effort
        to canonize these ranges. This function does the same by taking
        a closed interval and turning it into a half-open interval of
        the NumericRange type.

        """
        return BoundedIntegerRange(lower, upper + 1, bounds='[)')

    def add(  # type:ignore[override]
        self,
        activity: Activity,
        period: BookingPeriod,
        start: datetime,
        end: datetime,
        timezone: str,
        meeting_point: str | None = None,
        age: Sequence[int] | None = None,
        spots: Sequence[int] | None = None,
        note: str | None = None,
        cost: Decimal = Decimal(0),
        exclude_from_overlap_check: bool = False
    ) -> Occasion:

        occasion = super().add(
            meeting_point=meeting_point,
            age=age and self.to_half_open_interval(*age),
            spots=spots and self.to_half_open_interval(*spots),
            note=note,
            activity_id=activity.id,
            period_id=period.id,
            cost=cost,
            exclude_from_overlap_check=exclude_from_overlap_check
        )

        self.add_date(occasion, start, end, timezone)

        return occasion

    def add_date(
        self,
        occasion: Occasion,
        start: datetime,
        end: datetime,
        timezone: str
    ) -> OccasionDate:

        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        date = OccasionDate(
            start=start,
            end=end,
            timezone=timezone
        )

        occasion.dates.append(date)
        self.session.flush()

        return date

    def find_date(
        self,
        occasion: Occasion,
        start: datetime,
        end: datetime,
        timezone: str
    ) -> OccasionDate | None:

        start = standardize_date(start, timezone)
        end = standardize_date(end, timezone)

        q = self.session.query(OccasionDate)
        q = q.filter(OccasionDate.start == start)
        q = q.filter(OccasionDate.end == end)
        q = q.filter(OccasionDate.timezone == timezone)

        return q.first()

    def remove_date(self, date: OccasionDate) -> None:
        q = self.session.query(OccasionDate)
        q = q.filter(OccasionDate.id == date.id)

        occasion_date = q.first()

        if occasion_date:
            self.session.delete(occasion_date)

    def clear_dates(self, occasion: Occasion) -> None:
        q = self.session.query(OccasionDate)
        q = q.filter(OccasionDate.occasion_id == occasion.id)

        for date in q:
            self.session.delete(date)

        occasion.dates = []
        self.session.flush()
