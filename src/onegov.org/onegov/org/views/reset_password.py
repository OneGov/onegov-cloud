""" The request password views. """

import morepath

from onegov.core.security import Public
from onegov.org import _, log, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import RequestPasswordResetForm, PasswordResetForm
from onegov.org.layout import DefaultLayout
from onegov.org.mail import send_html_mail
from onegov.org.models import Organisation
from onegov.user import UserCollection


@OrgApp.form(model=Organisation, name='request-password', template='form.pt',
             permission=Public, form=RequestPasswordResetForm)
def handle_password_reset_request(self, request, form):
    """ Handles the GET and POST password reset requests. """
    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Reset password"), request.link(self, name='request-password'))
    ]

    if form.submitted(request):

        users = UserCollection(request.app.session())
        user = users.by_username(form.email.data)
        url = layout.password_reset_url(user)

        if url:
            send_html_mail(
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

        response = morepath.redirect(request.link(self))
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


@OrgApp.form(model=Organisation, name='reset-password', template='form.pt',
             permission=Public, form=PasswordResetForm)
def handle_password_reset(self, request, form):
    request.include('common')
    request.include('check_password')

    if form.submitted(request):
        # do NOT log the user in at this point - only onegov.user.auth does
        # logins - we only ever want one path to be able to login, which makes
        # it easier to do it correctly.
        #
        # XXX move this to onegov.user.auth as well
        if form.update_password(request):
            request.success(_("Password changed."))
            return morepath.redirect(request.link(self))
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
