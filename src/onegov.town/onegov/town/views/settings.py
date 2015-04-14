""" The login/logout views. """

from colour import Color
from onegov.core.security import Secret
from onegov.form import Form
from wtforms import StringField, validators
from wtforms_components import ColorField
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import DefaultLayout
from onegov.town.model import Town


class SettingsForm(Form):
    """ Defines the settings form for onegov town. """

    name = StringField(_(u"Name"), [validators.InputRequired()])
    primary_color = ColorField(_(u"Primary Color"))


@TownApp.html(
    model=Town, name='settings', template='form.pt',
    permission=Secret, request_method='GET')
def view_settings(self, request):
    return handle_settings(self, request)


@TownApp.html(
    model=Town, name='settings', template='form.pt',
    permission=Secret, request_method='POST')
def view_post_settings(self, request):
    return handle_settings(self, request)


def handle_settings(self, request):
    """ Handles the GET and POST login requests. """

    form = request.get_form(SettingsForm)
    form.action = request.link(self, name='settings')

    if form.submitted(request):
        self.name = form.name.data
        self.theme_options['primary-color'] = form.primary_color.data.get_hex()
        request.app.session().flush()
    else:
        form.name.data = self.name
        form.primary_color.data = self.theme_options.get('primary-color')

    return {
        'layout': DefaultLayout(self, request),
        'title': _(u'Settings for ${town}', mapping={'town': self.name}),
        'form': form
    }
