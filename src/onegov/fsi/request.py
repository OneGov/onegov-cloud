from cached_property import cached_property
from onegov.org.request import OrgRequest


class FsiRequest(OrgRequest):

    @cached_property
    def current_attendee(self):
        self.current_user.attendee

    @cached_property
    def attendee_id(self):
        self.current_user.attendee and self.current_user.attendee.id or None