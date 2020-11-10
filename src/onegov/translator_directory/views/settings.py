from onegov.core.security import Secret
from onegov.org.models import Organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.forms.settings import LocationSettingsForm
from onegov.translator_directory.layout import DefaultLayout
from onegov.translator_directory import _


@TranslatorDirectoryApp.form(
    model=Organisation,
    name='location-settings',
    template='form.pt',
    permission=Secret,
    form=LocationSettingsForm
)
def view_locations_settings(self, request, form):
    layout = DefaultLayout(self, request)

    if form.submitted(request):
        form.apply_coordinates(request.app)
        request.success(_("Your changes were saved"))
        return request.redirect(request.class_link(TranslatorCollection))

    if not form.errors:
        form.process_coordinates(request.app)

    return {
        'layout': layout,
        'model': self,
        'title': _('Location Settings'),
        'form': form,
    }
