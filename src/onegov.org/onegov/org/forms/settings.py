import re

from lxml import etree
from onegov.form import Form
from onegov.form import with_options
from onegov.form.fields import MultiCheckboxField, TagsField
from onegov.form.fields import PreviewField
from onegov.gis import CoordinatesField
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.homepage_widgets import transform_homepage_structure
from onegov.org.homepage_widgets import XML_LINE_OFFSET
from onegov.org.theme import user_options
from wtforms import StringField, TextAreaField, RadioField
from wtforms import ValidationError
from wtforms import validators
from wtforms.fields.html5 import EmailField, URLField
from wtforms_components import ColorField


ERROR_LINE_RE = re.compile(r'line ([0-9]+)')


class GeneralSettingsForm(Form):
    """ Defines the settings form for onegov org. """

    name = StringField(
        label=_("Name"),
        validators=[validators.InputRequired()])

    logo_url = StringField(
        label=_("Logo"),
        description=_("URL pointing to the logo"),
        render_kw={'class_': 'image-url'})

    square_logo_url = StringField(
        label=_("Logo (Square)"),
        description=_("URL pointing to the logo"),
        render_kw={'class_': 'image-url'})

    reply_to = EmailField(
        _("E-Mail Reply Address"), [validators.InputRequired()],
        description=_("Replies to automated e-mails go to this address."))

    primary_color = ColorField(
        label=_("Primary Color"))

    locales = RadioField(
        label=_("Languages"),
        choices=(
            ('de_CH', _("German")),
            ('fr_CH', _("French"))
        ),
        validators=[validators.InputRequired()])

    @property
    def theme_options(self):
        options = self.model.theme_options

        try:
            options['primary-color'] = self.primary_color.data.get_hex()
        except AttributeError:
            options['primary-color'] = user_options['primary-color']

        # override the options using the default values if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        return options

    @theme_options.setter
    def theme_options(self, options):
        self.primary_color.data = options.get('primary-color')

    def populate_obj(self, model):
        super().populate_obj(model)
        model.theme_options = self.theme_options

    def process_obj(self, model):
        super().process_obj(model)
        self.theme_options = model.theme_options

    def on_request(self):

        @self.request.after
        def clear_locale(response):
            response.delete_cookie('locale')


class FooterSettingsForm(Form):

    contact = TextAreaField(
        label=_("Contact"),
        description=_("The address and phone number of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("Information"))

    contact_url = URLField(
        label=_("Contact Link"),
        description=_("URL pointing to a contact page"),
        fieldset=_("Information"),
        render_kw={'class_': 'internal-url'})

    opening_hours = TextAreaField(
        label=_("Opening Hours"),
        description=_("The opening hours of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("Information"))

    opening_hours_url = URLField(
        label=_("Opening Hours Link"),
        description=_("URL pointing to an opening hours page"),
        fieldset=_("Information"),
        render_kw={'class_': 'internal-url'})

    facebook_url = URLField(
        label=_("Facebook"),
        description=_("URL pointing to the facebook site"),
        fieldset=_("Social Media"))

    twitter_url = URLField(
        label=_("Twitter"),
        description=_("URL pointing to the twitter site"),
        fieldset=_("Social Media"))

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
        fieldset=_("First Partner"))

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
        fieldset=_("Second Partner"))

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
        fieldset=_("Third Partner"))

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
        fieldset=_("Fourth Partner"))


class HomepageSettingsForm(Form):

    homepage_image_1 = StringField(
        label=_("Homepage Image #1"),
        render_kw={'class_': 'image-url'})

    homepage_image_2 = StringField(
        label=_("Homepage Image #2"),
        render_kw={'class_': 'image-url'})

    homepage_image_3 = StringField(
        label=_("Homepage Image #3"),
        render_kw={'class_': 'image-url'})

    homepage_image_4 = StringField(
        label=_("Homepage Image #4"),
        render_kw={'class_': 'image-url'})

    homepage_image_5 = StringField(
        label=_("Homepage Image #5"),
        render_kw={'class_': 'image-url'})

    homepage_image_6 = StringField(
        label=_("Homepage Image #6"),
        render_kw={'class_': 'image-url'})

    homepage_cover = HtmlField(
        label=_("Homepage Cover"),
        render_kw={'rows': 10})

    homepage_structure = TextAreaField(
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
        ])

    def validate_homepage_structure(self, field):
        if field.data:
            try:
                transform_homepage_structure(self.request.app, field.data)
            except etree.XMLSyntaxError as e:
                correct_line = e.position[0] - XML_LINE_OFFSET

                correct_msg = 'line {}'.format(correct_line)
                correct_msg = ERROR_LINE_RE.sub(correct_msg, e.msg)

                field.widget = with_options(
                    field.widget, **{'data-highlight-line': correct_line}
                )

                raise ValidationError(correct_msg)

    @property
    def theme_options(self):
        options = self.model.theme_options

        # set the images only if provided
        for i in range(1, 7):
            image = getattr(self, 'homepage_image_{}'.format(i)).data

            if not image:
                options.pop(f'tile-image-{i}', None)
            else:
                options[f'tile-image-{i}'] = '"{}"'.format(image)

        # override the options using the default values if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        return options

    @theme_options.setter
    def theme_options(self, options):
        self.homepage_image_1.data = options.get('tile-image-1', '').strip('"')
        self.homepage_image_2.data = options.get('tile-image-2', '').strip('"')
        self.homepage_image_3.data = options.get('tile-image-3', '').strip('"')
        self.homepage_image_4.data = options.get('tile-image-4', '').strip('"')
        self.homepage_image_5.data = options.get('tile-image-5', '').strip('"')
        self.homepage_image_6.data = options.get('tile-image-6', '').strip('"')

    def populate_obj(self, model):
        super().populate_obj(model)
        model.theme_options = self.theme_options

    def process_obj(self, model):
        super().process_obj(model)
        self.theme_options = model.theme_options


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
            ('phone_direct', _("Direct Phone Number")),
            ('website', _("Website")),
            ('address', _("Address")),
            ('notes', _("Notes")),
        ])

    event_locations = TagsField(
        label=_("Values of the location filter"),
        fieldset=_("Events"),)


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
            ('geo-mapbox', _("Mapbox (Default)")),
            ('geo-vermessungsamt-winterthur', "Vermessungsamt Winterthur"),
            ('geo-zugmap-luftbild', "ZugMap Luftbild"),
            ('geo-zugmap-ortsplan', "ZugMap Ortsplan"),
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
            ('AG', 'Aargau'),
            ('AR', 'Appenzell Ausserrhoden'),
            ('AI', 'Appenzell Innerrhoden'),
            ('BL', 'Basel-Landschaft'),
            ('BS', 'Basel-Stadt'),
            ('BE', 'Berne'),
            ('FR', 'Fribourg'),
            ('GE', 'Geneva'),
            ('GL', 'Glarus'),
            ('GR', 'Grisons'),
            ('JU', 'Jura'),
            ('LU', 'Lucerne'),
            ('NE', 'Neuchâtel'),
            ('NW', 'Nidwalden'),
            ('OW', 'Obwalden'),
            ('SH', 'Schaffhausen'),
            ('SZ', 'Schwyz'),
            ('SO', 'Solothurn'),
            ('SG', 'St. Gallen'),
            ('TG', 'Thurgau'),
            ('TI', 'Ticino'),
            ('UR', 'Uri'),
            ('VS', 'Valais'),
            ('VD', 'Vaud'),
            ('ZG', 'Zug'),
            ('ZH', 'Zürich'),
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

    def validate_other_holidays(self, field):
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

    @property
    def holiday_settings(self):

        def parse_line(line):
            date, desc = line.strip().split('-')
            day, month = date.split('.')

            return int(month), int(day), desc.strip()

        return {
            'cantons': self.cantonal_holidays.data,
            'other': (
                parse_line(l) for l in self.other_holidays.data.splitlines()
                if l.strip()
            )
        }

    @holiday_settings.setter
    def holiday_settings(self, data):
        data = data or {}

        def format_other(d):
            return f'{d[1]:02d}.{d[0]:02d} - {d[2]}'

        self.cantonal_holidays.data = data.get(
            'cantons', ())

        self.other_holidays.data = '\n'.join(
            format_other(d) for d in data.get('other', ()))

    def populate_obj(self, model):
        super().populate_obj(model)
        model.holiday_settings = self.holiday_settings

    def process_obj(self, model):
        super().process_obj(model)
        self.holiday_settings = model.holiday_settings
