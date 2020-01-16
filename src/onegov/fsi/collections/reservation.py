from sqlalchemy import or_

from onegov.core.collection import GenericCollection, Pagination
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_reservation import CourseReservation


class ReservationCollection(GenericCollection, Pagination):

    def __init__(self, session,
                 attendee_id=None,
                 course_event_id=None,
                 external_only=False,
                 auth_attendee=None,
                 page=0
                 ):
        super().__init__(session)
        self.attendee_id = attendee_id
        self.page = page
        # current attendee permissions of auth user
        self.course_event_id = course_event_id
        self.external_only = external_only
        self.auth_attendee = auth_attendee

    def __eq__(self, other):
        return all((
            self.page == other.page,
            self.attendee_id == other.attendee_id,
            self.course_event_id == other.course_event_id,
            self.external_only == other.external_only,
            self.auth_attendee == other.auth_attendee
        ))

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
            self.session, external_only=self.external_only,
            auth_attendee=self.auth_attendee
        )

    @property
    def for_himself(self):
        return str(self.auth_attendee.id) == str(self.attendee_id)

    def query(self):
        query = super().query()
        if self.auth_attendee and self.auth_attendee.role == 'editor':
            query = query.join(CourseAttendee)
            query = query.filter(
                or_(CourseAttendee.organisation.in_(
                    self.auth_attendee.permissions, ),
                    CourseReservation.attendee_id == self.auth_attendee.id)
            )
        if self.attendee_id:
            # Always set in path for members to their own
            query = query.filter(
                CourseReservation.attendee_id == self.attendee_id)
        if self.course_event_id:
            query = query.filter(
                CourseReservation.course_event_id == self.course_event_id)
        return query

    def by_id(self, id):
        return super().query().filter(self.primary_key == id).first()

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, page=index,
            auth_attendee=self.auth_attendee,
            attendee_id=self.attendee_id,
            course_event_id=self.course_event_id,
            external_only=self.external_only
        )
