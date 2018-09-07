from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.event.models.mixins import OccurrenceMixin
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from uuid import uuid4


class Occurrence(Base, OccurrenceMixin, TimestampMixin):
    """ Defines an occurrence of an event. """

    __tablename__ = 'event_occurrences'

    #: Internal number of the occurence
    id = Column(UUID, primary_key=True, default=uuid4)

    #: Event this occurrence belongs to
    event_id = Column(UUID, ForeignKey('events.id'), nullable=False)

    def as_ical(self, url=None):
        """ Returns the occurrence as iCalendar string. """

        return super().as_ical(
            description=self.event.description,
            url=url
        )
