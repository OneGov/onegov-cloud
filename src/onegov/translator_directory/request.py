from cached_property import cached_property

from onegov.org.request import OrgRequest


class TranslatorAppRequest(OrgRequest):

    @cached_property
    def is_member(self):
        if self.current_user and self.current_user.role == 'member':
            return True
        return False

    @cached_property
    def is_editor(self):
        if self.current_user and self.current_user.role == 'editor':
            return True
        return False

    @cached_property
    def is_translator(self):
        if self.current_user and self.current_user.role == 'translator':
            return True
        return False
