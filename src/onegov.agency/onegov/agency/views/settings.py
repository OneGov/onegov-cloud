from onegov.agency import _
from onegov.agency.app import AgencyApp
from onegov.core.security import Secret
from onegov.form import Form
from onegov.form import merge_forms
from onegov.org.forms import SettingsForm
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_settings
from wtforms import RadioField


def settings_form(model, request):

    class CustomFieldsForm(Form):

        pdf_layout = RadioField(
            label=_("PDF Layout"),
            fieldset=_("Agencies"),
            default='default',
            choices=[
                ('default', _("Default")),
                ('ar', "Kanton Appenzell Ausserrhoden"),
                ('zg', "Kanton Zug"),
            ],
        )

        def process_obj(self, obj):
            super().process_obj(obj)
            self.pdf_layout.data = obj.meta.get('pdf_layout', 'default')

        def populate_obj(self, obj, *args, **kwargs):
            super().populate_obj(obj, *args, **kwargs)
            obj.meta['pdf_layout'] = self.pdf_layout.data

    return merge_forms(SettingsForm, CustomFieldsForm)


@AgencyApp.form(
    model=Organisation,
    name='settings',
    template='form.pt',
    permission=Secret,
    form=settings_form
)
def custom_handle_settings(self, request, form):
    form.delete_field('default_map_view')
    return handle_settings(self, request, form)
