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
        'lists', 'districts', 'candidates', 'statistics'
    )

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
        return (
            'lists',
            'districts',
            'candidates',
            'mandate-allocation',
            'party-strengths',
            'parties-panachage',
            'statistics',
            'data'
        )

    @property
    def results(self):
        for e in self.model.elections:
            for result in e.results:
                yield result

    def label(self, value):
        if self.model.aggregated_by_entity and value == 'district':
            return self.principal.label('entity')
        if self.model.aggregated_by_entity and value == 'districts':
            return self.principal.label('entities')
        return self.principal.label(value)

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'lists':
            return _("Lists")
        if tab == 'districts':
            return self.label('districts')
        if tab == 'candidates':
            return _("Elected candidates")
        if tab == 'mandate-allocation':
            return _("Mandate allocation")
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
        if tab == 'lists':
            return self.model.show_lists is True
        if tab == 'mandate-allocation':
            return (
                self.model.show_mandate_allocation is True
                and self.model.party_results.first() is not None
            )
        if tab == 'party-strengths':
            return (
                self.model.show_party_strengths is True
                and self.has_party_results
            )
        if tab == 'parties-panachage':
            return (
                self.model.show_party_panachage is True
                and self.model.panachage_results.first() is not None
            )

        return True

    def election_title(self, election):
        result = election.results.first()
        if result:
            if self.model.aggregated_by_entity:
                return result.name
            else:
                return election.district
        return election.title

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
    def majorz(self):
        if not self.model.elections:
            return False
        return self.model.elections[0].type == 'majorz'

    @cached_property
    def proporz(self):
        if not self.model.elections:
            return False
        return self.model.elections[0].type == 'proporz'

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
