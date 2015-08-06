""" The login/logout views. """

import morepath

from onegov.core.security import Public, Private
from onegov.town import _, log
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import LoginForm
from onegov.town.layout import DefaultLayout
from onegov.town.models import Town
from purl import URL


@TownApp.form(
    model=Town, name='login', template='login.pt', permission=Public,
    form=LoginForm
)
def handle_login(self, request, form):
    """ Handles the GET and POST login requests. """

    if 'to' in request.params:
        url = URL(form.action).query_param('to', request.params['to'])
        form.action = url.as_string()

    if form.submitted(request):
        identity = form.get_identity(request)

        if identity is not None:

            # redirect to the url the 'to' parameter points to, or to the
            # homepage of the town
            to = request.params.get('to', request.link(self))
            response = morepath.redirect(to)

            morepath.remember_identity(response, request, identity)

            request.success(_("You have been logged in."))
            return response
        else:
            request.alert(_("Wrong username or password."))
            log.info("Failed login attempt by {}".format(request.client_addr))

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Login"), request.link(self, name='login'))
    ]

    return {
        'layout': layout,
        'password_reset_link': request.link(self, name='request-password'),
        'title': _(u'Login to ${town}', mapping={'town': self.name}),
        'form': form
    }


@TownApp.html(
    model=Town, name='logout', permission=Private,
    request_method='GET')
def view_logout(self, request):
    """ Handles the logout requests. """

    response = morepath.redirect(request.link(self))
    morepath.forget_identity(response, request)

    request.info(_("You have been logged out."))
    return response
