from cached_property import cached_property
from onegov.election_day.layouts.default import DefaultLayout


class HiddenTabsMixin:
    """
    Mixin for a generic handling of hiding any kind of menu or submenu
    tab on election, election_compound and vote detail layouts in
    combination with the yaml file config.
    """

    @cached_property
    def hidden_tabs(self):
        return self.request.app.principal.hidden_tabs.get(self.section, [])

    def hide_tab(self, tab):
        return tab in self.hidden_tabs

    @cached_property
    def section(self):
        """Represents section under
          principal:
            hidden_elements:
              tabs:
                <section>:
                    - tab1
                    - tab2
        """
        mapping = {
            'votes': 'vote',
            'elections': 'election',
            'election_compounds': 'elections'
        }
        return mapping.get(self.model.__tablename__, '')


class DetailLayout(DefaultLayout, HiddenTabsMixin):

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

    @cached_property
    def related_link_label(self):
        return self.model.related_link_label.get(self.request.locale, None)
