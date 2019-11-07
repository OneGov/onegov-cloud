from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.models.course_attendee import CourseAttendee


class CourseAttendeeCollection(GenericCollection, Pagination):

    def __init__(self, session, page=0, exclude_external=False):
        super().__init__(session)
        self.page = page
        self.exclude_external = exclude_external

    @property
    def model_class(self):
        return CourseAttendee

    def query(self):
        query = super().query()
        query = query.order_by(
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

    def add_from_user(self, user):
        default = 'Default Value'
        data = dict(
            user_id=user.id,
            first_name=default,
            last_name=default,
            email=user.username,
        )
        self.add(**data)
