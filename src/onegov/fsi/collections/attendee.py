from onegov.core.collection import Pagination
from onegov.fsi.models.course_attendee import CourseAttendee


class CourseAttendeeCollection(Pagination):

    def __init__(self, session, page=0, exclude_external=False):
        self.session = session
        self.page = page
        self.exclude_external = exclude_external

    def __eq__(self, other):
        return (
            self.page == other.page
            and self.exclude_external == other.exclude_external)

    def query(self):
        query = self.session.query(CourseAttendee).order_by(
            CourseAttendee.last_name, CourseAttendee.first_name)
        if self.exclude_external:
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
            exclude_external=self.exclude_external
        )
