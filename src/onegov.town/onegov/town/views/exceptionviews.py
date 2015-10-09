from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.layout import DefaultLayout
from webob.exc import HTTPForbidden


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
