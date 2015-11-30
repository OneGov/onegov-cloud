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

    layout = DefaultLayout(self, request)
    layout.include_editor()

    request.include('check_contrast')

    if form.submitted(request):
        with request.app.update_town() as town:
            town.name = form.name.data
            town.logo_url = form.logo_url.data
            town.theme_options = form.theme_options
            town.meta = {
                'contact': form.contact.data,
                'contact_html': linkify(
                    form.contact.data).replace('\n', '<br>'),
                'contact_url': form.contact_url.data,
                'opening_hours': form.opening_hours.data,
                'opening_hours_html': linkify(
                    form.opening_hours.data).replace('\n', '<br>'),
                'opening_hours_url': form.opening_hours_url.data,
                'reply_to': form.reply_to.data,
                'facebook_url': form.facebook_url.data,
                'twitter_url': form.twitter_url.data,
                'analytics_code': form.analytics_code.data,
                'online_counter_label': form.online_counter_label.data,
                'reservations_label': form.reservations_label.data,
                'sbb_daypass_label': form.sbb_daypass_label.data,
            }

        request.success(_("Your changes were saved"))
    else:
        form.name.data = self.name
        form.logo_url.data = self.logo_url
        form.theme_options = self.theme_options
        form.contact.data = self.meta.get('contact')
        form.contact_url.data = self.meta.get('contact_url')
        form.opening_hours.data = self.meta.get('opening_hours')
        form.opening_hours_url.data = self.meta.get('opening_hours_url')
        form.reply_to.data = self.meta.get('reply_to')
        form.facebook_url.data = self.meta.get('facebook_url')
        form.twitter_url.data = self.meta.get('twitter_url')
        form.analytics_code.data = self.meta.get('analytics_code')
        form.online_counter_label.data = self.meta.get('online_counter_label')
        form.reservations_label.data = self.meta.get('reservations_label')
        form.sbb_daypass_label.data = self.meta.get('sbb_daypass_label')

    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Settings"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _('Settings'),
        'form': form,
        'form_width': 'large'
    }
