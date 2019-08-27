""" The authentication views. """

from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.templates import render_template
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day import log
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import MailLayout
from onegov.election_day.models import Principal
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.utils import password_reset_url


@ElectionDayApp.form(
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
            request.app.principal, name='request-password'
        ),
    }


@ElectionDayApp.html(
    model=Auth,
    name='logout',
    permission=Private
)
def view_logout(self, request):

    """ Handles the logout requests. """

    return self.logout_to(request)


@ElectionDayApp.form(
    model=Principal,
    name='request-password',
    template='form.pt',
    form=RequestPasswordResetForm,
    permission=Public
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
        'layout': DefaultLayout(self, request),
        'title': _('Reset password'),
        'form': form,
        'show_form': show_form,
        'callout': callout
    }


@ElectionDayApp.form(
    model=Principal,
    name='reset-password',
    template='form.pt',
    form=PasswordResetForm,
    permission=Public
)
def handle_password_reset(self, request, form):

    """ Handles password reset requests. """

    callout = None
    show_form = True
    if form.submitted(request):
        if form.update_password(request):
            show_form = False
            callout = _("Password changed.")
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
        'layout': DefaultLayout(self, request),
        'title': _('Reset password'),
        'form': form,
        'show_form': show_form,
        'callout': callout
    }
