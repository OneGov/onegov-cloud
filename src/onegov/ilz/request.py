from __future__ import annotations

from onegov.core.orm import orm_cached
from onegov.town6.request import TownRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import PageMeta


class ILZRequest(TownRequest):

    def is_visible(self, model: object) -> bool:
        if not super().is_visible(model):
            return False

        if self.is_manager:
            return True

        locale = getattr(model, 'locale', None)
        if locale is None:
            return True

        return locale == self.locale

    @orm_cached(policy='on-table-change:pages', by_role=True)
    def pages_tree(self) -> tuple[PageMeta, ...]:
        """ Only includes the pages of the current locale, even for managers,
        so the navigation is the same as for the public. Managers can still
        reach the pages of other locales through the translation links.

        """

        def in_locale(
            pages: tuple[PageMeta, ...]
        ) -> tuple[PageMeta, ...]:
            return tuple(
                page._replace(children=in_locale(page.children))
                for page in pages
                if page.locale is None or page.locale == self.locale
            )

        return in_locale(super().pages_tree)
