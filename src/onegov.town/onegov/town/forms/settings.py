from onegov.form import Form
from wtforms import HiddenField, StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField, URLField
from wtforms_components import ColorField
from onegov.gis import CoordinatesField
from onegov.town import _
from onegov.town.theme import user_options


class SettingsForm(Form):
    """ Defines the settings form for onegov town. """

    name = StringField(
        label=_("Name"),
        validators=[validators.InputRequired()],
        fieldset=_("General")
    )
    logo_url = StringField(
        label=_("Logo"),
        description=_("URL pointing to the logo"),
        fieldset=_("General"),
        render_kw={'class_': 'image-url'}
    )
    reply_to = EmailField(
        _("E-Mail Reply Address"), [validators.InputRequired()],
        description=_("Replies to automated e-mails go to this address."),
        fieldset=_("General")
    )
    primary_color = ColorField(
        label=_("Primary Color"),
        fieldset=_("General")
    )
    contact = TextAreaField(
        label=_("Contact"),
        description=_("The address and phone number of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("General")
    )
    contact_url = URLField(
        label=_("Contact Page"),
        description=_("URL pointing to a contact page"),
        fieldset=_("General"),
        render_kw={'class_': 'internal-url'}
    )
    opening_hours = TextAreaField(
        label=_("Opening Hours"),
        description=_("The opening hours of the municipality"),
        render_kw={'rows': 8},
        fieldset=_("General")
    )
    opening_hours_url = URLField(
        label=_("Opening Hours Page"),
        description=_("URL pointing to an opening hours page"),
        fieldset=_("General"),
        render_kw={'class_': 'internal-url'}
    )
    facebook_url = URLField(
        label=_("Facebook"),
        description=_("URL pointing to the facebook site"),
        fieldset=_("General")
    )
    twitter_url = URLField(
        label=_("Twitter"),
        description=_("URL pointing to the twitter site"),
        fieldset=_("General")
    )
    homepage_image_1 = StringField(
        label=_("Homepage Image #1"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_2 = StringField(
        label=_("Homepage Image #2"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_3 = StringField(
        label=_("Homepage Image #3"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_4 = StringField(
        label=_("Homepage Image #4"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_5 = StringField(
        label=_("Homepage Image #5"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    homepage_image_6 = StringField(
        label=_("Homepage Image #6"),
        render_kw={'class_': 'image-url'},
        fieldset=_("Homepage")
    )
    online_counter_label = StringField(
        label=_("Online Counter Label"),
        description=_("Forms and applications"),
        fieldset=_("Homepage")
    )
    reservations_label = StringField(
        label=_("Reservations Label"),
        description=_("Daypasses and rooms"),
        fieldset=_("Homepage")
    )
    sbb_daypass_label = StringField(
        label=_("SBB Daypass Label"),
        description=_("Generalabonnement for Towns"),
        fieldset=_("Homepage")
    )
    default_map_view = CoordinatesField(
        label=_("The default map view. This should show the whole town"),
        render_kw={
            'data-map-type': 'crosshair'
        },
        fieldset=_("Maps")
    )
    analytics_code = TextAreaField(
        label=_("Analytics Code"),
        description=_("JavaScript for web statistics support"),
        render_kw={'rows': 10},
        fieldset=_("Advanced")
    )

    # the footer height is determined by javascript, see town.scss and
    # common.js for more information (search for footer)
    footer_height = HiddenField()

    @property
    def theme_options(self):
        try:
            primary_color = self.primary_color.data.get_hex()
        except AttributeError:
            primary_color = user_options['primary-color']

        options = {
            'primary-color': primary_color,
            'footer-height': self.footer_height.data
        }

        # set the images only if provided
        for i in range(1, 7):
            image = getattr(self, 'homepage_image_{}'.format(i)).data

            if not image:
                continue

            options['tile-image-{}'.format(i)] = '"{}"'.format(image)

        # override the options using the default vaules if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        return options

    @theme_options.setter
    def theme_options(self, options):
        self.primary_color.data = options.get('primary-color')
        self.footer_height.data = options.get('footer-height')
        self.homepage_image_1.data = options.get('tile-image-1', '').strip('"')
        self.homepage_image_2.data = options.get('tile-image-2', '').strip('"')
        self.homepage_image_3.data = options.get('tile-image-3', '').strip('"')
        self.homepage_image_4.data = options.get('tile-image-4', '').strip('"')
        self.homepage_image_5.data = options.get('tile-image-5', '').strip('"')
        self.homepage_image_6.data = options.get('tile-image-6', '').strip('"')
