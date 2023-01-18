from cached_property import cached_property
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout


class ElectionCompoundPartLayout(DetailLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    tabs_with_embedded_tables = (
        'districts',
        'candidates',
        'party-strengths',
        'statistics'
    )

    majorz = False
    proporz = True
    type = 'compound_part'

    def table_link(self, query_params={}):
        if self.tab not in self.tabs_with_embedded_tables:
            return None
        return self.request.link(
            self.model, f'{self.tab}-table', query_params=query_params
        )

    @cached_property
    def all_tabs(self):
        """ Return the tabs in order of their appearance. """
        result = [
            'districts',
            'candidates',
            'party-strengths',
            'statistics',
        ]
        if self.model.horizontal_party_strengths:
            result.remove('party-strengths')
            result.insert(0, 'party-strengths')
        return tuple(result)

    @cached_property
    def results(self):
        return self.model.results

    def label(self, value):
        if value == 'district':
            if self.model.election_compound.domain_elections == 'region':
                return self.principal.label('region')
            if self.model.election_compound.domain_elections == 'municipality':
                return _("Municipality")
        if value == 'districts':
            if self.model.election_compound.domain_elections == 'region':
                return self.principal.label('regions')
            if self.model.election_compound.domain_elections == 'municipality':
                return _("Municipalities")
        return self.principal.label(value)

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'districts':
            return self.label('districts')
        if tab == 'candidates':
            return _("Elected candidates")
        if tab == 'party-strengths':
            return _("Party strengths")
        if tab == 'statistics':
            return _("Election statistics")

        return ''

    def tab_visible(self, tab):

        if not self.has_results:
            return False
        if self.hide_tab(tab):
            return False
        if tab == 'party-strengths':
            return (
                self.model.show_party_strengths is True
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

    @property
    def svg_path(self):
        return None

    @property
    def summarize(self):
        return False
