from functools import cached_property
from onegov.election_day.layouts.default import DefaultLayout


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.ballot.models import Election
    from onegov.ballot.models import ElectionCompound
    from onegov.ballot.models import ElectionCompoundPart
    from onegov.ballot.models import Vote
    from onegov.election_day.request import ElectionDayRequest
    from onegov.file import File


class HiddenTabsMixin:
    """
    Mixin for a generic handling of hiding any kind of menu or submenu
    tab on election, election_compound and vote detail layouts in
    combination with the yaml file config.
    """

    model: Any
    request: 'ElectionDayRequest'

    # FIXME: We don't appear to use this setting anymore and we're inconsistent
    #        about whether this is a list or a dictionary of booleans, this
    #        implementation expects a list, but principal.yaml expects a map
    #        of names to booleans, just like the other hidden elements.
    @cached_property
    def hidden_tabs(self) -> dict[str, bool]:
        return self.request.app.principal.hidden_tabs.get(self.section, {})

    def hide_tab(self, tab: str | None) -> bool:
        return tab in self.hidden_tabs

    @cached_property
    def section(self) -> str:
        """Represents section under
          principal:
            hidden_elements:
              tabs:
                <section>:
                    - tab1
                    - tab2
        """
        mapping = {
            'Vote': 'vote',
            'ComplexVote': 'vote',
            'Election': 'election',
            'ProporzElection': 'election',
            'ElectionCompound': 'elections',
            'ElectionCompoundPart': 'elections-part',
        }
        return mapping.get(self.model.__class__.__name__, '')


class DetailLayout(DefaultLayout, HiddenTabsMixin):

    """ A common base layout for election and votes which caches some values
    used in the macros.

    """

    model: 'Election | ElectionCompound | ElectionCompoundPart | Vote'
    request: 'ElectionDayRequest'

    @cached_property
    def has_results(self) -> bool:
        return self.model.has_results

    @cached_property
    def completed(self) -> bool:
        return self.model.completed

    @cached_property
    def last_result_change(self) -> 'datetime | None':
        return self.model.last_result_change

    @cached_property
    def last_modified(self) -> 'datetime | None':
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
    def explanations_pdf(self) -> 'File | None':
        return getattr(self.model, 'explanations_pdf', None)

    @cached_property
    def show_map(self) -> bool:
        if (
            self.principal.domain == 'canton'
            and getattr(self.model, 'domain', None) == 'municipality'
        ):
            return False
        return self.principal.is_year_available(self.model.date.year)
