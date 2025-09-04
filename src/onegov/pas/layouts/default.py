from __future__ import annotations

from functools import cached_property
from onegov.pas import _
from onegov.pas.custom import get_current_settlement_run
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models.settlement_run import SettlementRun


class DefaultLayout(BaseDefaultLayout):

    @cached_property
    def current_settlement_run(self) -> SettlementRun | None:
        try:
            return get_current_settlement_run(self.request.session)
        except Exception:  # layout.pt checks for None
            return None

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
