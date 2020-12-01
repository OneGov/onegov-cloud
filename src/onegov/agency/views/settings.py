from onegov.agency import _
from onegov.agency.app import AgencyApp
from onegov.core.security import Secret
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from wtforms import BooleanField, RadioField


class AgencySettingsForm(Form):

    topmost_levels = 1, 2, 3

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
        default='1'
    )

    orga_pdf_page_break = RadioField(
        label=_("For organisation PDF's, page after every:"),
        fieldset=_("Layout"),
        choices=[
            ('1', _("1 Heading")),
            ('2', _("1.1 Heading")),
            ('3', _("1.1.1 Heading")),
        ],
        default='1'
    )

    agency_display = ChosenSelectMultipleField(
        label=_('Show additional agencies to search results'),
        fieldset=_('Customize search results'),
        description=_(
            'Level 1 represents the root agencies, Level 2 their children'),
        choices=[]
    )

    agency_path_display_on_people = BooleanField(
        label=_('Show full agency path'),
        description=_('Always show the full path of the memberships agency'),
        fieldset=_('People detail page'),
        default=False
    )

    report_changes = BooleanField(
        label=_("Users may report corrections"),
        fieldset=_("Data"),
        default=True,
    )

    def level_choice(self, lvl):
        return str(lvl), self.request.translate(
            _('Level ${lvl}', mapping={'lvl': lvl}))

    def on_request(self):
        self.agency_display.choices = [
            self.level_choice(lvl) for lvl in self.topmost_levels
        ]

    def process_obj(self, obj):
        super().process_obj(obj)
        self.pdf_layout.data = obj.pdf_layout or 'default'
        self.root_pdf_page_break.data = str(
            obj.page_break_on_level_root_pdf or 1)
        self.orga_pdf_page_break.data = str(
            obj.page_break_on_level_org_pdf or 1)
        self.report_changes.data = obj.meta.get('report_changes', True)
        self.agency_display.data = [
            str(num) for num in obj.agency_display_levels or []
        ]
        self.agency_path_display_on_people.data = \
            obj.agency_path_display_on_people

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.pdf_layout = self.pdf_layout.data
        obj.report_changes = self.report_changes.data
        obj.page_break_on_level_root_pdf = int(self.root_pdf_page_break.data)
        obj.page_break_on_level_org_pdf = int(self.orga_pdf_page_break.data)
        obj.agency_display_levels = [
            int(num) for num in self.agency_display.data
        ]
        obj.agency_path_display_on_people = \
            self.agency_path_display_on_people.data


class PersonSettingsForm(Form):

    prevent_delete_person_with_memberships = BooleanField(
        label=_("People with memberships can't be deleted"),
        fieldset=_("Security"),
        default=False,
    )


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


@AgencyApp.form(
    model=Organisation,
    name='person-settings',
    template='form.pt',
    permission=Secret,
    form=PersonSettingsForm,
    setting=_("People"),
    icon='fa-university'
)
def handle_pdf_layout_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("People"))
