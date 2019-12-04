from sqlalchemy import or_

from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.models.course_attendee import CourseAttendee


class CourseAttendeeCollection(GenericCollection, Pagination):

    def __init__(self, session,
                 page=0,
                 exclude_external=False,
                 external_only=False,
                 attendee_id=None,
                 editors_only=False
                 ):
        super().__init__(session)
        self.page = page
        self.exclude_external = exclude_external
        self.external_only = external_only
        self.attendee_id = attendee_id
        self.editors_only = editors_only

    @property
    def unfiltered(self):
        return all((
            self.exclude_external is False,
            self.external_only is False,
            self.editors_only is False
        ))

    @property
    def model_class(self):
        return CourseAttendee

    def __eq__(self, other):
        """ Returns True if the current and the other Pagination instance
        are equal. Used to find the current page in a list of pages.

        """
        return all((
            self.page == other.page,
            self.external_only == other.exclude_external,
            self.external_only == other.external_only))

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
            query = query.filter(or_(
                CourseAttendee.organisation.in_(self.attendee_permissions,),
                CourseAttendee.user_id == None
            )
                )
        if self.editors_only:
            query = query.filter(CourseAttendee.permissions != [])

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
