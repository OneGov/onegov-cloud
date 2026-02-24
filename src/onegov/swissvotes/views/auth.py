from __future__ import annotations

from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Public
from onegov.core.templates import render_template
from onegov.core.utils import relative_url
from onegov.swissvotes import _
from onegov.swissvotes import log
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.layouts import DefaultLayout
from onegov.swissvotes.layouts import MailLayout
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user.auth.second_factor import TOTPFactor
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.forms import TOTPForm
from onegov.user.utils import password_reset_url
from webob import exc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.swissvotes.request import SwissvotesRequest
    from webob import Response


@SwissvotesApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    form=LoginForm,
    permission=Public
)
def handle_login(
    self: Auth,
    request: SwissvotesRequest,
    form: LoginForm
) -> RenderData | Response:
    """ Handles the login requests. """
    layout = DefaultLayout(self, request)

    if form.submitted(request):
        self.to = relative_url(layout.homepage_url)
        response = self.login_to(request=request, **form.login_data)
        form.error_message = _('Wrong username or password')  # type:ignore
    else:
        response = None

    return response or {
        'layout': layout,
        'title': _('Login'),
        'form': form,
        'password_reset_link': request.link(
            Auth.from_request(request), name='request-password'
        ),
        'button_text': _('Submit'),
    }


@SwissvotesApp.html(
    model=Auth,
    name='logout',
    permission=Personal
)
def view_logout(self: Auth, request: SwissvotesRequest) -> Response:
    """ Handles the logout requests. """

    return self.logout_to(request)


@SwissvotesApp.form(
    model=Auth,
    name='request-password',
    template='form.pt',
    form=RequestPasswordResetForm,
    permission=Public
)
def handle_password_reset_request(
    self: Auth,
    request: SwissvotesRequest,
    form: RequestPasswordResetForm
) -> RenderData | Response:
    """ Handles the password reset requests. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        assert form.email.data is not None
        users = UserCollection(request.session)
        user = users.by_username(form.email.data)
        if user:
            url = password_reset_url(
                user,
                request,
                request.link(self, name='reset-password')
            )

            assert request.app.mail is not None
            request.app.send_transactional_email(
                subject=request.translate(_('Password reset')),
                receivers=(user.username, ),
                reply_to=request.app.mail['transactional']['sender'],
                content=render_template(
                    'mail_password_reset.pt',
                    request,
                    {
                        'title': request.translate(_('Password reset')),
                        'model': None,
                        'url': url,
                        'layout': MailLayout(self, request)
                    }
                )
            )
        else:
            log.info(
                'Failed password reset attempt by {}'.format(
                    request.client_addr
                )
            )

        message = _(
            'A password reset link has been sent to ${email}, provided an '
            'account exists for this email address.',
            mapping={'email': form.email.data}
        )
        request.message(message, 'success')
        return request.redirect(layout.homepage_url)

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
        'button_text': _('Submit'),
    }


@SwissvotesApp.form(
    model=Auth,
    name='reset-password',
    template='form.pt',
    form=PasswordResetForm,
    permission=Public
)
def handle_password_reset(
    self: Auth,
    request: SwissvotesRequest,
    form: PasswordResetForm
) -> RenderData | Response:
    """ Handles password reset requests. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        if form.update_password(request):
            request.message(_('Password changed.'), 'success')
            return request.redirect(layout.login_url or layout.homepage_url)
        else:
            form.error_message = _(  # type:ignore[attr-defined]
                'Wrong username or password reset link not valid any more.'
            )
            log.info(
                'Failed password reset attempt by {}'.format(
                    request.client_addr
                )
            )

    if isinstance((token := request.params.get('token')), str):
        form.token.data = token

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
        'button_text': _('Submit'),
    }


@SwissvotesApp.form(
    model=Auth,
    name='totp',
    template='form.pt',
    permission=Public,
    form=TOTPForm
)
def handle_totp_second_factor(
    self: Auth,
    request: SwissvotesRequest,
    form: TOTPForm
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
        if request.is_logged_in:
            # redirect already logged in users to the redirect_to
            return self.redirect(request, self.to)

        request.alert(
            _('Failed to continue login, please ensure cookies are allowed.')
        )
        return redirect(request.link(self, name='login'))

    if form.submitted(request):
        assert form.totp.data is not None
        factor = self.factors['totp']
        assert isinstance(factor, TOTPFactor)

        if factor.is_valid(request, user, form.totp.data):
            del request.browser_session['pending_username']
            return self.complete_login(user, request)
        else:
            request.alert(_('Invalid or expired TOTP provided.'))
            client = request.client_addr or 'unknown'
            log.info(f'Failed login by {client} (TOTP)')
    else:
        request.info(
            _('Please enter the six digit code from your authenticator app')
        )

    return {
        'layout': DefaultLayout(self, request),
        'title': _('Enter TOTP'),
        'form': form,
        'form_width': 'small'
    }
