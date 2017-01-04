from cached_property import cached_property
from onegov.core.request import CoreRequest


class OrgRequest(CoreRequest):

    @cached_property
    def is_manager(self):
        """ Returns true if the current user is logged in, and has the role
        editor or admin.

        """

        return self.has_role('admin', 'editor')

    @cached_property
    def is_admin(self):
        """ Returns true if the current user is an admin.

        """

        return self.has_role('admin')

    @property
    def current_username(self):
        return self.identity and self.identity.userid or None
