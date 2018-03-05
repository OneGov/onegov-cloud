""" The authentication views. """

import morepath

from onegov.core.security import Public, Personal
from onegov.org import _, OrgApp
from onegov.org import log
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.mail import send_transactional_html_mail
from onegov.user import Auth, UserCollection
from onegov.user.errors import AlreadyActivatedError
from onegov.user.errors import ExistingUserError
from onegov.user.errors import ExpiredSignupLinkError
from onegov.user.errors import InvalidActivationTokenError
from onegov.user.errors import UnknownUserError
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestPasswordResetForm
from purl import URL
from webob import exc


@OrgApp.form(model=Auth, name='login', template='login.pt', permission=Public,
             form=LoginForm)
def handle_login(self, request, form):
    """ Handles the login requests. """

    if not request.app.enable_yubikey:
        form.delete_field('yubikey')

    if self.skippable(request):
        return self.redirect(request)

    if form.submitted(request):

        redirected_to_userprofile = False

        org_settings = request.app.settings.org
        if org_settings.require_complete_userprofile:
            username = form.username.data

            if not org_settings.is_complete_userprofile(request, username):
                redirected_to_userprofile = True

                self.to = request.return_to(
                    '/userprofile',
                    self.to
                )

        response = self.login_to(request=request, **form.login_data)

        if response:
            if redirected_to_userprofile:
                request.warning(_(
                    "Your userprofile is incomplete. "
                    "Please update it before you continue."
                ))
            else:
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
        'password_reset_link': request.link(self, name='request-password'),
        'register_link': request.link(self, name='register'),
        'may_register': request.app.enable_user_registration,
        'title': _('Login to ${org}', mapping={
            'org': request.app.org.title
        }),
        'form': form
    }


@OrgApp.form(model=Auth, name='register', template='form.pt',
             permission=Public, form=RegistrationForm)
def handle_registration(self, request, form):
    """ Handles the user registration. """

    if not request.app.enable_user_registration:
        raise exc.HTTPNotFound()

    if form.submitted(request):

        try:
            user = self.register(form, request)
        except ExistingUserError:
            request.alert(_("A user with this address already exists"))
        except ExpiredSignupLinkError:
            request.alert(_("This signup link has expired"))
        else:
            url = URL(request.link(self, 'activate'))
            url = url.query_param('username', form.username.data)
            url = url.query_param('token', user.data['activation_token'])

            subject = request.translate(
                _("Your ${org} Registration", mapping={
                    'org': request.app.org.title
                })
            )

            send_transactional_html_mail(
                request=request,
                template='mail_activation.pt',
                subject=subject,
                receivers=(form.username.data, ),
                content={
                    'activation_link': url.as_string(),
                    'model': self
                }
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

    if not request.app.enable_user_registration:
        raise exc.HTTPNotFound()

    users = UserCollection(request.session)

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


@OrgApp.form(model=Auth, name='request-password', template='form.pt',
             permission=Public, form=RequestPasswordResetForm)
def handle_password_reset_request(self, request, form):
    """ Handles the GET and POST password reset requests. """

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Reset password"), request.link(self, name='request-password'))
    ]

    if form.submitted(request):

        user = UserCollection(request.session)\
            .by_username(form.email.data)

        url = layout.password_reset_url(user)

        if url:
            send_transactional_html_mail(
                request=request,
                template='mail_password_reset.pt',
                subject=_("Password reset"),
                receivers=(user.username, ),
                content={'model': None, 'url': url}
            )
        else:
            log.info(
                "Failed password reset attempt by {}".format(
                    request.client_addr
                )
            )

        response = morepath.redirect(request.link(self, name='login'))
        request.success(
            _(('A password reset link has been sent to ${email}, provided an '
               'account exists for this email address.'),
              mapping={'email': form.email.data})
        )
        return response

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(model=Auth, name='reset-password', template='form.pt',
             permission=Public, form=PasswordResetForm)
def handle_password_reset(self, request, form):
    if form.submitted(request):
        # do NOT log the user in at this point - only onegov.user.auth does
        # logins - we only ever want one path to be able to login, which makes
        # it easier to do it correctly.

        if form.update_password(request):
            request.success(_("Password changed."))
            return morepath.redirect(request.link(self, name='login'))
        else:
            request.alert(
                _("Wrong username or password reset link not valid any more.")
            )
            log.info(
                "Failed password reset attempt by {}".format(
                    request.client_addr
                )
            )

    if 'token' in request.params:
        form.token.data = request.params['token']

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Reset password"), request.link(self, name='request-password'))
    ]

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
        'form_width': 'small'
    }
