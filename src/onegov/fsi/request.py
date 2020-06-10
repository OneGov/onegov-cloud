from cached_property import cached_property
from onegov.org.request import OrgRequest


class FsiRequest(OrgRequest):

    @cached_property
    def attendee(self):
        return self.current_user and self.current_user.attendee or None

    @cached_property
    def attendee_id(self):
        return (
                self.attendee and self.attendee.id or None
        )

    @cached_property
    def is_editor(self):
        return self.current_user \
            and self.current_user.role == 'editor' or False

    @cached_property
    def is_member(self):
        return self.current_user \
            and self.current_user.role == 'member' or False
