from onegov.core.security import Secret
from onegov.org.models import Organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.settings import \
    TranslatorDirectorySettingsForm
from onegov.translator_directory.layout import DefaultLayout
from onegov.translator_directory import _


@TranslatorDirectoryApp.form(
    model=Organisation,
    name='directory-settings',
    template='form.pt',
    permission=Secret,
    form=TranslatorDirectorySettingsForm
)
def view_locations_settings(self, request, form):
    layout = DefaultLayout(self, request)

    if form.submitted(request):
        form.update_model(request.app)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self, 'directory-settings'))

    form.apply_model(request.app)

    return {
        'layout': layout,
        'model': self,
        'title': _('Settings translator directory'),
        'form': form,
    }
