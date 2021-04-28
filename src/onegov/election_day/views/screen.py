from chameleon import PageTemplate
from onegov.core.security import Public
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Screen
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.html(
    model=Screen,
    template='screen.pt',
    permission=Public
)
def view_screen(self, request):

    """ Shows a screen """

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    registry = request.app.config.screen_widget_registry
    widgets = registry.by_categories(self.screen_type.categories).values()
    if self.type in ('simple_vote', 'complex_vote'):
        layout = VoteLayout(self.model, request)
    elif self.type in ('majorz_election', 'proporz_election'):
        layout = ElectionLayout(self.model, request)
    elif self.type == 'election_compound':
        layout = ElectionCompoundLayout(self.model, request)

    template = PageTemplate(transform_structure(widgets, self.structure))

    default = {
        'layout': layout,
        'template': template,
        'screen': self,
    }

    return inject_variables(widgets, layout, self.structure, default, False)


@ElectionDayApp.view(
    model=Screen,
    request_method='HEAD',
    permission=Public
)
def view_screen_head(self, request):

    """ Shows a screen """

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)
