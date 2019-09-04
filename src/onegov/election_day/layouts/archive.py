from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout
from cached_property import cached_property
from onegov.election_day.models import ArchivedResult


class ArchiveLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

    @cached_property
    def menu(self):

        return [
            (label, self.link_for(abbrev), self.model.item_type == abbrev)
            for abbrev, label in ArchivedResult.types_of_results[0:2]
        ]

    @cached_property
    def tab_menu_title(self):
        mapping = {k: v for k, v in ArchivedResult.types_of_results}
        return mapping[self.model.item_type]

    def link_for(self, item_type):
        return self.request.link(
            SearchableArchivedResultCollection(
                self.request.session,
                item_type=item_type))

    def instance_link(self):
        return self.link_for(self.model.item_type)
