from __future__ import annotations

from functools import cached_property
from onegov.town6.request import TownRequest
from onegov.user import UserGroup


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.app import TranslatorDirectoryApp


class TranslatorAppRequest(TownRequest):

    app: TranslatorDirectoryApp

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

    @cached_property
    def is_accountant(self) -> bool:
        if not self.current_user:
            return False

        username = self.current_user.username
        groups = (
            self.session.query(UserGroup)
            .filter(UserGroup.meta['finanzstelle'].astext.isnot(None))
            .all()
        )

        for group in groups:
            accountant_emails = group.meta.get('accountant_emails', [])
            if username in accountant_emails:
                return True

        return False
