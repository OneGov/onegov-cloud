from cached_property import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


class ElectionCompoundLayout(DetailLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    tabs_with_embedded_tables = (
        'seat-allocation',
        'list-groups',
        'superregions',
        'districts',
        'candidates',
        'statistics'
    )

    majorz = False
    proporz = True
    type = 'compound'

    @cached_property
    def table_link(self):
        if self.tab not in self.tabs_with_embedded_tables:
            return None
        return self.request.link(
            self.model, f'{self.tab}-table'
        )

    @cached_property
    def all_tabs(self):
        """ Return the tabs in order of their appearance. """
        result = [
            'seat-allocation',
            'list-groups',
            'superregions',
            'districts',
            'candidates',
            'party-strengths',
            'parties-panachage',
            'statistics',
            'data'
        ]
        if self.model.horizontal_party_strengths:
            result.remove('party-strengths')
            result.insert(1, 'party-strengths')
        return tuple(result)

    @cached_property
    def results(self):
        return self.model.results

    @cached_property
    def has_districts(self):
        if not self.principal.has_districts:
            return False
        if self.model.domain_elections == 'municipality':
            return False
        return True

    @cached_property
    def has_superregions(self):
        return (
            self.principal.has_superregions
            and self.model.domain_elections == 'region'
        )

    def label(self, value):
        if value == 'district':
            if self.model.domain_elections == 'region':
                return self.principal.label('region')
            if self.model.domain_elections == 'municipality':
                return _("Municipality")
        if value == 'districts':
            if self.model.domain_elections == 'region':
                return self.principal.label('regions')
            if self.model.domain_elections == 'municipality':
                return _("Municipalities")
        return self.principal.label(value)

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'seat-allocation':
            return _("Seat allocation")
        if tab == 'list-groups':
            return _("List groups")
        if tab == 'superregions':
            return self.label('superregions')
        if tab == 'districts':
            return self.label('districts')
        if tab == 'candidates':
            return _("Elected candidates")
        if tab == 'party-strengths':
            return _("Party strengths")
        if tab == 'parties-panachage':
            return _("Panachage")
        if tab == 'data':
            return _("Downloads")
        if tab == 'statistics':
            return _("Election statistics")

        return ''

    def tab_visible(self, tab):

        if not self.has_results:
            return False
        if self.hide_tab(tab):
            return False
        if tab == 'superregions':
            return self.has_superregions
        if tab == 'seat-allocation':
            return (
                self.model.show_seat_allocation is True
                and self.has_party_results
            )
        if tab == 'list-groups':
            return (
                self.model.show_list_groups is True
                and self.model.pukelsheim is True
                and self.has_party_results
            )
        if tab == 'party-strengths':
            return (
                self.model.show_party_strengths is True
                and self.has_party_results
            )
        if tab == 'parties-panachage':
            return (
                self.model.show_party_panachage is True
                and self.has_party_results
            )

        return True

    @cached_property
    def has_party_results(self):
        return self.model.party_results.first() is not None

    @cached_property
    def visible(self):
        return self.tab_visible(self.tab)

    @cached_property
    def main_view(self):
        for tab in self.all_tabs:
            if self.tab_visible(tab):
                return self.request.link(self.model, tab)
        return self.request.link(self.model, 'districts')

    @cached_property
    def menu(self):
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
    def svg_path(self):
        """ Returns the path to the SVG or None, if it is not available. """

        path = 'svg/{}'.format(
            svg_filename(
                self.model,
                self.tab,
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

        return self.request.link(self.model, name='{}-svg'.format(self.tab))

    @cached_property
    def svg_name(self):
        """ Returns a nice to read SVG filename. """

        return '{}.svg'.format(
            normalize_for_url(
                '{}-{}'.format(
                    self.model.id,
                    self.request.translate(self.title() or '')
                )
            )
        )

    @property
    def summarize(self):
        return False
