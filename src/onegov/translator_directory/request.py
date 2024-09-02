from functools import cached_property

from onegov.town6.request import TownRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.app import TranslatorDirectoryApp


class TranslatorAppRequest(TownRequest):

    app: 'TranslatorDirectoryApp'

    @cached_property
    def is_member(self) -> bool:
        if self.current_user and self.current_user.role == 'member':
            return True
        return False

    @cached_property
    def is_editor(self) -> bool:
        if self.current_user and self.current_user.role == 'editor':
            return True
        return False

    @cached_property
    def is_translator(self) -> bool:
        if self.current_user and self.current_user.role == 'translator':
            return True
        return False
