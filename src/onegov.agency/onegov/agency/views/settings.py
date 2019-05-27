from onegov.agency import _
from onegov.agency.app import AgencyApp
from onegov.core.security import Secret
from onegov.form import Form
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from wtforms import BooleanField, RadioField


class AgencySettingsForm(Form):
    pdf_layout = RadioField(
        label=_("PDF Layout"),
        fieldset=_("Layout"),
        default='default',
        choices=[
            ('default', _("Default")),
            ('ar', "Kanton Appenzell Ausserrhoden"),
            ('zg', "Kanton Zug"),
        ],
    )

    report_changes = BooleanField(
        label=_("Users may report corrections"),
        fieldset=_("Data"),
        default=True,
    )

    def process_obj(self, obj):
        super().process_obj(obj)
        self.pdf_layout.data = obj.meta.get('pdf_layout', 'default')
        self.report_changes.data = obj.meta.get('report_changes', True)

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.meta['pdf_layout'] = self.pdf_layout.data
        obj.meta['report_changes'] = self.report_changes.data


@AgencyApp.form(
    model=Organisation,
    name='agency-settings',
    template='form.pt',
    permission=Secret,
    form=AgencySettingsForm,
    setting=_("Agencies"),
    icon='fa-university'
)
def handle_pdf_layout_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Agencies"))
