from functools import cached_property
from onegov.core.request import CoreRequest
from onegov.core.security import Private
from onegov.org.models import TANAccessCollection
from onegov.user import User
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.app import OrgApp


class OrgRequest(CoreRequest):

    if TYPE_CHECKING:
        app: 'OrgApp'

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

    @cached_property
    def auto_accept_user(self):
        username = self.app.org.auto_closing_user
        usr = None
        if username:
            usr = self.session.query(User)
            usr = usr.filter_by(username=username, role='admin').first()
        return usr or self.first_admin_available

    @cached_property
    def email_for_new_tickets(self):
        return self.app.org.email_for_new_tickets

    @cached_property
    def active_mtan_session(self) -> bool:
        mtan_verified = self.browser_session.get('mtan_verified')
        if mtan_verified is None:
            return False

        session_duration = self.app.org.mtan_session_duration
        if mtan_verified + session_duration < utcnow():
            return False

        return True

    @cached_property
    def mtan_accesses(self) -> TANAccessCollection:
        return TANAccessCollection(
            self.session,
            session_id=self.browser_session.mtan_number,
            access_window=self.app.org.mtan_access_window
        )

    @cached_property
    def mtan_access_limit_exceeded(self) -> bool:
        limit = self.app.org.mtan_access_window_requests
        if limit is None:
            # no limit so we can't exceed it
            return False

        # if we're below the limit we're fine
        if self.mtan_accesses.count() < limit:
            return False

        # if we already accessed this url we are also still fine
        return self.mtan_accesses.by_url(self.path_url) is None

    def auto_accept(self, ticket):
        if self.app.org.ticket_auto_accept_style == 'role':
            roles = self.app.org.ticket_auto_accept_roles
            if not roles:
                return False
            return self.has_role(*roles)
        return ticket.handler_code in (self.app.org.ticket_auto_accepts or [])
