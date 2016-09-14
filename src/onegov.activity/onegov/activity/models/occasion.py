from onegov.core.orm import Base
from onegov.core.orm.types import UTCDateTime, UUID
from sedate import to_timezone
from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship
from uuid import uuid4


class Occasion(Base):
    """ Describes a single occurrence of an Activity. "Occurence" would have
    been a good word for it too, but that's used by onegov.event.

    So occasion it is.

    """

    __tablename__ = 'occasions'

    #: the public id of this occasion
    id = Column(UUID, primary_key=True, default=uuid4)

    #: Timezone of the occasion
    timezone = Column(Text, nullable=False)

    #: Start date and time of the occasion
    start = Column(UTCDateTime, nullable=False)

    #: End date and time of the event (of the first event if recurring)
    end = Column(UTCDateTime, nullable=False)

    #: Describes the location of the activity
    location = Column(Text, nullable=False)

    #: The minimal age of participants
    min_age = Column(Integer, nullable=False, default=6)

    #: The maximal age of participants
    max_age = Column(Integer, nullable=False, default=16)

    #: The number of available spots
    spots = Column(Integer, nullable=False)

    #: The activity this occasion belongs to
    activity = relationship('Activity', backref='occasions')

    @property
    def localized_start(self):
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    @property
    def localized_end(self):
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)
