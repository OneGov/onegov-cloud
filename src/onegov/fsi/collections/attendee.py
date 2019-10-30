from onegov.core.collection import Pagination
from onegov.fsi.models.course_attendee import CourseAttendee


class CourseAttendeeCollection(Pagination):

    def __init__(self, session, page=0, no_placeholders=False):
        self.session = session
        self.page = page
        self.no_placeholders = no_placeholders

    def __eq__(self, other):
        return (
            self.page == other.page
            and self.no_placeholders == other.no_placeholders)

    def query(self):
        query = self.session.query(CourseAttendee).order_by(
            CourseAttendee.last_name, CourseAttendee.first_name)
        if self.no_placeholders:
            query = query.filter(CourseAttendee.user_id.isnot(None))
        return query

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, index,
            no_placeholders=self.no_placeholders
        )
