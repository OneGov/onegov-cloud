from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultLayout
from onegov.user.auth import Auth
from webob.exc import HTTPForbidden, HTTPNotFound


@OrgApp.html(model=HTTPForbidden, permission=Public, template='forbidden.pt')
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
        'login_url': request.link(
            Auth.from_request_path(request), name='login')
    }


@OrgApp.html(model=HTTPNotFound, permission=Public, template='notfound.pt')
def handle_notfound(self, request):

    @request.after
    def set_status_code(response):
        response.status_code = self.code  # pass along 404

    return {
        'layout': DefaultLayout(self, request),
        'title': _("Not Found"),
    }
