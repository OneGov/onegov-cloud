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
            'candidates',
            'connections',
            'party-strengths',
            'parties-panachage',
            'statistics',
            'lists-panachage',
            'data'
        )

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'lists':
            return _("Lists")
        if tab == 'candidates':
            return _("Candidates")
        if tab == 'connections':
            return _("List connections")
        if tab == 'party-strengths':
            return _("Party strengths")
        if tab == 'parties-panachage':
            return _("Panachage (parties)")
        if tab == 'statistics':
            return _("Election statistics")
        if tab == 'lists-panachage':
            return _("Panachage (lists)")
        if tab == 'data':
            return _("Downloads")

        return ''

    def tab_visible(self, tab):
        if not self.has_results:
            return False

        if tab == 'lists':
            return (
                self.proporz and
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
    def summarize(self):
        return self.model.results.count() != 1

    @cached_property
    def main_view(self):
        if self.majorz or self.tacit:
            return self.request.link(self.model, 'candidates')
        return self.request.link(self.model, 'lists')

    @cached_property
    def menu(self):
        return [
            (
                self.title(tab),
                self.request.link(self.model, tab),
                'active' if self.tab == tab else ''
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
                    self.model.id, self.title() or ''
                )
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
