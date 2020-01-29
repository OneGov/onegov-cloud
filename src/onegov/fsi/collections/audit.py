from cached_property import cached_property

from onegov.core.collection import GenericCollection
from onegov.fsi.models import CourseAttendee, CourseReservation, CourseEvent, \
    Course


class AuditCollection(GenericCollection):
    """
    Displays the list of attendees filtered by a course and organisation
    for evauluation if they subscribed and completed a course event.

    The organisation filter should also be exact and not fuzzy.

    """

    def __init__(self, session, course_id, auth_attendee, organisation=None):
        super().__init__(session)
        self.course_id = course_id
        self.auth_attendee = auth_attendee

        # e.g. SD / STVA or nothing in case of editor
        if auth_attendee.role != 'editor':
            assert organisation
        self.organisation = organisation

    def query(self):
        query = self.session.query(
            CourseAttendee.first_name,
            CourseAttendee.last_name,
            CourseEvent.start,
            CourseEvent.end,
            CourseReservation.event_completed
        )
        query = query.join(CourseReservation).join(CourseEvent).join(Course)
        query = query.filter(Course.id == self.course_id)

        if self.auth_attendee.role == 'editor':
            query = query.filter(CourseAttendee.organisation.in_(
                self.auth_attendee.permissions,))
        else:
            query = query.filter(
                CourseAttendee.organisation == self.organisation)

        query.order_by(
            CourseReservation.event_completed,
            CourseAttendee.last_name,
            CourseAttendee.first_name
        )

        return query

    @property
    def model_class(self):
        return CourseAttendee

    @cached_property
    def course(self):
        return self.session.query(Course).filter_by(id=self.course_id).one()
