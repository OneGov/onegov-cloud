from onegov.agency import _
from onegov.agency.app import AgencyApp
from onegov.core.security import Secret
from onegov.form import Form
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from wtforms import RadioField


class PDFLayoutForm(Form):
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


@AgencyApp.form(
    model=Organisation,
    name='pdf-layout-settings',
    template='form.pt',
    permission=Secret,
    form=PDFLayoutForm,
    setting=_("PDF Layout"),
    icon='fa-file-pdf-o'
)
def handle_pdf_layout_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("PDF Layout"))
