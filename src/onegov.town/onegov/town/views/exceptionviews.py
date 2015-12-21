from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.layout import DefaultLayout
from webob.exc import HTTPForbidden, HTTPNotFound


@TownApp.html(model=HTTPForbidden, permission=Public, template='forbidden.pt')
def handle_forbidden(self, request):
    """ If a view is forbidden, the request is redirected to the login
    view. There, the user may login to the site and be redirected back
    to the originally forbidden view.

    """

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 403

    layout = DefaultLayout(self, request)

    return {
        'layout': layout,
        'title': _("Access Denied"),
        'login_url': layout.login_url
    }


@TownApp.html(model=HTTPNotFound, permission=Public, template='notfound.pt')
def handle_notfound(self, request):

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 404

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Not Found"),
    }
