from markupsafe import Markup
from onegov.core.markdown import render_untrusted_markdown
from onegov.core.security import Public
from onegov.core.templates import render_template
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.utils import password_reset_url
from onegov.wtfs import _
from onegov.wtfs import log
from onegov.wtfs import WtfsApp
from onegov.wtfs.layouts import DefaultLayout
from onegov.wtfs.layouts import MailLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from onegov.user.auth.provider import AuthenticationProvider
    from webob.response import Response


@WtfsApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    form=LoginForm,
    permission=Public
)
def handle_login(
    self: Auth,
    request: 'CoreRequest',
    form: LoginForm
) -> 'Response | RenderData':
    """ Handles the login requests. """

    form.delete_field('yubikey')

    if form.submitted(request):
        response = self.login_to(request=request, **form.login_data)
        form.error_message = _("Wrong username or password")  # type:ignore
    else:
        response = None

    def provider_login(provider: 'AuthenticationProvider') -> str:
        provider.to = self.to
        return request.link(provider)

    return response or {
        'layout': DefaultLayout(self, request),
        'title': _("Login"),
        'form': form,
        'providers': request.app.providers,  # type:ignore[attr-defined]
        'provider_login': provider_login,
        # FIXME: render_untrusted_markdown/sanitize_html should return Markup
        'render_untrusted_markdown': lambda m: Markup(  # noqa: MS001
            render_untrusted_markdown(m)),
        'password_reset_link': request.link(
            Auth.from_request(request), name='request-password'
        ),
    }


@WtfsApp.html(
    model=Auth,
    name='logout',
    permission=Public
)
def view_logout(self: Auth, request: 'CoreRequest') -> 'Response':
    """ Handles the logout requests. """

    return self.logout_to(request)


@WtfsApp.form(
    model=Auth,
    name='request-password',
    template='form.pt',
    form=RequestPasswordResetForm,
    permission=Public
)
def handle_password_reset_request(
    self: Auth,
    request: 'CoreRequest',
    form: RequestPasswordResetForm
) -> 'Response | RenderData':
    """ Handles the password reset requests. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        users = UserCollection(request.session)
        assert form.email.data is not None
        user = users.by_username(form.email.data)
        if user:
            url = password_reset_url(
                user,
                request,
                request.link(self, name='reset-password')
            )

            assert request.app.mail is not None
            request.app.send_transactional_email(
                subject=request.translate(_("Password reset")),
                receivers=(user.username, ),
                reply_to=request.app.mail['transactional']['sender'],
                content=render_template(
                    'mail_password_reset.pt',
                    request,
                    {
                        'title': request.translate(_("Password reset")),
                        'model': None,
                        'url': url,
                        'layout': MailLayout(self, request)
                    }
                )
            )
        else:
            log.info(f"Failed password reset attempt by {request.client_addr}")

        message = _(
            'A password reset link has been sent to ${email}, provided an '
            'account exists for this email address.',
            mapping={'email': form.email.data}
        )
        request.message(message, 'success')
        # FIXME: This won't work if the user is already logged in
        return request.redirect(layout.login_url)  # type:ignore[arg-type]

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
    }


@WtfsApp.form(
    model=Auth,
    name='reset-password',
    template='form.pt',
    form=PasswordResetForm,
    permission=Public
)
def handle_password_reset(
    self: Auth,
    request: 'CoreRequest',
    form: PasswordResetForm
) -> 'Response | RenderData':
    """ Handles password reset requests. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        if form.update_password(request):
            request.message(_("Password changed."), 'success')
            # FIXME: This won't work if the user is already logged in
            return request.redirect(layout.login_url)  # type:ignore
        else:
            form.error_message = _(  # type:ignore[attr-defined]
                "Wrong username or password reset link not valid any more."
            )
            log.info(
                "Failed password reset attempt by {}".format(
                    request.client_addr
                )
            )

    if 'token' in request.params:
        token = request.params['token']
        assert isinstance(token, str)
        form.token.data = token

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
    }
