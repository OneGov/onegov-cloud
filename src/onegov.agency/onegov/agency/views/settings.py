from onegov.agency import _
from onegov.agency.app import AgencyApp
from onegov.core.security import Secret
from onegov.form import Form
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from wtforms import BooleanField, RadioField


class AgencySettingsForm(Form):

    default_page_break_level = '1'

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

    root_pdf_page_break = RadioField(
        label=_('For root PDF, page after every:'),
        fieldset=_("Layout"),
        choices=[
            ('1', _("1 Heading")),
            ('2', _("1.1 Heading")),
            ('3', _("1.1.1 Heading")),
        ],
    )

    orga_pdf_page_break = RadioField(
        label=_("For organisation PDF's, page after every:"),
        fieldset=_("Layout"),
        choices=[
            ('1', _("1 Heading")),
            ('2', _("1.1 Heading")),
            ('3', _("1.1.1 Heading")),
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
        self.root_pdf_page_break.data = obj.meta.get(
            'page_break_on_level_root_pdf', self.default_page_break_level)
        self.orga_pdf_page_break.data = obj.meta.get(
            'page_break_on_level_orga_pdf', self.default_page_break_level)
        self.report_changes.data = obj.meta.get('report_changes', True)

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.meta['pdf_layout'] = self.pdf_layout.data
        obj.meta['report_changes'] = self.report_changes.data
        obj.meta['page_break_on_level_root_pdf'] = \
            self.root_pdf_page_break.data
        obj.meta['page_break_on_level_orga_pdf'] = \
            self.orga_pdf_page_break.data


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
