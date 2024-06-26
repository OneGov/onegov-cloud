""" The authentication views. """

import morepath

from onegov.core.markdown import render_untrusted_markdown
from onegov.core.security import Public, Personal
from onegov.org import _, OrgApp
from onegov.org import log
from onegov.org.auth import MTANAuth
from onegov.org.elements import Link
from onegov.org.forms import MTANForm, RequestMTANForm
from onegov.org.layout import DefaultLayout
from onegov.org.mail import send_transactional_html_mail
from onegov.user import Auth, UserCollection
from onegov.user.auth.provider import OauthProvider
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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.layout import Layout
    from onegov.org.request import OrgRequest
    from onegov.user.auth.provider import AuthenticationProvider
    from webob import Response


@OrgApp.form(model=Auth, name='login', template='login.pt', permission=Public,
             form=LoginForm)
def handle_login(
    self: Auth,
    request: 'OrgRequest',
    form: LoginForm,
    layout: DefaultLayout | None = None
) -> 'RenderData | Response':
    """ Handles the login requests. """

    if not request.app.enable_yubikey:
        form.delete_field('yubikey')

    if self.skippable(request):
        return self.redirect(request, self.to)

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

    layout = layout or DefaultLayout(self, request)
    request.include('scroll-to-username')
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Login"), request.link(self, name='login'))
    ]

    def provider_login(provider: 'AuthenticationProvider') -> str:
        provider.to = self.to
        return request.link(provider)

    return {
        'layout': layout,
        'password_reset_link': request.link(self, name='request-password'),
        'register_link': request.link(self, name='register'),
        'may_register': request.app.enable_user_registration,
        'button_text': _("Login"),
        'providers': request.app.providers,
        'provider_login': provider_login,
        'render_untrusted_markdown': render_untrusted_markdown,
        'title': _('Login to ${org}', mapping={
            'org': request.app.org.title
        }),
        'form': form
    }


@OrgApp.form(model=Auth, name='register', template='form.pt',
             permission=Public, form=RegistrationForm)
def handle_registration(
    self: Auth,
    request: 'OrgRequest',
    form: RegistrationForm,
    layout: DefaultLayout | None = None
) -> 'RenderData | Response':
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

            assert form.username.data is not None
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
                "on the activiation e-mail sent to you. Please check your "
                "spam folder if you have not received the email."
            ))

            return morepath.redirect(request.link(request.app.org))

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Register"), request.link(self, name='register'))
    ]
    request.include('scroll-to-username')

    return {
        'layout': layout,
        'title': _('Account Registration'),
        'form': form
    }


@OrgApp.view(model=Auth, name='activate', permission=Public)
def handle_activation(self: Auth, request: 'OrgRequest') -> 'Response':

    if not request.app.enable_user_registration:
        raise exc.HTTPNotFound()

    users = UserCollection(request.session)

    username = request.params.get('username')
    if not isinstance(username, str):
        username = ''
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


def do_logout(
    self: Auth,
    request: 'OrgRequest',
    to: str | None = None
) -> 'Response':
    # the message has to be set after the log out code has run, since that
    # clears all existing messages from the session
    @request.after
    def show_hint(response: 'Response') -> None:
        request.success(_("You have been logged out."))

    return self.logout_to(request, to)


def do_logout_with_external_provider(
    self: Auth,
    request: 'OrgRequest'
) -> 'Response':
    """ Use this function if you want to go the way to the external auth
    provider first and then logout on redirect. """
    from onegov.user.integration import UserApp  # circular import

    user = request.current_user
    if not user:
        return do_logout(self, request)

    if isinstance(self.app, UserApp) and user.source:
        for provider in self.app.providers:
            if isinstance(provider, OauthProvider):
                response = provider.do_logout(request, user, self.to)
                # some providers may not need to redirect, in which
                # case we just fall through to regular do_logout or
                # the next provider
                if response is not None:
                    return response

    return do_logout(self, request)


@OrgApp.html(model=Auth, name='logout', permission=Personal)
def view_logout(self: Auth, request: 'OrgRequest') -> 'Response':
    """ Handles the logout requests """
    return do_logout_with_external_provider(self, request)


@OrgApp.form(model=Auth, name='request-password', template='form.pt',
             permission=Public, form=RequestPasswordResetForm)
def handle_password_reset_request(
    self: Auth,
    request: 'OrgRequest',
    form: RequestPasswordResetForm,
    layout: DefaultLayout | None = None
) -> 'RenderData | Response':
    """ Handles the GET and POST password reset requests. """

    if request.app.disable_password_reset:
        raise exc.HTTPNotFound()

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Reset password"), request.link(self, name='request-password'))
    ]

    if form.submitted(request):

        assert form.email.data is not None
        user = UserCollection(request.session).by_username(form.email.data)

        url = layout.password_reset_url(user)

        if url and user and user.active:
            send_transactional_html_mail(
                request=request,
                template='mail_password_reset.pt',
                subject=_("Password reset"),
                receivers=(user.username, ),
                content={'model': None, 'url': url}
            )
        else:
            log.info(
                f"Failed password reset attempt by {request.client_addr}"
            )

        response = morepath.redirect(request.link(self, name='login'))
        request.success(
            _(('A password reset link has been sent to ${email}, provided an '
               'active account exists for this email address.'),
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
def handle_password_reset(
    self: Auth,
    request: 'OrgRequest',
    form: PasswordResetForm,
    layout: DefaultLayout | None = None
) -> 'RenderData | Response':

    if request.app.disable_password_reset:
        raise exc.HTTPNotFound()

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

    if isinstance(token := request.params.get('token'), str):
        form.token.data = token

    layout = layout or DefaultLayout(self, request)
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


@OrgApp.form(
    model=MTANAuth,
    name='request',
    template='form.pt',
    permission=Public,
    form=RequestMTANForm
)
def handle_request_mtan(
    self: MTANAuth,
    request: 'OrgRequest',
    form: RequestMTANForm,
    layout: 'Layout | None' = None
) -> 'RenderData | Response':

    if not request.app.can_deliver_sms:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: 'Response') -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    if form.submitted(request):
        phone_number = form.phone_number.formatted_data
        assert phone_number is not None
        return self.send_mtan(request, phone_number)

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Enter mTAN"), request.link(self, name='auth'))
    ]

    request.info(_(
        'The requested resource is protected. To obtain time-limited '
        'access, please enter your mobile phone number in the field below. '
        'You will receive an mTAN via SMS, which will grant you access '
        'after correct entry.'
    ))

    return {
        'layout': layout,
        'title': _('Request mTAN'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=MTANAuth,
    name='auth',
    template='form.pt',
    permission=Public,
    form=MTANForm
)
def handle_authenticate_mtan(
    self: MTANAuth,
    request: 'OrgRequest',
    form: MTANForm,
    layout: 'Layout | None' = None
) -> 'RenderData | Response':

    if not request.app.can_deliver_sms:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: 'Response') -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    if form.submitted(request):
        assert form.tan.data is not None
        redirect_to = self.authenticate(request, form.tan.data)
        if redirect_to is not None:
            request.success(_('Successfully authenticated via mTAN.'))
            return morepath.redirect(request.transform(redirect_to))
        else:
            request.alert(_('Invalid or expired mTAN provided.'))

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Request mTAN"), request.link(self, name='request'))
    ]

    return {
        'layout': layout,
        'title': _('Enter mTAN'),
        'form': form,
        'form_width': 'small'
    }
