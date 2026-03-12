from __future__ import annotations

from functools import cached_property
from onegov.pas import _
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout

from typing import TYPE_CHECKING


class DefaultLayout(BaseDefaultLayout):

    if TYPE_CHECKING:
        from onegov.pas.request import PasRequest
        request: PasRequest

    @cached_property
    def pas_settings_url(self) -> str:
        return self.request.link(self.app.org, 'pas-settings')

    def format_minutes(self, value: int | None) -> str:
        if not value or value < 0:
            return ''

        hours = value // 60
        minutes = value % 60

        if hours and minutes:
            return _(
                '${hours} hours ${minutes} minutes',
                mapping={'hours': hours, 'minutes': minutes}
            )
        if hours:
            return _('${hours} hours', mapping={'hours': hours})
        return _('${minutes} minutes', mapping={'minutes': minutes})
