""" The settings view, defining things like the logo or color of the org. """

from onegov.core.security import Secret
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org import _
from onegov.org.app import OrgApp
from onegov.org.forms import SettingsForm
from onegov.org.models import Organisation


@OrgApp.form(
    model=Organisation, name='einstellungen', template='form.pt',
    permission=Secret, form=SettingsForm)
def handle_settings(self, request, form):
    """ Handles the GET and POST login requests. """

    layout = DefaultLayout(self, request)
    layout.include_editor()
    layout.include_code_editor()

    request.include('check_contrast')

    if form.submitted(request):
        with request.app.update_org() as org:
            form.populate_obj(org, exclude={'primary_color', 'footer-height'})
            org.theme_options = form.theme_options

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
        'form_width': 'huge'
    }
