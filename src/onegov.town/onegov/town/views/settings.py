""" The settings view, defining things like the logo or color of the town. """

from onegov.core.security import Secret
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
            form.populate_obj(town, exclude={'primary_color', 'footer-height'})
            town.theme_options = form.theme_options

        request.success(_("Your changes were saved"))
    elif request.method == 'GET':
        form.process(obj=self)
        form.theme_options = self.theme_options

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
