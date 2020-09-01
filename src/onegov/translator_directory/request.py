from cached_property import cached_property

from onegov.org.request import OrgRequest


class TranslatorAppRequest(OrgRequest):

    @cached_property
    def is_member(self):
        return self.current_user \
               and self.current_user.role == 'member' or False
