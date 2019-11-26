from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.models.course_attendee import CourseAttendee


class CourseAttendeeCollection(GenericCollection, Pagination):

    def __init__(self, session,
                 page=0,
                 exclude_external=False,
                 external_only=False,
                 attendee_id=None
                 ):
        super().__init__(session)
        self.page = page
        self.exclude_external = exclude_external
        self.external_only = external_only
        self.attendee_id = attendee_id

    @property
    def model_class(self):
        return CourseAttendee

    def __eq__(self, other):
        """ Returns True if the current and the other Pagination instance
        are equal. Used to find the current page in a list of pages.

        """
        return all((
            self.page == other.page,
            self.exclude_external == other.exclude_external,
            self.external_only == other.external_only,
            self.attendee_id == other.attendee_id
        ))

    @property
    def attendee_permissions(self):
        if self.attendee_id:
            return self.session.query(
                CourseAttendee).filter_by(
                id=self.attendee_id).one().permissions
        return None

    def query(self):

        query = super().query()
        query = query.order_by(
            CourseAttendee.last_name, CourseAttendee.first_name)
        if self.exclude_external:
            query = query.filter(CourseAttendee.user_id.isnot(None))
        elif self.external_only:
            query = query.filter(CourseAttendee.user_id == None)

        if self.attendee_permissions is not None:
            query = query.filter(
                CourseAttendee.organisation in self.attendee_permissions)
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
