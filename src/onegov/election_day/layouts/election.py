from __future__ import annotations

from functools import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.models import ProporzElection
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionResult
    from onegov.election_day.request import ElectionDayRequest
    from typing import TypeAlias

    NestedMenu: TypeAlias = list[tuple[
        str,
        str,
        bool,
        'NestedMenu'
    ]]


class ElectionLayout(DetailLayout):

    model: Election

    def __init__(
        self,
        model: Election,
        request: ElectionDayRequest,
        tab: str | None = None
    ) -> None:
        super().__init__(model, request)
        self.tab = tab

    tabs_with_embedded_tables = (
        'lists',
        'candidates',
        'party-strengths',
        'statistics',
        'connections'
    )

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
        return self.request.link(
            self.model, f'{self.tab}-table', query_params=query_params
        )

    @cached_property
    def all_tabs(self) -> tuple[str, ...]:
        return (
            'lists',
            'list-by-entity',
            'list-by-district',
            'connections',
            'lists-panachage',
            'candidates',
            'candidate-by-entity',
            'candidate-by-district',
            'party-strengths',
            'parties-panachage',
            'statistics',
            'data'
        )

    @cached_property
    def has_districts(self) -> bool:
        if not self.principal.has_districts:
            return False
        if self.model.domain in ('region', 'district', 'none'):
            return False
        if self.model.domain == 'municipality':
            if self.principal.domain != 'municipality':
                return False
        return True

    def title(self, tab: str | None = None) -> str:
        tab = (self.tab if tab is None else tab) or ''

        if tab.startswith('list') or tab == 'connections':
            return _('Lists')
        if tab.startswith('candidate'):
            return _('Candidates')
        if tab == 'party-strengths' or tab == 'parties-panachage':
            return _('Parties')
        if tab == 'statistics':
            return _('Election statistics')
        if tab == 'data':
            return _('Downloads')

        return ''

    def subtitle(self, tab: str | None = None) -> str:
        tab = (self.tab if tab is None else tab) or ''

        if tab.endswith('-by-entity'):
            by = self.request.translate(self.principal.label('entity'))
            by = by.lower() if self.request.locale != 'de_CH' else by
            return _('By ${by}', mapping={'by': by})
        if tab.endswith('-by-district'):
            by = self.request.translate(self.principal.label('district'))
            by = by.lower() if self.request.locale != 'de_CH' else by
            return _('By ${by}', mapping={'by': by})
        if tab.endswith('-panachage'):
            return _('Panachage')
        if tab == 'connections':
            return _('List connections')
        if tab == 'party-strengths':
            return _('Party strengths')

        return ''

    def tab_visible(self, tab: str | None) -> bool:
        if not self.has_results:
            return False
        if tab == 'lists':
            return (
                self.proporz
                and not self.tacit
            )
        if tab == 'list-by-entity':
            return (
                self.show_map
                and self.proporz
                and not self.tacit
            )
        if tab == 'list-by-district':
            return (
                self.show_map
                and self.has_districts
                and self.proporz
                and not self.tacit
            )
        if tab == 'candidate-by-entity':
            return (
                self.has_candidates
                and self.show_map
                and not self.tacit
            )
        if tab == 'candidate-by-district':
            return (
                self.has_candidates
                and self.show_map
                and self.has_districts
                and not self.tacit
            )
        if tab == 'connections':
            return (
                self.proporz
                and not self.tacit
                and self.model.list_connections  # type:ignore[attr-defined]
            )
        if tab == 'party-strengths':
            return (
                self.proporz
                and not self.tacit
                and self.model.show_party_strengths is True
                and self.has_party_results
            )
        if tab == 'parties-panachage':
            return (
                self.proporz
                and not self.tacit
                and self.model.show_party_panachage is True
                and self.has_party_panachage_results
            )
        if tab == 'statistics':
            return not self.tacit
        if tab == 'lists-panachage':
            return (
                self.proporz
                and not self.tacit
                and (
                    self.model
                    .has_lists_panachage_data  # type:ignore[attr-defined]
                )
            )

        return True

    @cached_property
    def visible(self) -> bool:
        return self.tab_visible(self.tab)

    @cached_property
    def type(self) -> str:
        return self.model.type

    @cached_property
    def majorz(self) -> bool:
        return self.type == 'majorz'

    @cached_property
    def proporz(self) -> bool:
        return self.type == 'proporz'

    @cached_property
    def tacit(self) -> bool:
        if self.model.tacit:
            return True
        return False

    @cached_property
    def has_candidates(self) -> bool:
        if self.model.candidates:
            return True
        return False

    @cached_property
    def has_party_results(self) -> bool:
        if isinstance(self.model, ProporzElection):
            return self.model.has_party_results
        return False

    @cached_property
    def has_party_panachage_results(self) -> bool:
        if isinstance(self.model, ProporzElection):
            return self.model.has_party_panachage_results
        return False

    @cached_property
    def summarize(self) -> bool:
        return len(self.model.results) != 1

    @cached_property
    def main_view(self) -> str:
        if self.majorz or self.tacit:
            return self.request.link(self.model, 'candidates')
        for tab in self.all_tabs:
            return self.request.link(self.model, tab)
        return self.request.link(self.model, 'lists')

    @cached_property
    def menu(self) -> NestedMenu:
        result: NestedMenu = []

        submenus = (
            (_('Lists'), ('lists', 'list-by-entity', 'list-by-district',
                          'lists-panachage', 'connections')),
            (_('Candidates'), ('candidates', 'candidate-by-entity',
                               'candidate-by-district')),
            (_('Parties'), ('party-strengths', 'parties-panachage'))
        )
        for title, group in submenus:
            if any(self.tab_visible(tab) for tab in group):
                submenu: NestedMenu = [
                    (
                        self.subtitle(tab) or self.title(tab),
                        self.request.link(self.model, tab),
                        self.tab == tab,
                        []
                    ) for tab in group if self.tab_visible(tab)
                ]
                if len(submenu) > 1:
                    result.append((
                        title,
                        '',
                        any(item[2] for item in submenu),
                        submenu
                    ))
                elif submenu:
                    result.append(submenu[0])

        for tab in ('statistics', 'data'):
            if self.tab_visible(tab):
                result.append((
                    self.title(tab),
                    self.request.link(self.model, tab),
                    self.tab == tab,
                    []
                ))

        return result

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
    def svg_path(self) -> str | None:
        """ Returns the path to the SVG or None, if it is not available. """

        assert self.request.locale
        path = 'svg/{}'.format(
            svg_filename(
                self.model,
                self.tab,
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

        return self.request.link(self.model, name='{}-svg'.format(self.tab))

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

    @cached_property
    def related_elections(self) -> list[tuple[str | None, str]]:
        result_set = {r.target for r in self.model.related_elections}
        result = sorted(result_set, key=lambda x: x.date, reverse=True)
        return [(e.title, self.request.link(e)) for e in result]

    @cached_property
    def results(self) -> list[ElectionResult]:
        return self.model.results
