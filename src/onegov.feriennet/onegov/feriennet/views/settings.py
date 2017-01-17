from onegov.core.security import Secret
from onegov.org.forms import SettingsForm
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_settings
from onegov.feriennet.app import FeriennetApp


@FeriennetApp.form(model=Organisation, name='einstellungen',
                   template='form.pt', permission=Secret, form=SettingsForm)
def custom_handle_settings(self, request, form):

    form.delete_field('homepage_cover')
    form.delete_field('homepage_structure')

    return handle_settings(self, request, form)
