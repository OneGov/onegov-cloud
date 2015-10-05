""" The authentication views. """

import morepath

from onegov.core.security import Public, Private
from onegov.town import _, log
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.models import Auth
from onegov.user.forms import LoginForm


@TownApp.form(model=Auth, name='login', template='login.pt', permission=Public,
              form=LoginForm)
def handle_login(self, request, form):
    """ Handles the login requests. """

    if form.submitted(request):
        identity = form.get_identity(request)

        if identity is not None:
            response = morepath.redirect(self.to)
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
        'password_reset_link': request.link(
            request.app.town, name='request-password'),
        'title': _(u'Login to ${town}', mapping={
            'town': request.app.town.name
        }),
        'form': form
    }


@TownApp.html(model=Auth, name='logout', permission=Private)
def view_logout(self, request):
    """ Handles the logout requests. """

    response = morepath.redirect(self.to)
    morepath.forget_identity(response, request)

    request.info(_("You have been logged out."))
    return response
