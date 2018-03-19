from cached_property import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.utils import svg_filename


class ElectionCompoundLayout(DetailLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    @cached_property
    def all_tabs(self):
        return (
            'districts',
            'candidates',
            'parties',
            'data'
        )

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'districts':
            return self.request.app.principal.label('districts')
        if tab == 'candidates':
            return _("Elected candidates")
        if tab == 'parties':
            return _("Parties")
        if tab == 'data':
            return _("Downloads")

        return ''

    def visible(self, tab=None):
        if not self.has_results:
            return False
        if tab == 'parties':
            return self.model.party_results.first()

        return True

    @cached_property
    def main_view(self):
        return self.request.link(self.model, 'districts')

    @cached_property
    def menu(self):
        return [
            (
                self.title(tab),
                self.request.link(self.model, tab),
                'active' if self.tab == tab else ''
            ) for tab in self.all_tabs if self.visible(tab)
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
    def svg_path(self):
        """ Returns the path to the SVG or None, if it is not available. """

        path = 'svg/{}'.format(
            svg_filename(self.model, self.tab)
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
