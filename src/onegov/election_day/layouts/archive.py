from __future__ import annotations

from functools import cached_property
from onegov.election_day import _
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest


class ArchiveLayout(DefaultLayout):

    model: SearchableArchivedResultCollection

    def __init__(
        self,
        model: SearchableArchivedResultCollection,
        request: ElectionDayRequest
    ) -> None:
        super().__init__(model, request)

    @cached_property
    def menu(self) -> list[tuple[str, str, bool]]:
        current = self.model.item_type
        return [
            (_('Votes'), self.link_for('vote'), current == 'vote'),
            (_('Elections'), self.link_for('election'), current == 'election')
        ]

    @cached_property
    def tab_menu_title(self) -> str:
        return _('Votes') if self.model.item_type == 'vote' else _('Elections')

    def link_for(self, item_type: str | None) -> str:
        return self.request.link(
            SearchableArchivedResultCollection(
                self.request.app,
                item_type=item_type))
