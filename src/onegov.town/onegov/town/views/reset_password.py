""" The request password views. """

import morepath

from onegov.core.security import Public
from onegov.form import Form
from onegov.town import _, log
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.mail import send_html_mail
from onegov.town.models import Town
from onegov.user import UserCollection
from wtforms import HiddenField, StringField, PasswordField, validators


class RequestPasswordResetForm(Form):
    """ Defines the password reset request form for onegov town. """

    email = StringField(
        _(u"Email Address"),
        [validators.InputRequired(), validators.Email()]
    )

    def get_token(self, request):
        """ Returns the user and a token for the given username to reset the
        password. If the username is not found, (None, None) is returned.

        """
        users = UserCollection(request.app.session())
        user = users.by_username(self.email.data)
        token = None

        if user is not None:
            modified = user.modified.isoformat() if user.modified else ''
            token = request.new_url_safe_token({
                'username': user.username,
                'modified': modified
            })
        return user, token


@TownApp.form(
    model=Town, name='request-password', template='form.pt', permission=Public,
    form=RequestPasswordResetForm
)
def handle_password_reset_request(self, request, form):
    """ Handles the GET and POST password reset requests. """
    if form.submitted(request):
        user, token = form.get_token(request)
        if user is not None and token is not None:
            url = '{0}?token={1}'.format(
                request.link(self, name='reset-password'), token
            )
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
            _((u'A password reset link has been sent to ${email}, provided an '
               u'account exists for this email address.'),
              mapping={'email': form.email.data})
        )
        return response

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Reset password"), request.link(self, name='request-password'))
    ]

    return {
        'layout': layout,
        'title': _(u'Reset password'),
        'form': form,
        'form_width': 'small'
    }


class PasswordResetForm(Form):
    """ Defines the password reset form for onegov town. """

    email = StringField(
        _(u"Email Address"),
        [validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(
        _(u"New Password"),
        [validators.InputRequired(), validators.Length(min=8)]
    )
    token = HiddenField()

    def get_identity(self, request):
        """ Returns the given user by username, token and the new password.
        If the username is not found or the token invalid, None is returned.

        """
        data = request.load_url_safe_token(self.token.data, max_age=86400)
        if data and data['username'] == self.email.data:
            users = UserCollection(request.app.session())
            user = users.by_username(self.email.data)
            if user:
                modified = user.modified.isoformat() if user.modified else ''
                if modified == data['modified']:
                    user.password = self.password.data
                    return morepath.Identity(
                        userid=user.username,
                        role=user.role,
                        application_id=request.app.application_id
                    )

        return None


@TownApp.form(
    model=Town, name='reset-password', template='form.pt', permission=Public,
    form=PasswordResetForm
)
def handle_password_reset(self, request, form):
    request.include('common')
    request.include('check_password')

    if form.submitted(request):
        identity = form.get_identity(request)
        if identity is not None:
            response = morepath.redirect(request.link(self))
            morepath.remember_identity(response, request, identity)
            request.success(_("Password changed."))
            return response
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
        'title': _(u'Reset password'),
        'form': form,
        'form_width': 'small'
    }
