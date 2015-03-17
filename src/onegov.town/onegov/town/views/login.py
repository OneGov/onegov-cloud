""" The login/logout views. """

import morepath

from onegov.core.security import Public, Private
from onegov.form import Form
from wtforms import StringField, PasswordField, validators
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import DefaultLayout
from onegov.town.model import Town
from onegov.user import UserCollection


class LoginForm(Form):
    """ Defines the login form for onegov town. """

    email = StringField(_(u'Email Address'), [validators.InputRequired()])
    password = PasswordField(_(u'Password'), [validators.InputRequired()])

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


@TownApp.html(
    model=Town, name='login', template='form.pt', permission=Public,
    request_method='GET')
def view_login(self, request):
    return handle_login(self, request)


@TownApp.html(
    model=Town, name='login', template='form.pt', permission=Public,
    request_method='POST')
def view_post_login(self, request):
    return handle_login(self, request)


def handle_login(self, request):
    """ Handles the GET and POST login requests. """

    form = LoginForm(request.POST)
    form.action = request.link(self, name='login')

    if form.submitted(request):
        identity = form.get_identity(request)

        if identity is not None:
            response = morepath.redirect(request.link(self))
            morepath.remember_identity(response, request, identity)
            return response

    return {
        'layout': DefaultLayout(self, request),
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
    return response
