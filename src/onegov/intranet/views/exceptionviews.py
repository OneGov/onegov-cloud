import morepath

from onegov.core.security import Public
from onegov.intranet import IntranetApp
from onegov.org.views.exceptionviews import handle_forbidden
from onegov.user import Auth
from purl import URL
from webob.exc import HTTPForbidden


@IntranetApp.html(model=HTTPForbidden, permission=Public,
                  template='forbidden.pt')
def handle_forbidden_for_homepage(self, request):
    """ Usually, the forbidden view offers no way to log in, as we usually
    do not need that feature (exception views should be simple).

    For the intranet though, we make an exception for requests hitting the
    front-page directly.

    This is not strictly correct as far as HTTP is concerned.

    """

    login_url = request.link(Auth.from_request_path(request), name='login')

    if URL(request.url).path() == '/':
        return morepath.redirect(login_url)

    return handle_forbidden(self, request)
