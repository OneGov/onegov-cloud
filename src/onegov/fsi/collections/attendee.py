from sqlalchemy import or_

from onegov.core.collection import Pagination, GenericCollection
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.user import User


class CourseAttendeeCollection(GenericCollection, Pagination):

    def __init__(self, session,
                 page=0,
                 exclude_external=False,
                 external_only=False,
                 auth_attendee=None,
                 editors_only=False,
                 admins_only=False
                 ):
        super().__init__(session)
        self.page = page
        self.exclude_external = exclude_external
        self.external_only = external_only
        self.auth_attendee = auth_attendee
        self.editors_only = editors_only
        self.admins_only = admins_only

    @property
    def unfiltered(self):
        return all((
            self.exclude_external is False,
            self.external_only is False,
            self.editors_only is False,
            self.admins_only is False
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
            self.exclude_external == other.exclude_external,
            self.external_only == other.external_only))

    @property
    def attendee_permissions(self):
        if self.auth_attendee:
            return self.auth_attendee.permissions or []
        return []

    def query(self):

        query = super().query()
        query = query.order_by(
            CourseAttendee.last_name, CourseAttendee.first_name)
        if self.exclude_external:
            query = query.filter(CourseAttendee.user_id.isnot(None))
        elif self.external_only:
            query = query.filter(CourseAttendee.user_id == None)

        if self.auth_attendee and self.auth_attendee.role == 'editor':
            query = query.filter(
                or_(CourseAttendee.organisation.in_(
                    self.attendee_permissions,),
                    CourseAttendee.id == self.auth_attendee.id)
            )
        if self.editors_only:
            assert not self.exclude_external
            assert not self.external_only
            query = query.join(User)
            query = query.filter(User.role == 'editor')
        elif self.admins_only:
            query = query.join(User)
            query = query.filter(User.role == 'admin')

        return query

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session, index,
            exclude_external=self.exclude_external,
            external_only=self.external_only,
            auth_attendee=self.auth_attendee,
            editors_only=self.editors_only
        )

    def add_from_user(self, user):
        default = 'Default Value'
        self.add(
            user_id=user.id,
            first_name=default,
            last_name=default,
            email=user.username
        )

    def by_id(self, id):
        return super().query().filter(self.primary_key == id).first()
