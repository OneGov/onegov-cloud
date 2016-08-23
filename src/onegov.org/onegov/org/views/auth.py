""" The authentication views. """

from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.user import Auth
from onegov.user.forms import LoginForm


@OrgApp.form(model=Auth, name='login', template='login.pt', permission=Public,
             form=LoginForm)
def handle_login(self, request, form):
    """ Handles the login requests. """

    if form.submitted(request):
        response = self.login_to(request=request, **form.login_data)

        if response:
            request.success(_("You have been logged in."))
            return response

        request.alert(_("Wrong e-mail address, password or yubikey."))

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Login"), request.link(self, name='login'))
    ]

    return {
        'layout': layout,
        'password_reset_link': request.link(
            request.app.org, name='request-password'),
        'title': _('Login to ${org}', mapping={
            'org': request.app.org.name
        }),
        'form': form
    }


@OrgApp.html(model=Auth, name='logout', permission=Private)
def view_logout(self, request):
    """ Handles the logout requests. """

    request.info(_("You have been logged out."))
    return self.logout_to(request)
