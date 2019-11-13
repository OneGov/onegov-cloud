from cached_property import cached_property
from onegov.org.request import OrgRequest


class FsiRequest(OrgRequest):

    @cached_property
    def current_attendee(self):
        return self.current_user and self.current_user.attendee or None

    @cached_property
    def attendee_id(self):
        return (
            self.current_attendee and self.current_attendee.id or None
        )
