from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.layout import DefaultLayout
from onegov.town.model import Town
from purl import URL
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

    town = request.app.session().query(Town).first()
    url = URL(request.link(town, name='login')).query_param('to', request.url)

    return {
        'layout': DefaultLayout(self, request),
        'title': _(u"Access Denied"),
        'login_url': url
    }
