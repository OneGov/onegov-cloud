""" The authentication views. """

import morepath

from onegov.core.security import Public, Personal
from onegov.core.templates import render_template
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout, DefaultMailLayout
from onegov.user import Auth, UserCollection
from onegov.user.errors import (
    AlreadyActivatedError,
    ExistingUserError,
    InvalidActivationTokenError,
    UnknownUserError,
)
from onegov.user.forms import LoginForm, RegistrationForm
from webob import exc
from purl import URL


@OrgApp.form(model=Auth, name='login', template='login.pt', permission=Public,
             form=LoginForm)
def handle_login(self, request, form):
    """ Handles the login requests. """

    if not request.app.settings.org.enable_yubikey:
        form.delete_field('yubikey')

    if self.skippable(request):
        return self.redirect(request)

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
        'register_link': request.link(self, name='register'),
        'may_register': request.app.settings.org.enable_user_registration,
        'title': _('Login to ${org}', mapping={
            'org': request.app.org.name
        }),
        'form': form
    }


@OrgApp.form(model=Auth, name='register', template='form.pt',
             permission=Public, form=RegistrationForm)
def handle_registration(self, request, form):
    """ Handles the user registration. """

    if not request.app.settings.org.enable_user_registration:
        raise exc.HTTPNotFound()

    if form.submitted(request):

        try:
            user = form.register_user(request)
        except ExistingUserError:
            request.alert(_("A user with this address already exists"))
        else:
            url = URL(request.link(self, 'activate'))
            url = url.query_param('username', form.username.data)
            url = url.query_param('token', user.data['activation_token'])

            title = subject = request.translate(
                _("Your ${org} Registration", mapping={
                    'org': request.app.org.name
                })
            )

            request.app.send_email(
                subject=subject,
                receivers=(form.username.data, ),
                content=render_template(
                    'mail_activation.pt', request, {
                        'layout': DefaultMailLayout(self, request),
                        'activation_link': url.as_string(),
                        'title': title
                    }
                )
            )

            request.success(_(
                "Thank you for registering. Please follow the instructions "
                "on the activiation e-mail sent to you."
            ))

            return morepath.redirect(request.link(request.app.org))

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Register"), request.link(self, name='register'))
    ]

    return {
        'layout': layout,
        'title': _('Account Registration'),
        'form': form
    }


@OrgApp.view(model=Auth, name='activate', permission=Public)
def handle_activation(self, request):

    if not request.app.settings.org.enable_user_registration:
        raise exc.HTTPNotFound()

    users = UserCollection(request.app.session())

    username = request.params.get('username')
    token = request.params.get('token')

    try:
        users.activate_with_token(username, token)
    except UnknownUserError:
        request.warning(_("Unknown user"))
    except InvalidActivationTokenError:
        request.warning(_("Invalid activation token"))
    except AlreadyActivatedError:
        request.success(_("Your account has already been activated."))
    else:
        request.success(_(
            "Your account has been activated. "
            "You may now log in with your credentials"
        ))

    return morepath.redirect(request.link(request.app.org))


@OrgApp.html(model=Auth, name='logout', permission=Personal)
def view_logout(self, request):
    """ Handles the logout requests. """

    request.info(_("You have been logged out."))
    return self.logout_to(request)
