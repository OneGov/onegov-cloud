from __future__ import annotations

from functools import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Ballot
    from onegov.election_day.models import Vote
    from onegov.election_day.request import ElectionDayRequest

    from .election import NestedMenu


class VoteLayout(DetailLayout):

    model: Vote

    def __init__(
        self,
        model: Vote,
        request: ElectionDayRequest,
        tab: str = 'entities'
    ) -> None:
        super().__init__(model, request)
        self.tab = tab

    tabs_with_embedded_tables = (
        'entities',
        'districts',
        'statistics',
        'proposal-entities',
        'proposal-districts',
        'proposal-statistics',
        'counter-proposal-entities',
        'counter-proposal-districts',
        'counter-proposal-statistics',
        'tie-breaker-entities',
        'tie-breaker-districts',
        'tie-breaker-statistics',
    )

    @cached_property
    def all_tabs(self) -> tuple[str, ...]:
        """Return all tabs. Ordering is important for the main view."""
        return (
            'entities',
            'districts',
            'statistics',
            'proposal-entities',
            'proposal-districts',
            'proposal-statistics',
            'counter-proposal-entities',
            'counter-proposal-districts',
            'counter-proposal-statistics',
            'tie-breaker-entities',
            'tie-breaker-districts',
            'tie-breaker-statistics',
            'data'
        )

    def title(self, tab: str | None = None) -> str:
        tab = (self.tab if tab is None else tab) or ''

        if tab == 'entities':
            return self.principal.label('entities')
        if tab == 'districts':
            return self.app.principal.label('districts')
        if tab == 'statistics':
            return _('Statistics')
        if tab.startswith('proposal'):
            return _('Proposal')
        if tab.startswith('counter-proposal'):
            return self.label('Counter Proposal')
        if tab.startswith('tie-breaker'):
            return _('Tie-Breaker')
        if tab == 'data':
            return _('Downloads')

        return ''

    def subtitle(self, tab: str | None = None) -> str:
        tab = (self.tab if tab is None else tab) or ''

        if tab.endswith('-entities'):
            return self.principal.label('entities')
        if tab.endswith('-districts'):
            return self.app.principal.label('districts')
        if tab.endswith('-statistics'):
            return _('Statistics')

        return ''

    def tab_visible(self, tab: str | None) -> bool:
        if not self.has_results:
            return False

        if tab == 'entities':
            return self.type == 'simple'
        if tab == 'proposal-entities':
            return self.type == 'complex'
        if tab == 'counter-proposal-entities':
            return self.type == 'complex'
        if tab == 'tie-breaker-entities':
            return self.type == 'complex'

        if tab == 'districts':
            return self.has_districts and self.type == 'simple'
        if tab == 'proposal-districts':
            return self.has_districts and self.type == 'complex'
        if tab == 'counter-proposal-districts':
            return self.has_districts and self.type == 'complex'
        if tab == 'tie-breaker-districts':
            return self.has_districts and self.type == 'complex'

        if tab == 'statistics':
            return self.type == 'simple'
        if tab == 'proposal-statistics':
            return self.type == 'complex'
        if tab == 'counter-proposal-statistics':
            return self.type == 'complex'
        if tab == 'tie-breaker-statistics':
            return self.type == 'complex'

        return True

    def label(self, value: str) -> str:
        tie_breaker = (
            self.ballot.type == 'tie-breaker'
            or self.model.tie_breaker_vocabulary
        )
        if value == 'Counter Proposal':
            if self.direct:
                return _('Direct Counter Proposal')
            return _('Indirect Counter Proposal')
        if value == 'Yay':
            return _('Proposal') if tie_breaker else _('Yay')
        if value == 'Nay':
            if not tie_breaker:
                return _('Nay')
            if self.direct:
                return _('Direct Counter Proposal')
            return _('Indirect Counter Proposal')
        if value == 'Yeas':
            return _('Proposal') if tie_breaker else _('Yeas')
        if value == 'Nays':
            if not tie_breaker:
                return _('Nays')
            if self.direct:
                return _('Direct Counter Proposal')
            return _('Indirect Counter Proposal')
        if value == 'Yes %':
            return _('Proposal %') if tie_breaker else _('Yes %')
        if value == 'No %':
            if not tie_breaker:
                return _('No %')
            if self.direct:
                return _('Direct Counter Proposal %')
            return _('Indirect Counter Proposal %')
        if value == 'Accepted':
            return _('Proposal') if tie_breaker else _('Accepted')
        if value == 'Rejected':
            if not tie_breaker:
                return _('Rejected')
            if self.direct:
                return _('Direct Counter Proposal')
            return _('Indirect Counter Proposal')

        return self.principal.label(value)

    @cached_property
    def visible(self) -> bool:
        return self.tab_visible(self.tab)

    @cached_property
    def type(self) -> str:
        return self.model.type

    @cached_property
    def scope(self) -> str | None:
        if 'entities' in self.tab:
            return 'entities'
        if 'district' in self.tab:
            return 'districts'
        return None

    @cached_property
    def ballot(self) -> Ballot:
        if self.type == 'complex' and 'counter' in self.tab:
            return self.model.counter_proposal  # type:ignore[attr-defined]
        if self.type == 'complex' and 'tie-breaker' in self.tab:
            return self.model.tie_breaker  # type:ignore[attr-defined]
        return self.model.proposal

    @cached_property
    def map_link(self) -> str | None:

        assert self.request.locale
        if self.scope == 'entities':
            return self.request.link(
                self.model,
                f'{self.ballot.type}-by-entities-map',
                query_params={'locale': self.request.locale}
            )

        if self.scope == 'districts':
            return self.request.link(
                self.model,
                f'{self.ballot.type}-by-districts-map',
                query_params={'locale': self.request.locale}
            )

        return None

    def table_link(
        self,
        query_params: dict[str, str] | None = None
    ) -> str | None:

        query_params = query_params or {}
        if self.tab not in self.tabs_with_embedded_tables:
            return None

        locale = self.request.locale
        if locale:
            query_params['locale'] = locale

        if self.scope == 'entities':
            return self.request.link(
                self.model,
                f'{self.ballot.type}-by-entities-table',
                query_params=query_params
            )

        if self.scope == 'districts':
            return self.request.link(
                self.model,
                f'{self.ballot.type}-by-districts-table',
                query_params=query_params
            )

        return self.request.link(
            self.model,
            f'{self.ballot.type}-statistics-table',
            query_params=query_params
        )

    @cached_property
    def widget_link(self) -> str:
        return self.request.link(
            self.model, name='vote-header-widget'
        )

    @cached_property
    def summarize(self) -> bool:
        return len(self.ballot.results) != 1

    @cached_property
    def main_view(self) -> str:
        if self.type == 'complex':
            return self.request.link(self.model, 'proposal-entities')
        for tab in self.all_tabs:
            return self.request.link(self.model, tab)
        return self.request.link(self.model, 'entities')

    @cached_property
    def answer(self) -> str | None:
        return self.model.answer

    @cached_property
    def direct(self) -> bool:
        return self.model.direct

    @cached_property
    def menu(self) -> NestedMenu:
        if self.type == 'complex':
            result: NestedMenu = []

            for title, prefix in (
                (_('Proposal'), 'proposal'),
                (self.label('Counter Proposal'), 'counter-proposal'),
                (_('Tie-Breaker'), 'tie-breaker')
            ):
                submenu: NestedMenu = [
                    (
                        self.subtitle(tab),
                        self.request.link(self.model, tab),
                        self.tab == tab,
                        []
                    ) for tab in (
                        f'{prefix}-entities',
                        f'{prefix}-districts',
                        f'{prefix}-statistics'
                    ) if self.tab_visible(tab)
                ]
                if submenu:
                    result.append((
                        title,
                        '',
                        self.tab.startswith(prefix),
                        submenu
                    ))
            if self.tab_visible('data'):
                result.append((
                    self.title('data'),
                    self.request.link(self.model, 'data'),
                    self.tab == 'data',
                    []
                ))
            return result

        return [
            (
                self.title(tab),
                self.request.link(self.model, tab),
                self.tab == tab,
                []
            ) for tab in self.all_tabs if self.tab_visible(tab)
        ]

    @cached_property
    def pdf_path(self) -> str | None:
        """ Returns the path to the PDF file or None, if it is not available.
        """

        assert self.request.locale
        path = 'pdf/{}'.format(
            pdf_filename(
                self.model,
                self.request.locale,
                last_modified=self.last_modified
            )
        )
        filestorage = self.request.app.filestorage
        assert filestorage is not None
        if filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_prefix(self) -> str:
        return 'districts-map' if 'districts' in self.tab else 'entities-map'

    @cached_property
    def svg_path(self) -> str | None:
        """ Returns the path to the SVG file or None, if it is not available.
        """

        if not self.ballot:
            return None

        assert self.request.locale
        path = 'svg/{}'.format(
            svg_filename(
                self.ballot,
                self.svg_prefix,
                self.request.locale,
                last_modified=self.last_modified
            )
        )
        filestorage = self.request.app.filestorage
        assert filestorage is not None
        if filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_link(self) -> str:
        """ Returns a link to the SVG download view. """

        return self.request.link(
            self.ballot, name='{}-svg'.format(self.svg_prefix)
        )

    @cached_property
    def svg_name(self) -> str:
        """ Returns a nice to read SVG filename. """

        return '{}.svg'.format(
            normalize_for_url(
                '{}-{}-{}'.format(
                    self.model.id,
                    self.request.translate(self.title() or ''),
                    self.request.translate(self.subtitle() or '')
                ).rstrip('-')
            )
        )
