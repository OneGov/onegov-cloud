from cached_property import cached_property
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts.default import DefaultLayout
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


class VoteLayout(DefaultLayout):

    def __init__(self, model, request, tab='proposal'):
        super().__init__(model, request)
        self.tab = tab

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'proposal':
            return _("Proposal")
        if tab == 'counter-proposal':
            return _("Counter Proposal")
        if tab == 'tie-breaker':
            return _("Tie-Breaker")
        if tab == 'data':
            return _("Downloads")

        return ''

    @cached_property
    def type(self):
        return self.model.type

    @cached_property
    def ballot(self):
        if self.tab == 'counter-proposal':
            if self.model.type == 'complex':
                return self.model.counter_proposal
            return None
        if self.tab == 'tie-breaker':
            if self.model.type == 'complex':
                return self.model.tie_breaker
            return None
        return self.model.proposal

    def visible(self, tab=None):
        if not self.model.has_results:
            return False

        tab = self.tab if tab is None else tab

        if tab == 'proposal':
            return True
        if self.tab == 'counter-proposal' or self.tab == 'tie-breaker':
            return self.model.type == 'complex'

        return True

    @cached_property
    def summarize(self):
        return self.ballot.results.count() != 1

    @cached_property
    def menu(self):
        if not self.model.has_results:
            return []

        if self.type == 'simple':
            return (
                (
                    self.title('proposal'),
                    self.request.link(self.model),
                    'active' if self.tab == 'proposal' else ''
                ), (
                    self.title('data'),
                    self.request.link(self.model, 'data'),
                    'active' if self.tab == 'data' else ''
                )
            )

        return (
            (
                self.title('proposal'),
                self.request.link(self.model),
                'active' if self.tab == 'proposal' else ''
            ), (
                self.title('counter-proposal'),
                self.request.link(self.model, 'counter-proposal'),
                'active' if self.tab == 'counter-proposal' else ''
            ), (
                self.title('tie-breaker'),
                self.request.link(self.model, 'tie-breaker'),
                'active' if self.tab == 'tie-breaker' else ''
            ), (
                self.title('data'),
                self.request.link(self.model, 'data'),
                'active' if self.tab == 'data' else ''
            )
        )

    @cached_property
    def pdf_path(self):
        """ Returns the path to the PDF file or None, if it is not available.
        """

        path = 'pdf/{}'.format(pdf_filename(self.model, self.request.locale))
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_path(self):
        """ Returns the path to the SVG file or None, if it is not available.
        """

        if not self.ballot:
            return None

        path = 'svg/{}'.format(
            svg_filename(self.ballot, 'map', self.request.locale)
        )
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_link(self):
        """ Returns a link to the SVG download view. """

        return self.request.link(self.ballot, name='svg')

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
