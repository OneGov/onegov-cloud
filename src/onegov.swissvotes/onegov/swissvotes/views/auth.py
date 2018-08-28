from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.templates import render_template
from onegov.swissvotes import _
from onegov.swissvotes import log
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.layouts import DefaultLayout
from onegov.swissvotes.layouts import MailLayout
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.utils import password_reset_url


@SwissvotesApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    form=LoginForm,
    permission=Public
)
def handle_login(self, request, form):
    """ Handles the login requests. """

    if form.submitted(request):
        response = self.login_to(request=request, **form.login_data)
        form.error_message = _("Wrong username or password")
    else:
        response = None

    return response or {
        'layout': DefaultLayout(self, request),
        'title': _("Login"),
        'form': form,
        'password_reset_link': request.link(
            Auth.from_request(request), name='request-password'
        ),
    }


@SwissvotesApp.html(
    model=Auth,
    name='logout',
    permission=Private
)
def view_logout(self, request):
    """ Handles the logout requests. """

    return self.logout_to(request)


@SwissvotesApp.form(
    model=Auth,
    name='request-password',
    template='form.pt',
    form=RequestPasswordResetForm,
    permission=Public
)
def handle_password_reset_request(self, request, form):
    """ Handles the password reset requests. """

    layout = DefaultLayout(self, request)

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

        message = _(
            'A password reset link has been sent to ${email}, provided an '
            'account exists for this email address.',
            mapping={'email': form.email.data}
        )
        request.message(message, 'success')
        return request.redirect(layout.login_link)

    return {
        'layout': layout,
        'title': _('Reset password'),
        'form': form,
    }


@SwissvotesApp.form(
    model=Auth,
    name='reset-password',
    template='form.pt',
    form=PasswordResetForm,
    permission=Public
)
def handle_password_reset(self, request, form):
    """ Handles password reset requests. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        if form.update_password(request):
            request.message(_("Password changed."), 'success')
            return request.redirect(layout.login_link)
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
    }
