import datetime
import json
import re
from functools import cached_property
from lxml import etree

from onegov.core.widgets import transform_structure
from onegov.core.widgets import XML_LINE_OFFSET
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ColorField
from onegov.form.fields import CssField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import PreviewField
from onegov.form.fields import TagsField
from onegov.gever.encrypt import encrypt_symmetric
from onegov.gis import CoordinatesField
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.user import AVAILABLE_ROLES
from onegov.org.forms.util import TIMESPANS
from onegov.org.theme import user_options
from onegov.ticket import handlers
from onegov.ticket import TicketPermission
from onegov.user import User
from purl import URL
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import FloatField
from wtforms.fields import IntegerField
from wtforms.fields import PasswordField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import URL as UrlRequired
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.org.models import Organisation
    from onegov.org.request import OrgRequest
    from onegov.org.theme import OrgTheme
    from webob import Response
    from wtforms import Field
    from wtforms.fields.choices import _Choice


ERROR_LINE_RE = re.compile(r'line ([0-9]+)')


class GeneralSettingsForm(Form):
    """ Defines the settings form for onegov org. """

    if TYPE_CHECKING:
        request: OrgRequest

    name = StringField(
        label=_("Name"),
        validators=[InputRequired()])

    logo_url = StringField(
        label=_("Logo"),
        description=_("URL pointing to the logo"),
        render_kw={'class_': 'image-url'})

    square_logo_url = StringField(
        label=_("Logo (Square)"),
        description=_("URL pointing to the logo"),
        render_kw={'class_': 'image-url'})

    reply_to = EmailField(
        _("E-Mail Reply Address (Reply-To)"), [InputRequired()],
        description=_("Replies to automated e-mails go to this address."))

    primary_color = ColorField(
        label=_("Primary Color"))

    font_family_sans_serif = ChosenSelectField(
        label=_('Default Font Family'),
        choices=[],
        validators=[InputRequired()]
    )

    locales = RadioField(
        label=_("Languages"),
        choices=(
            ('de_CH', _("German")),
            ('fr_CH', _("French")),
            ('it_CH', _("Italian"))
        ),
        validators=[InputRequired()]
    )

    custom_css = CssField(
        label=_('Additional CSS'),
        render_kw={'rows': 8},
    )

    standard_image = StringField(
        description=_(
            'Will be used if an image is needed, but none has been set'),
        fieldset=_('Images'),
        label=_("Standard Image"),
        render_kw={'class_': 'image-url'}
    )

    @property
    def theme_options(self) -> dict[str, Any]:
        options = self.model.theme_options

        if self.primary_color.data is None:
            options['primary-color'] = user_options['primary-color']
        else:
            options['primary-color'] = self.primary_color.data
        font_family = self.font_family_sans_serif.data
        if font_family not in self.theme.font_families.values():
            options['font-family-sans-serif'] = self.default_font_family
        else:
            options['font-family-sans-serif'] = font_family

        # override the options using the default values if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        return options

    @theme_options.setter
    def theme_options(self, options: dict[str, Any]) -> None:
        self.primary_color.data = options.get('primary-color')
        self.font_family_sans_serif.data = options.get(
            'font-family-sans-serif') or self.default_font_family

    @cached_property
    def theme(self) -> 'OrgTheme':
        return self.request.app.settings.core.theme

    @property
    def default_font_family(self) -> str | None:
        return self.theme.default_options.get('font-family-sans-serif')

    def populate_obj(self, model: 'Organisation') -> None:  # type:ignore
        super().populate_obj(model)
        model.theme_options = self.theme_options
        model.custom_css = self.custom_css.data or ''

    def process_obj(self, model: 'Organisation') -> None:  # type:ignore
        super().process_obj(model)
        self.theme_options = model.theme_options or {}
        self.custom_css.data = model.custom_css or ''

    def populate_font_families(self) -> None:
        self.font_family_sans_serif.choices = [
            (value, label) for label, value in self.theme.font_families.items()
        ]

    def on_request(self) -> None:
        self.populate_font_families()

        @self.request.after
        def clear_locale(response: 'Response') -> None:
            response.delete_cookie('locale')


class FooterSettingsForm(Form):

    footer_left_width = IntegerField(
        label=_("Column width left side"),
        fieldset=_("Footer Division"),
        default=3,
        validators=[InputRequired()]
    )

    footer_center_width = IntegerField(
        label=_("Column width for the center"),
        fieldset=_("Footer Division"),
        default=5,
        validators=[InputRequired()]
    )

    footer_right_width = IntegerField(
        label=_("Column width right side"),
        fieldset=_("Footer Division"),
        default=4,
        validators=[InputRequired()]
    )

    contact = TextAreaField(
        label=_("Contact"),
        description=_("The address and phone number of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("Information"))

    contact_url = URLField(
        label=_("Contact Link"),
        description=_("URL pointing to a contact page"),
        fieldset=_("Information"),
        render_kw={'class_': 'internal-url'},
        validators=[UrlRequired(), Optional()]
    )

    opening_hours = TextAreaField(
        label=_("Opening Hours"),
        description=_("The opening hours of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("Information"))

    opening_hours_url = URLField(
        label=_("Opening Hours Link"),
        description=_("URL pointing to an opening hours page"),
        fieldset=_("Information"),
        render_kw={'class_': 'internal-url'},
        validators=[UrlRequired(), Optional()]
    )

    hide_onegov_footer = BooleanField(
        label=_("Hide OneGov Cloud information"),
        description=_(
            "This includes the link to the marketing page, and the link "
            "to the privacy policy."
        ),
        fieldset=_("Information")
    )

    facebook_url = URLField(
        label=_("Facebook"),
        description=_("URL pointing to the Facebook site"),
        fieldset=_("Social Media"),
        validators=[UrlRequired(), Optional()]
    )

    twitter_url = URLField(
        label=_("Twitter"),
        description=_("URL pointing to the Twitter site"),
        fieldset=_("Social Media"),
        validators=[UrlRequired(), Optional()]
    )

    youtube_url = URLField(
        label=_("YouTube"),
        description=_("URL pointing to the YouTube site"),
        fieldset=_("Social Media"),
        validators=[UrlRequired(), Optional()]
    )

    instagram_url = URLField(
        label=_("Instagram"),
        description=_("URL pointing to the Instagram site"),
        fieldset=_("Social Media"),
        validators=[UrlRequired(), Optional()]
    )

    custom_link_1_name = StringField(
        label=_("Name"),
        description="Name of the Label",
        fieldset=_("Custom Link 1")
    )

    custom_link_1_url = URLField(
        label=_("URL"),
        description=_("URL to internal/external site"),
        fieldset=_("Custom Link 1"),
        validators=[UrlRequired(), Optional()]
    )

    custom_link_2_name = StringField(
        label=_("Name"),
        description="Name of the Label",
        fieldset=_("Custom Link 2")
    )

    custom_link_2_url = URLField(
        label=_("URL"),
        description=_("URL to internal/external site"),
        fieldset=_("Custom Link 2"),
        validators=[UrlRequired(), Optional()]
    )

    custom_link_3_name = StringField(
        label=_("Name"),
        description="Name of the Label",
        fieldset=_("Custom Link 3")
    )

    custom_link_3_url = URLField(
        label=_("URL"),
        description=_("URL to internal/external site"),
        fieldset=_("Custom Link 3"),
        validators=[UrlRequired(), Optional()]
    )

    partner_1_name = StringField(
        label=_("Name"),
        description=_("Name of the partner"),
        fieldset=_("First Partner"))

    partner_1_img = StringField(
        label=_("Image"),
        description=_("Logo of the partner"),
        render_kw={'class_': 'image-url'},
        fieldset=_("First Partner"))

    partner_1_url = URLField(
        label=_("Website"),
        description=_("The partner's website"),
        fieldset=_("First Partner"),
        validators=[UrlRequired(), Optional()]
    )

    partner_2_name = StringField(
        label=_("Name"),
        description=_("Name of the partner"),
        fieldset=_("Second Partner"))

    partner_2_img = StringField(
        label=_("Image"),
        description=_("Logo of the partner"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Second Partner"))

    partner_2_url = URLField(
        label=_("Website"),
        description=_("The partner's website"),
        fieldset=_("Second Partner"),
        validators=[UrlRequired(), Optional()]
    )

    partner_3_name = StringField(
        label=_("Name"),
        description=_("Name of the partner"),
        fieldset=_("Third Partner"))

    partner_3_img = StringField(
        label=_("Image"),
        description=_("Logo of the partner"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Third Partner"))

    partner_3_url = URLField(
        label=_("Website"),
        description=_("The partner's website"),
        fieldset=_("Third Partner"),
        validators=[UrlRequired(), Optional()]
    )

    partner_4_name = StringField(
        label=_("Name"),
        description=_("Name of the partner"),
        fieldset=_("Fourth Partner"))

    partner_4_img = StringField(
        label=_("Image"),
        description=_("Logo of the partner"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Fourth Partner"))

    partner_4_url = URLField(
        label=_("Website"),
        description=_("The partner's website"),
        fieldset=_("Fourth Partner"),
        validators=[UrlRequired(), Optional()]
    )

    def ensure_correct_footer_column_width(self) -> bool | None:

        for col in ('left', 'center', 'right'):
            if getattr(self, f'footer_{col}_width').data <= 0:
                field = getattr(self, f'footer_{col}_width')
                field.errors.append(
                    _('The width of the column must be greater than 0')
                )
                return False

        assert self.footer_left_width.data is not None
        assert self.footer_center_width.data is not None
        assert self.footer_right_width.data is not None
        summed_cols = sum([
            self.footer_left_width.data,
            self.footer_center_width.data,
            self.footer_right_width.data
        ])

        if summed_cols != 12:
            for col in ('left', 'center', 'right'):
                field = getattr(self, f'footer_{col}_width')
                field.errors.append(
                    _("The sum of all the footer columns must be equal to 12")
                )
            return False
        return None


class SocialMediaSettingsForm(Form):
    og_logo_default = StringField(
        label=_("Image"),
        description=_("Default social media preview image for rich link "
                      "previews. Optimal size is 1200:630 px."),
        fieldset="OpenGraph",
        render_kw={'class_': 'image-url'}
    )


class FaviconSettingsForm(Form):

    favicon_win_url = StringField(
        label=_("Icon 16x16 PNG (Windows)"),
        description=_("URL pointing to the icon"),
        render_kw={'class_': 'image-url'},
    )

    favicon_mac_url = StringField(
        label=_("Icon 32x32 PNG (Mac)"),
        description=_("URL pointing to the icon"),
        render_kw={'class_': 'image-url'},
    )

    favicon_apple_touch_url = StringField(
        label=_("Icon 57x57 PNG (iPhone, iPod, iPad)"),
        description=_("URL pointing to the icon"),
        render_kw={'class_': 'image-url'},
    )

    favicon_pinned_tab_safari_url = StringField(
        label=_("Icon SVG 20x20 (Safari)"),
        description=_("URL pointing to the icon"),
        render_kw={'class_': 'image-url'},
    )


class LinksSettingsForm(Form):
    disable_page_refs = BooleanField(
        label=_("Disable page references"),
        description=_(
            "Disable showing the copy link '#' for the site reference. "
            "The references themselves will still work. "
            "Those references are only showed for logged in users.")
    )

    open_files_target_blank = BooleanField(
        label=_("Open files in separate window")
    )


class HeaderSettingsForm(Form):

    announcement = StringField(
        label=_("Announcement"),
        fieldset=_("Announcement"),
    )

    announcement_url = StringField(
        label=_("Announcement URL"),
        fieldset=_("Announcement"),
    )

    announcement_bg_color = ColorField(
        label=_("Announcement bg color"),
        fieldset=_("Announcement")
    )

    announcement_font_color = ColorField(
        label=_("Announcement font color"),
        fieldset=_("Announcement")
    )

    announcement_is_private = BooleanField(
        label=_("Only show Announcement for logged-in users"),
        fieldset=_("Announcement")
    )

    header_links = StringField(
        label=_("Header links"),
        fieldset=_("Header links"),
        render_kw={'class_': 'many many-links'}
    )

    left_header_name = StringField(
        label=_("Text"),
        description=_(""),
        fieldset=_("Text header left side")
    )

    left_header_url = URLField(
        label=_("URL"),
        description=_("Optional"),
        fieldset=_("Text header left side"),
        validators=[UrlRequired(), Optional()]
    )

    left_header_color = ColorField(
        label=_("Font color"),
        fieldset=_("Text header left side")
    )

    left_header_rem = FloatField(
        label=_("Relative font size"),
        fieldset=_("Text header left side"),
        validators=[
            NumberRange(0.5, 7)
        ],
        default=1
    )

    header_additions_fixed = BooleanField(
        label=_(
            "Keep header links and/or header text fixed to top on scrolling"),
        fieldset=_("Header fixation")
    )

    @property
    def header_options(self) -> dict[str, Any]:
        return {
            'header_links': self.json_to_links(self.header_links.data) or None,
            'left_header_name': self.left_header_name.data or None,
            'left_header_url': self.left_header_url.data or None,
            'left_header_color': self.left_header_color.data,
            'left_header_rem': self.left_header_rem.data,
            'announcement': self.announcement.data,
            'announcement_url': self.announcement_url.data,
            'announcement_bg_color': self.announcement_bg_color.data,
            'announcement_font_color':
            self.announcement_font_color.data,
            'announcement_is_private': self.announcement_is_private.data,
            'header_additions_fixed': self.header_additions_fixed.data
        }

    @header_options.setter
    def header_options(self, options: dict[str, Any]) -> None:
        if not options.get('header_links'):
            self.header_links.data = self.links_to_json(None)
        else:
            self.header_links.data = self.links_to_json(
                options.get('header_links')
            )

        self.left_header_name.data = options.get('left_header_name')
        self.left_header_url.data = options.get('left_header_url')
        self.left_header_color.data = options.get(
            'left_header_color', '#000000'
        )
        self.left_header_rem.data = options.get('left_header_rem', 1)
        self.announcement.data = options.get('announcement', '')
        self.announcement_url.data = options.get('announcement_url', '')
        self.announcement_bg_color.data = options.get(
            'announcement_bg_color', '#FBBC05')
        self.announcement_font_color.data = options.get(
            'announcement_font_color', '#000000')
        self.announcement_is_private.data = options.get(
            'announcement_is_private', '')
        self.header_additions_fixed.data = options.get(
            'header_additions_fixed', '')

    if TYPE_CHECKING:
        link_errors: dict[int, str]
    else:
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.link_errors = {}

    def populate_obj(self, model: 'Organisation') -> None:  # type:ignore
        super().populate_obj(model)
        model.header_options = self.header_options

    def process_obj(self, model: 'Organisation') -> None:  # type:ignore
        super().process_obj(model)
        self.header_options = model.header_options or {}

    def validate_header_links(self, field: StringField) -> None:
        for text, url in self.json_to_links(self.header_links.data):
            if text and not url:
                raise ValidationError(_('Please add an url to each link'))
            if url and not re.match(r'^(http://|https://|/)', url):
                raise ValidationError(
                    _('Your URLs must start with http://,'
                        ' https:// or / (for internal links)')
                )

    def json_to_links(
        self,
        text: str | None = None
    ) -> list[tuple[str | None, str | None]]:
        result = []

        for value in json.loads(text or '{}').get('values', []):
            if value['link'] or value['text']:
                result.append((value['text'], value['link']))

        return result

    def links_to_json(
        self,
        header_links: 'Sequence[tuple[str | None, str | None]] | None' = None
    ) -> str:
        header_links = header_links or []

        return json.dumps({
            'labels': {
                'text': self.request.translate(_("Text")),
                'link': self.request.translate(_("URL")),
                'add': self.request.translate(_("Add")),
                'remove': self.request.translate(_("Remove")),
            },
            'values': [
                {
                    'text': l[0],
                    'link': l[1],
                    'error': self.link_errors.get(ix, '')
                } for ix, l in enumerate(header_links)
            ]
        })


class HomepageSettingsForm(Form):

    homepage_cover = HtmlField(
        label=_("Homepage Cover"),
        render_kw={'rows': 10})

    homepage_structure = TextAreaField(
        fieldset=_("Structure"),
        label=_("Homepage Structure (for advanced users only)"),
        description=_("The structure of the homepage"),
        render_kw={'rows': 32, 'data-editor': 'xml'})

    # see homepage.py
    redirect_homepage_to = RadioField(
        label=_("Homepage redirect"),
        default='no',
        choices=[
            ('no', _("No")),
            ('directories', _("Yes, to directories")),
            ('events', _("Yes, to events")),
            ('forms', _("Yes, to forms")),
            ('publications', _("Yes, to publications")),
            ('reservations', _("Yes, to reservations")),
            ('path', _("Yes, to a non-listed path")),
        ])

    redirect_path = StringField(
        label=_("Path"),
        validators=[InputRequired()],
        depends_on=('redirect_homepage_to', 'path'))

    def validate_redirect_path(self, field: StringField) -> None:
        if not field.data:
            return

        url = URL(field.data)

        if url.scheme() or url.host():
            raise ValidationError(
                _("Please enter a path without schema or host"))

    def validate_homepage_structure(self, field: TextAreaField) -> None:
        if field.data:
            try:
                registry = self.request.app.config.homepage_widget_registry
                widgets = registry.values()
                transform_structure(widgets, field.data)
            except etree.XMLSyntaxError as exception:
                correct_line = exception.position[0] - XML_LINE_OFFSET

                correct_msg = 'line {}'.format(correct_line)
                correct_msg = ERROR_LINE_RE.sub(correct_msg, exception.msg)

                field.render_kw = field.render_kw or {}
                field.render_kw['data-highlight-line'] = correct_line

                raise ValidationError(correct_msg) from exception


class ModuleSettingsForm(Form):

    hidden_people_fields = MultiCheckboxField(
        label=_("Hide these fields for non-logged-in users"),
        fieldset=_("People"),
        choices=[
            ('salutation', _("Salutation")),
            ('academic_title', _("Academic Title")),
            ('born', _("Born")),
            ('profession', _("Profession")),
            ('political_party', _("Political Party")),
            ('parliamentary_group', _("Parliamentary Group")),
            ('email', _("E-Mail")),
            ('phone', _("Phone")),
            ('phone_direct', _("Direct Phone Number or Mobile")),
            ('website', _("Website")),
            ('website_2', _("Website 2")),
            ('location_address', _("Location address")),
            ('location_code_city', _("Location Code and City")),
            ('postal_address', _("Postal address")),
            ('postal_code_city', _("Postal Code and City")),
            ('notes', _("Notes")),
        ])

    event_locations = TagsField(
        label=_("Values of the location filter"),
        fieldset=_("Events"),)

    event_filter_type = RadioField(
        label=_('Choose the filter type for events (default is \'tags\')'),
        choices=(
            ('tags', _('A predefined set of tags')),
            ('filters', _('Manually configurable filters')),
            ('tags_and_filters', _('Both, predefined tags as well as '
                                   'configurable filters')),
        ),
        default='tags'
    )

    mtan_session_duration_seconds = IntegerField(
        label=_('Duration of mTAN session'),
        description=_('Specify in number of seconds'),
        fieldset=_('mTAN Access'),
        validators=[Optional()]
    )

    mtan_access_window_requests = IntegerField(
        label=_(
            'Prevent further accesses to protected resources '
            'after this many have been accessed'
        ),
        description=_('Leave empty to disable limiting requests'),
        fieldset=_('mTAN Access'),
        validators=[Optional()]
    )

    mtan_access_window_seconds = IntegerField(
        label=_(
            'Prevent further accesses to protected resources '
            'in this time frame'
        ),
        description=_('Specify in number of seconds'),
        fieldset=_('mTAN Access'),
        validators=[Optional()]
    )


class MapSettingsForm(Form):

    default_map_view = CoordinatesField(
        label=_("The default map view. This should show the whole town"),
        render_kw={
            'data-map-type': 'crosshair'
        })

    geo_provider = RadioField(
        label=_("Geo provider"),
        default='geo-mapbox',
        choices=[
            ('geo-admin', _("Swisstopo (Default)")),
            ('geo-admin-aerial', _("Swisstopo Aerial")),
            ('geo-mapbox', "Mapbox"),
            ('geo-vermessungsamt-winterthur', "Vermessungsamt Winterthur"),
            ('geo-zugmap-basisplan', "ZugMap Basisplan Farbig"),
            ('geo-zugmap-orthofoto', "ZugMap Orthofoto"),
            ('geo-bs', "Geoportal Basel-Stadt"),
        ])


class AnalyticsSettingsForm(Form):

    analytics_code = TextAreaField(
        label=_("Analytics Code"),
        description=_("JavaScript for web statistics support"),
        render_kw={'rows': 10, 'data-editor': 'html'})


class HolidaySettingsForm(Form):

    cantonal_holidays = MultiCheckboxField(
        label=_("Cantonal holidays"),
        choices=[
            ('AG', _('Aargau')),
            ('AR', _('Appenzell Ausserrhoden')),
            ('AI', _('Appenzell Innerrhoden')),
            ('BL', _('Basel-Landschaft')),
            ('BS', _('Basel-Stadt')),
            ('BE', _('Berne')),
            ('FR', _('Fribourg')),
            ('GE', _('Geneva')),
            ('GL', _('Glarus')),
            ('GR', _('Grisons')),
            ('JU', _('Jura')),
            ('LU', _('Lucerne')),
            ('NE', _('Neuchâtel')),
            ('NW', _('Nidwalden')),
            ('OW', _('Obwalden')),
            ('SH', _('Schaffhausen')),
            ('SZ', _('Schwyz')),
            ('SO', _('Solothurn')),
            ('SG', _('St. Gallen')),
            ('TG', _('Thurgau')),
            ('TI', _('Ticino')),
            ('UR', _('Uri')),
            ('VS', _('Valais')),
            ('VD', _('Vaud')),
            ('ZG', _('Zug')),
            ('ZH', _('Zürich')),
        ])

    other_holidays = TextAreaField(
        label=_("Other holidays"),
        description=("31.10 - Halloween"),
        render_kw={'rows': 10})

    preview = PreviewField(
        label=_("Preview"),
        fields=('cantonal_holidays', 'other_holidays'),
        events=('change', 'click', 'enter'),
        url=lambda meta: meta.request.link(
            meta.request.app.org,
            name='holiday-settings-preview'
        ))

    school_holidays = TextAreaField(
        label=_("School holidays"),
        description=("12.03.2022 - 21.03.2022"),
        render_kw={'rows': 10})

    def validate_other_holidays(self, field: TextAreaField) -> None:
        if not field.data:
            return

        for line in field.data.splitlines():

            if not line.strip():
                continue

            if line.count('-') < 1:
                raise ValidationError(_("Format: Day.Month - Description"))
            if line.count('-') > 1:
                raise ValidationError(_("Please enter one date per line"))

            date, description = line.split('-')

            if date.count('.') < 1:
                raise ValidationError(_("Format: Day.Month - Description"))
            if date.count('.') > 1:
                raise ValidationError(_("Please enter only day and month"))

    def parse_date(self, date: str) -> datetime.date:
        day, month, year = date.split('.')
        try:
            return datetime.date(int(year), int(month), int(day))
        except (ValueError, TypeError) as exception:
            raise ValidationError(_(
                "${date} is not a valid date",
                mapping={'date': date}
            )) from exception

    def validate_school_holidays(self, field: TextAreaField) -> None:
        if not field.data:
            return

        for line in field.data.splitlines():

            if not line.strip():
                continue

            if line.count('-') < 1:
                raise ValidationError(
                    _("Format: Day.Month.Year - Day.Month.Year")
                )
            if line.count('-') > 1:
                raise ValidationError(_("Please enter one date pair per line"))

            start, end = line.split('-')
            if start.count('.') != 2:
                raise ValidationError(
                    _("Format: Day.Month.Year - Day.Month.Year")
                )
            if end.count('.') != 2:
                raise ValidationError(
                    _("Format: Day.Month.Year - Day.Month.Year")
                )

            start_date = self.parse_date(start)
            end_date = self.parse_date(end)
            if end_date <= start_date:
                raise ValidationError(
                    _("End date needs to be after start date")
                )

    # FIXME: Use TypedDict?
    @property
    def holiday_settings(self) -> dict[str, Any]:

        def parse_other_holidays_line(line: str) -> tuple[int, int, str]:
            date, desc = line.strip().split('-')
            day, month = date.split('.')

            return int(month), int(day), desc.strip()

        def parse_school_holidays_line(
            line: str
        ) -> tuple[int, int, int, int, int, int]:

            start, end = line.strip().split('-')
            start_day, start_month, start_year = start.split('.')
            end_day, end_month, end_year = end.split('.')

            return (
                int(start_year), int(start_month), int(start_day),
                int(end_year), int(end_month), int(end_day)
            )

        return {
            'cantons': self.cantonal_holidays.data,
            'school': (
                parse_school_holidays_line(l)
                for l in (self.school_holidays.data or '').splitlines()
                if l.strip()
            ),
            'other': (
                parse_other_holidays_line(l)
                for l in (self.other_holidays.data or '').splitlines()
                if l.strip()
            )
        }

    @holiday_settings.setter
    def holiday_settings(self, data: dict[str, Any]) -> None:
        data = data or {}

        def format_other(d: tuple[int, int, str]) -> str:
            return f'{d[1]:02d}.{d[0]:02d} - {d[2]}'

        def format_school(d: tuple[int, int, int, int, int, int]) -> str:
            return (
                f'{d[2]:02d}.{d[1]:02d}.{d[0]:04d} - '
                f'{d[5]:02d}.{d[4]:02d}.{d[3]:04d}'
            )

        self.cantonal_holidays.data = data.get(
            'cantons', ())

        self.other_holidays.data = '\n'.join(
            format_other(d) for d in data.get('other', ()))

        self.school_holidays.data = '\n'.join(
            format_school(d) for d in data.get('school', ()))

    def populate_obj(self, model: 'Organisation') -> None:  # type:ignore
        model.holiday_settings = self.holiday_settings

    def process_obj(self, model: 'Organisation') -> None:  # type:ignore
        self.holiday_settings = model.holiday_settings


class OrgTicketSettingsForm(Form):

    email_for_new_tickets = StringField(
        label=_("Email adress for notifications "
                "about newly opened tickets"),
        description=("info@example.ch")
    )

    ticket_auto_accept_style = RadioField(
        label=_("Accept request and close ticket automatically based on:"),
        choices=(
            ('category', _("Ticket category")),
            ('role', _("User role")),
        ),
        default='category'
    )

    ticket_auto_accepts = MultiCheckboxField(
        label=_("Accept request and close ticket automatically "
                "for these ticket categories"),
        description=_("If auto-accepting is not possible, the ticket will be "
                      "in state pending. Also note, that after the ticket is "
                      "closed, the submitter can't send any messages."),
        choices=[],
        depends_on=('ticket_auto_accept_style', 'category')
    )

    ticket_auto_accept_roles = MultiCheckboxField(
        label=_("Accept request and close ticket automatically "
                "for these user roles"),
        description=_("If auto-accepting is not possible, the ticket will be "
                      "in state pending. Also note, that after the ticket is "
                      "closed, the submitter can't send any messages."),
        choices=AVAILABLE_ROLES,
        depends_on=('ticket_auto_accept_style', 'role')
    )

    auto_closing_user = ChosenSelectField(
        label=_("User used to auto-accept tickets"),
        choices=[]
    )

    tickets_skip_opening_email = MultiCheckboxField(
        label=_("Block email confirmation when "
                "this ticket category is opened"),
        choices=[],
        description=_("This is enabled by default for tickets that get "
                      "accepted automatically")
    )

    tickets_skip_closing_email = MultiCheckboxField(
        label=_("Block email confirmation when "
                "this ticket category is closed"),
        choices=[],
        description=_("This is enabled by default for tickets that get "
                      "accepted automatically")
    )

    mute_all_tickets = BooleanField(
        label=_("Mute all tickets")
    )

    ticket_always_notify = BooleanField(
        label=_('Always send email notification '
                'if a new ticket message is sent'),
        default=True
    )

    permissions = MultiCheckboxField(
        label=_('Categories restriced by user group settings'),
        choices=[],
        render_kw={'disabled': True}
    )

    def ensure_not_muted_and_auto_accept(self) -> bool | None:
        if (
            self.mute_all_tickets.data is True
            and self.ticket_auto_accepts.data
        ):
            assert isinstance(self.mute_all_tickets.errors, list)
            self.mute_all_tickets.errors.append(
                _("Mute tickets individually if the auto-accept feature is "
                  "enabled.")
            )
            return False
        return None

    def code_title(self, code: str) -> str:
        """ Renders a better translation for handler_codes.
        Note that the registry of handler_codes is global and not all handlers
        might are used in this app. The translations give a hint whether the
        handler is used/defined in the app using this form.
        A better translation is only then possible.
        """
        trs = getattr(handlers.registry[code], 'code_title', None)
        if not trs:
            return code
        translated = self.request.translate(trs)
        if str(trs) == translated:
            # Code not used by app
            return code
        return f'{code} - {translated}'

    def on_request(self) -> None:

        choices: list[_Choice] = [
            (key, self.code_title(key)) for key in handlers.registry.keys()
        ]
        auto_accept_choices = ('RSV', 'FRM')
        self.ticket_auto_accepts.choices = [
            (key, self.code_title(key)) for key in auto_accept_choices
        ]
        self.tickets_skip_opening_email.choices = choices
        self.tickets_skip_closing_email.choices = choices

        permissions: list[_Choice] = sorted((
            (
                p.id.hex,
                ': '.join(x for x in (p.handler_code, p.group) if x)
            )
            for p in self.request.session.query(TicketPermission)
        ), key=lambda x: x[1])
        self.permissions.choices = permissions
        self.permissions.default = [p[0] for p in permissions]

        user_q = self.request.session.query(User).filter_by(role='admin')
        user_q = user_q.order_by(User.created.desc())
        self.auto_closing_user.choices = [
            (u.username, u.title) for u in user_q
        ]


class NewsletterSettingsForm(Form):

    show_newsletter = BooleanField(
        label=_('Enable newsletter'),
        default=False
    )

    logo_in_newsletter = BooleanField(
        label=_('Include logo in newsletter')
    )

    secret_content_allowed = BooleanField(
        label=_('Allow secret content in newsletter'),
        default=False
    )


class LinkMigrationForm(Form):

    old_domain = StringField(
        label=_('Old domain'),
        description='govikon.onegovcloud.ch',
        validators=[InputRequired()]
    )

    test = BooleanField(
        label=_('Test migration'),
        description=_('Compares links to the current domain'),
        default=True
    )

    def ensure_correct_domain(self) -> bool | None:
        if self.old_domain.data:
            errors = []
            if self.old_domain.data.startswith('http'):
                errors.append(
                    _('Use a domain name without http(s)')
                )
            if '.' not in self.old_domain.data:
                errors.append(_('Domain must contain a dot'))

            if errors:
                self.old_domain.errors = errors
                return False
        return None


class LinkHealthCheckForm(Form):

    scope = RadioField(
        label=_('Choose which links to check'),
        choices=(
            ('external', _('External links only')),
            ('internal', _('Internal links only')),
        ),
        default='external'
    )


def validate_https(form: Form, field: 'Field') -> None:
    if not field.data.startswith('https'):
        raise ValidationError(_("Link must start with 'https'"))


class GeverSettingsForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    gever_username = StringField(
        _("Username"),
        [InputRequired()],
        description=_("Username for the associated Gever account"),
    )

    gever_password = PasswordField(
        _("Password"),
        [InputRequired()],
        description=_("Password for the associated Gever account"),
    )

    gever_endpoint = URLField(
        _("Gever API Endpoint where the documents are uploaded."),
        [InputRequired(), UrlRequired(), validate_https],
        description=_("Website address including https://"),
    )

    def populate_obj(self, model: 'Organisation') -> None:  # type:ignore
        super().populate_obj(model)
        key_base64 = self.request.app.hashed_identity_key
        try:
            assert self.gever_password.data is not None
            encrypted = encrypt_symmetric(self.gever_password.data, key_base64)
            encrypted_str = encrypted.decode('utf-8')
            model.gever_username = self.gever_username.data or ''
            model.gever_password = encrypted_str or ''
        except Exception:
            model.gever_username = ''
            model.gever_password = ''  # nosec: B105

    def process_obj(self, model: 'Organisation') -> None:  # type:ignore
        super().process_obj(model)

        self.gever_username.data = model.gever_username or ''
        self.gever_password.data = model.gever_password or ''


class OneGovApiSettingsForm(Form):
    """Provides a form to generate API keys (UUID'S) for the OneGov API."""

    name = StringField(
        default=_("API Key"),
        label=_("Name"),
        validators=[InputRequired()],
    )


class EventSettingsForm(Form):

    submit_events_visible = BooleanField(
        label=_('Submit your event'),
        description=_('Enables website visitors to submit their own events'),
        default=True
    )

    delete_past_events = BooleanField(
        label=_('Delete events in the past'),
        description=_('Events are automatically deleted once they have '
                      'occurred'),
        default=False
    )


class DataRetentionPolicyForm(Form):

    auto_archive_timespan = RadioField(
        label=_('Duration from opening a ticket to its automatic archival'),
        validators=[InputRequired()],
        default=0,
        coerce=int,
        choices=TIMESPANS
    )

    auto_delete_timespan = RadioField(
        label=_('Duration from archived state until deleted automatically'),
        validators=[InputRequired()],
        default=0,
        coerce=int,
        choices=TIMESPANS
    )
