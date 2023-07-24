from datetime import date
from functools import cached_property
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
            'Vote': 'vote',
            'ComplexVote': 'vote',
            'Election': 'election',
            'ProporzElection': 'election',
            'ElectionCompound': 'elections',
            'ElectionCompoundPart': 'elections-part',
        }
        return mapping.get(self.model.__class__.__name__, '')


class DetailLayout(DefaultLayout, HiddenTabsMixin):

    """ A common base layout for election and votes which caches some values
    used in the macros.

    """

    def __init__(self, model, request):
        super().__init__(model, request)

        if self.model.date == date.today():
            self.custom_body_attributes['data-websocket-endpoint'] = \
                self.app.websockets_client_url(request)
            self.custom_body_attributes['data-websocket-schema'] = \
                self.app.schema
            self.custom_body_attributes['data-websocket-fallback'] = \
                request.link(self.model, 'last-notified')

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
    def related_link_label(self):
        return self.model.related_link_label.get(self.request.locale, None)

    @cached_property
    def explanations_pdf(self):
        return self.model.explanations_pdf

    @cached_property
    def show_map(self):
        if (
            self.principal.domain == 'canton'
            and getattr(self.model, 'domain', None) == 'municipality'
        ):
            return False
        return self.principal.is_year_available(self.model.date.year)
