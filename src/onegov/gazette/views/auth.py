""" The authentication views. """

from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Public
from onegov.core.templates import render_template
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette import log
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.gazette.models import Principal
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.utils import password_reset_url


@GazetteApp.form(
    model=Auth, name='login', template='login.pt',
    permission=Public, form=LoginForm
)
def handle_login(self, request, form):
    """ Handles the login requests. """

    layout = Layout(self, request)

    if form.submitted(request):
        response = self.login_to(request=request, **form.login_data)
        form.error_message = _("Wrong username or password")
    else:
        response = None

    return response or {
        'layout': layout,
        'title': _("Login"),
        'form': form,
        'password_reset_link': request.link(
            request.app.principal, name='request-password'
        ),
    }


@GazetteApp.html(model=Auth, name='logout', permission=Personal)
def view_logout(self, request):
    """ Handles the logout requests. """

    return self.logout_to(request)


@GazetteApp.form(
    model=Principal, name='request-password', template='form.pt',
    permission=Public, form=RequestPasswordResetForm
)
def handle_password_reset_request(self, request, form):
    """ Handles the password reset requests. """

    show_form = True
    callout = None

    if form.submitted(request):
        users = UserCollection(request.session)
        user = users.by_username(form.email.data)
        if user:
            url = password_reset_url(
                user,
                request,
                request.link(self, name='reset-password')
            )

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
            log.info(
                "Failed password reset attempt by {}".format(
                    request.client_addr
                )
            )

        show_form = False
        callout = _(
            (
                'A password reset link has been sent to ${email}, provided an '
                'account exists for this email address.'
            ),
            mapping={'email': form.email.data}
        )

    return {
        'layout': Layout(self, request),
        'title': _('Reset password'),
        'form': form,
        'show_form': show_form,
        'callout': callout
    }


@GazetteApp.form(
    model=Principal, name='reset-password', template='form.pt',
    permission=Public, form=PasswordResetForm
)
def handle_password_reset(self, request, form):

    layout = Layout(self, request)
    callout = None
    show_form = True
    if form.submitted(request):
        if form.update_password(request):
            show_form = False
            request.message(_("Password changed."), 'success')
            return redirect(layout.homepage_link)
        else:
            form.error_message = _(
                "Wrong username or password reset link not valid any more."
            )
            log.info(
                "Failed password reset attempt by {}".format(
                    request.client_addr
                )
            )

    if 'token' in request.params:
        form.token.data = request.params['token']

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
        'show_form': show_form,
        'callout': callout
    }
