from cached_property import cached_property
from onegov.org.request import OrgRequest
from onegov.user import User


class FeriennetRequest(OrgRequest):

    @cached_property
    def is_organiser(self):
        """ Returns true if the current user is an organiser or better.

        """

        return self.has_role('admin', 'editor')

    @cached_property
    def is_organiser_only(self):
        """ Returns true if the current user is an organiser, but not an admin.

        """

        return self.has_role('editor')

    @cached_property
    def is_manager(self):
        """ Using feriennet only admins are managers. The editors are
        organisers with a very limited set of capabilities.

        """

        return self.is_admin

    @cached_property
    def is_admin(self):
        """ Returns true if the current user is an admin. """

        return self.has_role('admin')

    @cached_property
    def current_user(self):
        if self.identity:
            return self.session.query(User)\
                .filter_by(username=self.identity.userid).first()
