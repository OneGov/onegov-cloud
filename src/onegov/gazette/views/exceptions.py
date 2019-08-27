from onegov.core.security import Public
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.layout import Layout
from webob.exc import HTTPForbidden
from webob.exc import HTTPNotFound


@GazetteApp.html(
    model=HTTPForbidden, permission=Public, template='exception.pt'
)
def handle_forbidden(self, request):

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 403

    return {
        'layout': Layout(self, request),
        'title': _("Access Denied"),
        'message': _(
            "You are trying to open a page for which you are not authorized."
        )
    }


@GazetteApp.html(
    model=HTTPNotFound, permission=Public, template='exception.pt'
)
def handle_notfound(self, request):

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 404

    return {
        'layout': Layout(self, request),
        'title': _("Page not Found"),
        'message': _("The page you are looking for could not be found."),
    }
