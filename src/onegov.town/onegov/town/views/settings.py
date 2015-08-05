""" The settings view, defining things like the logo or color of the town. """

from onegov.core.security import Secret
from onegov.core.utils import linkify
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import SettingsForm
from onegov.town.layout import DefaultLayout
from onegov.town.models import Town


@TownApp.form(
    model=Town, name='einstellungen', template='form.pt', permission=Secret,
    form=SettingsForm)
def handle_settings(self, request, form):
    """ Handles the GET and POST login requests. """

    if form.submitted(request):
        with request.app.update_town() as town:
            town.name = form.name.data
            town.logo_url = form.logo_url.data
            town.theme_options = form.theme_options
            town.meta = {
                'contact': form.contact.data,
                'contact_html': linkify(
                    form.contact.data).replace('\n', '<br>'),
                'opening_hours': form.opening_hours.data,
                'opening_hours_html': linkify(
                    form.opening_hours.data).replace('\n', '<br>'),
                'reply_to': form.reply_to.data,
                'analytics_code': form.analytics_code.data
            }

        request.success(_(u"Your changes were saved"))
    else:
        form.name.data = self.name
        form.logo_url.data = self.logo_url
        form.theme_options = self.theme_options
        form.contact.data = self.meta.get('contact')
        form.opening_hours.data = self.meta.get('opening_hours')
        form.reply_to.data = self.meta.get('reply_to')
        form.analytics_code.data = self.meta.get('analytics_code')

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Settings"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _(u'Settings'),
        'form': form,
        'form_width': 'large'
    }
