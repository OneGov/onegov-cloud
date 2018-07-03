from cached_property import cached_property
from onegov.election_day.layouts.default import DefaultLayout


class DetailLayout(DefaultLayout):

    """ A common base layout for election and votes which caches some values
    used in the macros.

    """

    @cached_property
    def has_results(self):
        return self.model.has_results

    @cached_property
    def completed(self):
        return self.model.completed

    @cached_property
    def last_result_change(self):
        return self.model.last_result_change

    @cached_property
    def last_modified(self):
        return self.model.last_modified

    @cached_property
    def related_link(self):
        return self.model.related_link

    @cached_property
    def show_map(self):
        return self.principal.is_year_available(self.model.date.year)
