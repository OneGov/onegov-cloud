from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import Layout
from webob.exc import HTTPForbidden, HTTPNotFound


@ElectionDayApp.html(
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


@ElectionDayApp.html(
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
