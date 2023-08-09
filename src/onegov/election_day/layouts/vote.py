from functools import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


class VoteLayout(DetailLayout):

    def __init__(self, model, request, tab='entities'):
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
    def all_tabs(self):
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

    def title(self, tab=None):
        tab = (self.tab if tab is None else tab) or ''

        if tab == 'entities':
            return self.principal.label('entities')
        if tab == 'districts':
            return self.app.principal.label('districts')
        if tab == 'statistics':
            return _("Statistics")
        if tab.startswith('proposal'):
            return _("Proposal")
        if tab.startswith('counter-proposal'):
            return _("Counter Proposal")
        if tab.startswith('tie-breaker'):
            return _("Tie-Breaker")
        if tab == 'data':
            return _("Downloads")

        return ''

    def subtitle(self, tab=None):
        tab = (self.tab if tab is None else tab) or ''

        if tab.endswith('-entities'):
            return self.principal.label('entities')
        if tab.endswith('-districts'):
            return self.app.principal.label('districts')
        if tab.endswith('-statistics'):
            return _("Statistics")

        return ''

    def tab_visible(self, tab):
        if self.hide_tab(tab):
            return False

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

    @cached_property
    def visible(self):
        return self.tab_visible(self.tab)

    @cached_property
    def type(self):
        return self.model.type

    @cached_property
    def scope(self):
        if 'entities' in self.tab:
            return 'entities'
        if 'district' in self.tab:
            return 'districts'

    @cached_property
    def ballot(self):
        if self.type == 'complex' and 'counter' in self.tab:
            return self.model.counter_proposal
        if self.type == 'complex' and 'tie-breaker' in self.tab:
            return self.model.tie_breaker
        return self.model.proposal

    @cached_property
    def map_link(self):

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

    def table_link(self, query_params=None):
        query_params = query_params or {}
        if self.tab not in self.tabs_with_embedded_tables:
            return None

        query_params['locale'] = self.request.locale

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
    def widget_link(self):
        return self.request.link(
            self.model, name='vote-header-widget'
        )

    @cached_property
    def summarize(self):
        return self.ballot.results.count() != 1

    @cached_property
    def main_view(self):
        if self.type == 'complex':
            return self.request.link(self.model, 'proposal-entities')
        for tab in self.all_tabs:
            if not self.hide_tab(tab):
                return self.request.link(self.model, tab)
        return self.request.link(self.model, 'entities')

    @cached_property
    def answer(self):
        return self.model.answer

    @cached_property
    def menu(self):
        if self.type == 'complex':
            result = []

            for title, prefix in (
                (_("Proposal"), 'proposal'),
                (_("Counter Proposal"), 'counter-proposal'),
                (_("Tie-Breaker"), 'tie-breaker')
            ):
                submenu = [
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
    def pdf_path(self):
        """ Returns the path to the PDF file or None, if it is not available.
        """

        path = 'pdf/{}'.format(
            pdf_filename(
                self.model,
                self.request.locale,
                last_modified=self.last_modified
            )
        )
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_prefix(self):
        return 'districts-map' if 'districts' in self.tab else 'entities-map'

    @cached_property
    def svg_path(self):
        """ Returns the path to the SVG file or None, if it is not available.
        """

        if not self.ballot:
            return None

        path = 'svg/{}'.format(
            svg_filename(
                self.ballot,
                self.svg_prefix,
                self.request.locale,
                last_modified=self.last_modified
            )
        )
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_link(self):
        """ Returns a link to the SVG download view. """

        return self.request.link(
            self.ballot, name='{}-svg'.format(self.svg_prefix)
        )

    @cached_property
    def svg_name(self):
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
