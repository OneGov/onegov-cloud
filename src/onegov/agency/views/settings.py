from __future__ import annotations

from onegov.agency import _
from onegov.agency.app import AgencyApp
from onegov.core.security import Secret
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField, ColorField
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from wtforms.fields import BooleanField, IntegerField, RadioField
from wtforms.validators import Optional, NumberRange

from onegov.town6.layout import SettingsLayout
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from webob import Response


class AgencySettingsForm(Form):

    topmost_levels = 1, 2, 3

    pdf_layout = RadioField(
        label=_('PDF Design'),
        fieldset=_('PDF Layout'),
        default='default',
        choices=[
            ('default', _('Default')),
            ('ar', 'Kanton Appenzell Ausserrhoden'),
            ('zg', 'Kanton Zug'),
            ('bs', 'Kanton Basel-Stadt'),
            ('lu', 'Kanton Luzern'),
        ],
    )

    root_pdf_page_break = RadioField(
        label=_('For root PDF, page after every:'),
        fieldset=_('PDF Layout'),
        choices=[
            ('1', _('1 Heading')),
            ('2', _('1.1 Heading')),
            ('3', _('1.1.1 Heading')),
        ],
        default='1'
    )

    orga_pdf_page_break = RadioField(
        label=_("For organisation PDF's, page after every:"),
        fieldset=_('PDF Layout'),
        choices=[
            ('1', _('1 Heading')),
            ('2', _('1.1 Heading')),
            ('3', _('1.1.1 Heading')),
        ],
        default='1'
    )

    link_color = ColorField(
        label=_('PDF link color'),
        fieldset=_('PDF Layout')
    )

    underline_links = BooleanField(
        label=_('Underline pdf links'),
        fieldset=_('PDF Layout')
    )

    agency_display = ChosenSelectMultipleField(
        label=_('Show additional agencies to search results'),
        fieldset=_('Customize search results'),
        description=_(
            'Level 1 represents the root agencies, Level 2 their children'),
        choices=[]
    )

    agency_phone_internal_digits = IntegerField(
        label=_(
            'Use the last digits as internal phone numbers '
            '(leave empty to disable)'
        ),
        fieldset=_('Customize search results'),
        validators=[
            NumberRange(min=1),
            Optional()
        ],
    )

    agency_phone_internal_field = RadioField(
        label=_('Field used for internal phone numbers'),
        fieldset=_('Customize search results'),
        choices=[
            ('phone', _('Phone')),
            ('phone_direct', _('Direct Phone Number or Mobile')),
        ],
    )

    agency_path_display_on_people = BooleanField(
        label=_('Show full agency path'),
        description=_('Always show the full path of the memberships agency'),
        fieldset=_('People detail page'),
        default=False
    )

    report_changes = BooleanField(
        label=_('Users may report corrections'),
        fieldset=_('Data'),
        default=True,
    )

    def level_choice(self, lvl: int) -> tuple[str, str]:
        return str(lvl), self.request.translate(
            _('Level ${lvl}', mapping={'lvl': lvl}))

    def on_request(self) -> None:
        self.agency_display.choices = [
            self.level_choice(lvl) for lvl in self.topmost_levels
        ]

    def process_obj(self, obj: Organisation) -> None:  # type:ignore
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

        self.agency_phone_internal_digits.data = (
            obj.agency_phone_internal_digits)
        self.agency_phone_internal_field.data = (
            obj.agency_phone_internal_field)

        self.agency_path_display_on_people.data = (
            obj.agency_path_display_on_people)

        self.underline_links.data = obj.pdf_underline_links
        self.link_color.data = obj.pdf_link_color or '#00538c'

    def populate_obj(  # type: ignore[override]
        self,
        obj: Organisation,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:

        super().populate_obj(obj, exclude, include)
        obj.pdf_layout = self.pdf_layout.data
        obj.report_changes = self.report_changes.data
        obj.page_break_on_level_root_pdf = int(self.root_pdf_page_break.data)
        obj.page_break_on_level_org_pdf = int(self.orga_pdf_page_break.data)
        obj.agency_display_levels = [
            int(num) for num in self.agency_display.data or ()
        ]
        obj.agency_phone_internal_digits = (
            self.agency_phone_internal_digits.data)
        obj.agency_phone_internal_field = (
            self.agency_phone_internal_field.data)
        obj.agency_path_display_on_people = (
            self.agency_path_display_on_people.data)
        obj.pdf_underline_links = self.underline_links.data
        obj.pdf_link_color = self.link_color.data


@AgencyApp.form(
    model=Organisation,
    name='agency-settings',
    template='form.pt',
    permission=Secret,
    form=AgencySettingsForm,
    setting=_('Agencies'),
    icon='fa-university'
)
def handle_agency_settings(
    self: Organisation,
    request: AgencyRequest,
    form: AgencySettingsForm
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Agencies'),
                                   SettingsLayout(self, request))
