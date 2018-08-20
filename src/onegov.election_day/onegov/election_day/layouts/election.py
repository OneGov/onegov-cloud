from cached_property import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


class ElectionLayout(DetailLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    @cached_property
    def all_tabs(self):
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

    def title(self, tab=None):
        tab = (self.tab if tab is None else tab) or ''

        if tab.startswith('list') or tab == 'connections':
            return _("Lists")
        if tab.startswith('candidate'):
            return _("Candidates")
        if tab == 'party-strengths' or tab == 'parties-panachage':
            return _("Parties")
        if tab == 'statistics':
            return _("Election statistics")
        if tab == 'data':
            return _("Downloads")

        return ''

    def subtitle(self, tab=None):
        tab = (self.tab if tab is None else tab) or ''

        if tab.endswith('-by-entity'):
            return self.principal.label('entities')
        if tab.endswith('-by-district'):
            return self.principal.label('districts')
        if tab.endswith('-panachage'):
            return _("Panachage")
        if tab == 'connections':
            return _("List connections")
        if tab == 'party-strengths':
            return _("Party strengths")

        return ''

    def tab_visible(self, tab):
        if not self.has_results:
            return False

        if tab == 'lists':
            return (
                self.proporz and
                not self.tacit
            )
        if tab == 'list-by-entity':
            return (
                self.show_map and
                self.proporz and
                not self.tacit
            )
        if tab == 'list-by-district':
            return (
                self.show_map and
                self.has_districts and
                self.proporz and
                not self.tacit
            )
        if tab == 'candidate-by-entity':
            return (
                self.has_candidates and
                self.show_map and
                not self.tacit
            )
        if tab == 'candidate-by-district':
            return (
                self.has_candidates and
                self.show_map and
                self.has_districts and
                not self.tacit
            )
        if tab == 'connections':
            return (
                self.proporz and
                not self.tacit and
                self.model.list_connections.first() is not None
            )
        if tab == 'party-strengths':
            return (
                self.proporz and
                not self.tacit and
                self.model.party_results.first() is not None
            )
        if tab == 'parties-panachage':
            return (
                self.proporz and
                not self.tacit and
                self.model.panachage_results.first() is not None
            )
        if tab == 'statistics':
            return not self.tacit
        if tab == 'lists-panachage':
            return (
                self.proporz and
                not self.tacit and
                self.model.has_lists_panachage_data
            )

        return True

    @cached_property
    def visible(self):
        return self.tab_visible(self.tab)

    @cached_property
    def majorz(self):
        if self.model.type == 'majorz':
            return True
        return False

    @cached_property
    def proporz(self):
        if self.model.type == 'proporz':
            return True
        return False

    @cached_property
    def tacit(self):
        if self.model.tacit:
            return True
        return False

    @cached_property
    def has_candidates(self):
        if self.model.candidates.first():
            return True
        return False

    @cached_property
    def summarize(self):
        return self.model.results.count() != 1

    @cached_property
    def main_view(self):
        if self.majorz or self.tacit:
            return self.request.link(self.model, 'candidates')
        return self.request.link(self.model, 'lists')

    @cached_property
    def menu(self):
        result = []

        submenus = (
            (_("Lists"), ('lists', 'list-by-entity', 'list-by-district',
                          'lists-panachage', 'connections')),
            (_("Candidates"), ('candidates', 'candidate-by-entity',
                               'candidate-by-district')),
            (_("Parties"), ('party-strengths', 'parties-panachage'))
        )
        for title, group in submenus:
            if any([self.tab_visible(tab) for tab in group]):
                submenu = [
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
                        any([item[2] for item in submenu]),
                        submenu
                    ))
                elif len(submenu):
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
                '{}-{}-{}'.format(
                    self.model.id,
                    self.request.translate(self.title() or ''),
                    self.request.translate(self.subtitle() or '')
                ).rstrip('-')
            )
        )

    @cached_property
    def related_elections(self):
        return [
            (
                association.target_election.title,
                self.request.link(association.target_election)
            )
            for association in self.model.related_elections
        ]
