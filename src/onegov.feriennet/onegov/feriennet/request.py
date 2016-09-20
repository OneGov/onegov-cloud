from cached_property import cached_property
from onegov.org.request import OrgRequest
from onegov.user import UserCollection


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
            return UserCollection(self.app.session()).by_username(
                self.identity.userid)

    @property
    def current_username(self):
        return self.identity and self.identity.userid or None
