from cached_property import cached_property
# todo: ?
# from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
# todo: ?
# from onegov.election_day.utils import svg_filename


class ElectionCompoundPartLayout(DetailLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    # todo: ?
    # tabs_with_embedded_tables = (
    #     'seat-allocation',
    #     'list-groups',
    #     'superregions',
    #     'districts',
    #     'candidates',
    #     'statistics'
    # )

    majorz = False
    proporz = True
    # todo: ?
    # type = 'compound'

    # todo: ?
    # @cached_property
    # def table_link(self):
    #     if self.tab not in self.tabs_with_embedded_tables:
    #         return None
    #     return self.request.link(
    #         self.model, f'{self.tab}-table'
    #     )

    @cached_property
    def all_tabs(self):
        """ Return the tabs in order of their appearance. """
        return (
            'districts',
            # todo: ?
            # 'candidates',
            # 'party-strengths',
            # 'statistics',
            # 'data'
        )

    # todo: ?
    # @cached_property
    # def results(self):
    #     return self.model.results

    # todo: ?
    # @cached_property
    # def has_districts(self):
    #     if not self.principal.has_districts:
    #         return False
    #     if self.model.domain_elections == 'municipality':
    #         return False
    #     return True

    # todo: ?
    # @cached_property
    # def has_superregions(self):
    #     return (
    #         self.principal.has_superregions
    #         and self.model.domain_elections == 'region'
    #     )

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
        # todo: ?
        # if tab == 'candidates':
        #     return _("Elected candidates")
        # if tab == 'party-strengths':
        #     return _("Party strengths")
        # if tab == 'data':
        #     return _("Downloads")
        # if tab == 'statistics':
        #     return _("Election statistics")

        return ''

    def tab_visible(self, tab):

        if not self.has_results:
            return False
        # todo: ?
        # if tab == 'party-strengths':
        #     return (
        #         self.model.show_party_strengths is True
        #         and self.has_party_results
        #     )
        return True

    # todo: ?
    # @cached_property
    # def has_party_results(self):
    #     return self.model.party_results.first() is not None

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

    # todo: ?
    # @cached_property
    # def svg_path(self):
    #     """ Returns the path to the SVG or None, if it is not available. """
    #
    #     path = 'svg/{}'.format(
    #         svg_filename(
    #             self.model,
    #             self.tab,
    #             self.request.locale,
    #             last_modified=self.last_modified
    #         )
    #     )
    #     if self.request.app.filestorage.exists(path):
    #         return path
    #
    #     return None

    # todo: ?
    # @cached_property
    # def svg_link(self):
    #     """ Returns a link to the SVG download view. """
    #
    #     return self.request.link(self.model, name='{}-svg'.format(self.tab))

    # todo: ?
    # @cached_property
    # def svg_name(self):
    #     """ Returns a nice to read SVG filename. """
    #
    #     return '{}.svg'.format(
    #         normalize_for_url(
    #             '{}-{}'.format(
    #                 self.model.id,
    #                 self.request.translate(self.title() or '')
    #             )
    #         )
    #     )

    # todo: ?
    # @property
    # def summarize(self):
    #     return False
