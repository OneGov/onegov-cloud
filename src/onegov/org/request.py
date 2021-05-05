from cached_property import cached_property
from onegov.core.request import CoreRequest
from onegov.core.security import Private
from onegov.user import User


class OrgRequest(CoreRequest):

    @cached_property
    def is_manager(self):
        """ Returns true if the current user is logged in, and has the role
        editor or admin.

        """

        return self.has_role('admin', 'editor')

    def is_manager_for_model(self, model):
        return self.has_permission(model, Private)

    @cached_property
    def is_admin(self):
        """ Returns true if the current user is an admin.

        """

        return self.has_role('admin')

    @cached_property
    def is_editor(self):
        """ Returns true if the current user is an editor.

        """

        return self.has_role('editor')

    @property
    def current_username(self):
        return self.identity and self.identity.userid or None

    @cached_property
    def current_user(self):
        if self.identity:
            return self.session.query(User) \
                .filter_by(username=self.identity.userid).first()

    @cached_property
    def first_admin_available(self):
        return self.session.query(User).filter_by(role='admin').order_by(
            User.created).first()

    def auto_accept(self, ticket):
        return ticket.handler_code in (self.app.org.ticket_auto_accepts or [])
