from datetime import timedelta

from sedate import utcnow
from sqlalchemy import and_

from onegov.core.collection import GenericCollection
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


class ReservationCollection(GenericCollection):

    @property
    def model_class(self):
        from onegov.fsi.models.reservation import Reservation
        return Reservation

    def for_reminder_mails(self):
        soon = utcnow() + timedelta(seconds=60)
        conditions = and_(
            Reservation.attendee_id != None,
            Reservation.reminder_sent == None,
            CourseEvent.scheduled_reminder <= soon
        )
        return self.query().join(CourseEvent).filter(conditions)
