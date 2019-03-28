from onegov.core.security import Public
from onegov.winterthur import WinterthurApp, _
from onegov.org.layout import DefaultLayout
from onegov.winterthur.roadwork import RoadworkConnectionError


@WinterthurApp.html(
    model=RoadworkConnectionError,
    permission=Public,
    template='roadwork_connection_error.pt')
def handle_roadwork_connection_error(self, request):

    @request.after
    def set_status_code(response):
        response.status_code = 500

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Connection Error"),
    }
