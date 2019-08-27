from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from webob.exc import HTTPForbidden
from webob.exc import HTTPNotFound


@ElectionDayApp.html(
    model=HTTPForbidden,
    template='exception.pt',
    permission=Public
)
def handle_forbidden(self, request):

    """ Displays a nice HTTP 403 error. """

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 403

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Access Denied"),
        'message': _(
            "You are trying to open a page for which you are not authorized."
        )
    }


@ElectionDayApp.html(
    model=HTTPNotFound,
    template='exception.pt',
    permission=Public
)
def handle_notfound(self, request):

    """ Displays a nice HTTP 404 error. """

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 404

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Page not Found"),
        'message': _("The page you are looking for could not be found."),
    }
