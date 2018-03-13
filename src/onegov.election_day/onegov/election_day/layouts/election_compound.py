from cached_property import cached_property
from onegov.election_day import _
from onegov.election_day.layouts.default import DefaultLayout


class ElectionCompoundLayout(DefaultLayout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    @cached_property
    def all_tabs(self):
        return (
            'districts',
            'candidates',
            'data'
        )

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'districts':
            return self.request.app.principal.label('districts')
        if tab == 'candidates':
            return _("Elected candidates")
        if tab == 'data':
            return _("Downloads")

        return ''

    def visible(self, tab=None):
        if not self.model.has_results:
            return False

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
