from __future__ import annotations

from functools import cached_property
from onegov.election_day.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import ElectionCompoundPart
    from onegov.election_day.models import Vote
    from onegov.election_day.request import ElectionDayRequest
    from onegov.file import File


class DetailLayout(DefaultLayout):

    """ A common base layout for election and votes which caches some values
    used in the macros.

    """

    model: Election | ElectionCompound | ElectionCompoundPart | Vote
    request: ElectionDayRequest

    @cached_property
    def has_results(self) -> bool:
        return self.model.has_results

    @cached_property
    def completed(self) -> bool:
        return self.model.completed

    @cached_property
    def last_result_change(self) -> datetime | None:
        return self.model.last_result_change

    @cached_property
    def last_modified(self) -> datetime | None:
        return self.model.last_modified

    @cached_property
    def related_link(self) -> str | None:
        return getattr(self.model, 'related_link', None)

    @cached_property
    def related_link_label(self) -> str | None:
        link_labels = getattr(self.model, 'related_link_label', None)
        locale = self.request.locale
        if link_labels is None or locale is None:
            return None

        return link_labels.get(locale, None)

    @cached_property
    def explanations_pdf(self) -> File | None:
        return getattr(self.model, 'explanations_pdf', None)

    @cached_property
    def show_map(self) -> bool:
        if (
            self.principal.domain == 'canton'
            and getattr(self.model, 'domain', None) == 'municipality'
        ):
            return False
        return self.principal.is_year_available(self.model.date.year)
