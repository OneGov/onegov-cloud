""" The authentication views. """
from __future__ import annotations

import morepath

from onegov.core.markdown import render_untrusted_markdown
from onegov.core.security import Public, Personal
from onegov.core.utils import append_query_param
from onegov.org import _, OrgApp
from onegov.org import log
from onegov.org.auth import MTANAuth
from onegov.org.elements import Link
from onegov.org.forms import PublicMTANForm, PublicRequestMTANForm
from onegov.org.forms import CitizenLoginForm, ConfirmCitizenLoginForm
from onegov.org.layout import DefaultLayout
from onegov.org.mail import send_transactional_html_mail
from onegov.user import Auth, UserCollection
from onegov.user.auth.provider import OauthProvider
from onegov.user.auth.second_factor import MTANFactor
from onegov.user.auth.second_factor import TOTPFactor
from onegov.user.collections import TANCollection
from onegov.user.errors import AlreadyActivatedError
from onegov.user.errors import ExistingUserError
from onegov.user.errors import ExpiredSignupLinkError
from onegov.user.errors import InvalidActivationTokenError
from onegov.user.errors import UnknownUserError
from onegov.user.forms import LoginForm
from onegov.user.forms import MTANForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestMTANForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.forms import TOTPForm
from onegov.user.models import TAN
from purl import URL
from webob import exc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.layout import Layout
    from onegov.org.request import OrgRequest
    from onegov.user.auth.provider import AuthenticationProvider
    from webob import Response


def redirect_to_userprofile(
    self: Auth,
    username: str | None,
    request: OrgRequest
) -> bool:

    redirected_to_userprofile = False

    org_settings = request.app.settings.org
    if org_settings.require_complete_userprofile:

        if not org_settings.is_complete_userprofile(request, username):
            redirected_to_userprofile = True

            self.to = request.return_to(
                '/userprofile',
                self.to
            )

    return redirected_to_userprofile


@OrgApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=LoginForm
)
def handle_login(
    self: Auth,
    request: OrgRequest,
    form: LoginForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    """ Handles the login requests. """

    if not request.app.enable_yubikey:
        form.delete_field('yubikey')

    if self.skippable(request):
        return self.redirect(request, self.to)

    if form.submitted(request):

        redirected_to_userprofile = redirect_to_userprofile(
            self,
            form.username.data,
            request
        )
        response = self.login_to(request=request, **form.login_data)

        if response:
            # HACK: It might be a good idea to move these messages to
            #       complete_login instead, so they always happen
            if not getattr(response, 'completed_login', False):
                pass
            elif redirected_to_userprofile:
                request.warning(_(
                    'Your userprofile is incomplete. '
                    'Please update it before you continue.'
                ))
            else:
                request.success(_('You have been logged in.'))

            return response

        request.alert(_('Wrong e-mail address, password or yubikey.'))

    layout = layout or DefaultLayout(self, request)
    request.include('scroll-to-username')
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Login'), request.link(self, name='login'))
    ]

    def provider_login(provider: AuthenticationProvider) -> str:
        provider.to = self.to
        return request.link(provider)

    return {
        'layout': layout,
        'password_reset_link': request.link(self, name='request-password'),
        'register_link': request.link(self, name='register'),
        'may_register': request.app.enable_user_registration,
        'button_text': _('Login'),
        'providers': request.app.providers.values(),
        'provider_login': provider_login,
        'render_untrusted_markdown': render_untrusted_markdown,
        'title': _('Login to ${org}', mapping={
            'org': request.app.org.title
        }),
        'form': form
    }


@OrgApp.form(
    model=Auth,
    name='register',
    template='form.pt',
    permission=Public,
    form=RegistrationForm
)
def handle_registration(
    self: Auth,
    request: OrgRequest,
    form: RegistrationForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    """ Handles the user registration. """

    if not request.app.enable_user_registration:
        raise exc.HTTPNotFound()

    if form.submitted(request):

        try:
            user = self.register(form, request)
        except ExistingUserError:
            request.alert(_('A user with this address already exists'))
        except ExpiredSignupLinkError:
            request.alert(_('This signup link has expired'))
        else:
            assert form.username.data is not None
            url = URL(request.link(self, 'activate'))
            url = url.query_param('username', form.username.data)
            url = url.query_param('token', user.data['activation_token'])

            subject = request.translate(
                _('Your ${org} Registration', mapping={
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
                'Thank you for registering. Please follow the instructions '
                'on the activiation e-mail sent to you. Please check your '
                'spam folder if you have not received the email.'
            ))

            return morepath.redirect(request.link(request.app.org))

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Register'), request.link(self, name='register'))
    ]
    request.include('scroll-to-username')

    return {
        'layout': layout,
        'title': _('Account Registration'),
        'form': form
    }


@OrgApp.view(model=Auth, name='activate', permission=Public)
def handle_activation(self: Auth, request: OrgRequest) -> Response:

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
        request.warning(_('Unknown user'))
    except InvalidActivationTokenError:
        request.warning(_('Invalid activation token'))
    except AlreadyActivatedError:
        request.success(_('Your account has already been activated.'))
    else:
        request.success(_(
            'Your account has been activated. '
            'You may now log in with your credentials'
        ))

    return morepath.redirect(request.link(request.app.org))


def do_logout(
    self: Auth,
    request: OrgRequest,
    to: str | None = None
) -> Response:
    # the message has to be set after the log out code has run, since that
    # clears all existing messages from the session
    @request.after
    def show_hint(response: Response) -> None:
        request.success(_('You have been logged out.'))

    return self.logout_to(request, to)


def do_logout_with_external_provider(
    self: Auth,
    request: OrgRequest
) -> Response:
    """ Use this function if you want to go the way to the external auth
    provider first and then logout on redirect. """
    from onegov.user.integration import UserApp  # circular import

    user = request.current_user
    if not user:
        return do_logout(self, request)

    if isinstance(self.app, UserApp) and user.source:
        for provider in self.app.providers.values():
            if isinstance(provider, OauthProvider):
                response = provider.do_logout(request, user, self.to)
                # some providers may not need to redirect, in which
                # case we just fall through to regular do_logout or
                # the next provider
                if response is not None:
                    return response

    return do_logout(self, request)


@OrgApp.html(model=Auth, name='logout', permission=Personal)
def view_logout(self: Auth, request: OrgRequest) -> Response:
    """ Handles the logout requests """
    return do_logout_with_external_provider(self, request)


@OrgApp.form(
    model=Auth,
    name='request-password',
    template='form.pt',
    permission=Public,
    form=RequestPasswordResetForm
)
def handle_password_reset_request(
    self: Auth,
    request: OrgRequest,
    form: RequestPasswordResetForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    """ Handles the GET and POST password reset requests. """

    if request.app.disable_password_reset:
        raise exc.HTTPNotFound()

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Reset password'), request.link(self, name='request-password'))
    ]

    if form.submitted(request):

        assert form.email.data is not None
        user = UserCollection(request.session).by_username(form.email.data)

        url = layout.password_reset_url(user)

        if url and user and user.active:
            send_transactional_html_mail(
                request=request,
                template='mail_password_reset.pt',
                subject=_('Password reset'),
                receivers=(user.username, ),
                content={'model': None, 'url': url}
            )
        else:
            log.info(
                f'Failed password reset attempt by {request.client_addr}'
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


@OrgApp.form(
    model=Auth,
    name='reset-password',
    template='form.pt',
    permission=Public,
    form=PasswordResetForm
)
def handle_password_reset(
    self: Auth,
    request: OrgRequest,
    form: PasswordResetForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:

    if request.app.disable_password_reset:
        raise exc.HTTPNotFound()

    if form.submitted(request):
        # do NOT log the user in at this point - only onegov.user.auth does
        # logins - we only ever want one path to be able to login, which makes
        # it easier to do it correctly.

        if form.update_password(request):
            request.success(_('Password changed.'))
            return morepath.redirect(request.link(self, name='login'))
        else:
            request.alert(
                _('Wrong username or password reset link not valid any more.')
            )
            log.info(
                'Failed password reset attempt by {}'.format(
                    request.client_addr
                )
            )

    if isinstance(token := request.params.get('token'), str):
        form.token.data = token

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Reset password'), request.link(self, name='request-password'))
    ]

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=Auth,
    name='mtan',
    template='form.pt',
    permission=Public,
    form=MTANForm
)
def handle_mtan_second_factor(
    self: Auth,
    request: OrgRequest,
    form: MTANForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:

    if not request.app.mtan_second_factor_enabled:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: Response) -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    users = UserCollection(request.session)
    username = request.browser_session.get('pending_username')
    user = users.by_username(username) if username else None
    if user is None:
        if request.current_user:
            # redirect already logged in users to the redirect_to
            return self.redirect(request, self.to)

        request.alert(
            _('Failed to continue login, please ensure cookies are allowed.')
        )
        return morepath.redirect(request.link(self, name='login'))

    mobile_number: str | None = request.browser_session.get('mtan_setup')
    if not (is_mtan_setup := mobile_number is not None):
        if not user.second_factor or user.second_factor['type'] != 'mtan':
            raise exc.HTTPNotFound()

        mobile_number = user.second_factor['data']
        assert mobile_number is not None

    if form.submitted(request):
        username = user.username
        assert form.tan.data is not None
        factor = self.factors['mtan']
        assert isinstance(factor, MTANFactor)

        if factor.is_valid(request, username, mobile_number, form.tan.data):
            del request.browser_session['pending_username']
            if is_mtan_setup:
                factor.complete_activation(user, mobile_number)
                del request.browser_session['mtan_setup']

            response = self.complete_login(user, request)
            # HACK: These messages should probably happen in complete_login
            if redirect_to_userprofile(
                self,
                user.username,
                request
            ):
                request.warning(_(
                    'Your userprofile is incomplete. '
                    'Please update it before you continue.'
                ))
            else:
                request.success(_('You have been logged in.'))
            return response
        else:
            request.alert(_('Invalid or expired mTAN provided.'))
            client = request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (mTAN)')

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url)
    ]

    if is_mtan_setup:
        layout.breadcrumbs.append(
            Link(_('Request mTAN'), request.link(self, name='mtan-setup'))
        )
    else:
        layout.breadcrumbs.append(
            Link(_('Login'), request.link(self, name='login'))
        )

    return {
        'layout': layout,
        'title': _('Enter mTAN'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=Auth,
    name='mtan-setup',
    template='form.pt',
    permission=Public,
    form=RequestMTANForm
)
def handle_mtan_second_factor_setup(
    self: Auth,
    request: OrgRequest,
    form: RequestMTANForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:

    if not request.app.mtan_second_factor_enabled:
        raise exc.HTTPNotFound()

    if not request.app.mtan_automatic_setup:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: Response) -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    users = UserCollection(request.session)
    username = request.browser_session.get('pending_username')
    user = users.by_username(username) if username else None
    if user is None:
        if request.current_user:
            # redirect already logged in users to the redirect_to
            return self.redirect(request, self.to)

        request.alert(
            _('Failed to continue login, please ensure cookies are allowed.')
        )
        return morepath.redirect(request.link(self, name='login'))

    if form.submitted(request):
        phone_number = form.phone_number.formatted_data
        assert phone_number is not None
        factor = self.factors['mtan']
        assert isinstance(factor, MTANFactor)
        request.browser_session['mtan_setup'] = phone_number
        return factor.send_challenge(request, user, self, phone_number)
    elif current_number := request.browser_session.get('mtan_setup'):
        # pre-fill the form with the number that was last entered
        form.phone_number.data = current_number

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Enter mTAN'), request.link(self, name='mtan'))
    ]

    return {
        'layout': layout,
        'title': _('Setup mTAN'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=Auth,
    name='totp',
    template='form.pt',
    permission=Public,
    form=TOTPForm
)
def handle_totp_second_factor(
    self: Auth,
    request: OrgRequest,
    form: TOTPForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:

    if not request.app.totp_enabled:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: Response) -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    users = UserCollection(request.session)
    username = request.browser_session.get('pending_username')
    user = users.by_username(username) if username else None
    if user is None:
        if request.current_user:
            # redirect already logged in users to the redirect_to
            return self.redirect(request, self.to)

        request.alert(
            _('Failed to continue login, please ensure cookies are allowed.')
        )
        return morepath.redirect(request.link(self, name='login'))

    if form.submitted(request):
        assert form.totp.data is not None
        factor = self.factors['totp']
        assert isinstance(factor, TOTPFactor)

        if factor.is_valid(request, user, form.totp.data):
            del request.browser_session['pending_username']

            response = self.complete_login(user, request)
            # HACK: These messages should probably happen in complete_login
            if redirect_to_userprofile(
                self,
                user.username,
                request
            ):
                request.warning(_(
                    'Your userprofile is incomplete. '
                    'Please update it before you continue.'
                ))
            else:
                request.success(_('You have been logged in.'))
            return response
        else:
            request.alert(_('Invalid or expired TOTP provided.'))
            client = request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (TOTP)')
    else:
        request.info(
            _('Please enter the six digit code from your authenticator app')
        )

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Login'), request.link(self, name='login'))
    ]

    return {
        'layout': layout,
        'title': _('Enter TOTP'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=MTANAuth,
    name='request',
    template='form.pt',
    permission=Public,
    form=PublicRequestMTANForm
)
def handle_request_mtan(
    self: MTANAuth,
    request: OrgRequest,
    form: RequestMTANForm,
    layout: Layout | None = None
) -> RenderData | Response:

    if not request.app.can_deliver_sms:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: Response) -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    if form.submitted(request):
        phone_number = form.phone_number.formatted_data
        assert phone_number is not None
        return self.send_mtan(request, phone_number)

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Enter mTAN'), request.link(self, name='auth'))
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
    form=PublicMTANForm
)
def handle_authenticate_mtan(
    self: MTANAuth,
    request: OrgRequest,
    form: MTANForm,
    layout: Layout | None = None
) -> RenderData | Response:

    if not request.app.can_deliver_sms:
        raise exc.HTTPNotFound()

    @request.after
    def respond_with_no_index(response: Response) -> None:
        response.headers['X-Robots-Tag'] = 'noindex'

    if form.submitted(request):
        assert form.tan.data is not None
        redirect_to = self.authenticate(request, form.tan.data.strip())
        if redirect_to is not None:
            request.success(_('Successfully authenticated via mTAN.'))
            return morepath.redirect(request.transform(redirect_to))
        else:
            request.alert(_('Invalid or expired mTAN provided.'))

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Request mTAN'), request.link(self, name='request'))
    ]

    return {
        'layout': layout,
        'title': _('Enter mTAN'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=Auth,
    name='citizen-login',
    template='form.pt',
    permission=Public,
    form=CitizenLoginForm
)
def handle_citizen_login(
    self: Auth,
    request: OrgRequest,
    form: CitizenLoginForm,
    layout: Layout | None = None
) -> RenderData | Response:

    if not request.app.org.citizen_login_enabled:
        raise exc.HTTPNotFound()

    if request.authenticated_email:
        return self.redirect(request, self.to)

    if form.submitted(request):
        assert form.email.data is not None
        collection = TANCollection(request.session, scope='citizen-login')
        tan_obj = collection.add(
            client=request.client_addr or 'unknown',
            email=form.email.data,
            redirect_to=self.to
        )
        title = request.translate(_(
            'Login Token for ${organisation}',
            mapping={'organisation': request.app.org.title}
        ))
        confirm_link = request.link(self, name='confirm-citizen-login')
        send_transactional_html_mail(
            request,
            'mail_citizen_login.pt',
            content={
                'model': self,
                'title': title,
                'token': tan_obj.tan,
                'confirm_link': append_query_param(
                    confirm_link, 'token', tan_obj.tan
                )
            },
            receivers=form.email.data,
            subject=title,
        )
        return morepath.redirect(confirm_link)

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Citizen Login'), '#')
    ]

    return {
        'layout': layout,
        'title': _('Citizen Login'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.form(
    model=Auth,
    name='confirm-citizen-login',
    template='form.pt',
    permission=Public,
    form=ConfirmCitizenLoginForm
)
def handle_confirm_citizen_login(
    self: Auth,
    request: OrgRequest,
    form: ConfirmCitizenLoginForm,
    layout: Layout | None = None
) -> RenderData | Response:

    if not request.app.org.citizen_login_enabled:
        raise exc.HTTPNotFound()

    if request.authenticated_email:
        return self.redirect(request, self.to)

    if form.submitted(request):
        assert form.token.data is not None
        collection = TANCollection(request.session, scope='citizen-login')
        tan_obj = collection.by_tan(form.token.data.strip())
        if tan_obj is None or 'email' not in tan_obj.meta:
            client = request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (Citizen Login)')
            request.alert(_('Invalid or expired login token provided.'))
            return morepath.redirect(request.link(self, 'citizen-login'))
        else:
            request.browser_session['authenticated_email'] = email = (
                tan_obj.meta['email'])

            # expire the TAN we just used
            tan_obj.expire()
            # expire any other TANs issued to the same email
            for tan_obj in collection.query().filter(
                TAN.meta['email'] == email
            ):
                tan_obj.expire()
            return self.redirect(
                request,
                tan_obj.meta.get('redirect_to', self.to)
            )
    elif not request.POST and (token := request.GET.get('token')):
        form.token.data = token

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Citizen Login'), request.link(self, name='citizen-login')),
        Link(_('Confirm'), '#')
    ]

    return {
        'layout': layout,
        'title': _('Confirm Citizen Login'),
        'form': form,
        'form_width': 'small'
    }


@OrgApp.view(
    model=Auth,
    name='citizen-logout',
    permission=Public,
)
def handle_citizen_logout(
    self: Auth,
    request: OrgRequest
) -> Response:

    if not request.app.org.citizen_login_enabled:
        raise exc.HTTPNotFound()

    if request.authenticated_email:
        del request.browser_session['authenticated_email']

    return self.redirect(request, self.to)
