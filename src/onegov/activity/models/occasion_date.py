from __future__ import annotations

import sedate

from datetime import datetime, time
from enum import IntEnum
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from sqlalchemy import event
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator, Sequence
    from onegov.activity.models import Occasion
    from sqlalchemy.orm import UOWTransaction  # type:ignore[attr-defined]


class DAYS(IntEnum):
    half = 0b1
    full = 0b10
    many = 0b100

    @staticmethod
    def has(value: int, mask: int) -> bool:
        return value & mask > 0 if value else False

    @staticmethod
    def compute(
        localized_start: datetime,
        localized_end: datetime,
        total_seconds: float
    ) -> DAYS:
        hours = total_seconds / 3600

        if hours <= 6:
            return DAYS.half
        elif hours <= 24:
            start, end = localized_start, localized_end

            # if a less than 24 hours long activity ends on another day, the
            # end time is relevant. An end before 06:00 indicates that this
            # is an activity that lasts very long. An end after 06:00 is an
            # multi-day activity.
            if start.date() != end.date() and end.time() >= time(6, 0):
                return DAYS.many

            return DAYS.full
        else:
            return DAYS.many


class OccasionDate(Base, TimestampMixin):
    """ A single start/end date of an occurrence (which may have multiple
    date ranges).

    """

    __tablename__ = 'occasion_dates'

    def __hash__(self) -> int:
        return hash(self.id)

    #: the internal id of this occasion date
    id: Column[int] = Column(Integer, primary_key=True)

    #: Timezone of the occasion date
    timezone: Column[str] = Column(Text, nullable=False)

    #: The start of the range
    start: Column[datetime] = Column(UTCDateTime, nullable=False)

    #: The end of the range
    end: Column[datetime] = Column(UTCDateTime, nullable=False)

    #: The associated occasion
    occasion_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('occasions.id'),
        nullable=False
    )
    occasion: relationship[Occasion] = relationship(
        'Occasion',
        back_populates='dates'
    )

    __table_args__ = (
        CheckConstraint('"start" <= "end"', name='start_before_end'),
    )

    @property
    def localized_start(self) -> datetime:
        return sedate.to_timezone(self.start, self.timezone)

    @property
    def localized_end(self) -> datetime:
        return sedate.to_timezone(self.end, self.timezone)

    @property
    def active_days(self) -> Iterator[int]:
        for dt in sedate.dtrange(self.localized_start, self.localized_end):
            yield dt.date().toordinal()

    @property
    def weekdays(self) -> list[int]:
        return list({
            dt.weekday() for dt in sedate.dtrange(
                self.localized_start, self.localized_end
            )
        })

    if TYPE_CHECKING:
        duration_in_seconds: Column[float]
        duration: Column[DAYS]

    @hybrid_property  # type:ignore[no-redef]
    def duration_in_seconds(self) -> float:
        return (self.end - self.start).total_seconds()

    # FIXME: I don't think this works as a hybrid_property because
    #        localized_start/localized_end aren't hybrid_property
    @hybrid_property  # type:ignore[no-redef]
    def duration(self) -> DAYS:
        return DAYS.compute(
            self.localized_start,
            self.localized_end,
            self.duration_in_seconds
        )

    def overlaps(self, other: OccasionDate) -> bool:
        return sedate.overlaps(self.start, self.end, other.start, other.end)


# # changes to the dates need to be propagated to the parent occasion
# # so it can update its aggregated values
@event.listens_for(Session, 'before_flush')  # type:ignore[untyped-decorator]
def before_flush(
    session: Session,
    context: UOWTransaction,
    instances: Sequence[Any]
) -> None:
    for obj in session.dirty:
        if isinstance(obj, OccasionDate):
            obj.occasion.on_date_change()
