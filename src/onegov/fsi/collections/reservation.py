from datetime import timedelta

from sedate import utcnow
from sqlalchemy import and_

from onegov.core.collection import GenericCollection
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_reservation import CourseReservation


class ReservationCollection(GenericCollection):

    def __init__(self, session,
                 attendee_id=None,
                 course_event_id=None,
                 role=None,
                 external_only=False
                 ):
        super().__init__(session)
        self.attendee_id = attendee_id
        self.course_event_id = course_event_id
        self.role = role
        self.external_only = external_only

    @property
    def model_class(self):
        return CourseReservation

    @property
    def course_event(self):
        return self.session.query(CourseEvent).filter_by(
            id=self.course_event_id).first()

    @property
    def attendee(self):
        return self.session.query(CourseAttendee).filter_by(
            id=self.attendee_id).first()

    @property
    def attendee_collection(self):
        return CourseAttendeeCollection(
            self.session, external_only=self.external_only)

    def for_reminder_mails(self):
        soon = utcnow() + timedelta(seconds=60)
        conditions = and_(
            CourseReservation.attendee_id != None,
            CourseReservation.reminder_sent == None,
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
