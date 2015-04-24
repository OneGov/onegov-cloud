""" The login/logout views. """

import morepath

from onegov.core.security import Public, Private
from onegov.form import Form
from onegov.town import _, log
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.model import Town
from onegov.user import UserCollection
from purl import URL
from wtforms import StringField, PasswordField, validators


class LoginForm(Form):
    """ Defines the login form for onegov town. """

    email = StringField(_(u"Email Address"), [validators.InputRequired()])
    password = PasswordField(_(u"Password"), [validators.InputRequired()])

    def get_identity(self, request):
        """ Returns the identity if the username and password match. If they
        don't match, None is returned.

        """
        users = UserCollection(request.app.session())
        user = users.by_username_and_password(
            self.email.data, self.password.data
        )

        if user is None:
            return None
        else:
            return morepath.Identity(
                userid=user.username,
                role=user.role,
                application_id=request.app.application_id
            )


@TownApp.form(
    model=Town, name='login', template='form.pt', permission=Public,
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
