from datetime import timedelta

from sedate import utcnow
from sqlalchemy import and_

from onegov.core.collection import GenericCollection
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


class ReservationCollection(GenericCollection):

    def __init__(self, session,
                 attendee_id=None,
                 course_event_id=None,
                 role=None):
        super().__init__(session)
        self.attendee_id = attendee_id
        self.course_event_id = course_event_id
        self.role = role

    @property
    def model_class(self):
        return Reservation

    @property
    def course_event(self):
        return self.session.query(CourseEvent).filter_by(
            id=self.course_event_id).first()

    def for_reminder_mails(self):
        soon = utcnow() + timedelta(seconds=60)
        conditions = and_(
            Reservation.attendee_id != None,
            Reservation.reminder_sent == None,
            CourseEvent.scheduled_reminder <= soon
        )
        return self.query().join(CourseEvent).filter(conditions)

    def query(self):
        query = super().query()
        if not self.role:
            pass
        if self.attendee_id:
            query = query.filter_by(attendee_id=self.attendee_id)
        if self.course_event_id:
            query = query.filter_by(course_event_id=self.course_event_id)
        return query
