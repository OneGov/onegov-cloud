from __future__ import annotations

import datetime
import json
import re
import yaml

from decimal import Decimal
from functools import cached_property

from cryptography.fernet import InvalidToken
from lxml import etree
from markupsafe import Markup
from onegov.core.templates import render_macro
from onegov.core.widgets import transform_structure
from onegov.core.widgets import XML_LINE_OFFSET
from onegov.form import Form
from onegov.form.fields import (ChosenSelectField, URLPanelField,
                                ChosenSelectMultipleEmailField)
from onegov.form.fields import ColorField
from onegov.form.fields import CssField
from onegov.form.fields import MarkupField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import PreviewField
from onegov.form.fields import TagsField
from onegov.form.fields import URLField
from onegov.form.validators import StrictOptional
from onegov.gis import CoordinatesField
from onegov.org import _, log
from onegov.org.forms.fields import (
    HtmlField,
    UploadOrSelectExistingMultipleFilesField,
)
from onegov.org.forms.user import AVAILABLE_ROLES
from onegov.org.forms.util import KABA_CODE_RE
from onegov.org.forms.util import TIMESPANS
from onegov.org.kaba import KabaApiError, KabaClient
from onegov.org.theme import user_options
from onegov.ticket import handlers
from onegov.ticket import TicketPermission
from onegov.user import User
from operator import itemgetter
from purl import URL
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import FieldList
from wtforms.fields import FloatField
from wtforms.fields import FormField
from wtforms.fields import IntegerField
from wtforms.fields import PasswordField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.utils import unset_value
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import URL as URLValidator
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
    from wtforms.fields.core import _Filter
    from wtforms.meta import _MultiDictLikeWithGetlist


ERROR_LINE_RE = re.compile(r'line ([0-9]+)')
COLOR_RE = re.compile(r'^#?(?:[0-9a-fA-F]{3}){1,2}$')


class GeneralSettingsForm(Form):
    """ Defines the settings form for onegov org. """

    if TYPE_CHECKING:
        request: OrgRequest

    name = StringField(
        label=_('Name'),
        validators=[InputRequired()])

    logo_url = StringField(
        label=_('Logo'),
        description=_('URL pointing to the logo'),
        render_kw={'class_': 'image-url'})

    square_logo_url = StringField(
        label=_('Logo (Square)'),
        description=_('URL pointing to the logo'),
        render_kw={'class_': 'image-url'})

    reply_to = EmailField(
        _('E-Mail Reply Address (Reply-To)'), [InputRequired()],
        description=_('Replies to automated e-mails go to this address.'))

    primary_color = ColorField(
        label=_('Primary Color'))

    font_family_sans_serif = ChosenSelectField(
        label=_('Default Font Family'),
        choices=[],
        validators=[InputRequired()]
    )

    locales = RadioField(
        label=_('Languages'),
        choices=(
            ('de_CH', _('German')),
            ('fr_CH', _('French')),
            ('it_CH', _('Italian'))
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
        label=_('Standard Image'),
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
    def theme(self) -> OrgTheme:
        return self.request.app.settings.core.theme

    @property
    def default_font_family(self) -> str | None:
        return self.theme.default_options.get('font-family-sans-serif')

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)
        model.theme_options = self.theme_options
        model.custom_css = self.custom_css.data or ''

    def process_obj(self, model: Organisation) -> None:  # type:ignore
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
        def clear_locale(response: Response) -> None:
            response.delete_cookie('locale')


class FooterSettingsForm(Form):

    footer_left_width = IntegerField(
        label=_('Column width left side'),
        fieldset=_('Footer Division'),
        default=3,
        validators=[InputRequired()]
    )

    footer_center_width = IntegerField(
        label=_('Column width for the center'),
        fieldset=_('Footer Division'),
        default=5,
        validators=[InputRequired()]
    )

    footer_right_width = IntegerField(
        label=_('Column width right side'),
        fieldset=_('Footer Division'),
        default=4,
        validators=[InputRequired()]
    )

    contact = TextAreaField(
        label=_('Contact'),
        description=_('The address and phone number of the municipality'),
        render_kw={'rows': 8},
        fieldset=_('Information'))

    contact_url = URLField(
        label=_('Contact Link'),
        description=_('URL pointing to a contact page'),
        fieldset=_('Information'),
        render_kw={'class_': 'internal-url'},
        validators=[Optional()]
    )

    opening_hours = TextAreaField(
        label=_('Opening Hours'),
        description=_('The opening hours of the municipality'),
        render_kw={'rows': 8},
        fieldset=_('Information'))

    opening_hours_url = URLField(
        label=_('Opening Hours Link'),
        description=_('URL pointing to an opening hours page'),
        fieldset=_('Information'),
        render_kw={'class_': 'internal-url'},
        validators=[Optional()]
    )

    hide_onegov_footer = BooleanField(
        label=_('Hide OneGov Cloud information'),
        description=_(
            'This includes the link to the marketing page, and the link '
            'to the privacy policy.'
        ),
        fieldset=_('Information')
    )

    facebook_url = URLField(
        label=_('Facebook'),
        description=_('URL pointing to the Facebook site'),
        fieldset=_('Social Media'),
        validators=[Optional()]
    )

    twitter_url = URLField(
        label=_('Twitter'),
        description=_('URL pointing to the Twitter site'),
        fieldset=_('Social Media'),
        validators=[Optional()]
    )

    youtube_url = URLField(
        label=_('YouTube'),
        description=_('URL pointing to the YouTube site'),
        fieldset=_('Social Media'),
        validators=[Optional()]
    )

    instagram_url = URLField(
        label=_('Instagram'),
        description=_('URL pointing to the Instagram site'),
        fieldset=_('Social Media'),
        validators=[Optional()]
    )

    linkedin_url = URLField(
        label=_('Linkedin'),
        description=_('URL pointing to the LinkedIn site'),
        fieldset=_('Social Media'),
        validators=[Optional()]
    )

    tiktok_url = URLField(
        label=_('TikTok'),
        description=_('URL pointing to the TikTok site'),
        fieldset=_('Social Media'),
        validators=[Optional()]
    )

    custom_link_1_name = StringField(
        label=_('Name'),
        description='Name of the Label',
        fieldset=_('Custom Link 1')
    )

    custom_link_1_url = URLField(
        label=_('URL'),
        description=_('URL to internal/external site'),
        fieldset=_('Custom Link 1'),
        validators=[Optional()]
    )

    custom_link_2_name = StringField(
        label=_('Name'),
        description='Name of the Label',
        fieldset=_('Custom Link 2')
    )

    custom_link_2_url = URLField(
        label=_('URL'),
        description=_('URL to internal/external site'),
        fieldset=_('Custom Link 2'),
        validators=[Optional()]
    )

    custom_link_3_name = StringField(
        label=_('Name'),
        description='Name of the Label',
        fieldset=_('Custom Link 3')
    )

    custom_link_3_url = URLField(
        label=_('URL'),
        description=_('URL to internal/external site'),
        fieldset=_('Custom Link 3'),
        validators=[Optional()]
    )

    partner_1_name = StringField(
        label=_('Name'),
        description=_('Name of the partner'),
        fieldset=_('First Partner'))

    partner_1_img = StringField(
        label=_('Image'),
        description=_('Logo of the partner'),
        render_kw={'class_': 'image-url'},
        fieldset=_('First Partner'))

    partner_1_url = URLField(
        label=_('Website'),
        description=_("The partner's website"),
        fieldset=_('First Partner'),
        validators=[Optional()]
    )

    partner_2_name = StringField(
        label=_('Name'),
        description=_('Name of the partner'),
        fieldset=_('Second Partner'))

    partner_2_img = StringField(
        label=_('Image'),
        description=_('Logo of the partner'),
        render_kw={'class_': 'image-url'},
        fieldset=_('Second Partner'))

    partner_2_url = URLField(
        label=_('Website'),
        description=_("The partner's website"),
        fieldset=_('Second Partner'),
        validators=[Optional()]
    )

    partner_3_name = StringField(
        label=_('Name'),
        description=_('Name of the partner'),
        fieldset=_('Third Partner'))

    partner_3_img = StringField(
        label=_('Image'),
        description=_('Logo of the partner'),
        render_kw={'class_': 'image-url'},
        fieldset=_('Third Partner'))

    partner_3_url = URLField(
        label=_('Website'),
        description=_("The partner's website"),
        fieldset=_('Third Partner'),
        validators=[Optional()]
    )

    partner_4_name = StringField(
        label=_('Name'),
        description=_('Name of the partner'),
        fieldset=_('Fourth Partner'))

    partner_4_img = StringField(
        label=_('Image'),
        description=_('Logo of the partner'),
        render_kw={'class_': 'image-url'},
        fieldset=_('Fourth Partner'))

    partner_4_url = URLField(
        label=_('Website'),
        description=_("The partner's website"),
        fieldset=_('Fourth Partner'),
        validators=[Optional()]
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
                    _('The sum of all the footer columns must be equal to 12')
                )
            return False
        return None


class SocialMediaSettingsForm(Form):
    og_logo_default = StringField(
        label=_('Image'),
        description=_('Default social media preview image for rich link '
                      'previews. Optimal size is 1200:630 px.'),
        fieldset='OpenGraph',
        render_kw={'class_': 'image-url'}
    )


class FaviconSettingsForm(Form):

    favicon_win_url = StringField(
        label=_('Icon 16x16 PNG (Windows)'),
        description=_('URL pointing to the icon'),
        render_kw={'class_': 'image-url'},
    )

    favicon_mac_url = StringField(
        label=_('Icon 32x32 PNG (Mac)'),
        description=_('URL pointing to the icon'),
        render_kw={'class_': 'image-url'},
    )

    favicon_apple_touch_url = StringField(
        label=_('Icon 57x57 PNG (iPhone, iPod, iPad)'),
        description=_('URL pointing to the icon'),
        render_kw={'class_': 'image-url'},
    )

    favicon_pinned_tab_safari_url = StringField(
        label=_('Icon SVG 20x20 (Safari)'),
        description=_('URL pointing to the icon'),
        render_kw={'class_': 'image-url'},
    )


class LinksSettingsForm(Form):
    disable_page_refs = BooleanField(
        label=_('Disable page references'),
        description=_(
            "Disable showing the copy link '#' for the site reference. "
            "The references themselves will still work. "
            "Those references are only showed for logged in users.")
    )

    open_files_target_blank = BooleanField(
        label=_('Open files in separate window')
    )


class HeaderSettingsForm(Form):

    announcement = StringField(
        label=_('Announcement'),
        fieldset=_('Announcement'),
    )

    announcement_url = StringField(
        label=_('Announcement URL'),
        fieldset=_('Announcement'),
    )

    announcement_bg_color = ColorField(
        label=_('Announcement bg color'),
        fieldset=_('Announcement')
    )

    announcement_font_color = ColorField(
        label=_('Announcement font color'),
        fieldset=_('Announcement')
    )

    announcement_is_private = BooleanField(
        label=_('Only show Announcement for logged-in users'),
        fieldset=_('Announcement')
    )

    header_links = StringField(
        label=_('Header links'),
        fieldset=_('Header links'),
        render_kw={'class_': 'many many-links'}
    )

    left_header_name = StringField(
        label=_('Text'),
        description=_(''),
        fieldset=_('Text header left side')
    )

    left_header_url = URLField(
        label=_('URL'),
        description=_('Optional'),
        fieldset=_('Text header left side'),
        validators=[Optional()]
    )

    left_header_color = ColorField(
        label=_('Font color'),
        fieldset=_('Text header left side')
    )

    left_header_rem = FloatField(
        label=_('Relative font size'),
        fieldset=_('Text header left side'),
        validators=[
            NumberRange(0.5, 7)
        ],
        default=1
    )

    header_additions_fixed = BooleanField(
        label=_(
            'Keep header links and/or header text fixed to top on scrolling'),
        fieldset=_('Header fixation')
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

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)
        model.header_options = self.header_options

    def process_obj(self, model: Organisation) -> None:  # type:ignore
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

        if not text:
            return []

        return [
            (value['text'], link)
            for value in json.loads(text).get('values', [])
            if (link := value['link']) or value['text']
        ]

    def links_to_json(
        self,
        header_links: Sequence[tuple[str | None, str | None]] | None = None
    ) -> str:
        header_links = header_links or []

        return json.dumps({
            'labels': {
                'text': self.request.translate(_('Text')),
                'link': self.request.translate(_('URL')),
                'add': self.request.translate(_('Add')),
                'remove': self.request.translate(_('Remove')),
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
        label=_('Homepage Cover'),
        render_kw={'rows': 10})

    homepage_structure = TextAreaField(
        fieldset=_('Structure'),
        label=_('Homepage Structure (for advanced users only)'),
        description=_('The structure of the homepage'),
        render_kw={'rows': 32, 'data-editor': 'xml'})

    # see homepage.py
    redirect_homepage_to = RadioField(
        label=_('Homepage redirect'),
        default='no',
        choices=[
            ('no', _('No')),
            ('directories', _('Yes, to directories')),
            ('events', _('Yes, to events')),
            ('forms', _('Yes, to forms')),
            ('publications', _('Yes, to publications')),
            ('reservations', _('Yes, to reservations')),
            ('path', _('Yes, to a non-listed path')),
        ])

    redirect_path = StringField(
        label=_('Path'),
        validators=[InputRequired()],
        depends_on=('redirect_homepage_to', 'path'))

    def validate_redirect_path(self, field: StringField) -> None:
        if not field.data:
            return

        url = URL(field.data)

        if url.scheme() or url.host():
            raise ValidationError(
                _('Please enter a path without schema or host'))

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
        label=_('The default map view. This should show the whole town'),
        render_kw={
            'data-map-type': 'crosshair'
        })

    geo_provider = RadioField(
        label=_('Geo provider'),
        default='geo-mapbox',
        choices=[
            ('geo-admin', _('Swisstopo (Default)')),
            ('geo-admin-aerial', _('Swisstopo Aerial')),
            ('geo-mapbox', 'Mapbox'),
            ('geo-vermessungsamt-winterthur', 'Vermessungsamt Winterthur'),
            ('geo-zugmap-basisplan', 'ZugMap Basisplan Farbig'),
            ('geo-zugmap-orthofoto', 'ZugMap Orthofoto'),
            ('geo-bs', 'Geoportal Basel-Stadt'),
        ])


class AnalyticsSettingsForm(Form):

    analytics_code = MarkupField(
        label=_('Analytics Code'),
        description=_('JavaScript for web statistics support'),
        render_kw={'rows': 10, 'data-editor': 'html'})

    # Points the user to the analytics url e.g. matomo or plausible
    analytics_url = URLPanelField(
        label=_('Analytics URL'),
        description=_('URL pointing to the analytics page'),
        render_kw={'readonly': True},
        validators=[Optional()],
        text='',
        kind='panel',
        hide_label=False
    )

    def derive_analytics_url(self) -> str:
        analytics_code = self.analytics_code.data or ''

        if 'analytics.seantis.ch' in analytics_code:
            data_domain = analytics_code.split(
                'data-domain="', 1)[1].split('"', 1)[0]
            return f'https://analytics.seantis.ch/{data_domain}'
        elif 'matomo' in analytics_code:
            return 'https://stats.seantis.ch'
        else:
            return ''

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        super().process_obj(model)
        self.analytics_url.text = self.derive_analytics_url()


class HolidaySettingsForm(Form):

    cantonal_holidays = MultiCheckboxField(
        label=_('Cantonal holidays'),
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
        label=_('Other holidays'),
        description=('31.10 - Halloween'),
        render_kw={'rows': 10})

    preview = PreviewField(
        label=_('Preview'),
        fields=('cantonal_holidays', 'other_holidays'),
        events=('change', 'click', 'enter'),
        url=lambda meta: meta.request.link(
            meta.request.app.org,
            name='holiday-settings-preview'
        ))

    school_holidays = TextAreaField(
        label=_('School holidays'),
        description=('12.03.2022 - 21.03.2022'),
        render_kw={'rows': 10})

    def validate_other_holidays(self, field: TextAreaField) -> None:
        if not field.data:
            return

        for line in field.data.splitlines():

            if not line.strip():
                continue

            if line.count('-') < 1:
                raise ValidationError(_('Format: Day.Month - Description'))
            if line.count('-') > 1:
                raise ValidationError(_('Please enter one date per line'))

            date, _description = line.split('-', 1)

            if date.count('.') < 1:
                raise ValidationError(_('Format: Day.Month - Description'))
            if date.count('.') > 1:
                raise ValidationError(_('Please enter only day and month'))

    def parse_date(self, date: str) -> datetime.date:
        day, month, year = date.split('.', 2)
        try:
            return datetime.date(int(year), int(month), int(day))
        except (ValueError, TypeError) as exception:
            raise ValidationError(_(
                '${date} is not a valid date',
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
                    _('Format: Day.Month.Year - Day.Month.Year')
                )
            if line.count('-') > 1:
                raise ValidationError(_('Please enter one date pair per line'))

            start, end = line.split('-', 1)
            if start.count('.') != 2:
                raise ValidationError(
                    _('Format: Day.Month.Year - Day.Month.Year')
                )
            if end.count('.') != 2:
                raise ValidationError(
                    _('Format: Day.Month.Year - Day.Month.Year')
                )

            start_date = self.parse_date(start)
            end_date = self.parse_date(end)
            if end_date <= start_date:
                raise ValidationError(
                    _('End date needs to be after start date')
                )

    # FIXME: Use TypedDict?
    @property
    def holiday_settings(self) -> dict[str, Any]:

        def parse_other_holidays_line(line: str) -> tuple[int, int, str]:
            date, desc = line.strip().split('-', 1)
            day, month = date.split('.')

            return int(month), int(day), desc.strip()

        def parse_school_holidays_line(
            line: str
        ) -> tuple[int, int, int, int, int, int]:

            start, end = line.strip().split('-', 1)
            start_day, start_month, start_year = start.split('.', 2)
            end_day, end_month, end_year = end.split('.', 2)

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

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        model.holiday_settings = self.holiday_settings

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        self.holiday_settings = model.holiday_settings


class OrgTicketSettingsForm(Form):

    hide_personal_email = BooleanField(
        label=_('Hide personal email addresses'),
        description=_('Hide personal email addresses in the ticket system'),
        fieldset=_('General')
    )

    general_email = EmailField(
        label=_('General email address'),
        description=_('Email address that is displayed instead of the '
                      'personal email address'),
        depends_on=('hide_personal_email', 'y'),
        validators=[InputRequired()],
        fieldset=_('General')
    )

    ticket_auto_accept_style = RadioField(
        label=_('Accept request and close ticket automatically based on:'),
        choices=(
            ('category', _('Ticket category')),
            ('role', _('User role')),
        ),
        fieldset=_('Auto-accept and auto-close'),
        default='category'
    )

    ticket_auto_accepts = MultiCheckboxField(
        label=_('Accept request and close ticket automatically '
                'for these ticket categories'),
        description=_("If auto-accepting is not possible, the ticket will be "
                      "in state pending. Also note, that after the ticket is "
                      "closed, the submitter can't send any messages."),
        choices=[],
        fieldset=_('Auto-accept and auto-close'),
        depends_on=('ticket_auto_accept_style', 'category')
    )

    ticket_auto_accept_roles = MultiCheckboxField(
        label=_('Accept request and close ticket automatically '
                'for these user roles'),
        description=_("If auto-accepting is not possible, the ticket will be "
                      "in state pending. Also note, that after the ticket is "
                      "closed, the submitter can't send any messages."),
        choices=AVAILABLE_ROLES,
        fieldset=_('Auto-accept and auto-close'),
        depends_on=('ticket_auto_accept_style', 'role')
    )

    auto_closing_user = ChosenSelectField(
        label=_('User used to auto-accept tickets'),
        choices=[],
        fieldset=_('Auto-accept and auto-close'),
    )

    email_for_new_tickets = StringField(
        label=_('Email address for notifications '
                'about newly opened tickets'),
        fieldset=_('Notifications'),
        description=('info@example.ch')
    )

    tickets_skip_opening_email = MultiCheckboxField(
        label=_('Block email confirmation when '
                'this ticket category is opened'),
        choices=[],
        description=_('This is enabled by default for tickets that get '
                      'accepted automatically'),
        fieldset=_('Notifications'),
    )

    tickets_skip_closing_email = MultiCheckboxField(
        label=_('Block email confirmation when '
                'this ticket category is closed'),
        choices=[],
        description=_('This is enabled by default for tickets that get '
                      'accepted automatically'),
        fieldset=_('Notifications'),
    )

    mute_all_tickets = BooleanField(
        label=_('Mute all tickets'),
        fieldset=_('Notifications'),

    )

    ticket_always_notify = BooleanField(
        label=_('Always send email notification '
                'if a new ticket message is sent'),
        default=True,
        fieldset=_('Notifications'),
    )

    ticket_tags = TextAreaField(
        label=_('Tags'),
        description=_(
            'Each tag can be associated with arbitrary key value pairs '
            'which will be displayed in the ticket alongside the submitted '
            'form values. If a key exactly matches the name of a form field '
            "that field's value will be pre-populated according to the value."
            '\n\nExample:\n'
            '```yaml\n'
            '- High Priority\n'
            '- Medium Priority\n'
            '- Low Priority\n'
            '- FC Govikon:\n'
            '    E-Mail: fc@govikon.ch\n'
            '    Postal Code / City: 1234 Govikon\n'
            '- HC Govikon:\n'
            '    E-Mail: hc@govikon.ch\n'
            '    Postal Code / City: 1234 Govikon\n'
            '```'
        ),
        render_kw={
            'rows': 16,
        },
    )

    permissions = MultiCheckboxField(
        label=_('Categories restricted by user group settings'),
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
                _('Mute tickets individually if the auto-accept feature is '
                  'enabled.')
            )
            return False
        return None

    def ensure_valid_ticket_tags(self) -> bool | None:
        assert isinstance(self.ticket_tags.errors, list)

        if not self.ticket_tags.data:
            return None

        error_msg = _('Invalid format. Please define tags and '
                      'their meta data according to the example.')

        try:
            items = yaml.safe_load(self.ticket_tags.data)
        except yaml.YAMLError:
            self.ticket_tags.errors.append(error_msg)
            return False

        if not items:
            return None

        if not isinstance(items, list):
            self.ticket_tags.errors.append(error_msg)
            return False

        for item in items:

            if isinstance(item, str) and item:
                continue

            if not isinstance(item, dict) or len(item) != 1:
                self.ticket_tags.errors.append(error_msg)
                return False

            for tag, meta in item.items():
                # we only allow string tags
                if not isinstance(tag, str):
                    self.ticket_tags.errors.append(error_msg)
                    return False

                # we allow tags without meta data
                if not meta:
                    continue

                # the meta data needs to be a valid mapping
                if not isinstance(meta, dict) or any(
                    True
                    for field, value in meta.items()
                    # we only allow string keys
                    if not isinstance(field, str)
                    # we allow any value type except for containers
                    or isinstance(value, (dict, list))
                ):
                    self.ticket_tags.errors.append(error_msg)
                    return False

                if 'Price' in meta or 'Preis' in meta:
                    price = meta.get('Price', meta.get('Preis'))
                    try:
                        assert price and Decimal(price) >= Decimal('0')
                    except Exception:
                        self.ticket_tags.errors.append(_(
                            'Invalid price "${price}", needs to be a '
                            'non-negative number.',
                            mapping={'price': price}
                        ))
                        return False

                if 'Color' in meta:
                    raw_color = meta['Color']
                    if isinstance(raw_color, str):
                        color = raw_color.strip()
                    elif isinstance(raw_color, int):
                        color = str(raw_color)
                        # leading zeroes can be interpreted as octal
                        # so we need to convert it back to its orginal
                        # representation
                        if color not in self.ticket_tags.data:
                            color = f'{raw_color:o}'
                        if len(color) < 6:
                            # try to restore any leading zeroes YAML stripped
                            for __ in range(6 - len(color)):
                                prefixed = f'0{color}'
                                if prefixed in self.ticket_tags.data:
                                    color = prefixed
                                else:
                                    break
                    else:
                        color = str(raw_color).strip()

                    if COLOR_RE.match(color):
                        # Store normalized color
                        meta['Color'] = '#' + color.removeprefix('#')
                    else:
                        self.ticket_tags.errors.append(_(
                            'Invalid color "${color}", needs to be a 3 or 6 '
                            'digit hex code, e.g. "ff9000" for orange. '
                            'If you use a "#" prefix, make sure to enclose '
                            'the value in quotation marks.',
                            mapping={'color': color or ''}
                        ))
                        return False

                if 'Kaba Code' in meta:
                    raw_code = meta['Kaba Code']
                    if isinstance(raw_code, str):
                        code = raw_code
                    elif isinstance(raw_code, int):
                        code = str(raw_code)
                        # leading zeroes can be interpreted as octal
                        # so we need to convert it back to its orginal
                        # representation
                        if code not in self.ticket_tags.data:
                            code = f'{raw_code:o}'
                        if len(code) < 6:
                            # try to restore any leading zeroes YAML stripped
                            for __ in range(6 - len(code)):
                                prefixed = f'0{code}'
                                if prefixed in self.ticket_tags.data:
                                    code = prefixed
                                else:
                                    break
                    else:
                        code = str(raw_code)

                    if not KABA_CODE_RE.match(code):
                        self.ticket_tags.errors.append(_(
                            'Invalid Kaba Code. '
                            'Needs to be a 4 to 6 digit number code.'
                        ))
                        return False

                    # Store normalized Kaba code
                    meta['Kaba Code'] = code

        self.ticket_tags.parsed_data = items  # type: ignore[attr-defined]

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
            for p in self.request.session.query(
                TicketPermission.id,
                TicketPermission.handler_code,
                TicketPermission.group
            ).filter(TicketPermission.exclusive.is_(True))
        ), key=itemgetter(1))

        if not permissions:
            self.delete_field('permissions')
        else:
            self.permissions.choices = permissions
            self.permissions.default = [p[0] for p in permissions]

        user_q = self.request.session.query(User).filter_by(role='admin')
        user_q = user_q.order_by(User.created.desc())
        self.auto_closing_user.choices = [
            (u.username, u.title) for u in user_q
        ]

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model, exclude={'ticket_tags'})

        if hasattr(self.ticket_tags, 'parsed_data'):
            data = self.ticket_tags.parsed_data
        else:
            yaml_data = self.ticket_tags.data
            data = yaml.safe_load(yaml_data) if yaml_data else []

        model.ticket_tags = data

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        super().process_obj(model)

        tags = model.ticket_tags
        if not tags:
            self.ticket_tags.data = ''
            return

        yaml_data = yaml.safe_dump(
            tags,
            default_flow_style=False,
            allow_unicode=True
        )
        self.ticket_tags.data = yaml_data


class NewsletterSettingsForm(Form):

    show_newsletter = BooleanField(
        label=_('Enable newsletter'),
        default=False
    )

    secret_content_allowed = BooleanField(
        label=_('Allow secret content in newsletter'),
        default=False
    )

    newsletter_categories = TextAreaField(
        label=_('Newsletter categories'),
        description=_(
            'Example for newsletter topics with subtopics in yaml format. '
            'Note: Deeper structures are not supported.\n'
            '```\n'
            '- Topic 1\n'
            '- Topic 2:\n'
            '  - Subtopic 2.1\n'
            '- Topic 3:\n'
            '  - Subtopic 3.1\n'
            '  - Subtopic 3.2\n'
            '```'
        ),
        render_kw={
            'rows': 16,
        },
    )

    notify_on_unsubscription = ChosenSelectMultipleEmailField(
        label=_('Notify on newsletter unsubscription'),
        description=_('Send an email notification to the following users '
                      'when a recipient unsubscribes from the newsletter'),
        validators=[StrictOptional()],
        choices=[]
    )

    enable_automatic_newsletters = BooleanField(
        label=_('Enable automatic daily newsletters'),
        description=_('Automatically creates a daily newsletter containing '
        'all new news items since the last sending time. It will only send a '
        'newsletter if there is at least one new news item. Only subscribers '
        'who subscribed to the daily newsletter will receive it, independent '
        'of their selected categories if there are any.'),
        fieldset=_('Automatic newsletters'),
        default=False
    )

    newsletter_times = TagsField(
        label=_('Newsletter sending times (24h format)'),
        fieldset=_('Automatic newsletters'),
        validators=[InputRequired()],
        description=_(
            'Specify times for sending newsletters. e.g., 8, 12, 18.'
            ),
        depends_on=('enable_automatic_newsletters', 'y'),
    )

    def ensure_categories(self) -> bool | None:
        assert isinstance(self.newsletter_categories.errors, list)

        if self.newsletter_categories.data:
            try:
                data = yaml.safe_load(self.newsletter_categories.data)
            except yaml.YAMLError:
                self.newsletter_categories.errors.append(
                    _('Invalid YAML format. Please refer to the example.')
                )
                return False

            if data:
                if not isinstance(data, list):
                    self.newsletter_categories.errors.append(
                        _('Invalid format. Please define topics and '
                          'subtopics according to the example.')
                    )
                    return False
                for item in data:
                    if not isinstance(item, (str, dict)):
                        self.newsletter_categories.errors.append(
                            _('Invalid format. Please define topics and '
                              'subtopics according to the example.')
                        )
                        return False

                    if isinstance(item, str):
                        continue

                    for topic, sub_topic in item.items():
                        if not isinstance(sub_topic, list):
                            self.newsletter_categories.errors.append(
                                _(f'Invalid format. Please define '
                                  f"subtopic(s) for '{topic}' "
                                  f"or remove the ':'.")
                            )
                            return False

                        if not all(isinstance(sub, str) for sub in sub_topic):
                            self.newsletter_categories.errors.append(
                                _('Invalid format. Only topics '
                                  'and subtopics are allowed - no '
                                  'deeper structures supported.')
                            )
                            return False

        return None

    def ensure_valid_times(self) -> bool | None:
        assert isinstance(self.newsletter_times.errors, list)

        if self.enable_automatic_newsletters.data:
            if not self.newsletter_times.data:
                self.newsletter_times.errors.append(
                    _('Please specify at least one time.')
                )
                return False

            for time in self.newsletter_times.data:
                try:
                    time_int = int(time)
                    if time_int < 0 or time_int > 24:
                        self.newsletter_times.errors.append(
                            _('Invalid time format. Please use a value '
                              'between 0 and 24.')
                        )
                        return False
                except ValueError:
                    self.newsletter_times.errors.append(
                        _('Invalid time format. Please use 24h format.')
                    )
                    return False

        return None

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)

        yaml_data = self.newsletter_categories.data
        data = yaml.safe_load(yaml_data) if yaml_data else []
        model.newsletter_categories = data
        if isinstance(self.newsletter_times.data, list):
            times = self.newsletter_times.data
            times.sort(key=int)
            model.newsletter_times = times

        model.notify_on_unsubscription = self.notify_on_unsubscription.data

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        super().process_obj(model)

        categories = model.newsletter_categories or []
        if not categories:
            self.newsletter_categories.data = ''
            return

        yaml_data = yaml.safe_dump(
            categories,
            default_flow_style=False,
            allow_unicode=True
        )
        self.newsletter_categories.data = yaml_data

        if model.notify_on_unsubscription:
            self.notify_on_unsubscription.data = model.notify_on_unsubscription

    def on_request(self) -> None:
        users = self.request.session.query(User).filter(
            User.role.in_(['admin', 'editor']))
        users = users.order_by(User.username.desc())
        self.notify_on_unsubscription.choices = [
            (u.username) for u in users if '@' in u.username
        ]


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


def validate_https(form: Form, field: Field) -> None:
    if not field.data.startswith('https'):
        raise ValidationError(_("Link must start with 'https'"))


class GeverSettingsForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    gever_username = StringField(
        _('Username'),
        [InputRequired()],
        description=_('Username for the associated Gever account'),
    )

    gever_password = PasswordField(
        _('Password'),
        [InputRequired()],
        description=_('Password for the associated Gever account'),
    )

    gever_endpoint = URLField(
        _('Gever API Endpoint where the documents are uploaded.'),
        [InputRequired(), URLValidator(), validate_https],
        description=_('Website address including https://'),
    )

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)
        try:
            assert self.gever_password.data is not None
            encrypted = self.request.app.encrypt(self.gever_password.data)
            encrypted_str = encrypted.decode('utf-8')
            model.gever_username = self.gever_username.data or ''
            model.gever_password = encrypted_str or ''
        except Exception:
            model.gever_username = ''
            model.gever_password = ''  # nosec: B105

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        super().process_obj(model)

        self.gever_username.data = model.gever_username or ''
        self.gever_password.data = model.gever_password or ''


class KabaConfigurationForm(Form):

    site_id = StringField(
        label=_('Site ID'),
    )

    api_key = StringField(
        label='API_KEY',
        depends_on=('site_id', '!'),
    )

    api_secret = PasswordField(
        label='API_SECRET',
        depends_on=('site_id', '!'),
    )


if TYPE_CHECKING:
    FieldBase = FieldList[FormField[KabaConfigurationForm]]
else:
    FieldBase = FieldList


class KabaConfigurationsField(FieldBase):
    def process(
        self,
        formdata: _MultiDictLikeWithGetlist | None,
        data: Any = unset_value,
        extra_filters: Sequence[_Filter] | None = None
    ) -> None:

        # FIXME: I'm not quite sure why we need to do this
        #        but it looks like the last_index gets updated
        #        to 0 by something, so we start counting at 1
        #        instead of 0, which breaks the field
        self.last_index = -1
        super().process(formdata, data, extra_filters)

        # always have an empty extra entry
        if formdata is None and self[-1].form.site_id.data is not None:
            self.append_entry()

    def populate_obj(self, obj: object, name: str) -> None:
        assert name == 'kaba_configurations'
        assert hasattr(obj, 'meta')

        previous_secrets = {
            config['site_id']: config['api_secret']
            for config in obj.meta.get('kaba_configurations', [])
        }
        obj.meta['kaba_configurations'] = [
            {
                'site_id': site_id,
                'api_key': item['api_key'],
                # if we already submitted this then just use the existing
                # key, unless we specified a new one
                'api_secret':
                    self.meta.request.app.encrypt(item['api_secret']).hex()
                    if item['api_secret'] else previous_secrets[site_id]
            }
            for item in self.data
            # skip de-selected entries
            if (site_id := item['site_id'])
        ]


def kaba_configurations_widget(field: FieldBase, **kwargs: Any) -> Markup:
    field.meta.request.include('kaba-configurations')
    return Markup('').join(
        Markup(
            '<label><b>{}.</b></label>'
            '<div id="{}" style="margin-left:1.55rem">{}</div>'
        ).format(idx, f.id, f())
        for idx, f in enumerate(field, start=1)
    )


class KabaSettingsForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    kaba_configurations = KabaConfigurationsField(
        FormField(
            KabaConfigurationForm,
            widget=lambda field, **kw: Markup('').join(
                Markup('<div><label>{}</label></div>').format(render_macro(
                    field.meta.request.template_loader.macros['field'],
                    field.meta.request,
                    {
                        'field': f,
                        # FIXME: only used for rendering descriptions
                        #        we should probably move this logic
                        #        into a template macro or a method on
                        #        CoreRequest, this doesn't really need
                        #        to be part of Form, we could also move
                        #        it to the form meta and access it
                        #        through the field instead
                        'form': field.meta.request.get_form(
                            Form, csrf_support=False
                        )
                    }
                )) for f in field
            )
        ),
        label=_('Kaba Sites'),
        min_entries=1,
        widget=kaba_configurations_widget
    )

    default_key_code_lead_time = IntegerField(
        label=_('Default Lead Time'),
        validators=[InputRequired(), NumberRange(0, 1440)],
        render_kw={
            'step': 5,
            'long_description': _('In minutes'),
        },
    )

    default_key_code_lag_time = IntegerField(
        label=_('Default Lag Time'),
        validators=[InputRequired(), NumberRange(0, 1440)],
        render_kw={
            'step': 5,
            'long_description': _('In minutes'),
        },
    )

    def on_request(self) -> None:
        # NOTE: Ensures translations work in FormField
        for field in self.kaba_configurations:
            field.form.meta = self.meta
            for subfield in field.form:
                subfield.meta = self.meta

    def ensure_valid_configurations(self) -> bool | None:
        seen: set[str] = set()
        for field in self.kaba_configurations:
            site_id = field.form.site_id.data
            if not site_id:
                continue

            if site_id in seen:
                assert isinstance(self.kaba_configurations.errors, list)
                self.kaba_configurations.errors.append(_(
                    'Duplicate site ID ${site_id}',
                    mapping={'site_id': site_id}
                ))
                return False

            seen.add(site_id)

            if not field.form.api_key.data:
                assert isinstance(self.kaba_configurations.errors, list)
                self.kaba_configurations.errors.append(
                    self.kaba_configurations.gettext(_(
                        '${field} for site ID ${site_id} is required',
                        mapping={
                            'field': 'API_KEY',
                            'site_id': field.form.site_id.data
                        }
                    ))
                )
                return False

            if field.form.api_secret.data:
                api_secret = field.form.api_secret.data
            elif (cfg := self.model.get_kaba_configuration(site_id)) is None:
                assert isinstance(self.kaba_configurations.errors, list)
                self.kaba_configurations.errors.append(
                    self.kaba_configurations.gettext(_(
                        '${field} for site ID ${site_id} is required',
                        mapping={
                            'field': 'API_SECRET',
                            'site_id': field.form.site_id.data
                        }
                    ))
                )
                return False
            elif cfg.api_key == field.form.api_key.data:
                # no need to re-validate
                return None
            else:
                # decrypt existing API secret
                api_secret = self.request.app.decrypt(
                    bytes.fromhex(cfg.api_secret)
                )

            api_key = field.form.api_key.data
            assert site_id is not None and api_key is not None

            client = KabaClient(site_id, api_key, api_secret)
            try:
                client.site_name()
            except KabaApiError:
                assert isinstance(self.kaba_configurations.errors, list)
                error = _(
                    'Invalid credentials for site ID ${site_id}',
                    mapping={'site_id': site_id}
                )
                self.kaba_configurations.errors.append(error)
                return False
            except Exception:
                self.request.alert(
                    _('Unexpected error encountered, please try again.')
                )
                log.exception('Unexpected error connecting to Kaba')
                return False
        return True


class OneGovApiSettingsForm(Form):
    """Provides a form to generate API keys (UUID'S) for the OneGov API."""

    name = StringField(
        label=_('Name'),
        default=_('API Key'),
        validators=[InputRequired()],
    )

    read_only = BooleanField(
        label=_('Read only'),
        default=True,
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

    event_locations = TagsField(
        label=_('Values of the location filter'),
    )

    event_filter_type = RadioField(
        label=_("Choose the filter type for events (default is 'Tags')"),
        choices=(
            ('tags', _('A predefined set of tags')),
            ('filters', _('Manually configurable filters')),
            ('tags_and_filters', _('Both, predefined tags as well as '
                                   'configurable filters')),
        ),
        default='tags'
    )

    event_header_html = HtmlField(
        label=_('General information above the event list'),

    )

    event_footer_html = HtmlField(
        label=_('General information below the event list'),
    )

    event_files = UploadOrSelectExistingMultipleFilesField(
        label=_('Documents'),
        fieldset=_('General event documents')
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


class FirebaseSettingsForm(Form):
    """Allows to setup sending firebase notifications for News with
    hashtags. Used with PublicationFormExtension .

    """

    if TYPE_CHECKING:
        request: OrgRequest

    firebase_adminsdk_credential = TextAreaField(
        _('Firebase adminsdk credentials (JSON)'),
        [Optional()],
        render_kw={
            'rows': 32,
            'data-editor': 'json'
        },
    )

    selectable_push_notification_options = StringField(
        label=_('Topics'),
        fieldset=_('Defines the firebase topic id'),
        render_kw={
            'class_': 'many many-firebasetopics',
        },
    )

    if TYPE_CHECKING:
        hashtag_errors: dict[int, str]
    else:

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.hashtag_errors = {}

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)
        try:
            assert self.firebase_adminsdk_credential.data is not None
            encrypted = self.request.app.encrypt(
                self.firebase_adminsdk_credential.data
            )
            encrypted_str = encrypted.decode('utf-8')
            model.firebase_adminsdk_credential = encrypted_str or ''
        except Exception:
            model.firebase_adminsdk_credential = ''  # nosec: B105

        # Save selectable_push_notification_options to the model
        model.selectable_push_notification_options = (
            self.json_to_links(self.selectable_push_notification_options.data)
            or []
        )

    def validate_firebase_adminsdk_credential(
        self, field: TextAreaField
    ) -> None:
        expected_keys = {
            'auth_provider_x509_cert_url',
            'auth_uri',
            'client_email',
            'client_id',
            'client_x509_cert_url',
            'private_key',
            'private_key_id',
            'project_id',
            'token_uri',
            'type',
            'universe_domain',
        }
        # Basic sanity checks on the json
        try:
            data = json.loads(field.data)  # type:ignore[arg-type]
            if not isinstance(data, dict):
                raise ValidationError(
                    _(
                        'Invalid Firebase credentials format '
                        '- must be a JSON object'
                    )
                )
            missing_keys = [key for key in expected_keys if key not in data]
            if missing_keys:
                error_message = _(
                    'Missing required keys in Firebase credentials: {0}'
                ).format(', '.join(missing_keys))
                raise ValidationError(error_message)
        except json.JSONDecodeError as err:
            raise ValidationError(
                _('Invalid JSON format in Firebase credentials')
            ) from err
        except Exception as e:
            raise ValidationError(
                _('Error validating Firebase credentials: {0}').format(str(e))
            ) from e

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        super().process_obj(model)

        if model.firebase_adminsdk_credential:
            try:
                self.firebase_adminsdk_credential.data = (
                    self.request.app.decrypt(
                        model.firebase_adminsdk_credential.encode('utf-8')
                    )
                )
            except InvalidToken:
                self.firebase_adminsdk_credential.data = ''

        if (
            not hasattr(model, 'selectable_push_notification_options')
            or not model.selectable_push_notification_options
        ):
            self.selectable_push_notification_options.data = self.tags_to_json(
               []
            )
        else:
            self.selectable_push_notification_options.data = self.tags_to_json(
                model.selectable_push_notification_options
            )

    def on_request(self) -> None:
        # Initialize the field if it's empty
        if not self.selectable_push_notification_options.data:
            self.selectable_push_notification_options.data = (
                self.tags_to_json([])
            )

    def choices_for_news_specific_firebase_topics(self) -> list[list[str]]:
        from onegov.org.models import News
        session = self.request.session
        query = session.query(News.meta['hashtags'])
        hashtag_set = set()
        for (hashtags,) in query:
            hashtag_set.update(hashtags)
        all_hashtags = sorted(hashtag_set)

        # The first topic is just the schema, includes all News
        choices_for_topics = []
        for label in all_hashtags:
            normalized_hashtag = label.lower().replace(' ', '_')
            key = (
                self.request.app.schema + '_' + normalized_hashtag
            )
            pair = [key, label]
            choices_for_topics.append(pair)
        return choices_for_topics

    def json_to_links(
        self,
        text: str | None = None
    ) -> list[list[str]]:
        if not text:
            return []
        return [
            [value['text'], link]
            for value in json.loads(text).get('values', [])
            if (link := value['link']) or value['text']
        ]

    def tags_to_json(self, tags: list[list[str]]) -> str:
        if not tags:
            # set default topic News (which is all)
            app_id = self.request.app.schema
            topic_and_label_pairs = [[app_id, 'News']]
        else:
            topic_and_label_pairs = tags

            # Check if the default pair exists, if not add it
            app_id = self.request.app.schema
            if not any(pair[0] == app_id for pair in topic_and_label_pairs):
                topic_and_label_pairs.insert(
                    0, [app_id, 'News']
                )

        choices = self.choices_for_news_specific_firebase_topics()
        text_options = [value for value, __ in choices]
        link_options = [label for __, label in choices]

        return json.dumps(
            {
                'labels': {
                    'text': 'Key',
                    'link': 'Label',
                    'add': self.request.translate(_('Add')),
                    'remove': self.request.translate(_('Remove')),
                },
                'placeholders': {'text': 'Key', 'link': 'Label'},
                'textOptions': text_options,
                'linkOptions': link_options,
                'values': [
                    {
                        'text': l[0],
                        'link': l[1],
                        'error': self.hashtag_errors.get(ix, ''),
                    }
                    for ix, l in enumerate(topic_and_label_pairs)
                ],
            }
        )


class PeopleSettingsForm(Form):

    organisation_hierarchy = TextAreaField(
        label=_('Organisation hierarchy'),
        description=_(
            'Example for organisation hierarchy with subtopics in yaml '
            'format. Note: Deeper structures are not supported.'
            '\n'
            '```\n'
            '- Organisation 1:\n'
            '  - Sub-Organisation 1.1\n'
            '  - Sub-Organisation 1.2\n'
            '- Organisation 2\n'
            '- Organisation 3:\n'
            '  - Sub-Organisation 3.1\n'
            '```'
        ),
        render_kw={
            'rows': 16,
        },
    )

    hidden_people_fields = MultiCheckboxField(
        label=_('Hide these fields for non-logged-in users'),
        choices=[
            ('salutation', _('Salutation')),
            ('academic_title', _('Academic Title')),
            ('born', _('Born')),
            ('profession', _('Profession')),
            ('political_party', _('Political Party')),
            ('parliamentary_group', _('Parliamentary Group')),
            ('email', _('E-Mail')),
            ('phone', _('Phone')),
            ('phone_direct', _('Direct Phone Number or Mobile')),
            ('organisation', _('Organisation')),
            ('website', _('Website')),
            ('website_2', _('Website 2')),
            ('location_address', _('Location address')),
            ('location_code_city', _('Location Code and City')),
            ('postal_address', _('Postal address')),
            ('postal_code_city', _('Postal Code and City')),
            ('notes', _('Notes')),
            ('external_user_id', _('External ID'))
        ])

    def ensure_categories(self) -> bool | None:
        assert isinstance(self.organisation_hierarchy.errors, list)

        if self.organisation_hierarchy.data:
            try:
                data = yaml.safe_load(self.organisation_hierarchy.data)
            except yaml.YAMLError:
                self.organisation_hierarchy.errors.append(
                    _('Invalid YAML format. Please refer to the example.')
                )
                return False

            if data:
                if not isinstance(data, list):
                    self.organisation_hierarchy.errors.append(
                        _('Invalid format. Please define a list with '
                          'organisations and sub-organisations according the '
                          'example.')
                    )
                    return False
                for item in data:
                    if not isinstance(item, (str, dict)):
                        self.organisation_hierarchy.errors.append(
                            _('Invalid format. Please define organisations '
                              'and sub-organisations according to the '
                              'example.')
                        )
                        return False

                    if isinstance(item, str):
                        continue

                    for topic, sub_topic in item.items():
                        if not isinstance(sub_topic, list):
                            self.organisation_hierarchy.errors.append(
                                _('Invalid format. Please define at least '
                                  "one sub-organisation for '${topic}' "
                                  "or remove the ':'",
                                    mapping={'topic': topic}
                                )
                            )
                            return False

                        if not all(isinstance(sub, str) for sub in sub_topic):
                            self.organisation_hierarchy.errors.append(
                                _('Invalid format. Only organisations '
                                  'and sub-organisations are allowed - no '
                                  'deeper structures supported.')
                            )
                            return False

        return None

    def populate_obj(self, model: Organisation) -> None:  # type:ignore
        super().populate_obj(model)

        yaml_data = self.organisation_hierarchy.data
        data = yaml.safe_load(yaml_data) if yaml_data else []
        model.organisation_hierarchy = data

    def process_obj(self, model: Organisation) -> None:  # type:ignore
        super().process_obj(model)

        categories = model.organisation_hierarchy or []
        if not categories:
            self.organisation_hierarchy.data = ''
            return

        yaml_data = yaml.safe_dump(
            categories,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )
        self.organisation_hierarchy.data = yaml_data


class VATSettingsForm(Form):

    vat_rate = FloatField(
        label=_('VAT Rate'),
        description=_('This is the VAT rate in percent. The VAT rate will '
                      'apply to all prices in the forms.'),
        validators=[InputRequired(), NumberRange(0, 100)],
    )


class CitizenLoginSettingsForm(Form):

    citizen_login_enabled = BooleanField(
        label=_('Enable Citizen Login'),
        default=False,
    )
