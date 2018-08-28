from onegov.core.security import Public
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.layouts import DefaultLayout
from webob.exc import HTTPForbidden
from webob.exc import HTTPNotFound


@SwissvotesApp.html(
    model=HTTPForbidden,
    template='exception.pt',
    permission=Public
)
def handle_forbidden(self, request):
    """ Displays a nice HTTP 403 error. """

    @request.after
    def set_status_code(response):
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Access Denied"),
        'message': _(
            "You are trying to open a page for which you are not authorized."
        )
    }


@SwissvotesApp.html(
    model=HTTPNotFound,
    template='exception.pt',
    permission=Public
)
def handle_notfound(self, request):
    """ Displays a nice HTTP 404 error. """

    @request.after
    def set_status_code(response):
        response.status_code = self.code

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Page not Found"),
        'message': _("The page you are looking for could not be found."),
    }
