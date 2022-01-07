from onegov.election_day import _
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout
from cached_property import cached_property


class ArchiveLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

    @cached_property
    def menu(self):
        current = self.model.item_type
        return [
            (_('Votes'), self.link_for('vote'), current == 'vote'),
            (_('Elections'), self.link_for('election'), current == 'election')
        ]

    @cached_property
    def tab_menu_title(self):
        return _('Votes') if self.model.item_type == 'vote' else _('Elections')

    def link_for(self, item_type):
        return self.request.link(
            SearchableArchivedResultCollection(
                self.request.session,
                item_type=item_type))

    def instance_link(self):
        return self.link_for(self.model.item_type)
