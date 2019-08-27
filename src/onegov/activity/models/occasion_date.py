import sedate

from datetime import time
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
from sqlalchemy.orm import Session


class DAYS(IntEnum):
    half = 2**1
    full = 2**2
    many = 2**3

    @staticmethod
    def has(value, mask):
        return value & mask > 0 if value else False

    @staticmethod
    def compute(localized_start, localized_end, total_seconds):
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

    def __hash__(self):
        return hash(self.id)

    #: the internal id of this occasion date
    id = Column(Integer, primary_key=True)

    #: Timezone of the occasion date
    timezone = Column(Text, nullable=False)

    #: The start of the range
    start = Column(UTCDateTime, nullable=False)

    #: The end of the range
    end = Column(UTCDateTime, nullable=False)

    #: The associated occasion
    occasion_id = Column(UUID, ForeignKey('occasions.id'), nullable=False)

    __table_args__ = (
        CheckConstraint('"start" <= "end"', name='start_before_end'),
    )

    @property
    def localized_start(self):
        return sedate.to_timezone(self.start, self.timezone)

    @property
    def localized_end(self):
        return sedate.to_timezone(self.end, self.timezone)

    @property
    def active_days(self):
        for dt in sedate.dtrange(self.localized_start, self.localized_end):
            yield dt.date().toordinal()

    @property
    def weekdays(self):
        return list({
            dt.weekday() for dt in sedate.dtrange(
                self.localized_start, self.localized_end
            )
        })

    @hybrid_property
    def duration_in_seconds(self):
        return (self.end - self.start).total_seconds()

    @hybrid_property
    def duration(self):
        return DAYS.compute(
            self.localized_start,
            self.localized_end,
            self.duration_in_seconds)

    def overlaps(self, other):
        return sedate.overlaps(self.start, self.end, other.start, other.end)


# # changes to the dates need to be propagated to the parent occasion
# # so it can update its aggreagated values
@event.listens_for(Session, 'before_flush')
def before_flush(session, context, instances):
    for obj in session.dirty:
        if isinstance(obj, OccasionDate):
            obj.occasion.on_date_change()
